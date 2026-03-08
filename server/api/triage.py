from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, Header
from typing import Optional, List
import datetime
import os
import json
import logging
import time
from services.triage_service import get_triage_service, TriageRecord, VitalSigns, SOAPNote
from services.ai_service import AudioProcessor, AIServiceError

logger = logging.getLogger(__name__)

APP_ENV = os.getenv("APP_ENV", "dev")
AUDIO_BUCKET = os.getenv("AUDIO_S3_BUCKET", "")
AUDIO_DIR = "storage/audio"
MAX_AUDIO_BYTES = 10 * 1024 * 1024  # 10 MB hard limit
os.makedirs(AUDIO_DIR, exist_ok=True)

router = APIRouter(prefix="/triage", tags=["triage"])
triage_service = get_triage_service()

# Initialize AI processor at startup
try:
    ai_processor = AudioProcessor()
except Exception as e:
    logger.warning(json.dumps({"event": "ai_processor_init_failed", "error": str(e)}))
    ai_processor = None

from starlette.concurrency import run_in_threadpool
import asyncio


def _calculate_preliminary_zone(vitals: Optional[VitalSigns]) -> str:
    """
    Deterministic vitals-only triage zone.
    Called after Whisper+HeAR complete if MedGemma hasn't responded within 10 seconds.
    Returns a zone string — same format as AI-derived triage_tier.
    """
    if not vitals:
        return "ROUTINE"

    bp_sys = vitals.blood_pressure_systolic
    hr = vitals.heart_rate
    spo2 = vitals.oxygen_saturation
    temp = vitals.temperature

    if bp_sys >= 180 or bp_sys < 70 or hr > 150 or hr < 40 or spo2 < 88 or temp >= 40.0:
        return "EMERGENCY"
    elif bp_sys >= 160 or hr > 120 or spo2 < 92 or temp >= 38.5:
        return "URGENT"
    elif bp_sys >= 140 or hr > 100 or spo2 < 95:
        return "SEMI_URGENT"
    else:
        return "ROUTINE"


def upload_audio(audio_bytes: bytes, filename: str) -> str:
    """Upload audio to S3 (demo) or save locally (dev). Returns the file URI/path."""
    if APP_ENV == "demo" and AUDIO_BUCKET:
        try:
            import boto3
            region = os.getenv("AWS_REGION", "ap-south-1")
            s3 = boto3.client("s3", region_name=region)
            s3_key = f"triage-audio/{filename}"
            s3.put_object(Bucket=AUDIO_BUCKET, Key=s3_key, Body=audio_bytes)
            uri = f"s3://{AUDIO_BUCKET}/{s3_key}"
            logger.info(json.dumps({"event": "audio_uploaded_s3", "uri": uri}))
            return uri
        except Exception as e:
            logger.warning(json.dumps({"event": "s3_upload_failed_fallback_local", "error": str(e)}))
    file_path = f"{AUDIO_DIR}/{filename}"
    with open(file_path, "wb") as f:
        f.write(audio_bytes)
    return file_path


