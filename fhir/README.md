# FHIR NHCX Converter

An open-source microservice and web UI that ingests healthcare documents in PDF format and converts them into **ABDM FHIR R4 profiles** and **NHCX Claim bundles** — built for the Indian healthcare ecosystem (ABDM / NHA).

---

## Overview

```
fhir/
├── client/    ← Web UI — upload PDFs, paste clinical text, view FHIR output
└── server/    ← FastAPI microservice — document processing & FHIR generation
```

The system addresses the **Claim Submission** use case:

> Accept multiple healthcare PDFs (discharge summaries, lab reports, clinical notes), detect their type automatically, extract clinical data using AI, and output a valid NHCX-conformant FHIR Bundle ready for submission to a payer.

---

## Problem Statement

Healthcare providers in India submit claims to insurers with multiple supporting documents — but these are typically unstructured PDFs. Converting them manually into ABDM FHIR profiles for NHCX claim submission is time-consuming and error-prone.

This service automates that conversion pipeline end-to-end.

---

## Key Features

| Feature | Detail |
|---|---|
| **Multi-document ingestion** | Upload up to N PDFs per claim in one request |
| **Auto HI-type detection** | Classifies each PDF: Discharge Summary, Lab Report, Radiology, Prescription, Clinical Note |
| **MedGemma AI extraction** | Uses Google MedGemma LLM to extract structured clinical data from free-text documents |
| **Deterministic fallback** | Generates valid FHIR bundles even when AI is unavailable |
| **NHCX Claim Bundle** | Produces a `Claim` resource with `supportingInfo` linking all uploaded documents |
| **ABDM FHIR R4 profiles** | Resources conform to [NRCeS FHIR profiles](https://nrces.in/ndhm/fhir/r4) |
| **Config-driven** | Switch use case, adjust profiles, add HI types — all via `server/config/profiles.yaml` |
| **Reusable** | Deployable as a standalone microservice or embedded as a Python library |

---

## Supported HI Types

| Document Type | FHIR Resource | LOINC Code |
|---|---|---|
| Discharge Summary | `Composition` | 18842-5 |
| Lab / Pathology Report | `DiagnosticReport` + `Observation[]` | 11502-2 |
| Radiology Report | `DiagnosticReport` | 18748-4 |
| Clinical / OP Note | `Composition` | 11488-4 |
| Prescription | `MedicationRequest[]` | 57833-6 |

---

## Output Bundle Structure

Every conversion produces a FHIR R4 Bundle containing:

```
Bundle (NHCX profile)
├── Claim               ← NHCX claim with supportingInfo refs to all docs
├── Patient             ← Beneficiary (ABHA ID if provided)
├── Coverage            ← Insurance policy details
├── Composition         ← From discharge summary / clinical note
├── DiagnosticReport    ← From lab / radiology report
│   └── Observation[]   ← Individual test results
└── MedicationRequest[] ← From prescription
```

---

## Quick Start

### 1. Start the Server

```bash
cd fhir/server
pip install -r requirements.txt

# Optional: start Ollama with MedGemma for AI-powered extraction
ollama pull alibayram/medgemma && ollama serve

uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

- **Swagger UI**: http://localhost:8001/docs  
- **Health check**: http://localhost:8001/health

### 2. Open the Client

Open `fhir/client/index.html` directly in any browser (no build step needed).

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Server liveness + MedGemma availability |
| `POST` | `/convert/claim` | Multi-PDF → NHCX Claim Bundle |
| `POST` | `/convert/text` | Pasted text → NHCX Claim Bundle |

### `POST /convert/claim` — Multipart Form

```bash
curl -X POST http://localhost:8001/convert/claim \
  -F "files=@discharge_summary.pdf" \
  -F "files=@lab_report.pdf" \
  -F "patient_name=Priya Sharma" \
  -F "insurer_name=Star Health" \
  -F "policy_number=POL-2024-123"
```

### `POST /convert/text` — JSON Body

```bash
curl -X POST http://localhost:8001/convert/text \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Patient admitted with STEMI. BP 140/90. Primary PCI performed.",
    "patient_name": "Rajan Kumar",
    "use_case": "claim"
  }'
```

### Response Shape

```json
{
  "success": true,
  "documents_processed": 2,
  "detected_hi_types": ["discharge_summary", "lab_report"],
  "document_results": [
    {
      "filename": "discharge_summary.pdf",
      "detected_hi_type": "discharge_summary",
      "fhir_resource_type": "Composition",
      "extraction_method": "medgemma",
      "text_length": 3420
    }
  ],
  "fhir_bundle": {
    "resourceType": "Bundle",
    "type": "collection",
    "meta": { "profile": ["https://nrces.in/ndhm/fhir/r4/StructureDefinition/Bundle"] },
    "entry": [ ... ]
  },
  "metadata": {
    "medgemma_used": true,
    "profile": "https://nrces.in/ndhm/fhir/r4/StructureDefinition/Bundle",
    "use_case": "claim_submission",
    "fhir_version": "4.0.1"
  }
}
```

---

## Configuration

Edit `server/config/profiles.yaml` to customise without touching code:

```yaml
use_case: claim_submission   # switch to pre_authorisation when needed

medgemma:
  enabled: true
  ollama_host: "http://localhost:11434"
  model: "alibayram/medgemma"
  fallback_on_error: true

hi_types:
  discharge_summary:
    loinc_code: "18842-5"
    keywords: ["discharge summary", "admitted", "ward", ...]
```

---

## Architecture

```
POST /convert/claim (PDFs)
        │
        ▼
  pdf_extractor.py       extract text from each PDF (pypdf)
        │
        ▼
  hi_type_detector.py    classify document type per file
        │
        ▼
  fhir_builder.py        MedGemma extraction → FHIR R4 resources
                         (Composition / DiagnosticReport / MedicationRequest)
        │
        ▼
  nhcx_packager.py       wrap into NHCX Claim Bundle
        │
        ▼
  JSON response with fhir_bundle
```

---

## ABDM Compliance

- Profile base URL: `https://nrces.in/ndhm/fhir/r4`
- Patient identity system: `https://healthid.ndhm.gov.in` (ABHA)
- NHCX Claim profile: `https://nrces.in/ndhm/fhir/r4/StructureDefinition/Bundle`
- Terminology: LOINC (observations), ICD-10 (conditions), SNOMED CT (procedures)

---

## License

Apache 2.0 — free to use, modify, and embed in any HMIS or healthcare application.
