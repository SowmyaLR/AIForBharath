"""
ABDM FHIR R4 Resource Builders.

Constructs individual FHIR resources from extracted document text,
using MedGemma (via Ollama) for rich clinical data extraction,
with a deterministic fallback when AI is unavailable.
"""
import json
import os
import uuid
import requests
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import yaml

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "profiles.yaml")


def _load_config() -> dict:
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_uuid() -> str:
    return str(uuid.uuid4())


# ─── MedGemma helpers ────────────────────────────────────────────────────────

def _call_medgemma(prompt: str, config: dict) -> Optional[str]:
    """Call MedGemma via Ollama. Returns raw response text or None on failure."""
    mg = config.get("medgemma", {})
    if not mg.get("enabled", True):
        return None
    host = mg.get("ollama_host", "http://localhost:11434")
    model = mg.get("model", "alibayram/medgemma")
    try:
        resp = requests.post(
            f"{host}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": mg.get("max_tokens", 3000),
                    "temperature": mg.get("temperature", 0.1),
                }
            },
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json().get("response", "")
    except Exception as e:
        print(f"[FHIR_BUILDER] MedGemma call failed: {e}")
        return None


def _extract_json_from_text(raw: str) -> Optional[dict]:
    """Extract the first valid JSON object from a string."""
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        return json.loads(raw[start:end + 1])
    except Exception:
        return None


