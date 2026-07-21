from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from backend.app.common.response import APIResponse
from backend.app.common.auth import create_access_token, get_password_hash, verify_password
from backend.app.auth.shcemas import UserResponse, UserCreate, LoginResponse, LoginRequest
from typing import Annotated
from backend.app.auth.models import User
from backend.app.common.deps import get_repository
from backend.app.common.repository import DatabaseRepository    
from backend.app.common.auth import create_access_token, get_password_hash, verify_password, verify_token, oauth2_scheme
from backend.app.auth.service import trigger_embedding_if_needed


router = APIRouter(prefix="/auth", tags=["Authentication"])

UserRepository = Annotated[
    DatabaseRepository[User],
    Depends(get_repository(User))
]

@router.post('/register', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, repository: UserRepository):
    if repository.get_by(email=user_in.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    data = user_in.model_dump(exclude={'password'})
    data['password_hash'] = get_password_hash(user_in.password)
    
    return repository.create(data)

    
@router.post("/login", response_model=APIResponse[LoginResponse])
def login(req: LoginRequest, repository: UserRepository, background_tasks: BackgroundTasks):
    user = repository.get_by(email = req.email)
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    trigger_embedding_if_needed(user, background_tasks)
    
    token = create_access_token(data={
        "sub": user.email,
        "id": user.user_id,
        "name": user.nickname,
        "level": user.current_level,
        "xp": user.current_xp
    })
    return APIResponse.ok(data={"access_token": token, "token_type": "bearer"}, message="Login successful")


def get_current_db_user(repository: UserRepository, token: str = Depends(oauth2_scheme)) -> User:
    email = verify_token(token)
    user = repository.get_by(email=email)
    if user is None:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    return user

@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_db_user)):
    return current_user
