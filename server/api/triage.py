from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from typing import Optional, List
from services.triage_service import TriageService, TriageRecord, VitalSigns, SOAPNote
from services.ai_service import AudioProcessor, AIServiceError
import os

router = APIRouter(prefix="/triage", tags=["triage"])
triage_service = TriageService()

# In production initialize conditionally or lazily to avoid startup blocking
try:
    ai_processor = AudioProcessor()
except Exception as e:
    print(f"Warning: Failed to init AudioProcessor: {e}")
    ai_processor = None

AUDIO_DIR = "storage/audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

from starlette.concurrency import run_in_threadpool
import asyncio

async def _process_triage_audio_task(triage_id: str, audio_bytes: bytes, language: str):
    """Background task to run the AI pipeline with threadpool offloading"""
    if not ai_processor:
         await triage_service.update_triage_status(triage_id, "failed_ai_init")
         return
         
    try:
        await triage_service.update_triage_status(triage_id, "in_progress")
        
        # 1. Pipeline execution in parallel threads as per prototype
        print(f"DEBUG: Processing Triage {triage_id}. Offloading to threads.")
        
        # Parallel transcription and acoustic analysis
        transcript_task = run_in_threadpool(ai_processor.transcribe, audio_bytes, language)
        anomaly_task = run_in_threadpool(ai_processor.detect_anomalies, audio_bytes)
        
        transcript, anomalies = await asyncio.gather(transcript_task, anomaly_task)
        
        # 2. Reasoning step
        analysis = await run_in_threadpool(ai_processor.generate_soap_note, transcript, anomalies)
        
        # 3. Save results
        record = await triage_service.get_triage(triage_id)
        if record:
            record.transcription = transcript
            record.soap_note = SOAPNote(**analysis.get("soap", {}))
            record.specialty = analysis.get("specialty", "General Medicine")
            record.risk_score = analysis.get("risk_score", 0)
            record.status = "ready_for_review"
            await triage_service.update_triage_status(triage_id, "ready_for_review")
            print(f"[API DEBUG] Triage {triage_id} updated and ready. Specialty: {record.specialty}. Risk: {record.risk_score}")
            print(f"[API DEBUG] SOAP Subjective: {record.soap_note.subjective[:50]}...")
        else:
            print(f"[API DEBUG] Record {triage_id} not found for update!")
            
    except Exception as e:
        print(f"AI Pipeline failed for {triage_id}: {e}")
        await triage_service.update_triage_status(triage_id, "failed")

@router.post("/", response_model=TriageRecord)
async def create_triage(
    background_tasks: BackgroundTasks,
    patient_id: str = Form(...),
    language: str = Form("English"),
    audio: UploadFile = File(...)
):
    """Upload audio for a patient and start triage pipeline"""
    audio_bytes = await audio.read()
    
    # Save file locally (Encrypted in prod)
    file_path = f"{AUDIO_DIR}/{audio.filename}"
    with open(file_path, "wb") as f:
        f.write(audio_bytes)
    
    record = await triage_service.create_triage_record(patient_id, file_path, language)
    
    # Process asynchronously
    background_tasks.add_task(_process_triage_audio_task, record.id, audio_bytes, language)
    
    return record

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

@router.post("/{triage_id}/finalize", response_model=TriageRecord)
async def finalize_triage(triage_id: str):
    record = await triage_service.update_triage_status(triage_id, "finalized")
    if not record:
         raise HTTPException(status_code=404, detail="Triage record not found")
    return record
