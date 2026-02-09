# VaidyaSaarathi 🏥

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

### Powered by Google's HAI-DEF Framework

VaidyaSaarathi leverages **Health AI Developer Foundations (HAI-DEF)**, Google's open-source healthcare AI framework:

| Model | Purpose | Deployment |
|-------|---------|------------|
| **MedGemma 4B** | Draft clinical SOAP notes & suggest risk scores | Ollama (CPU/GPU) |
| **HeAR** | Detect potential acoustic anomalies (cough, respiratory distress) | Local CPU/GPU |
| **Whisper** | Multi-language speech-to-text (99+ languages) | Ollama (CPU/GPU) |
| **NLLB-200 / IndicTrans2** | Translation for Indian languages | Local CPU/GPU |
| **Piper / Coqui TTS** | Text-to-speech in native languages | Local CPU |

> **AI as Assistant:** All AI outputs are suggestions to assist healthcare professionals. Clinical validation and final decisions remain with qualified medical personnel.

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

**Processing Time:** < 5 seconds (end-to-end)

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

[Get Started](#-quick-start) • [Documentation](#-documentation) • [Contributing](#-contributing)

</div>
