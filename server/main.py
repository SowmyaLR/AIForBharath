from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import auth, patients, triage, ehr
import os

app = FastAPI(
    title="VaidyaSaarathi API",
    description="Backend for the AI-Assisted Clinical Triage System",
    version="1.0.0"
)

# CORS config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(triage.router)
app.include_router(ehr.router)

@app.get("/")
def read_root():
    app_env = os.getenv("APP_ENV", "dev")
    backend = "AWS SageMaker" if app_env == "demo" else f"Ollama ({os.getenv('OLLAMA_HOST', 'http://localhost:11434')})"
    return {
        "status": "online",
        "environment": app_env.upper(),
        "message": "VaidyaSaarathi Backend API is running.",
        "inference_backend": backend,
        "models": {
            "MedGemma": "sagemaker" if app_env == "demo" else "ollama",
            "Whisper": "faster-whisper (local)",
            "HeAR": "google/hear (local HuggingFace)"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
