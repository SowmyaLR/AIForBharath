import os
import uuid
import json
import logging
import boto3
from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from botocore.exceptions import ClientError
from decimal import Decimal
from models.triage import TriageRecord

# Set up logging
logger = logging.getLogger(__name__)

class TriageRepository(ABC):
    @abstractmethod
    async def save(self, record: TriageRecord) -> TriageRecord:
        pass

    @abstractmethod
    async def get_by_id(self, triage_id: str) -> Optional[TriageRecord]:
        pass

    @abstractmethod
    async def list_all(self, specialty: Optional[str] = None) -> List[TriageRecord]:
        pass

class InMemoryTriageRepository(TriageRepository):
    def __init__(self):
        self._records: Dict[str, TriageRecord] = {}
        logger.info("Initialized InMemoryTriageRepository")

    async def save(self, record: TriageRecord) -> TriageRecord:
        self._records[record.id] = record
        return record

    async def get_by_id(self, triage_id: str) -> Optional[TriageRecord]:
        return self._records.get(triage_id)

    async def list_all(self, specialty: Optional[str] = None) -> List[TriageRecord]:
        records = list(self._records.values())
        if specialty:
            records = [r for r in records if r.specialty == specialty]
        return records

class DynamoDBTriageRepository(TriageRepository):
    def __init__(self, table_name: str, region: str = "ap-south-1"):
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.table = self.dynamodb.Table(table_name)
        logger.info(f"Initialized DynamoDBTriageRepository on table: {table_name}")

    def _to_dynamo(self, record: TriageRecord) -> dict:
        """Convert Pydantic model to DynamoDB compatible dict (handles floats/decimals)"""
        # Pydantic's .json() + json.loads(..., parse_float=Decimal) is a safe way to handle Floats for Dynamo
        return json.loads(record.json(), parse_float=Decimal)

    async def save(self, record: TriageRecord) -> TriageRecord:
        try:
            item = self._to_dynamo(record)
            self.table.put_item(Item=item)
            return record
        except ClientError as e:
            logger.error(f"Error saving to DynamoDB: {e.response['Error']['Message']}")
            raise

    async def get_by_id(self, triage_id: str) -> Optional[TriageRecord]:
        try:
            response = self.table.get_item(Key={'id': triage_id})
            if 'Item' in response:
                return TriageRecord(**response['Item'])
            return None
        except ClientError as e:
            logger.error(f"Error fetching from DynamoDB: {e.response['Error']['Message']}")
            return None

    async def list_all(self, specialty: Optional[str] = None) -> List[TriageRecord]:
        try:
            if specialty:
                response = self.table.scan(
                    FilterExpression="specialty = :s",
                    ExpressionAttributeValues={":s": specialty}
                )
            else:
                response = self.table.scan()
            
            return [TriageRecord(**item) for item in response.get('Items', [])]
        except ClientError as e:
            logger.error(f"Error scanning DynamoDB: {e.response['Error']['Message']}")
            return []
