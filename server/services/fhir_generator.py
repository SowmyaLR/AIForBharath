import logging
import uuid
import json
import os
import requests
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
from services.inference_provider import InferenceProvider
from models.triage import TriageRecord

# Set up logging
logger = logging.getLogger(__name__)

class FHIRGenerator(ABC):
    @abstractmethod
    async def generate_bundle(self, record: TriageRecord) -> Dict[str, Any]:
        pass

class DeterministicFHIRGenerator(FHIRGenerator):
    """Fallback generator that follows strict FHIR R4 rules without AI variability."""
    
    async def generate_bundle(self, record: TriageRecord) -> Dict[str, Any]:
        logger.info(f"Generating deterministic FHIR bundle for patient: {record.patient_id}")
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

        # 1. Composition
        composition = {
            "fullUrl": f"urn:uuid:{str(uuid.uuid4())}",
            "resource": {
                "resourceType": "Composition",
                "id": str(uuid.uuid4()),
                "status": "final",
                "type": {
                    "coding": [{"system": "http://loinc.org", "code": "11506-3", "display": "Progress note"}]
                },
                "subject": {"reference": patient_ref},
                "date": timestamp,
                "author": [{"display": "VaidyaSaarathi AI Triage"}],
                "title": f"Triage Summary - {record.patient_id}",
                "section": []
            }
        }

        if record.soap_note:
            for title, text in [
                ("Subjective", record.soap_note.subjective),
                ("Objective", record.soap_note.objective),
                ("Assessment", record.soap_note.assessment),
                ("Plan", record.soap_note.plan)
            ]:
                composition["resource"]["section"].append({
                    "title": title,
                    "text": {"status": "generated", "div": f"<div xmlns=\"http://www.w3.org/1999/xhtml\">{text}</div>"}
                })

        bundle["entry"].append(composition)

        # 2. Observations (Vitals)
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

class MedGemmaFHIRGenerator(FHIRGenerator):
    """AI-powered generator using MedGemma for rich clinical semantic mapping."""
    
    def __init__(self, inference_provider: InferenceProvider):
        self.inference = inference_provider

    async def generate_bundle(self, record: TriageRecord) -> Dict[str, Any]:
        logger.info(f"Requesting MedGemma AI for FHIR R4 generation (Patient: {record.patient_id})")
        
        prompt = self._build_prompt(record)
        
        try:
            # MedGemma typically needs more tokens for a full FHIR Bundle JSON
            raw_text = self.inference.invoke(prompt, max_tokens=2048)
            
            # Extract JSON and patch timestamps
            start_idx, end_idx = raw_text.find('{'), raw_text.rfind('}')
            if start_idx != -1 and end_idx != -1:
                bundle = json.loads(raw_text[start_idx:end_idx+1])
                return self._patch_timestamps(bundle)
            raise ValueError("Missing JSON in AI response")
        except Exception as e:
            logger.error(f"MedGemma FHIR generation failed: {str(e)}")
            raise

    def _build_prompt(self, record: TriageRecord) -> str:
        vitals_str = json.dumps(record.vitals.dict(), indent=2) if record.vitals else "None"
        soap_str = json.dumps(record.soap_note.dict(), indent=2) if record.soap_note else "None"
        
        return f"""
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

    def _patch_timestamps(self, obj: Any) -> Any:
        now = datetime.utcnow().isoformat() + "Z"
        keys = {"date", "dateTime", "effectiveDateTime", "timestamp", "issued", "authored"}
        if isinstance(obj, dict):
            return {k: (now if k in keys and isinstance(v, str) else self._patch_timestamps(v)) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._patch_timestamps(item) for item in obj]
        return obj