def check_medgemma_available(config: Optional[dict] = None) -> bool:
    """Quick liveness check for Ollama."""
    if config is None:
        config = _load_config()
    host = config.get("medgemma", {}).get("ollama_host", "http://localhost:11434")
    try:
        r = requests.get(f"{host}/api/tags", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


# ─── Per-HI-Type Resource Builders ───────────────────────────────────────────

def build_patient_resource(
    patient_name: Optional[str] = None,
    patient_id: Optional[str] = None,
    config: Optional[dict] = None,
) -> dict:
    if config is None:
        config = _load_config()
    pt_system = config["fhir"]["patient_system"]
    rid = _new_uuid()
    resource: dict = {
        "resourceType": "Patient",
        "id": rid,
        "meta": {
            "profile": [f"{config['fhir']['base_url']}/StructureDefinition/Patient"]
        },
        "identifier": [
            {
                "system": pt_system,
                "value": patient_id or f"UNKNOWN-{rid[:8]}"
            }
        ],
        "name": [{"text": patient_name or "Unknown Patient"}],
    }
    return resource


def build_organization_resource(
    org_name: Optional[str] = None,
    config: Optional[dict] = None,
) -> dict:
    if config is None:
        config = _load_config()
    return {
        "resourceType": "Organization",
        "id": _new_uuid(),
        "meta": {
            "profile": [f"{config['fhir']['base_url']}/StructureDefinition/Organization"]
        },
        "name": org_name or "Healthcare Provider",
    }


def build_coverage_resource(
    patient_id_ref: str,
    insurer_name: Optional[str] = None,
    policy_number: Optional[str] = None,
    config: Optional[dict] = None,
) -> dict:
    if config is None:
        config = _load_config()
    return {
        "resourceType": "Coverage",
        "id": _new_uuid(),
        "status": "active",
        "beneficiary": {"reference": f"Patient/{patient_id_ref}"},
        "payor": [{"display": insurer_name or "Unknown Insurer"}],
        "identifier": [
            {
                "system": config["fhir"]["payer_system"],
                "value": policy_number or "UNKNOWN-POLICY",
            }
        ],
    }


def build_composition_resource(
    text: str,
    hi_type_key: str,
    patient_id_ref: str,
    config: Optional[dict] = None,
    use_medgemma: bool = True,
) -> Tuple[dict, str]:
    """
    Build a FHIR Composition resource for Discharge Summary or Clinical Note.
    Returns (resource_dict, extraction_method).
    """
    if config is None:
        config = _load_config()
    hi_meta = config["hi_types"][hi_type_key]
    now = _now_iso()
    method = "deterministic"

    sections = []
    if use_medgemma:
        prompt = f"""
You are a clinical informatics expert. Extract structured information from the following healthcare document.
Return ONLY a JSON object with these fields:
{{
  "title": "<document title>",
  "patient_name": "<name or null>",
  "admission_date": "<ISO date or null>",
  "discharge_date": "<ISO date or null>",
  "diagnosis": "<primary diagnosis text>",
  "procedures": ["<procedure1>", ...],
  "medications": ["<med1>", ...],
  "summary": "<1-2 sentence clinical summary>"
}}

DOCUMENT:
{text[:3000]}

Respond with ONLY the JSON object, no explanation.
"""
        raw = _call_medgemma(prompt, config)
        if raw:
            extracted = _extract_json_from_text(raw)
            if extracted:
                method = "medgemma"
                sections = [
                    {
                        "title": "Clinical Summary",
                        "text": {
                            "status": "generated",
                            "div": f"<div xmlns=\"http://www.w3.org/1999/xhtml\">{extracted.get('summary', text[:500])}</div>"
                        }
                    },
                    {
                        "title": "Diagnosis",
                        "text": {
                            "status": "generated",
                            "div": f"<div xmlns=\"http://www.w3.org/1999/xhtml\">{extracted.get('diagnosis', 'Not extracted')}</div>"
                        }
                    },
                ]

    if not sections:
        sections = [
            {
                "title": "Document Content",
                "text": {
                    "status": "generated",
                    "div": f"<div xmlns=\"http://www.w3.org/1999/xhtml\">{text[:2000].replace('<','&lt;').replace('>','&gt;')}</div>"
                }
            }
        ]

    resource = {
        "resourceType": "Composition",
        "id": _new_uuid(),
        "status": "final",
        "type": {
            "coding": [{
                "system": "http://loinc.org",
                "code": hi_meta["loinc_code"],
                "display": hi_meta["display"],
            }]
        },
        "subject": {"reference": f"Patient/{patient_id_ref}"},
        "date": now,
        "author": [{"display": "NHCX FHIR Converter Service"}],
        "title": hi_meta["display"],
        "section": sections,
    }
    return resource, method


def build_diagnostic_report_resource(
    text: str,
    hi_type_key: str,
    patient_id_ref: str,
    config: Optional[dict] = None,
    use_medgemma: bool = True,
) -> Tuple[dict, str]:
    """Build a DiagnosticReport resource for Lab or Radiology reports."""
    if config is None:
        config = _load_config()
    hi_meta = config["hi_types"][hi_type_key]
    now = _now_iso()
    method = "deterministic"
    observations: List[dict] = []

    if use_medgemma:
        prompt = f"""
You are a clinical lab data extractor. From the following lab/radiology report, extract test results.
Return ONLY a JSON object:
{{
  "report_title": "<title>",
  "specimen_type": "<blood/urine/tissue/etc or null>",
  "result_summary": "<1 sentence summary>",
  "findings": "<key findings text>",
  "tests": [
    {{"name": "<test name>", "value": "<numeric value>", "unit": "<unit>", "reference_range": "<range>", "flag": "<H/L/N>"}}
  ]
}}

DOCUMENT:
{text[:3000]}

Respond with ONLY the JSON object.
"""
        raw = _call_medgemma(prompt, config)
        if raw:
            extracted = _extract_json_from_text(raw)
            if extracted:
                method = "medgemma"
                for test in extracted.get("tests", [])[:10]:
                    obs = {
                        "resourceType": "Observation",
                        "id": _new_uuid(),
                        "status": "final",
                        "code": {"text": test.get("name", "Unknown Test")},
                        "subject": {"reference": f"Patient/{patient_id_ref}"},
                        "valueString": f"{test.get('value', '')} {test.get('unit', '')}".strip(),
                        "referenceRange": [{"text": test.get("reference_range", "")}],
                        "issued": now,
                    }
                    observations.append(obs)

    resource = {
        "resourceType": "DiagnosticReport",
        "id": _new_uuid(),
        "status": "final",
        "category": [
            {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
                    "code": "LAB" if hi_type_key == "lab_report" else "RAD",
                    "display": "Laboratory" if hi_type_key == "lab_report" else "Radiology",
                }]
            }
        ],
        "code": {
            "coding": [{
                "system": "http://loinc.org",
                "code": hi_meta["loinc_code"],
                "display": hi_meta["display"],
            }]
        },
        "subject": {"reference": f"Patient/{patient_id_ref}"},
        "issued": now,
        "result": [{"reference": f"Observation/{obs['id']}"} for obs in observations],
        "conclusion": text[:500] if not observations else None,
        "_embedded_observations": observations,  # kept for bundle assembly
    }
    return resource, method


