import os
import json
import logging
from decimal import Decimal
from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel
import uuid

logger = logging.getLogger(__name__)
APP_ENV = os.getenv("APP_ENV", "dev")

# ── Models ───────────────────────────────────────────────────────────────────

class AcousticAnomaly(BaseModel):
    type: str
    confidence: float
    timestamp: float

class SOAPNote(BaseModel):
    subjective: str
    objective: str
    assessment: str
    plan: str

class VitalSigns(BaseModel):
    temperature: float
    blood_pressure_systolic: int
    blood_pressure_diastolic: int
    heart_rate: int
    respiratory_rate: int
    oxygen_saturation: int
    recorded_at: datetime
    recorded_by: str

class TriageRecord(BaseModel):
    id: str
    patient_id: str
    audio_file_url: str
    language: str
    transcription: str = ""
    translation: str = ""
    soap_note: Optional[SOAPNote] = None
    vitals: Optional[VitalSigns] = None
    risk_score: int = 0
    triage_tier: str = "ROUTINE"
    preliminary_zone: Optional[str] = None  # vitals-only fast estimate before AI completes
    specialty: str = "General Medicine"
    patient_age: Optional[int] = None
    status: str
    idempotency_key: Optional[str] = None  # prevents double-submit duplicates
    created_at: datetime
    updated_at: datetime


# ── In-Memory Service (dev mode) ─────────────────────────────────────────────

MOCK_TRIAGES: Dict[str, TriageRecord] = {}

