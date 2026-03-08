from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

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
    triage_tier: str = "ROUTINE" # 'EMERGENCY' | 'URGENT' | 'SEMI_URGENT' | 'ROUTINE'
    specialty: str = "General Medicine"
    status: str  # 'pending' | 'in_progress' | 'ready_for_review' | 'finalized'
    is_seen: bool = False
    created_at: datetime
    updated_at: datetime
