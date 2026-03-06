export interface SOAPNote {
    subjective: string;
    objective: string;
    assessment: string;
    plan: string;
}

export interface VitalSigns {
    temperature: number;
    blood_pressure_systolic: number;
    blood_pressure_diastolic: number;
    heart_rate: number;
    respiratory_rate: number;
    oxygen_saturation: number;
    recorded_at: string;
    recorded_by: string;
}

export interface TriageRecord {
    id: string;
    patient_id: string;
    audio_file_url: string;
    language: string;
    transcription: string;
    translation: string;
    soap_note?: SOAPNote | null;
    vitals?: VitalSigns | null;
    risk_score: number;
    triage_tier: 'EMERGENCY' | 'URGENT' | 'SEMI_URGENT' | 'ROUTINE';
    preliminary_zone?: 'EMERGENCY' | 'URGENT' | 'SEMI_URGENT' | 'ROUTINE' | 'STABLE' | 'ABNORMAL' | null; // vitals-only fast estimate
    vitals_status?: 'STABLE' | 'ABNORMAL';
    preliminary_precautions?: string[];
    specialty: string;
    patient_age?: number | null;
    status: 'pending' | 'in_progress' | 'ready_for_review' | 'finalized' | 'exported' | 'failed';
    created_at: string;
    updated_at: string;
}

