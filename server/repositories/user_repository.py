import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict
from models.auth import User
from passlib.context import CryptContext

# Set up logging
logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserRepository(ABC):
    @abstractmethod
    async def get_by_hospital_id(self, hospital_id: str) -> Optional[dict]:
        """Returns raw user dict including hashed password"""
        pass

class InMemoryUserRepository(UserRepository):
    def __init__(self):
        # Initial mock users for demo
        self._users = {
            "nur_01": {
                "id": "u1",
                "hospital_id": "nur_01",
                "name": "Nurse Anita (Intake)",
                "password": pwd_context.hash("password"),
                "role": "nurse",
                "specialty": None
            },
            "doc_cardio": {
                "id": "u3",
                "hospital_id": "doc_cardio",
                "name": "Dr. Sharma",
                "password": pwd_context.hash("password"),
                "role": "doctor",
                "specialty": "Cardiac"
            }
        }
        logger.info("Initialized InMemoryUserRepository with default mock users")

    async def get_by_hospital_id(self, hospital_id: str) -> Optional[dict]:
        return self._users.get(hospital_id)
