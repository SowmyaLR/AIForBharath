from dotenv import load_dotenv
load_dotenv()  # loads server/.env before any os.getenv() calls

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from api import auth, patients, triage, ehr
import os
import json
import logging
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

APP_ENV = os.getenv("APP_ENV", "dev")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")

app = FastAPI(
    title="VaidyaSaarathi API",
    description="Backend for the AI-Assisted Clinical Triage System",
    version="1.0.0"
)

# CORS — locked to specific frontend origin, not wildcard
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
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
    backend = "AWS SageMaker" if APP_ENV == "demo" else f"Ollama ({os.getenv('OLLAMA_HOST', 'http://localhost:11434')})"
    return {
        "status": "online",
        "environment": APP_ENV.upper(),
        "message": "VaidyaSaarathi Backend API is running.",
        "inference_backend": backend,
        "models": {
            "MedGemma": "sagemaker" if APP_ENV == "demo" else "ollama",
            "Whisper": "faster-whisper (in-container)",
            "HeAR": "google/hear (in-container)"
        }
    }


@app.get("/health")
async def health_check():
    """
    Deep health check — probes all critical dependencies.
    ALB uses this endpoint to determine if the task should receive traffic.
    Returns 200 only when all dependencies are reachable.
    Returns 503 if any dependency is unhealthy.
    """
    status = {
        "server": "ok",
        "dynamodb": "unknown",
        "sagemaker_endpoint": "not_checked"
    }
    http_status = 200

    # DynamoDB reachability
    triage_table = os.getenv("DYNAMODB_TRIAGE_TABLE", "")
    if triage_table:
        try:
            ddb = boto3.client("dynamodb", region_name=AWS_REGION)
            ddb.describe_table(TableName=triage_table)
            status["dynamodb"] = "ok"
        except Exception as e:
            status["dynamodb"] = f"error: {str(e)[:120]}"
            http_status = 503
    else:
        status["dynamodb"] = "not_configured"

    # SageMaker endpoint status — demo mode only
    medgemma_endpoint = os.getenv("SAGEMAKER_MEDGEMMA_ENDPOINT", "")
    if APP_ENV == "demo" and medgemma_endpoint:
        try:
            sm = boto3.client("sagemaker", region_name=AWS_REGION)
            resp = sm.describe_endpoint(EndpointName=medgemma_endpoint)
            ep_status = resp.get("EndpointStatus", "Unknown")
            status["sagemaker_endpoint"] = ep_status
            if ep_status != "InService":
                http_status = 503
        except Exception as e:
            status["sagemaker_endpoint"] = f"error: {str(e)[:120]}"
            http_status = 503

    logger.info(json.dumps({"event": "health_check", "status": status, "http_status": http_status}))
    return JSONResponse(content=status, status_code=http_status)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