def build_medication_request_resource(
    text: str,
    patient_id_ref: str,
    config: Optional[dict] = None,
    use_medgemma: bool = True,
) -> Tuple[dict, str]:
    """Build MedicationRequest resources from a prescription document."""
    if config is None:
        config = _load_config()
    now = _now_iso()
    method = "deterministic"
    medications = [{"display": "Medications as per prescription document"}]

    if use_medgemma:
        prompt = f"""
Extract medications from this prescription. Return ONLY JSON:
{{
  "medications": [
    {{"name": "<drug name>", "dose": "<dose>", "frequency": "<frequency>", "duration": "<duration>"}}
  ]
}}

DOCUMENT:
{text[:2000]}

Respond with ONLY the JSON object.
"""
        raw = _call_medgemma(prompt, config)
        if raw:
            extracted = _extract_json_from_text(raw)
            if extracted and extracted.get("medications"):
                method = "medgemma"
                medications = extracted["medications"]

    requests_list = []
    for med in medications[:10]:
        med_name = med.get("name", "Unknown Medication") if isinstance(med, dict) else str(med)
        dose_instruction = ""
        if isinstance(med, dict):
            dose_instruction = f"{med.get('dose', '')} {med.get('frequency', '')} for {med.get('duration', '')}".strip()

        resource = {
            "resourceType": "MedicationRequest",
            "id": _new_uuid(),
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {"text": med_name},
            "subject": {"reference": f"Patient/{patient_id_ref}"},
            "authoredOn": now,
            "dosageInstruction": [{"text": dose_instruction or "As directed"}],
        }
        requests_list.append(resource)

    # Return first as primary, embed all
    primary = requests_list[0] if requests_list else {
        "resourceType": "MedicationRequest",
        "id": _new_uuid(),
        "status": "active",
        "intent": "order",
        "medicationCodeableConcept": {"text": "As per prescription"},
        "subject": {"reference": f"Patient/{patient_id_ref}"},
        "authoredOn": now,
    }
    primary["_all_medications"] = requests_list
    return primary, method


# ─── Dispatcher ───────────────────────────────────────────────────────────────

def build_resource_for_document(
    text: str,
    hi_type_key: str,
    fhir_resource_type: str,
    patient_id_ref: str,
    config: Optional[dict] = None,
    use_medgemma: bool = True,
) -> Tuple[dict, str]:
    """
    Route to the correct builder based on HI type.
    Returns (fhir_resource_dict, extraction_method).
    """
    if config is None:
        config = _load_config()

    if fhir_resource_type == "DiagnosticReport":
        return build_diagnostic_report_resource(text, hi_type_key, patient_id_ref, config, use_medgemma)
    elif fhir_resource_type == "MedicationRequest":
        return build_medication_request_resource(text, patient_id_ref, config, use_medgemma)
    else:
        # Composition (discharge summary, clinical note)
        return build_composition_resource(text, hi_type_key, patient_id_ref, config, use_medgemma)
