from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
import uuid

class Patient(BaseModel):
    id: str
    hospital_id: str
    name: str
    date_of_birth: str
    gender: str
    contact_number: str
    address: str
    preferred_language: str
    created_at: datetime
    updated_at: datetime

# --- Mock Database ---
MOCK_PATIENTS = {
    "P-001": Patient(
        id=str(uuid.uuid4()),
        hospital_id="P-001",
        name="Ramesh Kumar",
        date_of_birth="1980-05-14",
        gender="Male",
        contact_number="9876543210",
        address="123 Anna Salai, Chennai",
        preferred_language="Tamil",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    ),
    "P-002": Patient(
        id=str(uuid.uuid4()),
        hospital_id="P-002",
        name="Lakshmi Devi",
        date_of_birth="1965-11-02",
        gender="Female",
        contact_number="9876543211",
        address="45 Mount Road, Chennai",
        preferred_language="Telugu",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
}

class PatientService:
    def __init__(self):
        pass

    async def get_patient_by_id(self, hospital_id: str) -> Optional[Patient]:
        """Retrieve patient by Hospital_ID"""
        return MOCK_PATIENTS.get(hospital_id)
    
    async def get_patient_by_qr_code(self, qr_data: str) -> Optional[Patient]:
        """
        Extract Hospital_ID from QR and retrieve patient.
        Assuming QR data is simply the patient's hospital_id for the demo.
        """
        return await self.get_patient_by_id(qr_data)
        
    async def create_patient(self, data: dict) -> Patient:
        """Create a new patient record"""
        hospital_id = data.get("hospital_id", f"P-{len(MOCK_PATIENTS)+1:03d}")
        
        new_patient = Patient(
            id=str(uuid.uuid4()),
            hospital_id=hospital_id,
            name=data.get("name", "Unknown"),
            date_of_birth=data.get("date_of_birth", "2000-01-01"),
            gender=data.get("gender", "Unspecified"),
            contact_number=data.get("contact_number", ""),
            address=data.get("address", ""),
            preferred_language=data.get("preferred_language", "English"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        MOCK_PATIENTS[hospital_id] = new_patient
        return new_patient
