import os
import requests
import json
import logging
from datetime import datetime
import uuid
from typing import Dict, Any, List, Optional
from .triage_service import TriageRecord

logger = logging.getLogger(__name__)

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
APP_ENV = os.getenv("APP_ENV", "dev")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
SAGEMAKER_MEDGEMMA_ENDPOINT = os.getenv("SAGEMAKER_MEDGEMMA_ENDPOINT", "")
FHIR_S3_BUCKET = os.getenv("FHIR_S3_BUCKET", "")

if APP_ENV == "demo":
    try:
        import boto3
        from botocore.config import Config
        _sm_config = Config(read_timeout=60, connect_timeout=5, retries={"max_attempts": 2})
        _sm_runtime = boto3.client("sagemaker-runtime", region_name=AWS_REGION, config=_sm_config)
        _s3 = boto3.client("s3", region_name=AWS_REGION)
        logger.info(json.dumps({"event": "ehr_demo_mode_init", "endpoint": SAGEMAKER_MEDGEMMA_ENDPOINT}))
    except ImportError:
        _sm_runtime = None
        _s3 = None
else:
    _sm_runtime = None
    _s3 = None

# In-memory fallback for dev mode
EXPORTED_RECORDS: List[Dict[str, Any]] = []

class EHRService:
    def __init__(self):
        pass

    async def get_exported_records(self) -> List[Dict[str, Any]]:
        """Returns all exported FHIR records. In demo mode, reads from S3."""
        if APP_ENV == "demo" and _s3 and FHIR_S3_BUCKET:
            try:
                resp = _s3.list_objects_v2(Bucket=FHIR_S3_BUCKET, Prefix="bundles/")
                records = []
                for obj in resp.get("Contents", []):
                    body = _s3.get_object(Bucket=FHIR_S3_BUCKET, Key=obj["Key"])
                    records.append(json.loads(body["Body"].read()))
                return records
            except Exception as e:
                logger.warning(json.dumps({"event": "fhir_s3_list_failed", "error": str(e)}))
        return EXPORTED_RECORDS

    async def generate_fhir_bundle(self, record: TriageRecord) -> Dict[str, Any]:
        """
        Attempts to generate a FHIR R4 Bundle using MedGemma.
        Falls back to a deterministic generator if AI fails.
        """
        try:
            return await self.generate_fhir_with_medgemma(record)
        except Exception as e:
            print(f"[EHR WARNING] MedGemma FHIR generation failed: {e}. Falling back to deterministic generator.")
            return self.generate_fhir_bundle_deterministic(record)

    async def generate_fhir_with_medgemma(self, record: TriageRecord) -> Dict[str, Any]:
        """Uses MedGemma via SageMaker/Ollama to generate a rich FHIR R4 Bundle"""
        print(f"[EHR DEBUG] Requesting MedGemma for FHIR R4 generation (Patient: {record.patient_id})...")
        
        vitals_list = []
        if record.vitals:
            v = record.vitals
            vitals_list.append(f"Temperature: {v.temperature}C")
            vitals_list.append(f"BP: {v.blood_pressure_systolic}/{v.blood_pressure_diastolic}")
            vitals_list.append(f"Heart Rate: {v.heart_rate} bpm")
            vitals_list.append(f"SpO2: {v.oxygen_saturation}%")
            vitals_list.append(f"Resp Rate: {v.respiratory_rate} bpm")
        
        age_info = f"Age: {record.patient_age}" if record.patient_age else "Age: Not provided"
        vitals_str = "\n".join(vitals_list) if vitals_list else "Not provided"

        soap_str = "No SOAP note available"
        if record.soap_note:
            soap_str = f"Subjective: {record.soap_note.subjective}\nObjective: {record.soap_note.objective}\nAssessment: {record.soap_note.assessment}\nPlan: {record.soap_note.plan}"

        prompt = f"""
        You are a highly specialized clinical informatics AI.
        Convert the following Clinical SOAP Note and Patient Vitals into a valid FHIR R4 Bundle JSON.
        
        INPUT DATA:
        - Hospital ID: {record.patient_id}
        - Patient {age_info}
        - Clinical SOAP Note:
        {soap_str}
        - Patient Vitals:
        {vitals_str}

        REQUIREMENTS:
        1. Output ONLY a valid FHIR R4 Bundle JSON object.
        2. No markdown, no pre-text, no post-text.
        3. Include a 'Composition' resource for the SOAP note content.
        4. Include 'Observation' resources for each vital sign using standard LOINC codes.
        5. Use a 'Patient' resource for the Hospital ID.
        6. Ensure 'Composition.subject' points to the 'Patient' resource.
        7. The 'Composition' should be the first entry in the Bundle.
        8. Set status to 'final' for all clinical resources.

        Generate the FHIR R4 Bundle JSON now:
        """

        from fastapi.concurrency import run_in_threadpool
        raw_text = await run_in_threadpool(self._call_inference_backend, prompt, 2048)
        
        try:
            fhir_bundle = self._extract_json_robust(raw_text)
            # ── Patch all date/timestamp fields with the real current time ──
            fhir_bundle = self._patch_fhir_timestamps(fhir_bundle)
            print(f"[EHR DEBUG] MedGemma successfully generated FHIR Bundle for {record.patient_id}")
            return fhir_bundle
        except Exception as e:
            print(f"[EHR WARNING] MedGemma FHIR extraction failed: {e}. Falling back to deterministic generator.")
            return self.generate_fhir_bundle_deterministic(record)

    def _extract_json_robust(self, text: str) -> Dict[str, Any]:
        """Robustly extracts the first valid JSON object from LLM output."""
        if not text:
            raise ValueError("Empty response from AI")

        # 1. Try pure parse first
        text = text.strip()
        try:
            return json.loads(text)
        except:
            pass

        # 2. Extract content starting from first '{'
        # Clean control characters (except tab/newline)
        text = "".join(ch for ch in text if ch >= ' ' or ch in '\n\r\t')
        
        start_idx = text.find('{')
        if start_idx == -1:
            raise ValueError("No JSON object starting character '{' found in response")

        # Find all potential closing braces
        end_indices = [i for i, ch in enumerate(text) if ch == '}']
        if not end_indices:
            raise ValueError("No JSON object closing character '}' found in response")

        # 3. Strategy: Try candidates from the absolute last '}' back to the first '{'
        # This handles models that append garbage/redundant braces at the end.
        for end_idx in reversed(end_indices):
            if end_idx <= start_idx:
                break
            
            candidate = text[start_idx:end_idx+1]
            try:
                # Basic cleaning of markdown fences inside the block
                clean_candidate = candidate.replace("```json", "").replace("```", "").strip()
                return json.loads(clean_candidate)
            except json.JSONDecodeError:
                continue

        # 4. If nothing parsed, reveal why the largest block failed
        try:
            largest = text[start_idx:end_indices[-1]+1]
            return json.loads(largest)
        except json.JSONDecodeError as e:
            print(f"[EHR DEBUG] FHIR JSON final parse attempt failed: line {e.lineno}, col {e.colno}: {e.msg}")
            raise ValueError(f"JSON parsing failed: {str(e)}")

    def _call_inference_backend(self, prompt: str, max_tokens: int = 2048) -> str:
        """Dispatch to SageMaker (demo) or Ollama (dev)."""
        if APP_ENV == "demo" and _sm_runtime and SAGEMAKER_MEDGEMMA_ENDPOINT:
            print(f"[EHR] Calling SageMaker for FHIR generation: {SAGEMAKER_MEDGEMMA_ENDPOINT}")
            response = _sm_runtime.invoke_endpoint(
                EndpointName=SAGEMAKER_MEDGEMMA_ENDPOINT,
                ContentType="application/json",
                Body=json.dumps({
                    "inputs": prompt,
                    "parameters": {"max_new_tokens": max_tokens, "temperature": 0.1}
                })
            )
            result = json.loads(response["Body"].read().decode("utf-8"))
            if isinstance(result, list) and result:
                return result[0].get("generated_text", "")
            return result.get("generated_text", str(result))
        else:
            print(f"[EHR] Calling Ollama for FHIR generation")
            response = requests.post(
                f"{OLLAMA_HOST}/api/generate",
                json={
                    "model": "alibayram/medgemma",
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_predict": max_tokens, "temperature": 0.1}
                }
            )
            response.raise_for_status()
            return response.json().get("response", "")


    def _patch_fhir_timestamps(self, obj: Any, now: Optional[str] = None) -> Any:
        """
        Recursively walks a FHIR bundle dict/list and replaces any
        date, dateTime, effectiveDateTime, timestamp, issued, or authored fields
        that look like hardcoded/hallucinated dates with the real UTC now.
        """
        if now is None:
            now = datetime.utcnow().isoformat() + "Z"

        DATE_KEYS = {"date", "dateTime", "effectiveDateTime", "timestamp", "issued", "authored", "start", "end"}

        if isinstance(obj, dict):
            return {
                k: (now if k in DATE_KEYS and isinstance(v, str) else self._patch_fhir_timestamps(v, now))
                for k, v in obj.items()
            }
        elif isinstance(obj, list):
            return [self._patch_fhir_timestamps(item, now) for item in obj]
        return obj

    def generate_fhir_bundle_deterministic(self, record: TriageRecord) -> Dict[str, Any]:
        """
        Generates a FHIR R4 Bundle deterministically (Fallback).
        """
        bundle_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat() + "Z"
        patient_ref = f"Patient/{record.patient_id}"
        
        bundle = {
            "resourceType": "Bundle",
            "id": bundle_id,
            "type": "document",
            "timestamp": timestamp,
            "entry": []
        }

        # Composition (Document Metadata & SOAP Sections)
        composition = {
            "fullUrl": f"urn:uuid:{str(uuid.uuid4())}",
            "resource": {
                "resourceType": "Composition",
                "id": str(uuid.uuid4()),
                "status": "final",
                "type": {
                    "coding": [{
                        "system": "http://loinc.org",
                        "code": "11506-3",
                        "display": "Provider-unspecified Progress note"
                    }]
                },
                "subject": {"reference": patient_ref},
                "date": timestamp,
                "author": [{"display": "VaidyaSaarathi AI Triage System"}],
                "title": f"Triage Summary - {record.patient_id}",
                "section": []
            }
        }

        if record.soap_note:
            sections = [
                ("Subjective", record.soap_note.subjective),
                ("Objective", record.soap_note.objective),
                ("Assessment", record.soap_note.assessment),
                ("Plan", record.soap_note.plan)
            ]
            for title, text in sections:
                composition["resource"]["section"].append({
                    "title": title,
                    "text": {
                        "status": "generated",
                        "div": f"<div xmlns=\"http://www.w3.org/1999/xhtml\">{text}</div>"
                    }
                })

        bundle["entry"].append(composition)

        # Observation Resources (Vital Signs)
        if record.vitals:
            vitals_map = [
                ("8310-5", "Body temperature", record.vitals.temperature, "Cel"),
                ("8867-4", "Heart rate", record.vitals.heart_rate, "/min"),
                ("2708-6", "Oxygen saturation", record.vitals.oxygen_saturation, "%"),
                ("9279-1", "Respiratory rate", record.vitals.respiratory_rate, "/min"),
            ]
            
            for loinc, display, value, unit in vitals_map:
                obs = {
                    "fullUrl": f"urn:uuid:{str(uuid.uuid4())}",
                    "resource": {
                        "resourceType": "Observation",
                        "status": "final",
                        "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "vital-signs"}]}],
                        "code": {"coding": [{"system": "http://loinc.org", "code": loinc, "display": display}]},
                        "subject": {"reference": patient_ref},
                        "valueQuantity": {"value": float(value), "unit": unit, "system": "http://unitsofmeasure.org", "code": unit}
                    }
                }
                bundle["entry"].append(obs)

        return bundle

    async def export_to_ehr(self, record: TriageRecord) -> bool:
        """
        Generates a FHIR R4 bundle and persists it.
        - Demo mode: writes to S3 fhir/bundles/{patient_id}/{uuid}.json (survives ECS restarts)
        - Dev mode: appends to in-memory list
        """
        fhir_data = await self.generate_fhir_bundle(record)
        bundle_id = str(uuid.uuid4())
        export_entry = {
            "patient_id": record.patient_id,
            "exported_at": datetime.utcnow().isoformat() + "Z",
            "fhir_bundle": fhir_data
        }

        if APP_ENV == "demo" and _s3 and FHIR_S3_BUCKET:
            try:
                s3_key = f"bundles/{record.patient_id}/{bundle_id}.json"
                _s3.put_object(
                    Bucket=FHIR_S3_BUCKET,
                    Key=s3_key,
                    Body=json.dumps(export_entry),
                    ContentType="application/json"
                )
                logger.info(json.dumps({
                    "event": "fhir_exported_s3",
                    "patient_id": record.patient_id,
                    "s3_key": s3_key
                }))
            except Exception as e:
                logger.warning(json.dumps({"event": "fhir_s3_write_failed_fallback_memory", "error": str(e)}))
                EXPORTED_RECORDS.append(export_entry)
        else:
            EXPORTED_RECORDS.append(export_entry)
            logger.info(json.dumps({
                "event": "fhir_exported_memory",
                "patient_id": record.patient_id,
                "total_in_memory": len(EXPORTED_RECORDS)
            }))

        return True

ehr_service = EHRService()
