from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from passlib.context import CryptContext
from backend.app.common.config import get_setting

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{get_setting().API_V1_STR}/auth/login", auto_error=False)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=get_setting().ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, get_setting().SECRET_KEY.get_secret_value(), algorithm=get_setting().JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> str:
    try:
        payload = jwt.decode(token, get_setting().SECRET_KEY.get_secret_value(), algorithms=[get_setting().JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Could not validate credentials"
            )
        return username
    except jwt.PyJWTError:  # 토큰이 위조되었거나 만료 시간이 초과된 경우 자동 차단 예외 처리
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Could not validate credentials"
        )    

def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    # 뼈대용 Mock 임시 사용자 반환 로직
    if not token:
        # 인증 토큰이 없을 경우 Mock 개발 사용자 반환 (편의성)
        return {"id": 1, "email": "mock-user@example.com", "name": "홍길동", "level": 1, "xp": 100}
        
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, get_setting().SECRET_KEY.get_secret_value(), algorithms=["HS256"])
        email: str = payload.get("sub")
        user_id: int = payload.get("id")
        if email is None or user_id is None:
            raise credentials_exception
        return {"id": user_id, "email": email, "name": payload.get("name", "사용자"), "level": payload.get("level", 1), "xp": payload.get("xp", 0)}
    except jwt.PyJWTError:
        raise credentials_exception
