import logging
import uuid
import json
import boto3
from abc import ABC, abstractmethod
from typing import Optional, List, Dict
from datetime import datetime
from botocore.exceptions import ClientError
from decimal import Decimal
from models.patient import Patient

# Set up logging
logger = logging.getLogger(__name__)

class PatientRepository(ABC):
    @abstractmethod
    async def get_by_hospital_id(self, hospital_id: str) -> Optional[Patient]:
        pass

    @abstractmethod
    async def create(self, patient: Patient) -> Patient:
        pass

    @abstractmethod
    async def list_all(self) -> List[Patient]:
        pass

class InMemoryPatientRepository(PatientRepository):
    def __init__(self):
        # Initial mock patients
        self._patients = {
            "P-001": Patient(
                id=str(uuid.uuid4()),
                hospital_id="P-001",
                name="Ramesh Kumar",
                date_of_birth="1980-05-14",
                gender="Male",
                contact_number="9876543210",
                address="123 Anna Salai, Chennai",
                preferred_language="Tamil",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            "P-002": Patient(
                id=str(uuid.uuid4()),
                hospital_id="P-002",
                name="Lakshmi Devi",
                date_of_birth="1965-11-02",
                gender="Female",
                contact_number="9876543211",
                address="45 Mount Road, Chennai",
                preferred_language="Telugu",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        }
        logger.info("Initialized InMemoryPatientRepository with default mock patients")

    async def get_by_hospital_id(self, hospital_id: str) -> Optional[Patient]:
        return self._patients.get(hospital_id)

    async def create(self, patient: Patient) -> Patient:
        self._patients[patient.hospital_id] = patient
        return patient

    async def list_all(self) -> List[Patient]:
        return list(self._patients.values())

class DynamoDBPatientRepository(PatientRepository):
    def __init__(self, table_name: str, region: str = "ap-south-1"):
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.table = self.dynamodb.Table(table_name)
        logger.info(f"Initialized DynamoDBPatientRepository on table: {table_name}")

    def _to_dynamo(self, patient: Patient) -> dict:
        return json.loads(patient.json(), parse_float=Decimal)

    async def get_by_hospital_id(self, hospital_id: str) -> Optional[Patient]:
        try:
            # Note: Assuming hospital_id is the primary key or a GSI
            # In simple demo, we Key by 'hospital_id' if that's the PK
            response = self.table.get_item(Key={'hospital_id': hospital_id})
            if 'Item' in response:
                return Patient(**response['Item'])
            return None
        except ClientError as e:
            logger.error(f"Error fetching patient from DynamoDB: {e.response['Error']['Message']}")
            return None

    async def create(self, patient: Patient) -> Patient:
        try:
            item = self._to_dynamo(patient)
            self.table.put_item(Item=item)
            return patient
        except ClientError as e:
            logger.error(f"Error creating patient in DynamoDB: {e.response['Error']['Message']}")
            raise

    async def list_all(self) -> List[Patient]:
        try:
            response = self.table.scan()
            return [Patient(**item) for item in response.get('Items', [])]
        except ClientError as e:
            logger.error(f"Error scanning patients in DynamoDB: {e.response['Error']['Message']}")
            return []
