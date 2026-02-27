from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import auth, patients, triage, ehr

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
    return {
        "status": "online",
        "message": "VaidyaSaarathi Backend API is running.",
        "models_status": {
            "Ollama": "Reachable via API", # Health check in a real app
            "Whisper": "Local HF Model",
            "HeAR": "Local HF Model/Fallback"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