async def _process_triage_audio_task(triage_id: str, audio_bytes: bytes, language: str):
    """
    Background task: run the full AI pipeline.

    Phase 1 (parallel):  Whisper ASR + HeAR bioacoustic analysis
    Vitals fallback:      If MedGemma takes > 10s, write preliminary_zone from vitals only
    Phase 2 (sequential): MedGemma SOAP note + triage zone
    """
    if not ai_processor:
        await triage_service.update_triage_status(triage_id, "failed")
        logger.error(json.dumps({"event": "pipeline_failed", "triage_id": triage_id, "reason": "ai_processor_not_initialized"}))
        return

    try:
        await triage_service.update_triage_status(triage_id, "in_progress")
        pipeline_start = time.time()

        # ── Phase 1: Serialized Whisper + HeAR (Optimized for 4 vCPU throughput) ──
        # Running these serially prevents CPU thrashing and actually lowers wall-clock time
        t_p1_start = time.time()
        
        # 1. Whisper first (High CPU)
        transcript = await run_in_threadpool(ai_processor.transcribe, audio_bytes, language)
        
        # 2. HeAR second (High CPU/Memory)
        anomalies = await run_in_threadpool(ai_processor.detect_anomalies, audio_bytes)
        
        t_p1_end = time.time()
        logger.info(json.dumps({
            "event": "asr_acoustic_complete",
            "triage_id": triage_id,
            "latency_s": round(t_p1_end - t_p1_start, 2)
        }))

        # ── Fetch record for vitals (for fallback and MedGemma context) ───────
        record = await triage_service.get_triage(triage_id)
        vitals_dict = record.vitals.dict() if (record and record.vitals) else None

        # ── Phase 2: MedGemma with 10-second vitals-only fallback ────────────
        t_soap_start = time.time()
        fallback_written = False

        async def _medgemma_with_fallback():
            nonlocal fallback_written
            # Run MedGemma in a thread — shield() prevents wait_for from cancelling it on timeout
            medgemma_task = asyncio.ensure_future(
                run_in_threadpool(ai_processor.generate_soap_note, transcript, anomalies, vitals_dict, record.patient_age)
            )
            try:
                # asyncio.shield() keeps medgemma_task alive even if wait_for times out
                analysis = await asyncio.wait_for(asyncio.shield(medgemma_task), timeout=10.0)
                return analysis
            except asyncio.TimeoutError:
                # Write vitals-only guardrail zone while MedGemma continues in background
                if record and record.vitals:
                    prelim = _calculate_preliminary_zone(record.vitals)
                    try:
                        await _update_preliminary_zone(triage_id, prelim)
                        fallback_written = True
                        logger.info(json.dumps({
                            "event": "preliminary_zone_written",
                            "triage_id": triage_id,
                            "preliminary_zone": prelim
                        }))
                    except Exception:
                        pass
                # medgemma_task is still running (not cancelled) — wait for it to finish
                return await medgemma_task

        analysis = await _medgemma_with_fallback()

        t_soap_end = time.time()
        logger.info(json.dumps({
            "event": "soap_complete",
            "triage_id": triage_id,
            "latency_s": round(t_soap_end - t_soap_start, 2),
            "fallback_was_shown": fallback_written
        }))

        # ── Write final results to DynamoDB ───────────────────────────────────
        record = await triage_service.get_triage(triage_id)
        if record:
            record.transcription = transcript
            record.soap_note = SOAPNote(**analysis.get("soap", {}))
            record.specialty = analysis.get("specialty", "General Medicine")
            record.risk_score = analysis.get("risk_score", 0)
            record.triage_tier = analysis.get("triage_tier", "ROUTINE")
            record.preliminary_zone = None  # clear fallback — final zone is now set
            record.status = "ready_for_review"
            # save_triage_record() does a full put_item — persists ALL fields, not just status
            await triage_service.save_triage_record(record)

            total = round(time.time() - pipeline_start, 2)
            p1_time = round(t_p1_end - t_p1_start, 2)
            soap_time = round(t_soap_end - t_soap_start, 2)

            # ── PERFORMANCE SUMMARY (for comparison) ──────────────────────────
            print(
                f"\n{'='*50}\n"
                f"  TRIAGE PERFORMANCE SUMMARY\n"
                f"{'─'*50}\n"
                f"  Triage ID        : {triage_id}\n"
                f"  Phase 1 (W+H)    : {p1_time}s\n"
                f"  Phase 2 (Gemma)  : {soap_time}s\n"
                f"  Total Latency    : {total}s\n"
                f"  Final Tier       : {record.triage_tier}\n"
                f"{'='*50}\n"
            )

            logger.info(json.dumps({
                "event": "triage_pipeline_complete",
                "triage_id": triage_id,
                "total_latency_s": total,
                "p1_latency_s": p1_time,
                "soap_latency_s": soap_time,
                "zone": record.triage_tier,
                "specialty": record.specialty
            }))

    except Exception as e:
        logger.error(json.dumps({
            "event": "pipeline_failed",
            "triage_id": triage_id,
            "error": str(e)
        }))
        await triage_service.update_triage_status(triage_id, "failed")
        # Write a user-facing error message so the frontend poll has something to show
        try:
            await triage_service.update_soap_note(triage_id, SOAPNote(
                subjective="AI analysis could not be completed. Your recording and vitals are saved. Please retry or contact support.",
                objective="",
                assessment="Analysis failed",
                plan="Please retry the submission or inform clinical staff."
            ))
        except Exception:
            pass  # Best-effort; do not mask the original error


