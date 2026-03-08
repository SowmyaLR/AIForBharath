import os
import requests
import json
import logging
import re
from datetime import datetime
import uuid
import time
from typing import Dict, Any, List, Optional
from .triage_service import TriageRecord

logger = logging.getLogger(__name__)

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
APP_ENV = os.getenv("APP_ENV", "dev")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
SAGEMAKER_MEDGEMMA_ENDPOINT = os.getenv("SAGEMAKER_MEDGEMMA_ENDPOINT", "")
SAGEMAKER_ASYNC_BUCKET = os.getenv("SAGEMAKER_ASYNC_BUCKET", "")
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
        """Robustly extracts and cleans the first valid JSON object from LLM output."""
        if not text:
            raise ValueError("Empty response from AI")

        # 1. Basic cleaning
        text = text.strip()
        
        # 2. Advanced cleaning: 
        # A. Remove non-printable control characters (0x00-0x1F) that break json.loads
        # We preserve \n (0x0A), \r (0x0D), and \t (0x09) but escape them if they are inside strings 
        # (or just strip them if they are unintended).
        # Simplest approach: remove all control characters except \n, \r, \t
        text = "".join(ch for ch in text if ch >= ' ' or ch in '\n\r\t')
        
        # B. Remove comments and trailing commas which break standard json.loads
        # Remove single-line comments //
        text = re.sub(r'//.*?\n', '\n', text)
        # Remove multi-line comments /* */
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
        # Remove trailing commas in objects/arrays
        text = re.sub(r',\s*([\]}])', r'\1', text)

        # 3. Use outermost { } as the search boundary
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        
        if start_idx == -1 or end_idx == -1:
            logger.error(f"[EHR] No JSON object found in text: {text[:500]}...")
            raise ValueError("No valid JSON structure found in response")

        candidate = text[start_idx:end_idx+1]
        
        # 4. Final attempt to parse
        try:
            # Clean possible markdown fences inside our candidate
            clean_candidate = candidate.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_candidate)
        except json.JSONDecodeError as e:
            logger.error(f"[EHR] JSON Parse Error at line {e.lineno}, col {e.colno}: {e.msg}")
            # Log the problematic area for debugging
            lines = candidate.splitlines()
            if 0 <= e.lineno-1 < len(lines):
                logger.error(f"[EHR] Problematic line: {lines[e.lineno-1]}")
            
            # Last ditch: try to use re to find anything that looks like a valid JSON block
            # This is a bit risky but can work if the model added text *inside* the braces
            raise ValueError(f"JSON parsing failed: {str(e)}")

    def _call_inference_backend(self, prompt: str, max_tokens: int = 2048) -> str:
        """Dispatch to SageMaker (demo) or Ollama (dev)."""
        if APP_ENV == "demo" and _sm_runtime and SAGEMAKER_MEDGEMMA_ENDPOINT:
            print(f"[EHR] Calling SageMaker Async for FHIR generation: {SAGEMAKER_MEDGEMMA_ENDPOINT}")
            
            # 1. Prepare Payload with Gemma Chat Template
            formatted_prompt = f"<start_of_turn>user\n{prompt}<end_of_turn>\n<start_of_turn>model\n"
            payload = {
                "inputs": formatted_prompt,
                "parameters": {
                    "max_new_tokens": max_tokens, 
                    "temperature": 0.1,
                    "stop": ["<end_of_turn>", "<eos>"]
                }
            }
            
            try:
                request_id = str(uuid.uuid4())
                if not SAGEMAKER_ASYNC_BUCKET:
                    logger.error("SAGEMAKER_ASYNC_BUCKET not set in EHR module")
                    raise ValueError("SAGEMAKER_ASYNC_BUCKET not set")

                input_key = f"fhir-inputs/{request_id}.json"
                input_location = f"s3://{SAGEMAKER_ASYNC_BUCKET}/{input_key}"
                
                _s3.put_object(
                    Bucket=SAGEMAKER_ASYNC_BUCKET,
                    Key=input_key,
                    Body=json.dumps(payload),
                    ContentType="application/json"
                )

                # 2. Start Async Inference
                response = _sm_runtime.invoke_endpoint_async(
                    EndpointName=SAGEMAKER_MEDGEMMA_ENDPOINT,
                    ContentType="application/json",
                    InputLocation=input_location
                )
                
                output_location = response["OutputLocation"]
                output_bucket = output_location.split("/")[2]
                output_key = "/".join(output_location.split("/")[3:])
                
                print(f"[EHR] Async FHIR request submitted. Output will be at: {output_location}")

                # 3. Poll for Result (up to 15 minutes for cold start)
                max_retries = 180 # 180 * 5s = 900s (15 minutes)
                for attempt in range(max_retries):
                    try:
                        resp = _s3.get_object(Bucket=output_bucket, Key=output_key)
                        result = json.loads(resp["Body"].read().decode("utf-8"))
                        
                        # Cleanup input
                        try:
                            _s3.delete_object(Bucket=SAGEMAKER_ASYNC_BUCKET, Key=input_key)
                        except: pass

                        if isinstance(result, list) and result:
                            return result[0].get("generated_text", "")
                        return result.get("generated_text", str(result))
                    except _s3.exceptions.NoSuchKey:
                        if attempt % 6 == 0:
                            print(f"[EHR] Polling for FHIR result... ({attempt * 5}s elapsed)")
                        time.sleep(5)
                
                raise TimeoutError("Asynchronous FHIR generation timed out.")

            except Exception as e:
                print(f"[EHR ERROR] SageMaker Async failed: {e}")
                raise
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
