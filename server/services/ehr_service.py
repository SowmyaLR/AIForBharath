import os
import requests
import json
from datetime import datetime
import uuid
from typing import Dict, Any, List, Optional
from .triage_service import TriageRecord

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# In-memory store for exported FHIR records (for hackathon demo)
EXPORTED_RECORDS: List[Dict[str, Any]] = []

class EHRService:
    def __init__(self):
        pass

    async def get_exported_records(self) -> List[Dict[str, Any]]:
        """Returns all exported FHIR records for the dashboard"""
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
        """Uses MedGemma via Ollama to generate a rich FHIR R4 Bundle"""
        print(f"[EHR DEBUG] Requesting MedGemma for FHIR R4 generation (Patient: {record.patient_id})...")
        
        vitals_str = ""
        if record.vitals:
            vitals_str = f"Temp: {record.vitals.temperature}, BP: {record.vitals.blood_pressure_systolic}/{record.vitals.blood_pressure_diastolic}, HR: {record.vitals.heart_rate}, SpO2: {record.vitals.oxygen_saturation}, RR: {record.vitals.respiratory_rate}"

        soap_str = "No SOAP note available"
        if record.soap_note:
            soap_str = f"Subjective: {record.soap_note.subjective}\nObjective: {record.soap_note.objective}\nAssessment: {record.soap_note.assessment}\nPlan: {record.soap_note.plan}"

        prompt = f"""
        You are a highly specialized clinical informatics AI.
        Convert the following Clinical SOAP Note and Patient Vitals into a valid FHIR R4 Bundle JSON.
        
        INPUT DATA:
        - Hospital ID: {record.patient_id}
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

        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": "alibayram/medgemma",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": 2048,
                    "temperature": 0.1
                }
            }
        )
        response.raise_for_status()
        result = response.json()
        raw_text = result.get("response", "")
        
        # Extract JSON from potential preamble
        start_idx = raw_text.find('{')
        end_idx = raw_text.rfind('}')
        
        if start_idx != -1 and end_idx != -1:
            json_str = raw_text[start_idx:end_idx+1]
            fhir_bundle = json.loads(json_str)
            # ── Patch all date/timestamp fields with the real current time ──
            fhir_bundle = self._patch_fhir_timestamps(fhir_bundle)
            print(f"[EHR DEBUG] MedGemma successfully generated FHIR Bundle for {record.patient_id}")
            return fhir_bundle
        else:
            raise ValueError("No JSON found in MedGemma response")

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
        Mock EHR Export Implementation.
        """
        fhir_data = await self.generate_fhir_bundle(record)
        
        # Store for the hackathon dashboard
        EXPORTED_RECORDS.append({
            "patient_id": record.patient_id,
            "exported_at": datetime.utcnow().isoformat() + "Z",
            "fhir_bundle": fhir_data
        })
        
        print(f"[EHR DEBUG] Exported FHIR Bundle for Patient {record.patient_id} to internal repository.")
        print(f"[EHR DEBUG] Total records in repository: {len(EXPORTED_RECORDS)}")
        
        return True

ehr_service = EHRService()
