# Design Document: VaidyaSaarathi

## Overview

VaidyaSaarathi is a web-based clinical workflow application that streamlines patient intake, triage, and specialist review through role-based interfaces, automated AI analysis, and multi-language support. The system architecture follows a three-tier model with a React-based frontend, Python/FastAPI backend API, and PostgreSQL database with encrypted storage.

**PRIVACY-FIRST ARCHITECTURE:** All AI/ML models run locally on hospital-owned GPU servers. NO patient data leaves the hospital premises. The system is fully offline-capable, ensuring complete data sovereignty and HIPAA compliance without external dependencies.

**AI/ML FRAMEWORK:** The system leverages Google's Health AI Developer Foundations (HAI-DEF) framework, which provides healthcare-specific AI models including MedGemma 4B for clinical SOAP note generation and HeAR (Health Acoustic Representations) for acoustic anomaly detection. Combined with OpenAI's Whisper for multi-language transcription, all models run locally on hospital infrastructure with zero external API dependencies.

The application supports three primary user roles:
- **Receptionists** perform patient identification (manual ID or QR scan), capture audio complaints in native languages, and provide localized instructions
- **Nurses** enter clinical vitals and measurements that augment triage analysis
- **Doctors** review prioritized patient queues filtered by specialty, edit AI-generated SOAP notes, and export finalized documentation to EHR systems

Key technical capabilities include:
- Mock SSO authentication with JWT-based session management
- LOCAL audio processing pipeline using HAI-DEF models (transcription → translation → SOAP generation → risk scoring)
- Real-time queue updates with WebSocket connections
- FHIR R4 compliant JSON export for EHR integration
- HIPAA-compliant encryption (AES-256 at rest, TLS 1.2+ in transit)
- Offline operation capability with local AI models
- Zero external API dependencies for PHI processing

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Receptionist │  │    Nurse     │  │    Doctor    │      │
│  │  Dashboard   │  │  Dashboard   │  │  Dashboard   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                            │                                 │
└────────────────────────────┼─────────────────────────────────┘
                             │ HTTPS/WSS
┌────────────────────────────┼─────────────────────────────────┐
│                  Backend API (Python/FastAPI)                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │     Auth     │  │    Triage    │  │     EHR      │      │
│  │   Service    │  │   Service    │  │   Service    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                            │                                 │
└────────────────────────────┼─────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌───────▼────────┐  ┌────────▼────────┐  ┌───────▼────────┐
│   PostgreSQL   │  │  Local Storage  │  │  Local Secrets │
│   (Encrypted)  │  │  (Encrypted)    │  │     Store      │
│   Data Store   │  │  Audio Storage  │  │  Key Storage   │
└────────────────┘  └─────────────────┘  └────────────────┘

AI/ML Models (LOCAL ON-PREMISE DEPLOYMENT ONLY):
┌──────────────────────────────────────────────────────────────┐
│  🔒 PRIVACY-FIRST: All models run locally within hospital    │
│     premises. NO data leaves the facility. Offline capable.  │
│                                                               │
│  Ollama - Local Model Serving (CPU/GPU Auto-Detection)       │
│  ┌──────────────────┐          ┌──────────────────┐         │
│  │  MedGemma 4B     │          │   HeAR Model     │         │
│  │  Clinical SOAP   │          │   Acoustic       │         │
│  │  Generation &    │          │   Anomaly        │         │
│  │  Risk Scoring    │          │   Detection      │         │
│  │  [OLLAMA]        │          │   [LOCAL CPU]    │         │
│  └──────────────────┘          └──────────────────┘         │
│                                                               │
│  ┌──────────────────┐          ┌──────────────────┐         │
│  │  Whisper Large   │          │  Local TTS       │         │
│  │  Multi-language  │          │  (piper/coqui)   │         │
│  │  Speech-to-Text  │          │  Multi-language  │         │
│  │  [OLLAMA]        │          │  [LOCAL CPU]     │         │
│  └──────────────────┘          └──────────────────┘         │
│                                                               │
│  ┌──────────────────────────────────────────────────┐       │
│  │  Local Translation (Llama 3.2 or similar)        │       │
│  │  Multi-language support for Indian languages     │       │
│  │  [OLLAMA]                                        │       │
│  └──────────────────────────────────────────────────┘       │
└──────────────────────────────────────────────────────────────┘

