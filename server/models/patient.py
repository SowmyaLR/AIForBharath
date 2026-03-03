from datetime import datetime
from pydantic import BaseModel

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
