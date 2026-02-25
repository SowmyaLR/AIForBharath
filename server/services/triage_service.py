from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel
import uuid

# Models
class AcousticAnomaly(BaseModel):
    type: str  # 'respiratory_distress' | 'cough' | 'voice_strain' | 'wheezing'
    confidence: float
    timestamp: float

class SOAPNote(BaseModel):
    subjective: str
    objective: str
    assessment: str
    plan: str

class VitalSigns(BaseModel):
    temperature: float  # Celsius
    blood_pressure_systolic: int  # mmHg
    blood_pressure_diastolic: int  # mmHg
    heart_rate: int  # bpm
    respiratory_rate: int  # breaths per minute
    oxygen_saturation: int  # percentage
    recorded_at: datetime
    recorded_by: str

class TriageRecord(BaseModel):
    id: str
    patient_id: str
    audio_file_url: str
    language: str
    transcription: str = ""
    translation: str = ""
    soap_note: Optional[SOAPNote] = None
    vitals: Optional[VitalSigns] = None
    risk_score: int = 0
    specialty: str = "General Medicine"
    status: str  # 'pending' | 'in_progress' | 'ready_for_review' | 'finalized'
    created_at: datetime
    updated_at: datetime

MOCK_TRIAGES: Dict[str, TriageRecord] = {}

class TriageService:
    def __init__(self):
        pass

    async def create_triage_record(self, patient_id: str, audio_file_path: str, language: str) -> TriageRecord:
        """Create new triage record with audio"""
        triage_id = str(uuid.uuid4())
        record = TriageRecord(
            id=triage_id,
            patient_id=patient_id,
            audio_file_url=audio_file_path,
            language=language,
            status="pending",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        MOCK_TRIAGES[triage_id] = record
        return record

    async def get_triage(self, triage_id: str) -> Optional[TriageRecord]:
        return MOCK_TRIAGES.get(triage_id)

    async def update_triage_status(self, triage_id: str, status: str) -> Optional[TriageRecord]:
        record = MOCK_TRIAGES.get(triage_id)
        if record:
            record.status = status
            record.updated_at = datetime.utcnow()
        return record

    async def add_vitals(self, triage_id: str, vitals: VitalSigns) -> Optional[TriageRecord]:
        record = MOCK_TRIAGES.get(triage_id)
        if record:
            record.vitals = vitals
            record.updated_at = datetime.utcnow()
        return record

    async def get_triage_queue(self, specialty: Optional[str] = None) -> List[TriageRecord]:
        """Get triage queue, optionally filtered by specialty"""
        records = list(MOCK_TRIAGES.values())
        if specialty:
            records = [r for r in records if r.specialty == specialty]
        
        # Sort by risk score descending, then by creation time
        return sorted(records, key=lambda x: (-x.risk_score, x.created_at))