Hardware Requirements:
┌──────────────────────────────────────────────────────────────┐
│  Server: Standard x86 CPU (Intel/AMD) - No GPU required     │
│  RAM: 16GB minimum, 32GB recommended                         │
│  Storage: 100GB SSD for models + 1TB for audio/data         │
│  Network: Isolated hospital network (air-gapped capable)     │
│  Ollama: Local model serving (CPU/GPU auto-detection)        │
└──────────────────────────────────────────────────────────────┘
```

### Technology Stack

**Frontend:**
- React 18 with TypeScript
- React Router for navigation
- Axios for HTTP requests
- Socket.io-client for real-time updates
- Recharts for analytics visualization
- HTML5 MediaRecorder API for audio capture
- QR code scanner library (html5-qrcode)

**Backend:**
- Python 3.11+ with FastAPI
- Pydantic for data validation and serialization
- JWT (python-jose) for authentication tokens
- WebSockets (FastAPI native) for real-time updates
- SQLAlchemy ORM for database access
- Alembic for database migrations
- python-multipart for file uploads
- APScheduler for scheduled tasks
- Cryptography library for encryption
- Uvicorn/Gunicorn for ASGI server

**Database:**
- PostgreSQL 14+ with pgcrypto extension
- SQLAlchemy ORM for data access
- Connection pooling (asyncpg) for performance
- Transparent Data Encryption (TDE) for data-at-rest
- Local deployment within hospital network

**File Storage:**
- Local encrypted file system for audio storage
- AES-256 encryption for audio files at rest
- Secure file permissions (chmod 600) for sensitive data
- Automatic file cleanup policies for compliance
- Optional: MinIO for S3-compatible local object storage

**AI/ML Models (ALL LOCAL DEPLOYMENT):**
- **Ollama**: Local model serving platform (CPU/GPU auto-detection)
  - **MedGemma 4B**: Clinical language model for SOAP note generation (via Ollama)
  - **Whisper Large**: Multi-language speech-to-text (via Ollama)
  - **Llama 3.2 or similar**: Local translation for Indian languages (via Ollama)
- **HeAR (Health Acoustic Representations)**: Acoustic anomaly detection (LOCAL CPU)
- **Piper or Coqui TTS**: Local text-to-speech engine (LOCAL CPU)
- All models run on-premise via Ollama, no external API calls
- Offline-capable operation
- No GPU required - runs on standard CPU hardware

**Privacy & Compliance:**
- Zero external data transmission for PHI
- Air-gapped deployment option available
- All processing within hospital network perimeter
- HIPAA-compliant local storage and encryption

### AI Model Architecture

The system integrates Google's Health AI Developer Foundations (HAI-DEF) framework along with OpenAI's Whisper for comprehensive clinical triage analysis.

#### HAI-DEF (Health AI Developer Foundations)

**Overview:**
HAI-DEF is Google's open-source framework providing healthcare-specific AI models and tools designed for clinical applications. It includes pre-trained foundation models optimized for medical use cases with a focus on safety, accuracy, and HIPAA compliance.

**Key Components Used:**
1. **MedGemma 4B** - Clinical language model
2. **HeAR** - Health acoustic representations model

**Benefits:**
- Pre-trained on medical data with clinical validation
- Designed for healthcare compliance (HIPAA, data privacy)
- Optimized for on-premise deployment to protect PHI
- Regular updates and improvements from Google Health
- Open-source with commercial use licensing

#### 1. Whisper - Speech Transcription

**Purpose:** Multi-language speech-to-text transcription

**Capabilities:**
- Supports 99+ languages including Tamil, Hindi, English, and other Indian languages
- Robust to background noise and accents
- Handles code-switching (mixing multiple languages in one conversation)
- High accuracy for medical terminology when fine-tuned

**Integration:**
- Deployed as a LOCAL model via Ollama on hospital server
- Processes audio files from local encrypted storage
- Returns timestamped transcription in original language
- Average processing time: 2-4 seconds for 30-second audio clips (CPU)
- NO external API calls - fully offline capable

**Model Specifications:**
- Model: OpenAI Whisper (Large variant)
- Model size: 1.55B parameters
- Input: Audio files (WAV, MP3, WebM formats)
- Output: Transcribed text with confidence scores and timestamps
- Deployment: Via Ollama (CPU/GPU auto-detection)
- Hardware: Standard CPU (4+ cores recommended), GPU optional for faster inference
- Privacy: All processing on-premise, no data leaves hospital network

#### 2. HeAR (Health Acoustic Representations) - HAI-DEF Component

**Purpose:** Detect acoustic biomarkers and respiratory anomalies

**Capabilities:**
- Identifies respiratory distress patterns (wheezing, stridor, labored breathing)
- Detects cough characteristics (dry, wet, productive)
- Analyzes voice strain and vocal cord issues
- Provides confidence scores for each detected anomaly
- Works across languages (acoustic features are language-independent)
- Pre-trained on large-scale health acoustic data

**Integration:**
- Part of Google's HAI-DEF framework
- Runs LOCALLY on hospital server (CPU-based implementation)
- Processes raw audio waveforms from local encrypted storage
- Returns structured anomaly data with timestamps and confidence scores
- Average processing time: 1-2 seconds for 30-second audio clips (CPU)
- NO external API calls - fully offline capable

**Model Specifications:**
- Model type: Self-supervised acoustic foundation model from HAI-DEF
- Input: Raw audio waveforms (16kHz sampling rate)
- Output: Anomaly classifications with confidence scores (0-1 range)
- Anomaly types: respiratory_distress, cough, voice_strain, wheezing, normal
- Deployment: Local inference via Python SDK on hospital CPU
- Hardware: Standard CPU (4+ cores recommended)
- Privacy: All processing on-premise, no data leaves hospital network

**Technical Details:**
- Based on contrastive learning on health acoustic data
- Trained on diverse patient populations and clinical settings
- Validated against clinical ground truth annotations
- Provides interpretable acoustic features for clinical review

#### 3. MedGemma 4B - HAI-DEF Component

**Purpose:** Generate structured clinical documentation and risk assessment

**Capabilities:**
- Generates SOAP notes (Subjective, Objective, Assessment, Plan) from transcribed patient complaints
- Incorporates acoustic anomaly findings into clinical assessment
- Calculates risk scores based on clinical indicators
- Assigns appropriate medical specialty (Cardiac, Respiratory, Neurology, General Medicine)
- Understands medical terminology and clinical context
- Provides evidence-based recommendations
- Fine-tuned on medical literature and clinical guidelines

**Integration:**
- Part of Google's HAI-DEF framework
- Runs LOCALLY via Ollama on hospital server
- Receives transcribed text (in English after translation) and acoustic anomaly data
- Generates structured SOAP note with four sections
- Calculates risk score (0-100) based on severity indicators
- Suggests appropriate triage zone (Critical/Zone A, Urgent/Zone B, Routine/Zone C)
- Average processing time: 3-5 seconds (CPU)
- NO external API calls - fully offline capable

**Model Specifications:**
- Model: MedGemma 4B (medical variant of Google's Gemma model)
- Model size: 4 billion parameters
- Model type: Medical domain-specific language model from HAI-DEF
- Input: Patient complaint text + acoustic anomaly data + optional vital signs
- Output: Structured SOAP note + risk score + specialty assignment + reasoning
- Context window: 8K tokens
- Deployment: Via Ollama on hospital server (CPU/GPU auto-detection)
- Hardware: Standard CPU (8+ cores recommended), 16GB+ RAM
- Privacy: All processing on-premise, no data leaves hospital network

**Safety Features:**
- Built-in medical safety guardrails
- Uncertainty quantification for predictions
- Explainable outputs with clinical reasoning
- Bias mitigation for diverse patient populations

### AI Pipeline Flow

```
Audio Recording (Patient Complaint)
         │
         ├─────────────────────────────────┐
         │                                 │
         ▼                                 ▼
   Whisper (via Ollama)            HeAR (Local CPU)
   Multi-language                   Acoustic Anomaly
   Transcription                    Detection
   [CPU/GPU AUTO]                   [CPU]
         │                                 │
         ▼                                 │
   Local Translation                       │
   (Llama 3.2 via Ollama)                 │
   [CPU/GPU AUTO]                          │
         │                                 │
         └─────────────┬───────────────────┘
                       │
                       ▼
              MedGemma 4B (via Ollama)
            Clinical Analysis Engine
         (SOAP + Risk Score + Specialty)
              [CPU/GPU AUTO]
                       │
                       ▼
              Triage Assignment
         (Zone A/B/C + Specialty)
                       │
                       ▼
              Local TTS (Piper/Coqui)
            Generate Audio Instructions
              [CPU]
```

**Processing Time Budget:**
- Whisper transcription: 2-4 seconds (CPU)
- HeAR acoustic analysis: 1-2 seconds (CPU, parallel with Whisper)
- Local translation: 1-2 seconds (CPU)
- MedGemma SOAP generation: 3-5 seconds (CPU)
- **Total: ~7-10 seconds** (CPU-based processing)
- **Note:** With GPU acceleration (if available), processing time can be reduced to ~4-5 seconds

**Privacy Guarantees:**
- All audio processing happens on local servers via Ollama
- No patient data transmitted outside hospital network
- Fully offline-capable operation
- Air-gapped deployment option available
- Zero external API dependencies for PHI processing
- CPU-based deployment - no expensive GPU hardware required

**Model Deployment Strategy:**

**LOCAL ON-PREMISE DEPLOYMENT VIA OLLAMA (REQUIRED FOR HIPAA COMPLIANCE)**

All AI/ML models MUST be deployed on hospital-owned servers within the hospital network perimeter using Ollama. This ensures:
- Complete data sovereignty - no PHI leaves hospital premises
- HIPAA compliance without Business Associate Agreements (BAA)
- Offline operation capability for network outages
- Low latency with local processing
- No recurring API costs
- **No GPU required** - runs on standard CPU hardware

**Hardware Requirements:**
- **CPU**: 8+ cores (Intel/AMD x86_64), 16+ cores recommended
- **RAM**: 16GB minimum (32GB recommended for concurrent processing)
- **Storage**: 
  - 100GB SSD for model files and cache
  - 1TB+ encrypted storage for audio files and database
- **Network**: Isolated hospital network (air-gapped option available)
- **GPU**: Optional (Ollama auto-detects and uses if available for faster inference)

**Model Files and Storage:**
- MedGemma 4B: ~2.5GB (via Ollama)
- Whisper Large: ~3GB (via Ollama)
- Llama 3.2 for translation: ~2GB (via Ollama)
- HeAR model: ~2GB
- Piper/Coqui TTS: ~500MB per language
- **Total**: ~10-15GB for all models

**Deployment Architecture:**

```python
# Local model initialization via Ollama (FastAPI startup)
import ollama
from typing import List, Dict

