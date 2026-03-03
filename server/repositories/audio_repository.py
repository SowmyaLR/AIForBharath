import os
import uuid
import logging
import boto3
from abc import ABC, abstractmethod
from botocore.exceptions import ClientError

# Set up logging
logger = logging.getLogger(__name__)

class AudioRepository(ABC):
    @abstractmethod
    async def upload(self, file_name: str, audio_bytes: bytes) -> str:
        pass

    @abstractmethod
    async def get_url(self, file_key: str) -> str:
        pass

class LocalAudioRepository(AudioRepository):
    def __init__(self, storage_dir: str = "storage/audio"):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)
        logger.info(f"Initialized LocalAudioRepository at: {storage_dir}")

    async def upload(self, file_name: str, audio_bytes: bytes) -> str:
        # Use a subfolder or prefix to avoid name collisions
        unique_name = f"{uuid.uuid4()}_{file_name}"
        file_path = os.path.join(self.storage_dir, unique_name)
        
        try:
            with open(file_path, "wb") as f:
                f.write(audio_bytes)
            return file_path
        except IOError as e:
            logger.error(f"Failed to write local audio file: {e}")
            raise

    async def get_url(self, file_key: str) -> str:
        # In local dev, the key IS the path
        return file_key

class S3AudioRepository(AudioRepository):
    def __init__(self, bucket_name: str, region: str = "ap-south-1"):
        self.s3 = boto3.client('s3', region_name=region)
        self.bucket = bucket_name
        logger.info(f"Initialized S3AudioRepository on bucket: {bucket_name}")

    async def upload(self, file_name: str, audio_bytes: bytes) -> str:
        # Standard S3 object key pattern
        key = f"triage_audio/{uuid.uuid4()}_{file_name}"
        try:
            self.s3.put_object(
                Bucket=self.bucket, 
                Key=key, 
                Body=audio_bytes,
                ContentType='audio/webm' # Default for current browser setup
            )
            return key
        except ClientError as e:
            logger.error(f"Failed to upload to S3: {e.response['Error']['Message']}")
            raise

    async def get_url(self, file_key: str) -> str:
        """Generate a secure Pre-Signed URL for downstream consumption"""
        try:
            url = self.s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket, 'Key': file_key},
                ExpiresIn=3600 # 1 hour expiry
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate pre-signed URL: {e.response['Error']['Message']}")
            return file_key