class TriageService:
    async def create_triage_record(
        self,
        patient_id: str,
        audio_file_path: str,
        language: str,
        vitals: Optional[VitalSigns] = None,
        idempotency_key: Optional[str] = None,
        patient_age: Optional[int] = None
    ) -> TriageRecord:
        triage_id = str(uuid.uuid4())
        record = TriageRecord(
            id=triage_id,
            patient_id=patient_id,
            audio_file_url=audio_file_path,
            language=language,
            vitals=vitals,
            patient_age=patient_age,
            idempotency_key=idempotency_key,
            status="pending",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        MOCK_TRIAGES[triage_id] = record
        return record

    async def get_by_idempotency_key(self, key: str) -> Optional[TriageRecord]:
        """Return existing record if this idempotency key was already used."""
        for record in MOCK_TRIAGES.values():
            if record.idempotency_key == key:
                return record
        return None

    async def get_triage(self, triage_id: str) -> Optional[TriageRecord]:
        return MOCK_TRIAGES.get(triage_id)

    async def update_triage_status(self, triage_id: str, status: str) -> Optional[TriageRecord]:
        record = MOCK_TRIAGES.get(triage_id)
        if record:
            record.status = status
            record.updated_at = datetime.utcnow()
        return record

    async def add_vitals(self, triage_id: str, vitals: VitalSigns) -> Optional[TriageRecord]:
        record = MOCK_TRIAGES.get(triage_id)
        if record:
            record.vitals = vitals
            record.updated_at = datetime.utcnow()
        return record

    async def update_soap_note(self, triage_id: str, soap_note: SOAPNote) -> Optional[TriageRecord]:
        record = MOCK_TRIAGES.get(triage_id)
        if record and record.status != "finalized":
            record.soap_note = soap_note
            record.updated_at = datetime.utcnow()
        return record

    async def save_triage_record(self, record: TriageRecord) -> TriageRecord:
        """Full record save — in dev mode just updates the in-memory dict."""
        record.updated_at = datetime.utcnow()
        MOCK_TRIAGES[record.id] = record
        return record

    async def get_triage_queue(self, specialty: Optional[str] = None) -> List[TriageRecord]:
        records = list(MOCK_TRIAGES.values())
        if specialty:
            records = [r for r in records if r.specialty == specialty]
        return sorted(records, key=lambda x: (-x.risk_score, x.created_at))


# ── DynamoDB Service (demo mode) ─────────────────────────────────────────────

def _floats_to_decimal(obj):
    """Recursively convert all float values to Decimal for DynamoDB compatibility."""
    if isinstance(obj, float):
        return Decimal(str(obj))
    if isinstance(obj, dict):
        return {k: _floats_to_decimal(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_floats_to_decimal(i) for i in obj]
    return obj


def _decimal_to_float(obj):
    """Recursively convert Decimal back to float when reading from DynamoDB."""
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: _decimal_to_float(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_decimal_to_float(i) for i in obj]
    return obj


def _serialize(record: TriageRecord) -> dict:
    """Convert a TriageRecord to a DynamoDB-compatible dict."""
    data = record.model_dump()
    # Convert datetime objects to ISO strings
    for key in ("created_at", "updated_at"):
        if isinstance(data.get(key), datetime):
            data[key] = data[key].isoformat()
    if data.get("vitals") and isinstance(data["vitals"].get("recorded_at"), datetime):
        data["vitals"]["recorded_at"] = data["vitals"]["recorded_at"].isoformat()
    if data.get("soap_note") is None:
        data.pop("soap_note", None)
    if data.get("vitals") is None:
        del data["vitals"]
    
    # Ensure patient_age is handled as an integer (DynamoDB likes consistency)
    if data.get("patient_age") is not None:
        data["patient_age"] = int(data["patient_age"])
        
    # Remove None values, then convert all floats → Decimal for DynamoDB
    data = {k: v for k, v in data.items() if v is not None}
    return _floats_to_decimal(data)


def _deserialize(item: dict) -> TriageRecord:
    """Convert a DynamoDB item back to a TriageRecord."""
    # Convert Decimal back to float/int before Pydantic validation
    item = _decimal_to_float(item)
    for key in ("created_at", "updated_at"):
        if isinstance(item.get(key), str):
            item[key] = datetime.fromisoformat(item[key])
    if item.get("vitals") and isinstance(item["vitals"].get("recorded_at"), str):
        item["vitals"]["recorded_at"] = datetime.fromisoformat(item["vitals"]["recorded_at"])
    return TriageRecord(**item)


class DynamoDBTriageService:
    def __init__(self):
        import boto3
        region = os.getenv("AWS_REGION", "ap-south-1")
        self.table_name = os.getenv("DYNAMODB_TRIAGE_TABLE", "vaidyasaarathi-demo-v2-triage")
        self._ddb = boto3.resource("dynamodb", region_name=region)
        self._table = self._ddb.Table(self.table_name)
        print(f"[DEMO] DynamoDBTriageService connected to table: {self.table_name}")

    async def create_triage_record(
        self,
        patient_id: str,
        audio_file_path: str,
        language: str,
        vitals: Optional[VitalSigns] = None,
        idempotency_key: Optional[str] = None,
        patient_age: Optional[int] = None
    ) -> TriageRecord:
        triage_id = str(uuid.uuid4())
        record = TriageRecord(
            id=triage_id,
            patient_id=patient_id,
            audio_file_url=audio_file_path,
            language=language,
            vitals=vitals,
            patient_age=patient_age,
            idempotency_key=idempotency_key,
            status="pending",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self._table.put_item(Item=_serialize(record))
        logger.info(json.dumps({"event": "triage_created", "triage_id": triage_id, "patient_id": patient_id}))
        return record

    async def get_by_idempotency_key(self, key: str) -> Optional[TriageRecord]:
        """Query idempotency_key via GSI to prevent duplicate submissions."""
        try:
            resp = self._table.query(
                IndexName="idempotency-key-index",
                KeyConditionExpression="idempotency_key = :k",
                ExpressionAttributeValues={":k": key},
                Limit=1
            )
            items = resp.get("Items", [])
            return _deserialize(items[0]) if items else None
        except Exception:
            return None  # GSI may not exist in dev; safe fallback

    async def get_triage(self, triage_id: str) -> Optional[TriageRecord]:
        response = self._table.get_item(Key={"id": triage_id})
        item = response.get("Item")
        return _deserialize(item) if item else None

    async def save_triage_record(self, record: TriageRecord) -> TriageRecord:
        """Full record overwrite — use after pipeline completes to persist all fields."""
        record.updated_at = datetime.utcnow()
        self._table.put_item(Item=_serialize(record))
        logger.info(json.dumps({"event": "triage_saved", "triage_id": record.id, "status": record.status}))
        return record

    async def update_triage_status(self, triage_id: str, status: str) -> Optional[TriageRecord]:
        now = datetime.utcnow().isoformat()
        self._table.update_item(
            Key={"id": triage_id},
            UpdateExpression="SET #s = :s, updated_at = :u",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":s": status, ":u": now}
        )
        return await self.get_triage(triage_id)

    async def add_vitals(self, triage_id: str, vitals: VitalSigns) -> Optional[TriageRecord]:
        vitals_data = vitals.model_dump()
        if isinstance(vitals_data.get("recorded_at"), datetime):
            vitals_data["recorded_at"] = vitals_data["recorded_at"].isoformat()
        now = datetime.utcnow().isoformat()
        self._table.update_item(
            Key={"id": triage_id},
            UpdateExpression="SET vitals = :v, updated_at = :u",
            ExpressionAttributeValues={":v": vitals_data, ":u": now}
        )
        return await self.get_triage(triage_id)

    async def update_soap_note(self, triage_id: str, soap_note: SOAPNote) -> Optional[TriageRecord]:
        now = datetime.utcnow().isoformat()
        self._table.update_item(
            Key={"id": triage_id},
            UpdateExpression="SET soap_note = :n, updated_at = :u",
            ConditionExpression="attribute_not_exists(#s) OR #s <> :finalized",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={
                ":n": soap_note.model_dump(),
                ":u": now,
                ":finalized": "finalized"
            }
        )
        return await self.get_triage(triage_id)

    async def get_triage_queue(self, specialty: Optional[str] = None) -> List[TriageRecord]:
        """
        Query the triage queue using the status-created-index GSI.
        Fetches records with status in [pending, in_progress, ready_for_review].
        Falls back to scan() if GSI is not available (first-deploy scenario).
        """
        active_statuses = ["pending", "in_progress", "ready_for_review"]
        records = []

        try:
            from boto3.dynamodb.conditions import Key
            for status_val in active_statuses:
                resp = self._table.query(
                    IndexName="status-created-index",
                    KeyConditionExpression=Key("status").eq(status_val),
                    ScanIndexForward=False,  # newest first
                    Limit=50
                )
                records.extend([_deserialize(item) for item in resp.get("Items", [])])
        except Exception as e:
            logger.warning(json.dumps({"event": "gsi_query_failed_fallback_to_scan", "error": str(e)}))
            response = self._table.scan()
            records = [_deserialize(item) for item in response.get("Items", [])]

        if specialty:
            records = [r for r in records if r.specialty == specialty]

        return sorted(records, key=lambda x: (-x.risk_score, x.created_at))


# ── Factory ──────────────────────────────────────────────────────────────────

def get_triage_service() -> TriageService:
    """Return the appropriate TriageService based on APP_ENV."""
    if APP_ENV == "demo":
        try:
            return DynamoDBTriageService()
        except Exception as e:
            logger.warning(json.dumps({"event": "dynamodb_unavailable_fallback", "error": str(e)}))
    return TriageService()
