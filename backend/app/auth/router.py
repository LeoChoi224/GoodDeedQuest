from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from backend.app.common.response import APIResponse
from backend.app.common.auth import create_access_token, get_password_hash, verify_password

router = APIRouter(prefix="/auth", tags=["Authentication"])

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str

class LoginRequest(BaseModel):
    email: str
    password: str

# 간단한 Mock 사용자 데이터베이스 대용
MOCK_USERS = {}

@router.post("/register")
def register(req: RegisterRequest):
    if req.email in MOCK_USERS:
        raise HTTPException(status_code=400, detail="User already exists")
    
    hashed = get_password_hash(req.password)
    MOCK_USERS[req.email] = {
        "id": len(MOCK_USERS) + 1,
        "email": req.email,
        "password": hashed,
        "name": req.name,
        "level": 1,
        "xp": 0
    }
    return APIResponse.ok(message="Registration successful")

@router.post("/login")
def login(req: LoginRequest):
    user = MOCK_USERS.get(req.email)
    if not user or not verify_password(req.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_access_token(data={
        "sub": user["email"],
        "id": user["id"],
        "name": user["name"],
        "level": user["level"],
        "xp": user["xp"]
    })
    return APIResponse.ok(data={"access_token": token, "token_type": "bearer"}, message="Login successful")