class OllamaModelService:
    def __init__(self, host: str = "http://localhost:11434"):
        self.client = ollama.Client(host=host)
        
        # Verify models are available
        self._verify_models()
    
    def _verify_models(self):
        """Verify required models are pulled in Ollama"""
        required_models = ["medgemma:4b", "whisper:large", "llama3.2:3b"]
        available_models = [m['name'] for m in self.client.list()['models']]
        
        for model in required_models:
            if model not in available_models:
                raise Exception(f"Model {model} not found. Run: ollama pull {model}")
    
    async def transcribe_audio(self, audio_path: str) -> str:
        """Transcribe audio using Whisper via Ollama"""
        # Ollama Whisper integration
        response = self.client.generate(
            model="whisper:large",
            prompt=f"transcribe:{audio_path}"
        )
        return response['response']
    
    async def generate_soap(self, complaint: str, anomalies: List[Dict]) -> Dict:
        """Generate SOAP note using MedGemma via Ollama"""
        prompt = self._build_soap_prompt(complaint, anomalies)
        
        response = self.client.generate(
            model="medgemma:4b",
            prompt=prompt,
            options={
                "temperature": 0.7,
                "num_predict": 512
            }
        )
        
        return self._parse_soap(response['response'])
    
    async def translate_text(self, text: str, target_lang: str) -> str:
        """Translate text using Llama via Ollama"""
        prompt = f"Translate the following to {target_lang}: {text}"
        
        response = self.client.generate(
            model="llama3.2:3b",
            prompt=prompt
        )
        
        return response['response']

class HeARService:
    def __init__(self, model_path: str):
        # Load HeAR model locally (CPU-based)
        self.model = self._load_hear_model(model_path)
    
    async def analyze_audio(self, audio_path: str) -> List[Dict]:
        """Analyze audio using local HeAR model on CPU"""
        audio_tensor = self._load_audio(audio_path)
        anomalies = self.model(audio_tensor)
        return self._parse_anomalies(anomalies)
```

**Model Optimization:**
- Ollama automatically handles model quantization and optimization
- CPU inference optimized with GGML/GGUF formats
- Automatic GPU detection and utilization if available
- Model caching for faster subsequent requests
- Concurrent request handling via Ollama's built-in queue management

**Offline Operation:**
- All models pre-pulled via Ollama and stored locally
- No internet connectivity required for inference
- Local model updates via USB/secure file transfer (export/import Ollama models)
- Fallback mechanisms for model failures

**Security Measures:**
- Models stored in Ollama's secure model directory
- Access restricted to FastAPI service account only
- Model files integrity verification via Ollama
- Audit logging for all model inference requests
- No telemetry or usage data sent externally

**Alternative: Cloud Deployment (NOT RECOMMENDED)**
If cloud deployment is absolutely necessary:
- Use Google Cloud Vertex AI with VPC Service Controls
- Requires HIPAA-compliant GCP setup and BAA with Google Cloud
- Higher latency and recurring costs
- Data sovereignty concerns
- **This option violates the privacy-first requirement**

**Ollama Integration:**
```python
# Example Ollama integration for VaidyaSaarathi
import ollama

class OllamaService:
    def __init__(self, host: str = "http://localhost:11434"):
        self.client = ollama.Client(host=host)
    
    async def generate_soap(
        self,
        complaint_text: str,
        acoustic_findings: List[dict],
        vitals: Optional[dict] = None
    ) -> dict:
        """Generate SOAP note using MedGemma via Ollama"""
        prompt = self._build_prompt(complaint_text, acoustic_findings, vitals)
        
        response = self.client.generate(
            model="medgemma:4b",
            prompt=prompt,
            options={
                "temperature": 0.7,
                "num_predict": 512
            }
        )
        
        return self._parse_soap(response['response'])

class HeARService:
    def __init__(self, model_path: str):
        # Load HeAR model locally for CPU inference
        self.model = self._load_hear_model(model_path)
    
    async def analyze_audio(self, audio_path: str) -> List[dict]:
        """Analyze audio using local HeAR model on CPU"""
        audio_tensor = self._load_audio(audio_path)
        anomalies = self.model(audio_tensor)
        return self._parse_anomalies(anomalies)
```

## Components and Interfaces

### Authentication Service

**Responsibilities:**
- Validate user credentials against mock SSO
- Generate and verify JWT tokens
- Manage user sessions
- Enforce role-based access control

**Interface:**
```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AuthService:
    async def login(self, hospital_id: str, password: str) -> AuthResponse:
        """Validate credentials and generate JWT token"""
        pass
    
    async def verify_token(self, token: str) -> UserSession:
        """Verify JWT token and return session info"""
        pass
    
    async def logout(self, token: str) -> None:
        """Invalidate user session"""
        pass
    
    async def check_permission(self, user_id: str, resource: str, action: str) -> bool:
        """Check if user has permission for resource action"""
        pass

class AuthResponse(BaseModel):
    token: str
    user: 'User'
    expires_in: int

class User(BaseModel):
    id: str
    hospital_id: str
    name: str
    role: str  # 'receptionist' | 'nurse' | 'doctor'
    specialty: Optional[str] = None  # For doctors only

class UserSession(BaseModel):
    user_id: str
    role: str
    specialty: Optional[str] = None
    issued_at: int
    expires_at: int
```

### Patient Service

**Responsibilities:**
- Retrieve patient profiles by Hospital_ID or QR code
- Fetch longitudinal visit history
- Manage patient demographics

**Interface:**
```python
from pydantic import BaseModel
from typing import List
from datetime import datetime

class PatientService:
    async def get_patient_by_id(self, hospital_id: str) -> Patient:
        """Retrieve patient by Hospital_ID"""
        pass
    
    async def get_patient_by_qr_code(self, qr_data: str) -> Patient:
        """Extract Hospital_ID from QR and retrieve patient"""
        pass
    
    async def get_visit_history(self, patient_id: str, limit: int) -> List[Visit]:
        """Get patient's visit history"""
        pass
    
    async def update_patient_demographics(self, patient_id: str, data: dict) -> Patient:
        """Update patient demographic information"""
        pass

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

class Visit(BaseModel):
    id: str
    patient_id: str
    visit_date: datetime
    chief_complaint: str
    diagnosis: str
    specialty: str
    risk_score: int
```

### Triage Service

**Responsibilities:**
- Process audio intake recordings
- Orchestrate transcription, translation, and SOAP generation
- Calculate risk scores
- Manage triage queue
- Store and retrieve triage records

**Interface:**
```python
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class TriageService:
    async def create_triage_record(self, patient_id: str, audio_file: bytes, language: str) -> TriageRecord:
        """Create new triage record with audio"""
        pass
    
    async def process_audio(self, triage_id: str) -> TriageAnalysis:
        """Process audio through analysis pipeline"""
        pass
    
    async def add_vitals(self, triage_id: str, vitals: VitalSigns) -> TriageRecord:
        """Add vital signs to triage record"""
        pass
    
    async def get_triage_queue(self, specialty: Optional[str] = None) -> List[TriageQueueItem]:
        """Get triage queue, optionally filtered by specialty"""
        pass
    
    async def update_soap_note(self, triage_id: str, soap_note: dict) -> TriageRecord:
        """Update SOAP note sections"""
        pass
    
    async def finalize_triage_record(self, triage_id: str) -> TriageRecord:
        """Mark triage record as finalized"""
        pass

class TriageRecord(BaseModel):
    id: str
    patient_id: str
    audio_file_url: str
    language: str
    transcription: str
    translation: str
    soap_note: 'SOAPNote'
    vitals: Optional['VitalSigns'] = None
    risk_score: int
    specialty: str
    status: str  # 'pending' | 'in_progress' | 'finalized' | 'exported'
    created_at: datetime
    updated_at: datetime

class TriageAnalysis(BaseModel):
    acoustic_anomalies: List['AcousticAnomaly']
    transcription: str
    translation: str
    soap_note: 'SOAPNote'
    risk_score: int
    specialty: str

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

