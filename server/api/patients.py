from fastapi import APIRouter, HTTPException, status
from services.patient_service import PatientService, Patient

router = APIRouter(prefix="/patients", tags=["patients"])
patient_service = PatientService()

@router.get("/{hospital_id}", response_model=Patient)
async def get_patient(hospital_id: str):
    patient = await patient_service.get_patient_by_id(hospital_id)
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return patient

@router.post("/", response_model=Patient)
async def create_patient(data: dict):
    return await patient_service.create_patient(data)
