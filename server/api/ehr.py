from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from services.ehr_service import ehr_service

router = APIRouter(prefix="/ehr", tags=["EHR"])

@router.get("/records", response_model=List[Dict[str, Any]])
async def get_ehr_records():
    """
    Returns the list of all exported FHIR records in the internal repository.
    Used by the Mock EHR Dashboard for hackathon verification.
    """
    try:
        return await ehr_service.get_exported_records()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
