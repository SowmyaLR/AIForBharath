from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from services.med_models import transcribe_audio, analyze_cough, generate_soap_note

from starlette.concurrency import run_in_threadpool

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TriageResponse(BaseModel):
    transcript: str
    risk_data: dict
    soap_note: dict

# In-memory storage for demo purposes
triage_queue = []

@app.get("/")
def read_root():
    return {"message": "Tele-Triage Backend is running"}

@app.post("/api/triage", response_model=TriageResponse)
async def run_triage(audio_file: UploadFile = File(...), patient_id: str = Form("Anonymous")):
    # 1. Read file bytes
    file_bytes = await audio_file.read()
    
    # 2. Parallel processing (in threadpool to avoid blocking main loop)
    print(f"DEBUG: Received triage request for Patient {patient_id}. Offloading to threads.")
    transcript_result = await run_in_threadpool(transcribe_audio, file_bytes)
    cough_analysis = await run_in_threadpool(analyze_cough, file_bytes)
    
    # 3. Reasoning step
    soap_result = await run_in_threadpool(generate_soap_note, transcript_result['text'], cough_analysis)
    
    result = {
        "transcript": transcript_result['text'],
        "risk_data": cough_analysis,
        "soap_note": soap_result
    }
    
    # Store in queue
    import uuid
    from datetime import datetime
    triage_queue.append({
        "id": str(len(triage_queue) + 101), # Simple incremental ID
        "patientName": patient_id, # Use the actual ID provided
        "userInitials": patient_id[:2].upper() if len(patient_id) >= 2 else "PT",
        "timestamp": datetime.now().strftime("%I:%M %p"),
        "riskScore": cough_analysis['risk_score'],
        "chiefComplaint": transcript_result['text'],
        "soapSummary": soap_result['soap_note'],
        "fullData": result
    })
    
    return result

@app.get("/api/queue")
def get_queue():
    return triage_queue

@app.get("/health")
def health_check():
    return {"status": "ok"}
