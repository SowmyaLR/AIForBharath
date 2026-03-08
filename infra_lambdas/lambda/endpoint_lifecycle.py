import boto3
import json
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ENDPOINT_NAME = os.environ["MEDGEMMA_ENDPOINT"]
ENDPOINT_CONFIG = os.environ["MEDGEMMA_ENDPOINT_CONFIG"]
REGION = os.environ.get("AWS_REGION", "ap-south-1")


def handler(event, context):
    """
    Start or stop the MedGemma SageMaker real-time endpoint.
    EventBridge sends {"action": "start"} at 07:50 IST and {"action": "stop"} at 20:00 IST.
    Saves ~$16.89/day by avoiding overnight idle GPU cost.
    """
    action = event.get("action")
    sm = boto3.client("sagemaker", region_name=REGION)

    if action == "start":
        try:
            # Check if already running
            resp = sm.describe_endpoint(EndpointName=ENDPOINT_NAME)
            status = resp.get("EndpointStatus", "")
            logger.info(json.dumps({
                "event": "endpoint_already_exists",
                "endpoint": ENDPOINT_NAME,
                "status": status
            }))
            return {"action": "skipped", "reason": f"already {status}"}
        except sm.exceptions.ClientError:
            # Endpoint does not exist — create it
            pass

        sm.create_endpoint(
            EndpointName=ENDPOINT_NAME,
            EndpointConfigName=ENDPOINT_CONFIG
        )
        logger.info(json.dumps({
            "event": "endpoint_started",
            "endpoint": ENDPOINT_NAME,
            "config": ENDPOINT_CONFIG
        }))
        return {"action": "started", "endpoint": ENDPOINT_NAME}

    elif action == "stop":
        try:
            sm.delete_endpoint(EndpointName=ENDPOINT_NAME)
            logger.info(json.dumps({
                "event": "endpoint_stopped",
                "endpoint": ENDPOINT_NAME
            }))
            return {"action": "stopped", "endpoint": ENDPOINT_NAME}
        except sm.exceptions.ClientError as e:
            # Already stopped — not an error
            logger.info(json.dumps({
                "event": "endpoint_already_stopped",
                "endpoint": ENDPOINT_NAME,
                "detail": str(e)
            }))
            return {"action": "skipped", "reason": "already stopped"}

    else:
        logger.error(json.dumps({
            "event": "invalid_action",
            "action": action
        }))
        return {"error": f"Unknown action: {action}. Expected 'start' or 'stop'."}
