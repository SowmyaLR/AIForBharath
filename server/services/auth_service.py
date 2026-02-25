from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel
from jose import JWTError, jwt
from passlib.context import CryptContext

# Configuration (In production, use secrets)
SECRET_KEY = "vaidyasaarathi_super_secret_key_change_in_prod"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Models ---
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

# --- Mock Database ---
# For the hackathon, hardcoding accounts for quick demo:
MOCK_USERS = {
    "rec_01": {
        "id": "u1",
        "hospital_id": "rec_01",
        "name": "Sowmya (Reception)",
        "password": pwd_context.hash("password"),
        "role": "receptionist",
        "specialty": None
    },
    "nur_01": {
        "id": "u2",
        "hospital_id": "nur_01",
        "name": "Nurse Anita",
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

class AuthService:
    def __init__(self):
        pass

    def verify_password(self, plain_password, hashed_password):
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password):
        return pwd_context.hash(password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    async def login(self, hospital_id: str, password: str) -> Optional[AuthResponse]:
        """Validate credentials and generate JWT token"""
        user_dict = MOCK_USERS.get(hospital_id)
        if not user_dict:
            return None
        if not self.verify_password(password, user_dict["password"]):
            return None
        
        # User is valid, create token
        user = User(**user_dict)
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        session_data = {
            "sub": user.hospital_id,
            "role": user.role,
            "specialty": user.specialty,
            "user_id": user.id
        }
        
        access_token = self.create_access_token(
            data=session_data, expires_delta=access_token_expires
        )
        
        return AuthResponse(
            token=access_token,
            user=user,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    async def verify_token(self, token: str) -> Optional[UserSession]:
        """Verify JWT token and return session info"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get("user_id")
            role: str = payload.get("role")
            if user_id is None or role is None:
                return None
            return UserSession(
                user_id=user_id,
                role=role,
                specialty=payload.get("specialty"),
                issued_at=int(datetime.utcnow().timestamp()), # Approximation for demo
                expires_at=payload.get("exp")
            )
        except JWTError:
            return None
