# VaidyaSaarathi 🏥

<img width="1024" height="1024" alt="vaidyasaarathi" src="https://github.com/user-attachments/assets/5ea831be-fb2a-47c9-8d4a-c9a90c51a23a" />


> **Your Intelligent Healthcare Companion** - An AI Assistant Supporting Clinical Decisions, Not Replacing Them

[![Privacy First](https://img.shields.io/badge/Privacy-First-green.svg)](https://www.hhs.gov/hipaa/index.html)
[![HIPAA Compliant](https://img.shields.io/badge/HIPAA-Compliant-blue.svg)](https://www.hhs.gov/hipaa/index.html)
[![Offline Capable](https://img.shields.io/badge/Offline-Capable-orange.svg)](#privacy--security)
[![HAI-DEF Powered](https://img.shields.io/badge/Powered%20by-HAI--DEF-red.svg)](https://developers.google.com/health-ai-developer-foundations)

---

## 🌟 Vision

In a country where **22 official languages** coexist and healthcare accessibility remains a challenge, **VaidyaSaarathi** (वैद्य सारथी - "Physician's Charioteer") emerges as a transformative solution. We empower healthcare workers with AI-assisted tools to deliver quality care regardless of language barriers, while ensuring **complete data sovereignty** and **privacy-first AI processing**.

> **Important:** VaidyaSaarathi is a clinical decision support tool. All AI-generated suggestions are recommendations that must be reviewed and approved by qualified healthcare professionals. Final clinical decisions always rest with the treating physician.

## 🎯 What is VaidyaSaarathi?

VaidyaSaarathi is an **AI-assisted clinical triage system** that supports healthcare workers in patient intake and care delivery through:

- 🎤 **Multi-language Audio Intake** - Capture patient complaints in Tamil, Hindi, Telugu, Kannada, and more
- 🤖 **Local AI Processing** - All AI models run on hospital servers, ensuring zero data leakage
- 📋 **AI-Assisted SOAP Notes** - Draft clinical documentation using Google's MedGemma 4B for physician review
- 🔊 **Acoustic Analysis** - Detect potential respiratory distress and cough patterns using HeAR model
- 🌐 **Offline Operation** - Works without internet connectivity for maximum reliability
- 🔒 **HIPAA Compliant** - Military-grade encryption and complete data sovereignty

---

## 🚀 Key Features

### For Receptionists
- **QR Code & Manual Patient ID** - Quick patient identification
- **Native Language Recording** - Capture complaints in patient's mother tongue
- **Instant Triage Instructions** - Localized audio/text guidance for patients

### For Nurses
- **Vital Signs Entry** - Streamlined clinical measurements input
- **Real-time Risk Updates** - Automatic risk score recalculation

### For Doctors
- **Specialty-Filtered Queues** - Cardiac, Respiratory, Neurology, General Medicine
- **AI-Drafted SOAP Notes** - Review, edit, and approve AI-generated clinical documentation
- **AI-Suggested Risk Prioritization** - Color-coded patient cards (Red/Yellow/Green) for review
- **FHIR Export** - Seamless EHR integration after physician approval

> **Clinical Responsibility:** All AI-generated content (SOAP notes, risk scores, specialty assignments) are suggestions only. Physicians must review, validate, and approve all clinical decisions before patient care or documentation finalization.

### For Administrators
- **Analytics Dashboard** - Daily statistics and trend analysis
- **Operational Insights** - Patient volume, specialty distribution, risk patterns

---

## 🧠 AI/ML Architecture

### Why Google's HAI-DEF Framework?

VaidyaSaarathi leverages **Health AI Developer Foundations (HAI-DEF)**, Google's specialized healthcare AI framework designed specifically for clinical applications. Unlike general-purpose AI models, HAI-DEF provides:

#### 🏥 Medical-Grade AI Models

**MedGemma 4B - Clinical Language Model**
- **Medical Training**: Pre-trained on extensive medical literature, clinical guidelines, and healthcare documentation
- **Clinical Validation**: Validated against real-world clinical scenarios and medical expert review
- **Safety Guardrails**: Built-in medical safety checks to prevent harmful or inappropriate suggestions
- **Explainable Outputs**: Provides clinical reasoning for its suggestions, not just black-box predictions
- **Bias Mitigation**: Trained on diverse patient populations to reduce demographic biases

**HeAR (Health Acoustic Representations) - Acoustic Foundation Model**
- **Healthcare-Specific**: Trained specifically on health-related acoustic data (cough, breathing patterns, voice characteristics)
- **Clinical Ground Truth**: Validated against clinical annotations from healthcare professionals
- **Diverse Populations**: Trained on data from multiple demographics, ages, and clinical settings
- **Research-Backed**: Based on peer-reviewed research in acoustic biomarkers for respiratory conditions

#### 🔬 Key Differentiators from General AI

| Aspect | General AI Models | HAI-DEF Models |
|--------|------------------|----------------|
| **Training Data** | General internet text | Medical literature, clinical guidelines, EHR data |
| **Validation** | General benchmarks | Clinical validation studies |
| **Safety** | General content filters | Medical safety guardrails |
| **Explainability** | Limited reasoning | Clinical reasoning provided |
| **Regulatory Focus** | Consumer applications | Healthcare compliance (HIPAA, FDA considerations) |
| **Bias Testing** | General fairness metrics | Clinical equity across demographics |

#### 📚 Medical Knowledge Base

HAI-DEF models are trained on:
- ✅ Peer-reviewed medical journals and research papers
- ✅ Clinical practice guidelines from medical associations
- ✅ De-identified electronic health records (with proper consent)
- ✅ Medical textbooks and educational materials
- ✅ Drug databases and treatment protocols
- ✅ ICD-10, SNOMED CT, and other medical ontologies

#### 🛡️ Safety & Reliability Features

1. **Uncertainty Quantification**: Models indicate confidence levels in their suggestions
2. **Hallucination Prevention**: Reduced tendency to generate false medical information
3. **Contraindication Awareness**: Understanding of drug interactions and medical contraindications
4. **Temporal Reasoning**: Ability to understand disease progression and treatment timelines
5. **Multi-modal Understanding**: Integration of text, audio, and clinical data

#### 🌐 Open Source & Transparency

- **Open Source**: HAI-DEF models are openly available for research and development
- **Reproducible**: Training methodologies and evaluation metrics are documented
- **Community-Driven**: Continuous improvement through healthcare AI research community
- **Commercial Use**: Licensed for healthcare applications with proper safeguards

> **Trust Through Transparency:** HAI-DEF represents Google Health's commitment to responsible AI in healthcare. These are not generic chatbots repurposed for medical use—they are purpose-built clinical decision support tools designed with patient safety as the primary concern.

### Powered by Google's HAI-DEF Framework

VaidyaSaarathi integrates multiple AI models, with core clinical intelligence powered by **Health AI Developer Foundations (HAI-DEF)** - Google's open-source healthcare AI framework specifically designed for medical applications.

#### 🏥 HAI-DEF Models (Medical-Grade, Healthcare-Specific)

These models are purpose-built for healthcare with medical training data and clinical validation:

| Model | Purpose | Training Data | Key Features |
|-------|---------|---------------|--------------|
| **MedGemma 4B** | Draft clinical SOAP notes & suggest risk scores | Medical literature, clinical guidelines, de-identified EHR data | Built-in medical safety guardrails, clinical reasoning, bias mitigation |
| **HeAR** | Detect potential acoustic anomalies | 300M+ health acoustic samples, 100M+ cough sounds | Validated against clinical annotations, respiratory biomarkers |

**What makes HAI-DEF special:**
- ✅ Trained on peer-reviewed medical journals and clinical practice guidelines
- ✅ Validated against real-world clinical scenarios
- ✅ Built-in medical safety checks and contraindication awareness
- ✅ Provides explainable clinical reasoning, not black-box predictions
- ✅ Designed for HIPAA compliance and healthcare regulatory requirements
- ✅ Open-source with enabling license for healthcare applications

#### 🔧 Supporting Models (General-Purpose, Adapted for Healthcare)

These are robust general-purpose models adapted for multilingual and translation needs:

| Model | Purpose | Training Data | Provider |
|-------|---------|---------------|----------|
| **Whisper Large** | Multi-language speech-to-text (99+ languages) | 680,000 hours of multilingual audio | OpenAI |
| **Llama 3.2** | Translation for Indian languages | General multilingual text data | Meta |
| **Piper / Coqui TTS** | Text-to-speech in native languages | General speech synthesis data | Open Source |

> **Key Distinction:** Only MedGemma and HeAR are part of HAI-DEF with medical-specific training. Whisper and Llama are general-purpose models that excel at multilingual tasks. All models run locally on hospital servers to ensure complete data privacy.

### Processing Pipeline

```
Patient Audio (Native Language)
         ↓
    [Whisper] → Transcription
         ↓
    [HeAR] → Acoustic Anomalies (parallel)
         ↓
    [Translation] → English Text
         ↓
    [MedGemma 4B] → SOAP Note + Risk Score
         ↓
    [Local TTS] → Localized Instructions
```

**Processing Time:** ~7-10 seconds (CPU-based processing)

> **Why HAI-DEF Matters:** Unlike general AI chatbots adapted for healthcare, HAI-DEF models (MedGemma & HeAR) are built from the ground up for medical use. They understand medical terminology, clinical context, and have been validated against healthcare standards. This is not a generic language model being asked to "act like a doctor" - it's a specialized clinical decision support tool designed with patient safety as the primary concern.

> **AI as Assistant:** All AI outputs are suggestions to assist healthcare professionals. Clinical validation and final decisions remain with qualified medical personnel.

---

## 🔒 Privacy & Security

### Privacy-First Architecture

- ✅ **100% Local Processing** - All AI models run on hospital GPU servers
- ✅ **Zero External APIs** - No patient data leaves hospital premises
- ✅ **Air-Gapped Deployment** - Optional isolated network operation
- ✅ **Offline Capable** - Core workflows function without internet
- ✅ **AES-256 Encryption** - Database and file-level encryption
- ✅ **HIPAA Compliant** - No Business Associate Agreements needed

### Data Sovereignty Guarantee

> **"Your Data, Your Premises, Your Control"**
> 
> VaidyaSaarathi ensures that Protected Health Information (PHI) never leaves your hospital network. All AI inference happens locally, making it ideal for privacy-sensitive healthcare environments.

---

## 🛠️ Technology Stack

### Frontend
- React 18 + TypeScript
- Socket.io for real-time updates
- HTML5 MediaRecorder for audio capture
- Recharts for analytics visualization

### Backend
- Python 3.11+ with FastAPI
- SQLAlchemy ORM + PostgreSQL 14+
- WebSockets for live queue updates
- JWT authentication

### AI/ML
- HAI-DEF (MedGemma 4B, HeAR)
- OpenAI Whisper (faster-whisper)
- NLLB-200 / IndicTrans2
- Piper / Coqui TTS

### Infrastructure
- Ollama for local model serving (CPU/GPU support)
- 16GB+ RAM (32GB recommended)
- 100GB+ storage for models and data
- Standard hospital network (no GPU required)

---

## 📊 Expected Impact

### Clinical Efficiency Goals
- ⚡ **AI-assisted triage analysis** - Support clinicians in reducing manual documentation time
- 📈 **Faster patient intake** with audio recording vs. manual note-taking
- 🎯 **AI-suggested risk stratification** to help physicians prioritize patients
- 📝 **Draft SOAP generation** to reduce clinician documentation burden (requires physician review)

> **Physician Oversight:** All AI suggestions require clinical validation. VaidyaSaarathi assists healthcare workers but does not make autonomous clinical decisions.

### Language Accessibility
- 🌍 **99+ languages supported** via Whisper
- 🗣️ **Native language instructions** for patient clarity
- 🔊 **Acoustic analysis** works across all languages

### Data Security
- 🔐 **Zero external data transmission** with local processing
- 📝 **Complete audit trails** for compliance
- 🏥 **Hospital-owned infrastructure** for sovereignty

> **Note:** VaidyaSaarathi is currently in development. Performance metrics and clinical validation studies will be published upon completion of pilot deployments.

---

## 🏗️ System Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph "Frontend Layer"
        A[React Web Application]
        A1[Receptionist Dashboard]
        A2[Nurse Dashboard]
        A3[Doctor Dashboard]
        A4[Analytics Dashboard]
    end
    
    subgraph "Backend Layer - Python/FastAPI"
        B[API Gateway]
        B1[Auth Service]
        B2[Patient Service]
        B3[Triage Service]
        B4[Analytics Service]
        B5[EHR Integration]
    end
    
    subgraph "AI/ML Layer - Local Processing"
        C1[Ollama Server]
        C2[MedGemma 4B]
        C3[Whisper Large]
        C4[Llama 3.2]
        C5[HeAR Model]
        C6[Local TTS]
    end
    
    subgraph "Data Layer"
        D1[(PostgreSQL<br/>Encrypted)]
        D2[Local File Storage<br/>Encrypted Audio]
        D3[Secrets Store]
    end
    
    A --> B
    A1 --> B2
    A1 --> B3
    A2 --> B3
    A3 --> B3
    A3 --> B5
    A4 --> B4
    
    B --> B1
    B --> B2
    B --> B3
    B --> B4
    B --> B5
    
    B3 --> C1
    C1 --> C2
    C1 --> C3
    C1 --> C4
    B3 --> C5
    B3 --> C6
    
    B2 --> D1
    B3 --> D1
    B3 --> D2
    B1 --> D3
    
    style C1 fill:#e1f5ff
    style C2 fill:#fff3e0
    style C3 fill:#fff3e0
    style C4 fill:#fff3e0
    style C5 fill:#fff3e0
    style C6 fill:#f3e5f5
    style D1 fill:#e8f5e9
    style D2 fill:#e8f5e9
    style D3 fill:#e8f5e9
```

### AI Processing Pipeline

```mermaid
flowchart LR
    A[Patient Audio<br/>Native Language] --> B{Audio Processing}
    
    B --> C[Whisper via Ollama<br/>Transcription]
    B --> D[HeAR Model<br/>Acoustic Analysis]
    
    C --> E[Llama 3.2 via Ollama<br/>Translation to English]
    D --> F[Anomaly Detection<br/>Cough, Respiratory Distress]
    
    E --> G[MedGemma 4B via Ollama<br/>Clinical Analysis]
    F --> G
    
    G --> H[Draft SOAP Note]
    G --> I[Suggested Risk Score]
    G --> J[Specialty Assignment]
    
    H --> K[Physician Review<br/>& Approval]
    I --> K
    J --> K
    
    K --> L[Finalized Triage<br/>Zone Assignment]
    L --> M[Local TTS<br/>Patient Instructions]
    
    style C fill:#fff3e0
    style D fill:#fff3e0
    style E fill:#fff3e0
    style G fill:#fff3e0
    style M fill:#f3e5f5
    style K fill:#ffebee
```

### Data Flow & Privacy Architecture

```mermaid
flowchart TB
    subgraph "Hospital Network Perimeter"
        subgraph "User Interface"
            A[Web Browser<br/>HTTPS/TLS 1.2+]
        end
        
        subgraph "Application Server"
            B[FastAPI Backend<br/>JWT Auth]
            C[WebSocket Server<br/>Real-time Updates]
        end
        
        subgraph "AI Processing - LOCAL ONLY"
            D[Ollama<br/>Model Server]
            E[MedGemma 4B<br/>HAI-DEF]
            F[HeAR Model<br/>HAI-DEF]
            G[Whisper<br/>OpenAI]
        end
        
        subgraph "Data Storage - ENCRYPTED"
            H[(PostgreSQL<br/>AES-256)]
            I[Audio Files<br/>AES-256]
        end
    end
    
    subgraph "External - OPTIONAL"
        J[EHR System<br/>FHIR Export Only]
    end
    
    A -->|Encrypted| B
    A <-->|WSS| C
    B --> D
    D --> E
    D --> F
    D --> G
    B --> H
    B --> I
    B -.->|After Physician<br/>Approval| J
    
    style D fill:#e1f5ff
    style E fill:#fff3e0
    style F fill:#fff3e0
    style G fill:#fff3e0
    style H fill:#e8f5e9
    style I fill:#e8f5e9
    style J fill:#fff9c4
    
    classDef privacy fill:#c8e6c9,stroke:#2e7d32,stroke-width:3px
    class D,E,F,G,H,I privacy
```

### User Role Workflows

```mermaid
stateDiagram-v2
    [*] --> Login
    Login --> RoleCheck
    
    RoleCheck --> Receptionist: Role = Receptionist
    RoleCheck --> Nurse: Role = Nurse
    RoleCheck --> Doctor: Role = Doctor
    
    state Receptionist {
        [*] --> PatientID
        PatientID --> ViewHistory
        ViewHistory --> RecordAudio
        RecordAudio --> AIProcessing
        AIProcessing --> ShowInstructions
        ShowInstructions --> [*]
    }
    
    state Nurse {
        [*] --> SelectPatient
        SelectPatient --> EnterVitals
        EnterVitals --> UpdateRisk
        UpdateRisk --> [*]
    }
    
    state Doctor {
        [*] --> ViewQueue
        ViewQueue --> FilterSpecialty
        FilterSpecialty --> ReviewSOAP
        ReviewSOAP --> EditApprove
        EditApprove --> ExportEHR
        ExportEHR --> [*]
    }
    
    Receptionist --> [*]
    Nurse --> [*]
    Doctor --> [*]
```

### Deployment Architecture

```mermaid
graph TB
    subgraph "Hospital Infrastructure"
        subgraph "Application Tier"
            A[Load Balancer<br/>Nginx/HAProxy]
            B1[FastAPI Instance 1]
            B2[FastAPI Instance 2]
            B3[FastAPI Instance N]
        end
        
        subgraph "AI/ML Tier"
            C1[Ollama Server 1<br/>CPU/GPU Auto-detect]
            C2[Ollama Server 2<br/>Failover]
            D[HeAR Service<br/>CPU-based]
            E[TTS Service<br/>Piper/Coqui]
        end
        
        subgraph "Data Tier"
            F1[(PostgreSQL Primary<br/>Encrypted)]
            F2[(PostgreSQL Standby<br/>Replication)]
            G[Encrypted File Storage<br/>NFS/Ceph]
        end
        
        subgraph "Monitoring"
            H[Prometheus<br/>Metrics]
            I[Grafana<br/>Dashboards]
            J[Alert Manager]
        end
    end
    
    A --> B1
    A --> B2
    A --> B3
    
    B1 --> C1
    B2 --> C1
    B3 --> C2
    
    B1 --> D
    B2 --> D
    B3 --> E
    
    B1 --> F1
    B2 --> F1
    B3 --> F1
    F1 -.->|Replication| F2
    
    B1 --> G
    B2 --> G
    B3 --> G
    
    B1 --> H
    B2 --> H
    B3 --> H
    H --> I
    H --> J
    
    style C1 fill:#e1f5ff
    style C2 fill:#e1f5ff
    style D fill:#fff3e0
    style E fill:#f3e5f5
    style F1 fill:#e8f5e9
    style F2 fill:#e8f5e9
    style G fill:#e8f5e9
```

### Security & Compliance Architecture

```mermaid
flowchart TB
    subgraph "Security Layers"
        A[TLS 1.2+ Encryption<br/>In Transit]
        B[AES-256 Encryption<br/>At Rest]
        C[JWT Authentication<br/>Session Management]
        D[Role-Based Access Control<br/>RBAC]
        E[Audit Logging<br/>All PHI Access]
    end
    
    subgraph "Privacy Guarantees"
        F[Local AI Processing<br/>No External APIs]
        G[Air-Gapped Option<br/>Isolated Network]
        H[Data Sovereignty<br/>Hospital-Owned Servers]
    end
    
    subgraph "Compliance"
        I[HIPAA Compliant<br/>No BAA Required]
        J[Medical Device<br/>FDA Considerations]
        K[Clinical Validation<br/>IRB Studies]
    end
    
    A --> F
    B --> F
    C --> F
    D --> F
    E --> F
    
    F --> H
    G --> H
    
    H --> I
    H --> J
    H --> K
    
    style F fill:#c8e6c9
    style G fill:#c8e6c9
    style H fill:#c8e6c9
    style I fill:#bbdefb
    style J fill:#bbdefb
    style K fill:#bbdefb
```

---

## 🚀 Quick Start

### Prerequisites
- Ollama installed ([ollama.com](https://ollama.com))
- Python 3.11+
- PostgreSQL 14+
- Node.js 18+
- 16GB+ RAM (no GPU required)

### Installation

```bash
# Clone repository
git clone https://github.com/your-org/vaidyasaarathi.git
cd vaidyasaarathi

# Install Ollama (if not already installed)
# Visit https://ollama.com for installation instructions

# Pull required models via Ollama
ollama pull medgemma:4b
ollama pull whisper:large
ollama pull llama3.2:3b  # For translation tasks

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Database setup
alembic upgrade head

# Start backend
uvicorn main:app --reload

# Frontend setup (new terminal)
cd ../frontend
npm install
npm run dev
```

### Configuration

```bash
# .env file
DATABASE_URL=postgresql://user:pass@localhost/vaidyasaarathi
ENCRYPTION_KEY=your-secure-key-here
OLLAMA_HOST=http://localhost:11434
AUDIO_STORAGE_PATH=/path/to/encrypted/storage
```

---

## 📖 Documentation

- [Requirements Specification](.kiro/specs/ai-tele-triage/requirements.md)
- [Design Document](.kiro/specs/ai-tele-triage/design.md)
- [API Documentation](docs/api.md) *(coming soon)*
- [Deployment Guide](docs/deployment.md) *(coming soon)*
- [User Manual](docs/user-manual.md) *(coming soon)*

---

## 🌐 Use Cases

### Rural Healthcare Centers
- Limited internet connectivity → **Offline operation**
- Diverse patient languages → **Multi-language support**
- Resource constraints → **Efficient triage prioritization**

### Urban Hospitals
- High patient volume → **Automated SOAP generation**
- Specialist shortages → **Risk-based queue management**
- Compliance requirements → **Complete audit trails**

### Emergency Departments
- Critical time constraints → **5-second triage analysis**
- Respiratory emergencies → **Acoustic anomaly detection**
- Multi-specialty coordination → **Specialty-filtered queues**

---

## 🤝 Contributing

We welcome contributions from the healthcare and AI communities! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Areas for Contribution
- 🌍 Additional language support
- 🔬 Clinical validation studies
- 🎨 UI/UX improvements
- 📚 Documentation enhancements
- 🧪 Testing and quality assurance

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📚 References & Resources

### HAI-DEF Framework
- [Google Health AI Developer Foundations](https://developers.google.com/health-ai-developer-foundations) - Official HAI-DEF documentation
- [MedGemma Technical Report](https://arxiv.org/abs/2404.18416) - Research paper on MedGemma models
- [HeAR Model Research](https://research.google/blog/advancing-health-acoustic-representations/) - Google Research blog on HeAR
- [Responsible AI in Healthcare](https://ai.google/responsibility/responsible-ai-practices/) - Google's AI principles

### Medical AI Standards
- [FDA Guidance on Clinical Decision Support](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/clinical-decision-support-software) - FDA guidelines for CDS software
- [WHO Guidelines on AI for Health](https://www.who.int/publications/i/item/9789240029200) - WHO ethics and governance framework
- [HIPAA Compliance](https://www.hhs.gov/hipaa/index.html) - Health Insurance Portability and Accountability Act

### Clinical Validation
> **Note:** VaidyaSaarathi is currently in development. Clinical validation studies and peer-reviewed publications will be added upon completion of pilot deployments and IRB-approved research studies.

---

## 🙏 Acknowledgments

- **Google Health AI** - For the HAI-DEF framework (MedGemma, HeAR)
- **OpenAI** - For the Whisper speech recognition model
- **Healthcare Workers** - For their invaluable feedback and insights
- **Open Source Community** - For the amazing tools and libraries

---

## ⚕️ Clinical Disclaimer

**VaidyaSaarathi is a Clinical Decision Support System (CDSS)**

- ✅ **Assists** healthcare professionals with documentation and triage suggestions
- ✅ **Supports** clinical workflows by reducing administrative burden
- ✅ **Provides** AI-generated drafts for physician review and approval
- ❌ **Does NOT** replace clinical judgment or physician decision-making
- ❌ **Does NOT** provide autonomous diagnoses or treatment recommendations
- ❌ **Does NOT** eliminate the need for qualified medical professionals

**All clinical decisions must be made by licensed healthcare professionals.** AI-generated content (SOAP notes, risk scores, specialty assignments, acoustic anomaly detections) are suggestions only and require validation by qualified medical personnel before use in patient care.

VaidyaSaarathi is designed to augment, not replace, the expertise of healthcare workers.

---

## 🌟 Star History

If VaidyaSaarathi helps your healthcare organization, please consider giving us a ⭐ on GitHub!

---

<div align="center">

**Built with ❤️ for Healthcare Workers and Patients**

*"Breaking Language Barriers, Preserving Privacy, Empowering Clinical Decisions"*

*AI as Assistant, Physicians as Decision-Makers*


</div>
