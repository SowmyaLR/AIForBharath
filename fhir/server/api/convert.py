"""
API router for FHIR/NHCX conversion endpoints.
"""
import os
from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from models.schemas import ConvertTextRequest, ConvertResponse, DocumentResult, HealthResponse
from services.pdf_extractor import extract_text_from_bytes, clean_extracted_text
from services.hi_type_detector import detect_hi_type, detect_hi_type_batch
from services.fhir_builder import (
    build_patient_resource,
    build_organization_resource,
    build_coverage_resource,
    build_resource_for_document,
    check_medgemma_available,
    _load_config,
)
from services.nhcx_packager import package_nhcx_bundle

router = APIRouter(prefix="", tags=["FHIR Conversion"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    config = _load_config()
    mg_available = check_medgemma_available(config)
    return {
        "status": "ok",
        "version": "1.0.0",
        "medgemma_available": mg_available,
        "use_case": config.get("use_case", "claim_submission"),
        "fhir_profile": config["nhcx"]["profile_url"],
    }


@router.post("/convert/claim")
async def convert_claim(
    files: List[UploadFile] = File(..., description="One or more PDF files (discharge summary, lab report, etc.)"),
    patient_name: Optional[str] = Form(default=None),
    patient_id: Optional[str] = Form(default=None),
    insurer_name: Optional[str] = Form(default=None),
    policy_number: Optional[str] = Form(default=None),
):
    """
    Convert one or more healthcare PDFs into an NHCX Claim FHIR Bundle.

    - Detects HI type per document (discharge summary, lab report, etc.)
    - Extracts clinical data using MedGemma (falls back to deterministic)
    - Returns a complete ABDM FHIR R4 Bundle conforming to NHCX Claim profiles
    """
    if not files:
        raise HTTPException(status_code=400, detail="At least one PDF file is required.")

    config = _load_config()
    mg_available = check_medgemma_available(config)

    # 1. Extract text from all PDFs
    document_texts: dict = {}
    for f in files:
        raw_bytes = await f.read()
        try:
            text = extract_text_from_bytes(raw_bytes)
            text = clean_extracted_text(text)
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Failed to read PDF '{f.filename}': {e}")
        document_texts[f.filename] = text

    # 2. Detect HI type per document
    detected_types = detect_hi_type_batch(document_texts)
    # {filename: (hi_type_key, fhir_resource_type)}

    # 3. Build shared resources
    patient = build_patient_resource(patient_name, patient_id, config)
    coverage = build_coverage_resource(patient["id"], insurer_name, policy_number, config)

    # 4. Build per-document FHIR resources
    document_results_meta: List[DocumentResult] = []
    document_resources: List[tuple] = []  # (filename, resource)

    for filename, text in document_texts.items():
        hi_type_key, fhir_type = detected_types[filename]
        resource, method = build_resource_for_document(
            text=text,
            hi_type_key=hi_type_key,
            fhir_resource_type=fhir_type,
            patient_id_ref=patient["id"],
            config=config,
            use_medgemma=mg_available,
        )
        document_resources.append((filename, resource))
        document_results_meta.append(DocumentResult(
            filename=filename,
            detected_hi_type=hi_type_key,
            fhir_resource_type=fhir_type,
            extraction_method=method,
            text_length=len(text),
        ))

    # 5. Package into NHCX Bundle
    fhir_bundle = package_nhcx_bundle(
        patient_resource=patient,
        coverage_resource=coverage,
        document_resources=document_resources,
        insurer_name=insurer_name,
        config=config,
    )

    return JSONResponse(content={
        "success": True,
        "documents_processed": len(files),
        "detected_hi_types": [r.detected_hi_type for r in document_results_meta],
        "document_results": [r.model_dump() for r in document_results_meta],
        "fhir_bundle": fhir_bundle,
        "metadata": {
            "generated_at": fhir_bundle["timestamp"],
            "medgemma_used": mg_available,
            "profile": config["nhcx"]["profile_url"],
            "use_case": config.get("use_case", "claim_submission"),
            "fhir_version": config["fhir"]["version"],
        },
    })


@router.post("/convert/text")
async def convert_text(body: ConvertTextRequest):
    """
    Convert pasted text (SOAP note, discharge summary) into an NHCX Claim FHIR Bundle.
    """
    config = _load_config()
    mg_available = check_medgemma_available(config)

    hi_type_key, fhir_type = detect_hi_type(body.text, hint=body.document_type)

    patient = build_patient_resource(body.patient_name, body.patient_id, config)
    coverage = build_coverage_resource(patient["id"], body.insurer_name, body.policy_number, config)

    resource, method = build_resource_for_document(
        text=body.text,
        hi_type_key=hi_type_key,
        fhir_resource_type=fhir_type,
        patient_id_ref=patient["id"],
        config=config,
        use_medgemma=mg_available,
    )

    fhir_bundle = package_nhcx_bundle(
        patient_resource=patient,
        coverage_resource=coverage,
        document_resources=[("pasted_text", resource)],
        insurer_name=body.insurer_name,
        config=config,
    )

    return JSONResponse(content={
        "success": True,
        "documents_processed": 1,
        "detected_hi_types": [hi_type_key],
        "document_results": [{
            "filename": "pasted_text",
            "detected_hi_type": hi_type_key,
            "fhir_resource_type": fhir_type,
            "extraction_method": method,
            "text_length": len(body.text),
        }],
        "fhir_bundle": fhir_bundle,
        "metadata": {
            "generated_at": fhir_bundle["timestamp"],
            "medgemma_used": mg_available,
            "profile": config["nhcx"]["profile_url"],
            "use_case": config.get("use_case", "claim_submission"),
            "fhir_version": config["fhir"]["version"],
        },
    })