async def _update_preliminary_zone(triage_id: str, zone: str):
    """Write preliminary vitals-only zone to DynamoDB without changing overall status."""
    import boto3
    region = os.getenv("AWS_REGION", "ap-south-1")
    table_name = os.getenv("DYNAMODB_TRIAGE_TABLE", "")
    if APP_ENV == "demo" and table_name:
        ddb = boto3.resource("dynamodb", region_name=region)
        table = ddb.Table(table_name)
        table.update_item(
            Key={"id": triage_id},
            UpdateExpression="SET preliminary_zone = :z, updated_at = :u",
            ExpressionAttributeValues={
                ":z": zone,
                ":u": datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z')
            }
        )
    else:
        # In-memory fallback for dev mode
        record = await triage_service.get_triage(triage_id)
        if record:
            record.preliminary_zone = zone


@router.post("/vitals", response_model=TriageRecord)
async def create_vitals_triage(
    patient_id: str = Form(...),
    patient_age: Optional[int] = Form(None),
    temp: Optional[float] = Form(None),
    bp_sys: Optional[int] = Form(None),
    bp_dia: Optional[int] = Form(None),
    hr: Optional[int] = Form(None),
    rr: Optional[int] = Form(None),
    spo2: Optional[int] = Form(None),
    x_idempotency_key: Optional[str] = Header(None)
):
    """Step 1: Create a triage record with vitals only. Returns immediate first-aid if abnormal."""
    # 1. Idempotency Check
    if x_idempotency_key:
        existing = await triage_service.get_by_idempotency_key(x_idempotency_key)
        if existing: return existing

    # 2. Build Vitals
    vitals = VitalSigns(
        temperature=temp or 37.0,
        blood_pressure_systolic=bp_sys or 120,
        blood_pressure_diastolic=bp_dia or 80,
        heart_rate=hr or 72,
        respiratory_rate=rr or 16,
        oxygen_saturation=spo2 or 98,
        recorded_at=datetime.datetime.now(datetime.timezone.utc),
        recorded_by="Nurse_Dashboard"
    )

    # 3. Create Record
    record = await triage_service.create_triage_record(
        patient_id=patient_id, 
        audio_file_path="", 
        language="English", 
        vitals=vitals,
        idempotency_key=x_idempotency_key,
        patient_age=patient_age
    )

    # 4. Fast-Path Check
    if ai_processor:
        t_vitals_start = time.time()
        vitals_dict = vitals.model_dump()
        if ai_processor.is_vitals_abnormal(vitals_dict):
            record.vitals_status = "ABNORMAL"
            precautions = await run_in_threadpool(ai_processor.get_vitals_precautions, vitals_dict, patient_age)
            record.preliminary_precautions = precautions
            await triage_service.save_triage_record(record)
        
        t_vitals_end = time.time()
        logger.info(json.dumps({
            "event": "vitals_triage_complete",
            "triage_id": record.id,
            "latency_s": round(t_vitals_end - t_vitals_start, 4),
            "status": record.vitals_status
        }))
        print(f"[LATENCY] Stage 1 (Vitals): {round(t_vitals_end - t_vitals_start, 2)}s")
    
    return record


@router.post("/audio/{triage_id}", response_model=TriageRecord)
async def upload_triage_audio(
    triage_id: str,
    background_tasks: BackgroundTasks,
    audio: UploadFile = File(...),
    language: str = Form("English")
):
    """Step 2: Upload audio for an existing triage record and start AI processing in background."""
    record = await triage_service.get_triage(triage_id)
    if not record:
        raise HTTPException(status_code=404, detail="Triage record not found")

    audio_bytes = await audio.read()
    if len(audio_bytes) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="Audio file too large")

    # 1. Upload audio
    audio_uri = upload_audio(audio_bytes, audio.filename)
    record.audio_file_url = audio_uri
    record.language = language
    record.status = "in_progress"
    await triage_service.save_triage_record(record)

    # 2. Start AI Pipeline (Background)
    background_tasks.add_task(_process_triage_audio_task, record.id, audio_bytes, language)
    
    return record


@router.post("/", response_model=TriageRecord)
async def create_triage(
    background_tasks: BackgroundTasks,
    patient_id: str = Form(...),
    language: str = Form("English"),
    audio: UploadFile = File(...),
    temp: Optional[float] = Form(None),
    bp_sys: Optional[int] = Form(None),
    bp_dia: Optional[int] = Form(None),
    hr: Optional[int] = Form(None),
    rr: Optional[int] = Form(None),
    spo2: Optional[int] = Form(None),
    patient_age: Optional[int] = Form(None),
    x_idempotency_key: Optional[str] = Header(None)
):
    """Legacy One-Shot API (kept for backward compatibility)."""
    # Simply call the new split logic internally
    record = await create_vitals_triage(
        patient_id=patient_id, patient_age=patient_age,
        temp=temp, bp_sys=bp_sys, bp_dia=bp_dia, hr=hr, rr=rr, spo2=spo2,
        x_idempotency_key=x_idempotency_key
    )
    
    return await upload_triage_audio(
        triage_id=record.id,
        background_tasks=background_tasks,
        audio=audio,
        language=language
    )


