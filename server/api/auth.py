from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from services.auth_service import AuthService, AuthResponse

router = APIRouter(prefix="/auth", tags=["auth"])
auth_service = AuthService()

class LoginRequest(BaseModel):
    hospital_id: str
    password: str

@router.post("/login", response_model=AuthResponse)
async def login(credentials: LoginRequest):
    response = await auth_service.login(credentials.hospital_id, credentials.password)
    if not response:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return response

@router.get("/me")
async def read_users_me(token: str):
    session = await auth_service.verify_token(token)
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return session
