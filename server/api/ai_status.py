"""
/ai/status endpoint — checks SageMaker endpoint health and triggers a warm-up
request if the GPU is sleeping (instance count == 0).

Strategy:
- Check CurrentInstanceCount via describe_endpoint
- If 0: fire a minimal async "warm-up" invocation to wake the GPU immediately,
  bypassing the ~4-minute CloudWatch metric lag.
- Debounce: only fire one warm-up every 10 minutes max.
"""

import os
import json
import time
import uuid
import logging
import boto3
from botocore.exceptions import ClientError
from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["AI Status"])

APP_ENV = os.getenv("APP_ENV", "dev")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
SAGEMAKER_ENDPOINT = os.getenv("SAGEMAKER_MEDGEMMA_ENDPOINT", "")
SAGEMAKER_ASYNC_BUCKET = os.getenv("SAGEMAKER_ASYNC_BUCKET", "")

# Debounce: track last warm-up ping via temp file (survives uvicorn hot-reloads)
WARMUP_DEBOUNCE_SECONDS = 300  # 5 minutes
WARMUP_LOCK_FILE = "/tmp/vaidya_warmup_last_sent"


def _get_last_warmup_time() -> float:
    """Read the last warm-up timestamp from disk (survives hot-reloads)."""
    try:
        with open(WARMUP_LOCK_FILE, "r") as f:
            return float(f.read().strip())
    except Exception:
        return 0.0


def _set_last_warmup_time():
    """Persist the warm-up timestamp so debounce survives uvicorn hot-reloads."""
    try:
        with open(WARMUP_LOCK_FILE, "w") as f:
            f.write(str(time.time()))
    except Exception:
        pass


def _get_endpoint_state() -> tuple[int | None, str | None]:
    """Returns (CurrentInstanceCount, EndpointStatus) for the endpoint, or (None, None) on error."""
    if not SAGEMAKER_ENDPOINT:
        return None, None
    try:
        sm = boto3.client("sagemaker", region_name=AWS_REGION)
        resp = sm.describe_endpoint(EndpointName=SAGEMAKER_ENDPOINT)
        status = resp.get("EndpointStatus", "Unknown")
        variants = resp.get("ProductionVariants", [])
        count = variants[0].get("CurrentInstanceCount", 0) if variants else 0
        return count, status
    except ClientError as e:
        logger.warning(f"describe_endpoint failed: {e}")
        return None, None


def _warmup_status() -> str:
    """
    Returns one of:
    - 'fired'     — we just sent a new warm-up ping this call
    - 'debounced' — warm-up was already sent recently (within 5 min), skip duplicate
    - 'never'     — ping failed (S3/network error)
    Uses a temp file to survive uvicorn hot-reloads.
    """
    if not SAGEMAKER_ENDPOINT or not SAGEMAKER_ASYNC_BUCKET:
        return "never"

    now = time.time()
    last_sent = _get_last_warmup_time()

    # If a ping was sent recently, don't send another — GPU is already booting
    if last_sent > 0 and (now - last_sent) < WARMUP_DEBOUNCE_SECONDS:
        logger.info("Warm-up debounced — GPU already booting, skipping duplicate request")
        return "debounced"

    # Fire the warm-up ping
    warmup_payload = {
        "inputs": "Warm-up ping. Patient: N/A. Vitals: N/A.",
        "parameters": {"max_new_tokens": 20, "temperature": 0.1}
    }
    input_key = f"warmup-inputs/{uuid.uuid4()}.json"

    try:
        # 1. Direct Capacity Update (The "Fast" Way)
        # This triggers immediate Scaling behavior bypassing CloudWatch lags
        sm = boto3.client("sagemaker", region_name=AWS_REGION)
        sm.update_endpoint_weights_and_capacities(
            EndpointName=SAGEMAKER_ENDPOINT,
            DesiredWeightsAndCapacities=[
                {
                    "VariantName": "primary",
                    "DesiredInstanceCount": 1
                }
            ]
        )
        logger.info("Direct capacity update sent: DesiredInstanceCount -> 1")

        # 2. Async Invocation (The "Backup" Way)
        # This ensures the 'ApproximateBacklogSize' metric is > 0 so that if 
        # the direct update is throttled/fails, the auto-scaler still sees demand.
        s3 = boto3.client("s3", region_name=AWS_REGION)
        s3.put_object(
            Bucket=SAGEMAKER_ASYNC_BUCKET,
            Key=input_key,
            Body=json.dumps(warmup_payload).encode(),
            ContentType="application/json"
        )

        sm_runtime = boto3.client("sagemaker-runtime", region_name=AWS_REGION)
        sm_runtime.invoke_endpoint_async(
            EndpointName=SAGEMAKER_ENDPOINT,
            InputLocation=f"s3://{SAGEMAKER_ASYNC_BUCKET}/{input_key}",
            ContentType="application/json"
        )

        _set_last_warmup_time()
        logger.info("Direct wake-up and backup ping initiated — GPU should start 'Updating' immediately")
        return "fired"

    except Exception as e:
        logger.error(f"Warm-up failed: {e}")
        return "never"


@router.get("/status")
async def get_ai_status(warmup: bool = False):
    """
    Returns the current status of the AI inference backend.

    Args:
        warmup: Set True ONLY on initial page load. Fires a warm-up ping if GPU is sleeping.
                Set False for all background polls — never triggers a ping, just reads count.
                This prevents the GPU from being kept alive by an idle browser tab.

    Response:
    - "ready"      — GPU is up, instance count >= 1
    - "warming_up" — GPU is sleeping, warm-up was initiated (warmup=True calls only)
    - "unavailable"— Not in demo mode or endpoint not configured
    """
    if APP_ENV != "demo" or not SAGEMAKER_ENDPOINT:
        return {"status": "unavailable", "instance_count": None, "message": "AI status only available in demo mode"}

    instance_count, endpoint_status = _get_endpoint_state()

    if instance_count is None:
        return {"status": "unavailable", "instance_count": None, "message": "Could not reach SageMaker endpoint"}

    if instance_count >= 1:
        return {
            "status": "ready",
            "instance_count": instance_count,
            "message": "AI engine is online and ready"
        }

    # GPU is at 0 instances
    if not warmup:
        # Poll-only call — just report the current state, NEVER fire a warm-up
        logger.info(json.dumps({"event": "ai_status_poll", "instance_count": 0, "sm_status": endpoint_status}))
        return {
            "status": "warming_up",
            "instance_count": 0,
            "message": "AI engine is sleeping — open a triage case to wake it up"
        }

    # warmup=true and instance_count == 0
    # BUT, if status is 'Updating', it means a wake-up is already in progress.
    # Don't trigger again even if the lock file has expired.
    if endpoint_status == "Updating":
        logger.info("Warm-up skipped — Endpoint already in 'Updating' state")
        return {
            "status": "warming_up",
            "instance_count": 0,
            "message": "AI engine is warming up — ready in a few minutes"
        }

    # Proceed with trigger (initial page load + count 0 + not already updating)
    ping_result = _warmup_status()

    if ping_result == "fired":
        message = "AI engine is waking up — GPU boots in ~3-4 min while you prepare the case"
    elif ping_result == "debounced":
        message = "AI engine is warming up — ready in a few minutes"
    else:
        message = "AI engine is starting — please wait a few minutes"

    logger.info(json.dumps({"event": "ai_status_warmup", "instance_count": instance_count, "ping": ping_result}))
    return {
        "status": "warming_up",
        "instance_count": instance_count,
        "message": message
    }
