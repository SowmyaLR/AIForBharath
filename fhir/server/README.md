# NHCX FHIR Converter — `nhir/server`

Open-source microservice that ingests healthcare PDFs and converts them into **ABDM FHIR R4 profiles** and **NHCX Claim bundles** for the Indian healthcare ecosystem.

## Features

- **Multi-document ingestion** — upload one or more PDFs per claim
- **Auto HI-type detection** — classifies each PDF as Discharge Summary, Lab Report, Radiology Report, Prescription, or Clinical Note
- **MedGemma-powered extraction** — uses Google's MedGemma LLM (via Ollama) to extract structured clinical data
- **Deterministic fallback** — generates valid FHIR bundles even without AI
- **NHCX Claim Bundle** — outputs a complete FHIR R4 Bundle with a `Claim` resource linking all supporting documents
- **Config-driven** — all NHCX profiles, LOINC codes, and AI settings are in `config/profiles.yaml`

## Quick Start

```bash
# 1. Install dependencies
cd nhir/server
pip install -r requirements.txt

# 2. (Optional) Start Ollama with MedGemma
ollama pull alibayram/medgemma
ollama serve

# 3. Start the server
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

Open the interactive API docs: [http://localhost:8001/docs](http://localhost:8001/docs)

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/health` | Liveness check + MedGemma status |
| `POST` | `/convert/claim` | Multi-PDF to NHCX Claim Bundle |
| `POST` | `/convert/text`  | Plain text to NHCX Claim Bundle |

### POST `/convert/claim` — multipart form

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `files` | PDF file(s) | ✅ | Discharge summary, lab report, etc. |
| `patient_name` | string | ❌ | Patient full name |
| `patient_id` | string | ❌ | ABHA / Health ID |
| `insurer_name` | string | ❌ | Insurance company name |
| `policy_number` | string | ❌ | Policy number |

### Example Response

```json
{
  "success": true,
  "documents_processed": 2,
  "detected_hi_types": ["discharge_summary", "lab_report"],
  "fhir_bundle": {
    "resourceType": "Bundle",
    "type": "collection",
    "meta": { "profile": ["https://nrces.in/ndhm/fhir/r4/StructureDefinition/Bundle"] },
    "entry": [
      { "resource": { "resourceType": "Claim", ... } },
      { "resource": { "resourceType": "Patient", ... } },
      { "resource": { "resourceType": "Composition", ... } },
      { "resource": { "resourceType": "DiagnosticReport", ... } }
    ]
  },
  "metadata": {
    "medgemma_used": true,
    "profile": "https://nrces.in/ndhm/fhir/r4/StructureDefinition/Bundle",
    "use_case": "claim_submission",
    "fhir_version": "4.0.1"
  }
}
```

## Configuration (`config/profiles.yaml`)

Edit `config/profiles.yaml` to:
- Switch between `claim_submission` and `pre_authorisation`
- Adjust NHCX FHIR profile URLs
- Add/modify HI-type detection keywords
- Configure MedGemma model and Ollama host

## Architecture

```
nhir/server/
├── main.py                      ← FastAPI app (port 8001)
├── requirements.txt
├── config/profiles.yaml         ← All profiles & keywords (edit me!)
├── api/convert.py               ← POST /convert/claim, /convert/text, GET /health
├── models/schemas.py            ← Pydantic request/response models
└── services/
    ├── pdf_extractor.py         ← pypdf text extraction
    ├── hi_type_detector.py      ← HI type classification (keyword scoring)
    ├── fhir_builder.py          ← ABDM FHIR R4 resource construction + MedGemma
    └── nhcx_packager.py         ← NHCX Claim Bundle assembly
```

## FHIR Resources Generated

| Document Type | FHIR Resources |
|---|---|
| Discharge Summary | `Composition` (LOINC 18842-5) + `Condition` + `Patient` |
| Lab Report | `DiagnosticReport` (LOINC 11502-2) + `Observation[]` |
| Radiology Report | `DiagnosticReport` (LOINC 18748-4) |
| Clinical Note | `Composition` (LOINC 11488-4) |
| Prescription | `MedicationRequest[]` |

All bundles include: `Claim`, `Patient`, `Coverage`, and per-document clinical resources.

## License

Apache 2.0 — open-source and reusable across HMIS and healthcare applications.
