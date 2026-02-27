"""
Pydantic schemas for nhir/server request and response models.
"""
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class ConvertTextRequest(BaseModel):
    text: str = Field(..., description="Raw text of a healthcare document (SOAP note, discharge summary, etc.)")
    document_type: Optional[str] = Field(
        default=None,
        description="Hint: discharge_summary | lab_report | clinical_note | prescription | radiology_report. Omit for auto-detection."
    )
    patient_name: Optional[str] = Field(default=None, description="Patient full name")
    patient_id: Optional[str] = Field(default=None, description="ABHA / Health ID")
    insurer_name: Optional[str] = Field(default=None, description="Insurance company name")
    policy_number: Optional[str] = Field(default=None, description="Insurance policy number")
    use_case: Optional[str] = Field(default="claim", description="claim | preauth")


class DocumentResult(BaseModel):
    filename: str
    detected_hi_type: str
    fhir_resource_type: str
    extraction_method: str  # "medgemma" | "deterministic"
    text_length: int


class ConvertResponse(BaseModel):
    success: bool
    documents_processed: int
    detected_hi_types: List[str]
    document_results: List[DocumentResult]
    fhir_bundle: Dict[str, Any]
    metadata: Dict[str, Any]


class HealthResponse(BaseModel):
    status: str
    version: str
    medgemma_available: bool
    use_case: str
    fhir_profile: str
