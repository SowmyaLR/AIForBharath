from typing import Optional
from pydantic import BaseModel

class User(BaseModel):
    id: str
    hospital_id: str
    name: str
    role: str
    specialty: Optional[str] = None

class AuthResponse(BaseModel):
    token: str
    user: User
    expires_in: int

class UserSession(BaseModel):
    user_id: str
    role: str
    specialty: Optional[str] = None
    issued_at: int
    expires_at: int