class TriageQueueItem(BaseModel):
    triage_id: str
    patient_id: str
    patient_name: str
    chief_complaint: str
    risk_score: int
    specialty: str
    time_in_queue: int  # minutes
    last_visit_date: Optional[datetime] = None
    trend_alerts: List[str]
```

### Audio Processing Pipeline

**Responsibilities:**
- Detect acoustic biomarkers using HeAR model (HAI-DEF) - LOCAL
- Transcribe audio to text using Whisper (OpenAI) - LOCAL
- Translate transcription using NLLB-200 or IndicTrans2 - LOCAL
- Generate SOAP notes using MedGemma 4B (HAI-DEF) - LOCAL
- Calculate risk scores based on clinical indicators
- Generate localized audio instructions using local TTS

**Interface:**
```python
from typing import List, Optional

class AudioProcessor:
    async def detect_anomalies(self, audio_buffer: bytes) -> List[AcousticAnomaly]:
        """Detect acoustic anomalies using LOCAL HeAR model (CPU-based)"""
        pass
    
    async def transcribe(self, audio_buffer: bytes, language: str) -> str:
        """Transcribe audio to text using Whisper via Ollama"""
        pass
    
    async def translate(self, text: str, source_language: str, target_language: str) -> str:
        """Translate text using Llama via Ollama"""
        pass
    
    async def generate_soap_note(self, translated_text: str, anomalies: List[AcousticAnomaly]) -> SOAPNote:
        """Generate SOAP note using MedGemma via Ollama"""
        pass
    
    async def calculate_risk_score(self, soap_note: SOAPNote, anomalies: List[AcousticAnomaly], vitals: Optional[VitalSigns] = None) -> int:
        """Calculate risk score using MedGemma analysis via Ollama"""
        pass
    
    async def generate_audio_instructions(self, text: str, language: str) -> bytes:
        """Generate audio instructions using LOCAL TTS (Piper/Coqui)"""
        pass

class WhisperService:
    """Wrapper for Whisper model via Ollama"""
    async def transcribe_audio(self, audio_path: str, language: str) -> TranscriptionResult:
        """Transcribe audio using Whisper via Ollama (CPU/GPU auto-detection)"""
        pass

class HeARService:
    """Wrapper for LOCAL HeAR acoustic model"""
    async def analyze_audio(self, audio_path: str) -> List[AcousticAnomaly]:
        """Analyze audio using local HeAR model on CPU"""
        pass

class MedGemmaService:
    """Wrapper for MedGemma 4B model via Ollama"""
    async def generate_soap(self, complaint: str, anomalies: List[AcousticAnomaly], vitals: Optional[VitalSigns] = None) -> ClinicalAnalysis:
        """Generate SOAP using MedGemma via Ollama (CPU/GPU auto-detection)"""
        pass

