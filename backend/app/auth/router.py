from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from backend.app.common.response import APIResponse
from backend.app.common.auth import create_access_token, get_password_hash, verify_password
from backend.app.auth.schemas import UserResponse, UserCreate, LoginResponse, LoginRequest, SocialLoginRequest, ProfileCompleteRequest, LocationUpdateRequest
from typing import Annotated
from backend.app.auth.models import User
from backend.app.common.deps import get_repository
from backend.app.common.repository import DatabaseRepository    
from backend.app.common.auth import create_access_token, get_password_hash, verify_password, verify_token, oauth2_scheme
from backend.app.auth.service import trigger_embedding_if_needed, verify_google_id_token, find_or_create_social_user, record_daily_user_activity


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
    record_daily_user_activity(repository=repository,user_id=user.user_id,)
    trigger_embedding_if_needed(user, background_tasks)
    
    token = create_access_token(data={
        "sub": user.email,
        "id": user.user_id,
        "name": user.nickname,
        "level": user.current_level,
        "xp": user.current_xp
    })
    return APIResponse.ok(data={"access_token": token, "token_type": "bearer"}, message="Login successful")

@router.post('/social-login', response_model=APIResponse[LoginResponse])
def social_login(req: SocialLoginRequest, repository: UserRepository, background_tasks: BackgroundTasks):
    if req.provider != "google":
        raise HTTPException(status_code=400, detail="Unsupported provider")
    try:
        idinfo = verify_google_id_token(req.id_token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Google token")
    
    email = idinfo.get("email")
    provider_user_id = idinfo.get("sub")
    nickname = idinfo.get("name") or email.split("@")[0]
    
    user, is_new_user = find_or_create_social_user(repository, "google", provider_user_id, email, nickname)
    record_daily_user_activity(repository=repository,user_id=user.user_id,)
    trigger_embedding_if_needed(user, background_tasks)
    
    token = create_access_token(data={
        "sub": user.email,
        "id": user.user_id,
        "name": user.nickname,
        "level": user.current_level,
        "xp": user.current_xp
    })
    return APIResponse.ok(data={"access_token": token, "token_type": "bearer", "is_new_user": is_new_user}, message="Social login successful")



def get_current_db_user(repository: UserRepository, token: str = Depends(oauth2_scheme)) -> User:
    email = verify_token(token)
    user = repository.get_by(email=email)
    if user is None:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    return user

@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_db_user)):
    return current_user

@router.patch("/me", response_model=UserResponse)
def update_my_profile(
    data: ProfileCompleteRequest,
    repository: UserRepository,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_db_user)
):
    current_user.nickname = data.nickname
    current_user.birthday = data.birthday
    current_user.category = data.category
    current_user.active_time = data.active_time
    repository.session.commit()
    repository.session.refresh(current_user)

    trigger_embedding_if_needed(current_user, background_tasks)

    return current_user


@router.patch("/me/location", response_model=UserResponse)
def update_my_location(
    data: LocationUpdateRequest,
    repository: UserRepository,
    current_user: User = Depends(get_current_db_user)
):
    """실시간 GPS 좌표 저장 (User.current_latitude/current_longitude). VolSearchScreen(내주변둘러보기 페이지) 진입 시마다 호출"""
    current_user.current_latitude = data.current_latitude
    current_user.current_longitude = data.current_longitude
    repository.session.commit()
    repository.session.refresh(current_user)
    return current_user