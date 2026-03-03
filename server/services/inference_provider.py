import os
import json
import logging
import requests
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
        import boto3
        self.client = boto3.client("sagemaker-runtime", region_name=region)
        self.endpoint_name = endpoint_name
        logger.info(f"Initialized SageMakerInferenceProvider with endpoint: {endpoint_name}")

    def invoke(self, prompt: str, max_tokens: int = 512) -> str:
        try:
            response = self.client.invoke_endpoint(
                EndpointName=self.endpoint_name,
                ContentType="application/json",
                Body=json.dumps({
                    "inputs": prompt, 
                    "parameters": {"max_new_tokens": max_tokens, "temperature": 0.1}
                })
            )
            result = json.loads(response["Body"].read().decode("utf-8"))
            if isinstance(result, list) and result:
                return result[0].get("generated_text", "")
            return result.get("generated_text", str(result))
        except Exception as e:
            logger.error(f"SageMaker inference failed: {e}")
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
