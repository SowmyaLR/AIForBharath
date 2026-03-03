import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)

class FHIRRepository(ABC):
    @abstractmethod
    async def save_export(self, patient_id: str, fhir_bundle: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    async def list_exports(self) -> List[Dict[str, Any]]:
        pass

class InMemoryFHIRRepository(FHIRRepository):
    def __init__(self):
        self._exports: List[Dict[str, Any]] = []
        logger.info("Initialized InMemoryFHIRRepository")

    async def save_export(self, patient_id: str, fhir_bundle: Dict[str, Any]) -> bool:
        self._exports.append({
            "patient_id": patient_id,
            "exported_at": datetime.utcnow().isoformat() + "Z",
            "fhir_bundle": fhir_bundle
        })
        return True

    async def list_exports(self) -> List[Dict[str, Any]]:
        return self._exports

# Future: DynamoDBFHIRRepository could be added here