@router.get("/queue", response_model=List[TriageRecord])
async def get_queue(specialty: Optional[str] = None):
    return await triage_service.get_triage_queue(specialty)


@router.get("/{triage_id}", response_model=TriageRecord)
async def get_triage(triage_id: str):
    record = await triage_service.get_triage(triage_id)
    if not record:
        raise HTTPException(status_code=404, detail="Triage record not found")
    return record


@router.post("/{triage_id}/vitals", response_model=TriageRecord)
async def add_vitals(triage_id: str, vitals: VitalSigns):
    record = await triage_service.add_vitals(triage_id, vitals)
    if not record:
        raise HTTPException(status_code=404, detail="Triage record not found")
    return record


@router.post("/{triage_id}/soap", response_model=TriageRecord)
async def update_soap(triage_id: str, soap_note: SOAPNote):
    record = await triage_service.update_soap_note(triage_id, soap_note)
    if not record:
        raise HTTPException(status_code=404, detail="Triage record not found or already finalized")
    return record


@router.post("/{triage_id}/finalize", response_model=TriageRecord)
async def finalize_triage(triage_id: str):
    record = await triage_service.update_triage_status(triage_id, "finalized")
    if not record:
        raise HTTPException(status_code=404, detail="Triage record not found")
    return record


@router.post("/{triage_id}/seen", response_model=TriageRecord)
async def mark_as_seen(triage_id: str):
    record = await triage_service.mark_as_seen(triage_id)
    if not record:
        raise HTTPException(status_code=404, detail="Triage record not found")
    return record


from services.ehr_service import ehr_service

async def _process_ehr_export_task(triage_id: str):
    """Background task to run FHIR generation and export."""
    try:
        print(f"[EHR DEBUG] Starting background export task for: {triage_id}")
        record = await triage_service.get_triage(triage_id)
        if not record:
            print(f"[EHR ERROR] Triage record {triage_id} not found for export.")
            return

        logger.info(json.dumps({"event": "ehr_export_started", "triage_id": triage_id}))
        success = await ehr_service.export_to_ehr(record)
        if success:
            await triage_service.update_triage_status(triage_id, "exported")
            logger.info(json.dumps({"event": "ehr_export_success", "triage_id": triage_id}))
            print(f"[EHR SUCCESS] Triage {triage_id} exported to FHIR.")
        else:
            logger.error(json.dumps({"event": "ehr_export_failed", "triage_id": triage_id}))
            print(f"[EHR ERROR] Export failed for triage {triage_id}.")
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(json.dumps({"event": "ehr_export_error", "triage_id": triage_id, "error": str(e)}))
        print(f"[EHR CRITICAL ERROR] {str(e)}")


@router.post("/{triage_id}/export")
async def export_triage(triage_id: str, background_tasks: BackgroundTasks):
    print("\n" + "="*50)
    print(f"[EHR API] >>> RECEIVED EXPORT REQUEST FOR: {triage_id}")
    print("="*50)
    
    try:
        record = await triage_service.get_triage(triage_id)
        if not record:
            print(f"[EHR API ERROR] Triage {triage_id} NOT FOUND in DB.")
            raise HTTPException(status_code=404, detail="Triage record not found")
        
        print(f"[EHR API] Current Record Status: {record.status}")
        
        # Relax status check for debugging: Allow 'finalized' or 'exported'
        valid_statuses = ["finalized", "exported"]
        if record.status not in valid_statuses:
            print(f"[EHR API REJECTED] Triage {triage_id} status is '{record.status}'. Must be in {valid_statuses}")
            raise HTTPException(status_code=400, detail=f"Triage status '{record.status}' is not eligible for export.")

        print(f"[EHR API] Queueing background task _process_ehr_export_task...")
        background_tasks.add_task(_process_ehr_export_task, triage_id)
        return {"status": "accepted", "message": "EHR Export started in background"}
    except Exception as e:
        print(f"[EHR API CRITICAL] Exception during export setup: {str(e)}")
        raise
