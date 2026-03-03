import os
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
import uuid

APP_ENV = os.getenv("APP_ENV", "dev")

# ── Models ───────────────────────────────────────────────────────────────────

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


# ── In-Memory Mock Data (dev mode) ────────────────────────────────────────────

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


# ── In-Memory PatientService (dev mode) ───────────────────────────────────────

class PatientService:
    def __init__(self):
        pass

    async def get_patient_by_id(self, hospital_id: str) -> Optional[Patient]:
        return MOCK_PATIENTS.get(hospital_id)

    async def get_patient_by_qr_code(self, qr_data: str) -> Optional[Patient]:
        return await self.get_patient_by_id(qr_data)

    async def create_patient(self, data: dict) -> Patient:
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


# ── DynamoDB PatientService (demo mode) ───────────────────────────────────────

def _deserialize(item: dict) -> Patient:
    for key in ("created_at", "updated_at"):
        if isinstance(item.get(key), str):
            item[key] = datetime.fromisoformat(item[key])
    return Patient(**item)


class DynamoDBPatientService:
    def __init__(self):
        import boto3
        region = os.getenv("AWS_REGION", "ap-south-1")
        self.table_name = os.getenv("DYNAMODB_PATIENTS_TABLE", "vaidyasaarathi-demo-v2-patients")
        self._ddb = boto3.resource("dynamodb", region_name=region)
        self._table = self._ddb.Table(self.table_name)
        print(f"[DEMO] DynamoDBPatientService connected to table: {self.table_name}")

    async def get_patient_by_id(self, hospital_id: str) -> Optional[Patient]:
        response = self._table.get_item(Key={"hospital_id": hospital_id})
        item = response.get("Item")
        return _deserialize(item) if item else None

    async def get_patient_by_qr_code(self, qr_data: str) -> Optional[Patient]:
        return await self.get_patient_by_id(qr_data)

    async def create_patient(self, data: dict) -> Patient:
        hospital_id = data.get("hospital_id", f"P-{uuid.uuid4().hex[:6].upper()}")
        now = datetime.utcnow()
        patient = Patient(
            id=str(uuid.uuid4()),
            hospital_id=hospital_id,
            name=data.get("name", "Unknown"),
            date_of_birth=data.get("date_of_birth", "2000-01-01"),
            gender=data.get("gender", "Unspecified"),
            contact_number=data.get("contact_number", ""),
            address=data.get("address", ""),
            preferred_language=data.get("preferred_language", "English"),
            created_at=now,
            updated_at=now
        )
        item = patient.model_dump()
        item["created_at"] = item["created_at"].isoformat()
        item["updated_at"] = item["updated_at"].isoformat()
        self._table.put_item(Item=item)
        return patient


# ── Factory ──────────────────────────────────────────────────────────────────

def get_patient_service() -> PatientService:
    """Return the appropriate PatientService based on APP_ENV."""
    if APP_ENV == "demo":
        try:
            return DynamoDBPatientService()
        except Exception as e:
            print(f"[WARNING] DynamoDB unavailable, falling back to in-memory: {e}")
    return PatientService()
