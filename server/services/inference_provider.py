import os
import json
import logging
import requests
import uuid
import time
import boto3
from abc import ABC, abstractmethod
from typing import Dict, Any, List

# Set up logging
logger = logging.getLogger(__name__)

class InferenceProvider(ABC):
    @abstractmethod
    def invoke(self, prompt: str, max_tokens: int = 512) -> str:
        pass

class OllamaInferenceProvider(InferenceProvider):
    def __init__(self, host: str, model_name: str = "alibayram/medgemma"):
        self.host = host
        self.model_name = model_name
        logger.info(f"Initialized OllamaInferenceProvider with model: {model_name}")

    def invoke(self, prompt: str, max_tokens: int = 512) -> str:
        try:
            response = requests.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_predict": max_tokens, "temperature": 0.1}
                }
            )
            response.raise_for_status()
            return response.json().get("response", "")
        except Exception as e:
            logger.error(f"Ollama inference failed: {e}")
            raise

class SageMakerInferenceProvider(InferenceProvider):
    def __init__(self, endpoint_name: str, region: str = "ap-south-1"):
        self.client = boto3.client("sagemaker-runtime", region_name=region)
        self.s3 = boto3.client("s3", region_name=region)
        self.endpoint_name = endpoint_name
        self.async_bucket = os.getenv("SAGEMAKER_ASYNC_BUCKET", "")
        logger.info(f"Initialized SageMakerInferenceProvider with endpoint: {endpoint_name}")

    def invoke(self, prompt: str, max_tokens: int = 512) -> str:
        try:
            if not self.async_bucket:
                logger.error("SAGEMAKER_ASYNC_BUCKET not set for SageMakerInferenceProvider")
                raise ValueError("SAGEMAKER_ASYNC_BUCKET not set")

            request_id = str(uuid.uuid4())
            input_key = f"inference-inputs/{request_id}.json"
            input_location = f"s3://{self.async_bucket}/{input_key}"

            # 1. Upload Payload to S3
            payload = {
                "inputs": prompt,
                "parameters": {"max_new_tokens": max_tokens, "temperature": 0.1}
            }
            self.s3.put_object(
                Bucket=self.async_bucket,
                Key=input_key,
                Body=json.dumps(payload),
                ContentType="application/json"
            )

            # 2. Start Async Inference
            response = self.client.invoke_endpoint_async(
                EndpointName=self.endpoint_name,
                ContentType="application/json",
                InputLocation=input_location
            )
            
            output_location = response["OutputLocation"]
            output_bucket = output_location.split("/")[2]
            output_key = "/".join(output_location.split("/")[3:])
            
            logger.info(f"Async inference requested. Output: {output_location}")

            # 3. Poll for result (up to 15 minutes)
            max_retries = 180 # 180 * 5s = 900s
            for attempt in range(max_retries):
                try:
                    resp = self.s3.get_object(Bucket=output_bucket, Key=output_key)
                    result = json.loads(resp["Body"].read().decode("utf-8"))
                    
                    # Cleanup
                    try:
                        self.s3.delete_object(Bucket=self.async_bucket, Key=input_key)
                    except: pass

                    if isinstance(result, list) and result:
                        return result[0].get("generated_text", "")
                    return result.get("generated_text", str(result))
                except self.s3.exceptions.NoSuchKey:
                    if attempt % 6 == 0:
                        logger.info(f"Polling for inference result... ({attempt * 5}s elapsed)")
                    time.sleep(5)
            
            raise TimeoutError("Asynchronous inference timed out.")

        except Exception as e:
            logger.error(f"SageMaker async inference failed: {e}")
            raise

def get_inference_provider() -> InferenceProvider:
    """Centralized factory for environment-aware LLM providers."""
    env = os.getenv("APP_ENV", "dev")
    
    if env == "demo":
        endpoint = os.getenv("SAGEMAKER_MEDGEMMA_ENDPOINT")
        region = os.getenv("AWS_REGION", "ap-south-1")
        if not endpoint:
            logger.warning("SAGEMAKER_MEDGEMMA_ENDPOINT not set, falling back to local Ollama")
            host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
            return OllamaInferenceProvider(host)
        return SageMakerInferenceProvider(endpoint, region)
    else:
        host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        return OllamaInferenceProvider(host)
