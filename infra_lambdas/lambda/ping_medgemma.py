import boto3
import json
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ENDPOINT_NAME = os.environ["MEDGEMMA_ENDPOINT"]
REGION = os.environ.get("AWS_REGION", "ap-south-1")


def handler(event, context):
    """
    Warm-ping for MedGemma SageMaker endpoint.
    Invoked by EventBridge every 8 minutes during clinic hours.
    Keeps model weights in GPU VRAM between real inference calls.
    """
    sm = boto3.client("sagemaker-runtime", region_name=REGION)

    try:
        sm.invoke_endpoint(
            EndpointName=ENDPOINT_NAME,
            ContentType="application/json",
            Body=json.dumps({
                "inputs": "ping",
                "parameters": {"max_new_tokens": 1, "temperature": 0.1}
            })
        )
        logger.info(json.dumps({
            "event": "warmup_success",
            "endpoint": ENDPOINT_NAME
        }))
        return {"status": "warm", "endpoint": ENDPOINT_NAME}

    except Exception as e:
        # Log but do not raise — a ping failure is not critical
        # The real invocation in ai_service.py has its own retry logic
        logger.warning(json.dumps({
            "event": "warmup_failed",
            "endpoint": ENDPOINT_NAME,
            "error": str(e)
        }))
        return {"status": "error", "endpoint": ENDPOINT_NAME, "detail": str(e)}