class LocalTranslationService:
    """Wrapper for translation model via Ollama"""
    async def translate_text(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate text using Llama via Ollama (CPU/GPU auto-detection)"""
        pass

class LocalTTSService:
    """Wrapper for LOCAL TTS engine (Piper or Coqui)"""
    async def synthesize_speech(self, text: str, language: str) -> bytes:
        """Generate speech audio using local TTS on CPU"""
        pass

class TranscriptionResult(BaseModel):
    text: str
    language: str
    confidence: float
    segments: List[dict]  # Timestamped segments

class ClinicalAnalysis(BaseModel):
    soap_note: SOAPNote
    risk_score: int
    specialty: str
    triage_zone: str  # 'A' (Critical), 'B' (Urgent), 'C' (Routine)
    reasoning: str  # Explanation for risk score and specialty
```

### Localization Service

**Responsibilities:**
- Generate zone instructions in patient's native language
- Provide text-to-speech audio output using LOCAL TTS engine
- Manage language-specific templates

**Interface:**
```python
from typing import List

class LocalizationService:
    async def generate_instructions(self, triage_record: TriageRecord, language: str) -> str:
        """Generate zone instructions in patient's language"""
        pass
    
    async def text_to_speech(self, text: str, language: str) -> bytes:
        """Convert text to speech audio using LOCAL Piper or Coqui TTS"""
        pass
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages"""
        pass
```

**Local TTS Implementation:**
```python
from piper import PiperVoice
import wave

class LocalTTSService:
    def __init__(self, models_path: str):
        self.models_path = Path(models_path)
        self.voices = {}
        
        # Load voice models for supported languages
        self._load_voices()
    
    def _load_voices(self):
        """Load Piper voice models for each language"""
        language_models = {
            'en': 'en_US-lessac-medium',
            'hi': 'hi_IN-medium',
            'ta': 'ta_IN-medium',
            'te': 'te_IN-medium',
            'kn': 'kn_IN-medium'
        }
        
        for lang, model_name in language_models.items():
            model_path = self.models_path / f"{model_name}.onnx"
            if model_path.exists():
                self.voices[lang] = PiperVoice.load(model_path)
    
    async def synthesize(self, text: str, language: str) -> bytes:
        """Generate speech audio from text"""
        if language not in self.voices:
            raise ValueError(f"Language {language} not supported")
        
        voice = self.voices[language]
        audio_data = voice.synthesize(text)
        
        # Convert to WAV format
        return self._to_wav(audio_data)
```

### File Storage Service

**Responsibilities:**
- Store audio files securely in local encrypted file system
- Generate secure file paths with access controls
- Manage file lifecycle and retention policies
- Ensure HIPAA compliance for audio storage
- Support optional MinIO for S3-compatible local object storage

**Interface:**
```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from pathlib import Path

class FileStorageService:
    async def upload_audio(self, file_data: bytes, patient_id: str, triage_id: str) -> FileUploadResult:
        """Upload audio file to local encrypted storage"""
        pass
    
    async def get_audio_path(self, file_key: str) -> Path:
        """Get secure file path for audio access"""
        pass
    
    async def delete_audio(self, file_key: str) -> bool:
        """Delete audio file from local storage"""
        pass
    
    async def check_file_exists(self, file_key: str) -> bool:
        """Check if file exists in local storage"""
        pass
    
    async def encrypt_file(self, file_path: Path) -> None:
        """Encrypt audio file using AES-256"""
        pass
    
    async def decrypt_file(self, file_path: Path) -> bytes:
        """Decrypt audio file for processing"""
        pass

class FileUploadResult(BaseModel):
    file_key: str
    file_path: str
    encryption_key_id: str
    uploaded_at: datetime
    file_size: int
```

**Local Storage Implementation:**
```python
import os
from pathlib import Path
from cryptography.fernet import Fernet
import hashlib

class LocalFileStorage:
    def __init__(self, base_path: str, encryption_key: bytes):
        self.base_path = Path(base_path)
        self.cipher = Fernet(encryption_key)
        
        # Create directory structure
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Set secure permissions (owner read/write only)
        os.chmod(self.base_path, 0o700)
    
    async def save_audio(self, file_data: bytes, patient_id: str, triage_id: str) -> str:
        """Save encrypted audio file to local storage"""
        # Generate secure file path
        file_key = f"{patient_id}/{triage_id}/{hashlib.sha256(file_data).hexdigest()}.enc"
        file_path = self.base_path / file_key
        
        # Create patient directory
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Encrypt and save
        encrypted_data = self.cipher.encrypt(file_data)
        file_path.write_bytes(encrypted_data)
        
        # Set secure file permissions
        os.chmod(file_path, 0o600)
        
        return file_key
    
    async def read_audio(self, file_key: str) -> bytes:
        """Read and decrypt audio file"""
        file_path = self.base_path / file_key
        encrypted_data = file_path.read_bytes()
        return self.cipher.decrypt(encrypted_data)
```

**Optional: MinIO for S3-Compatible Local Storage:**
```python
from minio import Minio
from minio.error import S3Error

class MinIOStorage:
    def __init__(self, endpoint: str, access_key: str, secret_key: str, bucket: str):
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=True  # Use TLS
        )
        self.bucket = bucket
        
        # Create bucket if not exists
        if not self.client.bucket_exists(bucket):
            self.client.make_bucket(bucket)
    
    async def upload_audio(self, file_data: bytes, file_key: str) -> str:
        """Upload encrypted audio to MinIO"""
        self.client.put_object(
            self.bucket,
            file_key,
            io.BytesIO(file_data),
            length=len(file_data),
            content_type="audio/webm"
        )
        return file_key
```

### EHR Integration Service

**Responsibilities:**
- Generate FHIR R4 compliant JSON documents
- Validate FHIR documents against schema
- Transmit documents to EHR endpoints
- Track export status

**Interface:**
```python
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class EHRService:
    async def generate_fhir_document(self, triage_record: TriageRecord, patient: Patient) -> FHIRDocument:
        """Generate FHIR R4 compliant document"""
        pass
    
    async def validate_fhir_document(self, document: FHIRDocument) -> ValidationResult:
        """Validate FHIR document against schema"""
        pass
    
    async def export_to_ehr(self, document: FHIRDocument) -> ExportResult:
        """Export document to EHR system"""
        pass
    
    async def get_export_status(self, triage_id: str) -> ExportStatus:
        """Get export status for triage record"""
        pass

class FHIRDocument(BaseModel):
    resourceType: str = 'Bundle'
    type: str = 'transaction'
    entry: List['FHIRResource']

class FHIRResource(BaseModel):
    resource: Dict[str, Any]

class ValidationResult(BaseModel):
    is_valid: bool
    errors: List[str]

class ExportResult(BaseModel):
    success: bool
    ehr_record_id: Optional[str] = None
    error: Optional[str] = None

class ExportStatus(BaseModel):
    triage_id: str
    status: str  # 'pending' | 'success' | 'failed'
    exported_at: Optional[str] = None
    ehr_record_id: Optional[str] = None
    error: Optional[str] = None
```

### Analytics Service

**Responsibilities:**
- Aggregate daily statistics
- Generate trend analysis data
- Provide visualization-ready datasets

**Interface:**
```python
from pydantic import BaseModel
from typing import List

class AnalyticsService:
    async def get_daily_stats(self, date: str) -> DailyStats:
        """Get statistics for a specific date"""
        pass
    
    async def get_trend_analysis(self, start_date: str, end_date: str) -> TrendData:
        """Get trend analysis for date range"""
        pass
    
    async def get_specialty_distribution(self, start_date: str, end_date: str) -> List[SpecialtyStats]:
        """Get specialty distribution for date range"""
        pass

class DailyStats(BaseModel):
    date: str
    total_patients: int
    average_risk_score: float
    critical_count: int
    urgent_count: int
    routine_count: int
    specialty_breakdown: List['SpecialtyStats']

class TrendData(BaseModel):
    time_series: List['TimeSeriesPoint']
    chief_complaint_frequency: List['ComplaintFrequency']

class TimeSeriesPoint(BaseModel):
    date: str
    patient_count: int
    average_risk_score: float

class ComplaintFrequency(BaseModel):
    complaint: str
    count: int
    percentage: float

class SpecialtyStats(BaseModel):
    specialty: str
    count: int
    percentage: float
    average_risk_score: float
```

## Data Models

### Database Schema

**users table:**
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  hospital_id VARCHAR(50) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  name VARCHAR(255) NOT NULL,
  role VARCHAR(20) NOT NULL CHECK (role IN ('receptionist', 'nurse', 'doctor')),
  specialty VARCHAR(50),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_hospital_id ON users(hospital_id);
CREATE INDEX idx_users_role ON users(role);
```

**patients table:**
```sql
CREATE TABLE patients (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  hospital_id VARCHAR(50) UNIQUE NOT NULL,
  name_encrypted BYTEA NOT NULL,
  date_of_birth_encrypted BYTEA NOT NULL,
  gender VARCHAR(20),
  contact_number_encrypted BYTEA,
  address_encrypted BYTEA,
  preferred_language VARCHAR(20) DEFAULT 'en',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_patients_hospital_id ON patients(hospital_id);
```

**triage_records table:**
```sql
CREATE TABLE triage_records (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  patient_id UUID NOT NULL REFERENCES patients(id),
  audio_file_path_encrypted BYTEA NOT NULL,  -- Encrypted local file path
  audio_encryption_key_id VARCHAR(255) NOT NULL,  -- Encryption key ID for audio file
  language VARCHAR(20) NOT NULL,
  transcription TEXT,
  translation TEXT,
  soap_subjective TEXT,
  soap_objective TEXT,
  soap_assessment TEXT,
  soap_plan TEXT,
  risk_score INTEGER CHECK (risk_score >= 0 AND risk_score <= 100),
  specialty VARCHAR(50),
  status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'finalized', 'exported')),
  acoustic_anomalies JSONB,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  finalized_at TIMESTAMP,
  finalized_by UUID REFERENCES users(id)
);

CREATE INDEX idx_triage_patient_id ON triage_records(patient_id);
CREATE INDEX idx_triage_status ON triage_records(status);
CREATE INDEX idx_triage_specialty ON triage_records(specialty);
CREATE INDEX idx_triage_risk_score ON triage_records(risk_score DESC);
CREATE INDEX idx_triage_created_at ON triage_records(created_at DESC);
```

**vital_signs table:**
```sql
CREATE TABLE vital_signs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  triage_id UUID NOT NULL REFERENCES triage_records(id),
  temperature DECIMAL(4, 1),
  blood_pressure_systolic INTEGER,
  blood_pressure_diastolic INTEGER,
  heart_rate INTEGER,
  respiratory_rate INTEGER,
  oxygen_saturation INTEGER,
  recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  recorded_by UUID NOT NULL REFERENCES users(id)
);

CREATE INDEX idx_vitals_triage_id ON vital_signs(triage_id);
```

**visits table:**
```sql
CREATE TABLE visits (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  patient_id UUID NOT NULL REFERENCES patients(id),
  triage_id UUID REFERENCES triage_records(id),
  visit_date TIMESTAMP NOT NULL,
  chief_complaint TEXT,
  diagnosis TEXT,
  specialty VARCHAR(50),
  risk_score INTEGER,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_visits_patient_id ON visits(patient_id);
CREATE INDEX idx_visits_visit_date ON visits(visit_date DESC);
```

**audit_logs table:**
```sql
CREATE TABLE audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  action VARCHAR(50) NOT NULL,
  resource_type VARCHAR(50) NOT NULL,
  resource_id UUID,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  ip_address VARCHAR(45)
);

CREATE INDEX idx_audit_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp DESC);
```

### Encryption Strategy

**PII Fields Requiring Encryption:**
- Patient name
- Date of birth
- Contact number
- Address
- Audio file paths (local file system)

**Database Encryption (Data-at-Rest):**
- Use PostgreSQL Transparent Data Encryption (TDE) or encrypted storage volumes
- Application-layer encryption using AES-256 for PII fields via pgcrypto
- Store encryption keys in local secrets store or environment variables (not in database)
- Encrypt at application layer before database insertion
- Decrypt at application layer after retrieval

**Audio File Encryption (Local File System):**
- Store all audio files in encrypted local file system with AES-256
- Use Python cryptography library (Fernet) for file encryption
- Encryption keys stored in local secrets management system
- File permissions set to 0600 (owner read/write only)
- Directory permissions set to 0700 (owner access only)
- Optional: Use LUKS (Linux Unified Key Setup) for full disk encryption
- Optional: MinIO with server-side encryption for S3-compatible local storage

**Encryption in Transit:**
- All API communications use TLS 1.2 or higher
- Local file access uses encrypted file system
- Database connections use SSL/TLS use SSL/TLS

**Implementation:**

**Database Encryption Example:**
```python
from cryptography.fernet import Fernet

class EncryptionService:
    def __init__(self, key: bytes):
        self.cipher = Fernet(key)
    
    def encrypt(self, plaintext: str) -> bytes:
        """Encrypt plaintext string to bytes"""
        return self.cipher.encrypt(plaintext.encode())
    
    def decrypt(self, ciphertext: bytes) -> str:
        """Decrypt bytes to plaintext string"""
        return self.cipher.decrypt(ciphertext).decode()
```

**Local File Storage with Encryption Example:**
```python
import os
from pathlib import Path
from cryptography.fernet import Fernet
import hashlib

class LocalEncryptedStorage:
    def __init__(self, base_path: str, encryption_key: bytes):
        self.base_path = Path(base_path)
        self.cipher = Fernet(encryption_key)
        
        # Create secure directory
        self.base_path.mkdir(parents=True, exist_ok=True)
        os.chmod(self.base_path, 0o700)
    
    async def save_file(self, file_data: bytes, file_key: str) -> str:
        """Save encrypted file to local storage"""
        file_path = self.base_path / file_key
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Encrypt and save
        encrypted_data = self.cipher.encrypt(file_data)
        file_path.write_bytes(encrypted_data)
        
        # Set secure permissions (owner read/write only)
        os.chmod(file_path, 0o600)
        
        return str(file_path)
    
    async def read_file(self, file_key: str) -> bytes:
        """Read and decrypt file from local storage"""
        file_path = self.base_path / file_key
        encrypted_data = file_path.read_bytes()
        return self.cipher.decrypt(encrypted_data)
    
    async def delete_file(self, file_key: str) -> bool:
        """Securely delete file"""
        file_path = self.base_path / file_key
        if file_path.exists():
            # Overwrite with random data before deletion (secure delete)
            file_size = file_path.stat().st_size
            file_path.write_bytes(os.urandom(file_size))
            file_path.unlink()
            return True
        return False
```

**Key Management:**
- Use local secrets management system (e.g., HashiCorp Vault, systemd-creds)
- Implement key rotation policies (manual or automated)
- Use separate encryption keys for different environments (dev, staging, prod)
- Store master key in hardware security module (HSM) or secure enclave
- Enable audit logging for all key access operations
- Never store keys in code or configuration files

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Authentication and Authorization Properties

**Property 1: Role-based access control**
*For any* user with an assigned role, the system should grant access only to features authorized for that role and deny access to all other features.
**Validates: Requirements 1.4, 1.5, 1.6, 1.7**

**Property 2: Successful authentication redirects to role-specific dashboard**
*For any* valid user credentials, successful authentication should redirect the user to the correct dashboard for their role within the specified time limit.
**Validates: Requirements 1.2, 1.3**

### Patient Identification Properties

**Property 3: Patient identification method equivalence**
*For any* valid Hospital_ID, retrieving a patient profile via manual entry should produce identical results to retrieving via QR code scan.
**Validates: Requirements 2.1, 2.2, 2.5**

**Property 4: Patient profile completeness**
*For any* retrieved patient profile, the display should include patient name, demographics, and the last 3-5 visits with associated diagnoses.
**Validates: Requirements 2.3**

**Property 5: Invalid Hospital_ID error handling**
*For any* Hospital_ID that does not exist in the system, retrieval attempts should return an appropriate error message.
**Validates: Requirements 2.4**

### Audio Intake Properties

**Property 6: Multi-language audio recording**
*For any* supported language selection, the system should successfully record, store, and associate audio with the patient's intake record.
**Validates: Requirements 3.2, 3.3, 3.4**

**Property 7: Triage analysis initiation timing**
*For any* submitted intake with audio recording, triage analysis should initiate within the specified time threshold.
**Validates: Requirements 3.5**

### Triage Analysis Pipeline Properties

**Property 8: Complete triage analysis pipeline**
*For any* submitted audio intake, the system should execute all pipeline steps (acoustic anomaly detection, transcription, translation, SOAP generation, risk scoring) and complete within 5 seconds.
**Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6**

**Property 9: SOAP note structure completeness**
*For any* generated SOAP note, it should contain all four required sections: Subjective, Objective, Assessment, and Plan.
**Validates: Requirements 4.4**

**Property 10: Risk score range validity**
*For any* calculated risk score, the value should be within the valid range of 0-100 inclusive.
**Validates: Requirements 4.5**

**Property 11: Triage analysis error handling**
*For any* triage analysis that encounters an error, the system should log the error and notify the receptionist with a descriptive message.
**Validates: Requirements 4.7**

### Localization Properties

**Property 12: Localized instruction generation**
*For any* completed triage analysis and any supported patient language, the system should generate zone assignment instructions in that language with both text and audio (TTS) options available.
**Validates: Requirements 5.1, 5.2, 5.3, 5.4**

### Vital Signs Properties

**Property 13: Vital signs input validation**
*For any* entered vital sign values, the system should validate physiological plausibility and display warnings for out-of-range values without blocking submission.
**Validates: Requirements 6.2, 6.3**

**Property 14: Vital signs persistence and association**
*For any* submitted vital signs, the system should associate them with the correct triage record, include a timestamp, and update the risk score if thresholds are exceeded.
**Validates: Requirements 6.4, 6.5**

### Triage Queue Properties

**Property 15: Specialty filtering**
*For any* selected specialty filter, the triage queue should display only patients assigned to that specialty.
**Validates: Requirements 7.2**

**Property 16: Risk score sorting**
*For any* displayed triage queue, patients should be sorted by risk score in descending order (highest risk first).
**Validates: Requirements 7.3**

**Property 17: Risk-based color coding**
*For any* patient card in the queue, the color should match the risk score range: Red for Critical (≥70), Yellow for Urgent (40-69), Green for Routine (<40).
**Validates: Requirements 7.4**

**Property 18: Patient card information completeness**
*For any* patient card in the queue, it should display patient name, chief complaint summary, risk score, and time in queue.
**Validates: Requirements 7.5**

**Property 19: Real-time queue updates**
*For any* change to the triage queue (new patient, status change), the display should refresh within the specified time threshold.
**Validates: Requirements 7.6**

### SOAP Note Editing Properties

**Property 20: SOAP note display completeness**
*For any* selected patient, the SOAP note view should display all four sections (Subjective, Objective, Assessment, Plan), the patient's last visit date, and any longitudinal trend alerts.
**Validates: Requirements 8.1, 8.4**

**Property 21: SOAP note inline editing**
*For any* SOAP note section, the system should provide inline editing capabilities and auto-save changes within the specified time threshold.
**Validates: Requirements 8.2, 8.3**

**Property 22: SOAP note finalization state management**
*For any* SOAP note that is approved by a doctor, the system should mark it as finalized and prevent further edits without explicit unlock action.
**Validates: Requirements 8.5**

### EHR Integration Properties

**Property 23: FHIR document generation and validation**
*For any* finalized SOAP note, the system should generate a FHIR R4 compliant JSON document containing patient demographics, SOAP content, vitals, and risk score that passes schema validation.
**Validates: Requirements 9.2, 9.3**

**Property 24: FHIR validation error handling**
*For any* FHIR document that fails validation, the system should display validation errors and prevent export.
**Validates: Requirements 9.4**

**Property 25: Successful EHR export state management**
*For any* successfully exported FHIR document, the system should mark the patient record as exported and remove it from the active triage queue.
**Validates: Requirements 9.6**

### Analytics Properties

**Property 26: Daily statistics completeness**
*For any* analytics dashboard access, the system should display total patients triaged, average risk score, specialty distribution, and risk level categorization (Critical, Urgent, Routine) with counts and percentages.
**Validates: Requirements 10.1, 10.2**

**Property 27: Trend analysis visualization**
*For any* selected time period (7, 30, or 90 days), the system should display time-series graphs showing patient volume and chief complaint frequencies.
**Validates: Requirements 10.3, 10.4**

**Property 28: Analytics performance**
*For any* trend data request, the system should generate visualizations within the specified time threshold.
**Validates: Requirements 10.5**

### Security and Privacy Properties

**Property 29: PII encryption at rest**
*For any* stored patient data containing PII (name, DOB, contact, address), the data should be encrypted using AES-256 in the database.
**Validates: Requirements 11.1**

**Property 30: Audio file encryption with local storage**
*For any* audio file stored in local file system, the file should be encrypted using AES-256 with secure file permissions (0600).
**Validates: Requirements 11.5**

**Property 31: TLS encryption in transit**
*For any* network transmission of patient data, the connection should use TLS 1.2 or higher.
**Validates: Requirements 11.2**

**Property 32: PII anonymization in analytics**
*For any* patient data displayed in analytics dashboards, PII should be masked or anonymized to prevent identification.
**Validates: Requirements 11.3**

**Property 33: Audit logging**
*For any* user access to patient records, the system should create an audit log entry containing user ID, timestamp, and patient ID.
**Validates: Requirements 11.4**

**Property 34: Local model processing**
*For any* audio or text processing operation, all AI/ML inference should occur on local GPU servers without external API calls.
**Validates: Requirements 11.6 (Privacy-first architecture)**

**Property 35: Offline operation capability**
*For any* core triage workflow (audio intake, transcription, SOAP generation), the system should function without internet connectivity.
**Validates: Requirements 11.7 (Offline capability)**

### Performance Properties

**Property 34: UI responsiveness**
*For any* user action, the system should provide visual feedback within 200 milliseconds.
**Validates: Requirements 12.1**

**Property 35: Dashboard navigation performance**
*For any* navigation between dashboards, the new view should load within 2 seconds.
**Validates: Requirements 12.3**

**Property 36: Queue rendering performance**
*For any* triage queue containing up to 100 patients, the system should render the queue within 1 second.
**Validates: Requirements 12.4**

**Property 37: Concurrent user performance**
*For any* system state with up to 50 concurrent users, all operations should maintain response times within specified thresholds.
**Validates: Requirements 12.5**

## Privacy-First Architecture & Offline Capability

### Core Privacy Principles

**Data Sovereignty:**
- All patient health information (PHI) remains within hospital network perimeter
- No external API calls for processing sensitive medical data
- Air-gapped deployment option available for maximum security
- Complete control over data lifecycle and retention

**Local AI Processing:**
- All AI/ML models deployed on hospital-owned GPU servers
- Whisper, HeAR, MedGemma, translation, and TTS models run locally
- Zero telemetry or usage data sent to external services
- Model updates via secure file transfer (USB/encrypted channels)

**Offline Operation:**
- Core triage workflow functions without internet connectivity
- Audio recording, transcription, SOAP generation work offline
- Local database and file storage ensure data availability
- Optional EHR export when network is available

### Deployment Models

**Standard Deployment (Recommended):**
- Hospital internal network with internet access for EHR integration
- Local AI models on GPU servers
- Encrypted local storage for audio files
- PostgreSQL database on local servers
- TLS-secured communication within hospital network

**Air-Gapped Deployment (Maximum Security):**
- Completely isolated from external networks
- All components run on isolated hospital network
- Model updates via physical media (USB drives)
- Manual EHR export via secure file transfer
- Ideal for high-security environments or regions with unreliable connectivity

**Hybrid Deployment (Not Recommended):**
- Local AI processing with cloud-based EHR integration
- Requires VPN or secure tunnel for EHR communication
- Maintains data sovereignty for PHI processing
- Only non-PHI metadata transmitted externally

### Hardware Requirements

**Minimum Configuration:**
- CPU: 8 cores (Intel/AMD x86_64)
- RAM: 16GB
- Storage: 100GB SSD + 500GB encrypted storage
- Network: Gigabit Ethernet (hospital internal)
- Ollama: Installed and configured

**Recommended Configuration:**
- CPU: 16+ cores (Intel/AMD x86_64)
- RAM: 32GB (64GB for high-volume hospitals)
- Storage: 200GB NVMe SSD + 1TB+ encrypted storage
- Network: 10 Gigabit Ethernet (hospital internal)
- Backup: Redundant power supply, RAID storage
- GPU: Optional NVIDIA GPU for faster inference (auto-detected by Ollama)

**High-Availability Configuration:**
- 2+ servers for load balancing and failover
- PostgreSQL replication (primary + standby)
- Shared storage (NFS/Ceph) for audio files
- Load balancer for FastAPI instances
- Monitoring and alerting system
- Ollama instances on each server

### Compliance and Certification

**HIPAA Compliance:**
- Administrative safeguards: Access controls, audit logs, training
- Physical safeguards: Secure server room, access restrictions
- Technical safeguards: Encryption, authentication, audit trails
- No Business Associate Agreements (BAA) required for local deployment

**Data Retention:**
- Audio files: Configurable retention (default 90 days)
- Triage records: Permanent storage with encryption
- Audit logs: Minimum 7 years retention
- Secure deletion: Overwrite with random data before file deletion

**Audit and Monitoring:**
- All PHI access logged with user ID, timestamp, action
- Failed authentication attempts logged and alerted
- Model inference requests logged for quality assurance
- System health monitoring (GPU utilization, disk space, etc.)

### Disaster Recovery

**Backup Strategy:**
- Daily encrypted database backups to separate storage
- Audio file backups with retention policy
- Model files backed up after updates
- Configuration and secrets backed up securely

**Recovery Procedures:**
- Database restore from latest backup (RPO: 24 hours)
- Audio file restore from backup storage
- Model redeployment from backup files
- Configuration restore and service restart

**Business Continuity:**
- Failover to standby server in high-availability setup
- Manual operation mode if AI models fail
- Paper-based triage as ultimate fallback
- Regular disaster recovery drills

## Error Handling

### Error Categories

**Authentication Errors:**
- Invalid credentials: Return 401 Unauthorized with message "Invalid Hospital ID or password"
- Expired session: Return 401 Unauthorized with message "Session expired, please log in again"
- Missing token: Return 401 Unauthorized with message "Authentication required"
- Insufficient permissions: Return 403 Forbidden with message "You do not have permission to access this resource"

**Patient Identification Errors:**
- Patient not found: Return 404 Not Found with message "Patient with Hospital ID {id} not found"
- Invalid QR code format: Return 400 Bad Request with message "Invalid QR code format"
- QR code scan failure: Display user-friendly message "Unable to scan QR code. Please try again or enter Hospital ID manually"

**Audio Processing Errors:**
- Audio recording failure: Display message "Unable to record audio. Please check microphone permissions"
- Unsupported language: Return 400 Bad Request with message "Language {language} is not supported"
- Transcription service failure: Log error, display message "Unable to process audio. Please try again or contact support"
- Translation service failure: Log error, display message "Unable to translate audio. Please try again or contact support"
- SOAP generation failure: Log error, display message "Unable to generate clinical notes. Please try again or contact support"
- Triage analysis timeout: Display message "Triage analysis is taking longer than expected. Please wait or try again"

**Vital Signs Errors:**
- Invalid vital value format: Display inline error "Please enter a valid numeric value"
- Physiologically implausible value: Display warning "This value is outside normal ranges. Please verify before submitting"
- Missing required vitals: Display message "Please enter all required vital signs before submitting"

**SOAP Note Errors:**
- Auto-save failure: Display toast notification "Unable to save changes. Retrying..."
- Concurrent edit conflict: Display message "This note was modified by another user. Please refresh and try again"
- Finalized note edit attempt: Display message "This note is finalized. Please unlock it before editing"

**EHR Integration Errors:**
- FHIR validation failure: Display detailed validation errors in modal dialog
- EHR endpoint unreachable: Log error, display message "Unable to connect to EHR system. Please try again later"
- EHR export failure: Log error, display message "Export failed. The record remains in the queue for retry"
- Network timeout: Display message "Export is taking longer than expected. The operation will continue in the background"

**Database Errors:**
- Connection failure: Log error, return 503 Service Unavailable with message "Database temporarily unavailable"
- Query timeout: Log error, return 504 Gateway Timeout with message "Request timed out. Please try again"
- Constraint violation: Log error, return 400 Bad Request with appropriate message based on constraint

**General Error Handling Strategy:**
- All errors should be logged with sufficient context for debugging (timestamp, user ID, request details, stack trace)
- User-facing error messages should be clear, actionable, and avoid exposing technical details
- Transient errors (network, timeout) should trigger automatic retry with exponential backoff
- Critical errors should trigger alerts to system administrators
- All API responses should follow consistent error format:
  ```json
  {
    "error": {
      "code": "ERROR_CODE",
      "message": "User-friendly error message",
      "details": {} // Optional additional context
    }
  }
  ```

## Testing Strategy

### Dual Testing Approach

The testing strategy employs both unit testing and property-based testing to ensure comprehensive coverage:

**Unit Tests:**
- Verify specific examples and edge cases
- Test integration points between components
- Validate error conditions and boundary cases
- Focus on concrete scenarios that demonstrate correct behavior

**Property-Based Tests:**
- Verify universal properties across all inputs
- Use randomized input generation to discover edge cases
- Ensure correctness properties hold for large input spaces
- Minimum 100 iterations per property test

Both approaches are complementary and necessary: unit tests catch concrete bugs in specific scenarios, while property tests verify general correctness across the entire input domain.

### Property-Based Testing Configuration

**Framework Selection:**
- **Python/FastAPI Backend**: Use `hypothesis` library for property-based testing
- **JavaScript/TypeScript Frontend**: Use `fast-check` library for frontend component testing

**Test Configuration:**
- Each property test must run minimum 100 iterations
- Use appropriate generators for domain-specific types (Hospital_ID, Risk_Score, etc.)
- Configure timeouts appropriately for async operations
- Seed random generators for reproducibility in CI/CD

**Property Test Tagging:**
Each property-based test must include a comment tag referencing the design document property:

**Python Backend Example:**
```python
from hypothesis import given, strategies as st
import pytest

# Feature: tele-triage-2.0, Property 1: Role-based access control
@given(
    user=user_generator(),
    feature=feature_generator()
)
@pytest.mark.asyncio
async def test_user_access_restricted_to_authorized_features(user, feature):
    """Verify users can only access features authorized for their role"""
    has_access = await check_access(user, feature)
    is_authorized = user.role == feature.required_role
    assert has_access == is_authorized
```

**TypeScript Frontend Example:**
```typescript
// Feature: tele-triage-2.0, Property 1: Role-based access control
test('user access is restricted to authorized features for their role', async () => {
  await fc.assert(
    fc.asyncProperty(
      userGenerator(),
      featureGenerator(),
      async (user, feature) => {
        const hasAccess = await checkAccess(user, feature);
        const isAuthorized = user.role === feature.requiredRole;
        expect(hasAccess).toBe(isAuthorized);
      }
    ),
    { numRuns: 100 }
  );
});
```

### Testing Scope by Component

**Authentication Service:**
- Unit tests: Valid login, invalid credentials, token expiration, role assignment
- Property tests: Property 1 (RBAC), Property 2 (authentication redirect)

**Patient Service:**
- Unit tests: Patient retrieval, visit history, demographics update
- Property tests: Property 3 (identification equivalence), Property 4 (profile completeness), Property 5 (error handling)

**Triage Service:**
- Unit tests: Audio upload, vitals entry, queue filtering, SOAP editing
- Property tests: Property 6-11 (audio intake and analysis), Property 13-14 (vitals), Property 15-19 (queue management), Property 20-22 (SOAP editing)

**Audio Processing Pipeline:**
- Unit tests: Mock local model responses, error scenarios, timeout handling
- Property tests: Property 8 (complete pipeline), Property 9 (SOAP structure), Property 10 (risk score range)
- Use pytest-asyncio for async test support
- Mock LOCAL Whisper, HeAR (HAI-DEF), and MedGemma 4B (HAI-DEF) model responses for consistent testing
- Test model integration with sample audio files and expected outputs
- Test offline operation without network connectivity

**Localization Service:**
- Unit tests: Specific language examples (Tamil, Hindi, English)
- Property tests: Property 12 (localized instruction generation)
- Test local TTS engine (Piper/Coqui) with multiple languages

**EHR Integration Service:**
- Unit tests: FHIR document structure, schema validation, export success/failure
- Property tests: Property 23-25 (FHIR generation, validation, export)

**Analytics Service:**
- Unit tests: Statistics calculation, time period filtering, data aggregation
- Property tests: Property 26-28 (analytics completeness and performance)

**Security and Encryption:**
- Unit tests: Encryption/decryption round-trip, TLS configuration, audit log creation, local file encryption
- Property tests: Property 29-35 (database encryption, local file encryption, TLS, anonymization, audit logging, local processing, offline capability)
- Test file permissions (0600 for files, 0700 for directories)
- Test secure file deletion with overwrite

**Performance Testing:**
- Load tests: Simulate 50 concurrent users, measure response times
- Property tests: Property 34-37 (UI responsiveness, navigation, rendering, concurrent users)

### Integration Testing

**End-to-End Workflows:**
1. Receptionist workflow: Login → Patient identification → Audio intake → Localized instructions
2. Nurse workflow: Login → Patient selection → Vitals entry → Risk score update
3. Doctor workflow: Login → Queue filtering → SOAP review/edit → EHR export
4. Analytics workflow: Login → Dashboard access → Trend analysis → Report generation

**Local Model Mocking:**
- Mock LOCAL Whisper model outputs for transcription testing
- Mock LOCAL HeAR (HAI-DEF) model outputs for acoustic anomaly testing
- Mock LOCAL MedGemma 4B (HAI-DEF) model outputs for SOAP generation testing
- Mock LOCAL translation model (NLLB-200/IndicTrans2) for translation testing
- Mock LOCAL TTS engine (Piper/Coqui) for audio generation testing
- Use pytest fixtures for reusable mocks
- Use httpx-mock or respx for HTTP mocking in FastAPI tests

**Database Testing:**
- Use test database with seed data for integration tests
- Test encryption/decryption with actual pgcrypto functions
- Verify audit log creation for all patient record access
- Test concurrent access scenarios with transaction isolation
- Use pytest-postgresql for test database management
- Use Alembic migrations in test environment

### Continuous Integration

**CI/CD Pipeline:**
1. Run unit tests on every commit
2. Run property-based tests on every pull request
3. Run integration tests on merge to main branch
4. Run load tests weekly or before major releases
5. Generate code coverage reports (target: 80% coverage)

**Test Environment:**
- Separate test database with anonymized data
- Mock external services to avoid API costs and rate limits
- Use Docker containers for consistent test environments
- Automated test data generation and cleanup
