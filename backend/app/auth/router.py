from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy.exc import IntegrityError
from backend.app.common.response import APIResponse
from backend.app.common.auth import create_access_token, get_password_hash, verify_password
from backend.app.auth.schemas import UserResponse, UserCreate, LoginResponse, LoginRequest, SocialLoginRequest, ProfileCompleteRequest, LocationUpdateRequest, RefreshRequest, AvailabilityResponse
from typing import Annotated
from backend.app.auth.models import User
from backend.app.common.deps import get_repository
from backend.app.common.repository import DatabaseRepository    
from backend.app.common.auth import create_access_token, get_password_hash, verify_password, verify_token, oauth2_scheme
from backend.app.auth.service import (
    trigger_embedding_if_needed, verify_google_id_token, find_or_create_social_user,
    record_daily_user_activity, issue_refresh_token, consume_refresh_token,
    revoke_all_refresh_tokens, verify_kakao_access_token
)


router = APIRouter(prefix="/auth", tags=["Authentication"])

UserRepository = Annotated[
    DatabaseRepository[User],
    Depends(get_repository(User))
]

@router.post('/register', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, repository: UserRepository):
    if repository.get_by(email=user_in.email):
        raise HTTPException(status_code=400, detail="이미 가입된 이메일입니다.")

    # 【판단】 중복확인 버튼을 눌러 통과했더라도 여기서 다시 센다. 확인 시점과 가입
    # 시점 사이에 남이 같은 닉네임으로 가입할 수 있어서다. 버튼은 안내용이고,
    # 실제로 막는 곳은 이 줄이다.
    nickname = user_in.nickname.strip()
    if repository.get_by(nickname=nickname):
        raise HTTPException(status_code=400, detail="이미 사용 중인 닉네임입니다.")

    data = user_in.model_dump(exclude={'password'})
    data['nickname'] = nickname
    data['password_hash'] = get_password_hash(user_in.password)

    try:
        return repository.create(data)
    except IntegrityError:
        # 【기능】 위의 두 검사를 통과한 뒤, 저장하기 직전에 남이 같은 이메일/닉네임으로
        # 먼저 가입한 경우다. DB 의 uq_user_email / uq_user_nickname 이 잡아낸다.
        # 그냥 두면 500 이 나가서 사용자는 서버 장애인 줄 안다.
        repository.session.rollback()
        raise HTTPException(status_code=400, detail="이미 사용 중인 이메일 또는 닉네임입니다.")


@router.get('/check-email', response_model=APIResponse[AvailabilityResponse])
def check_email(repository: UserRepository, email: str = Query(..., description="가입에 쓸 이메일")):
    """【기능】 이메일을 쓸 수 있는지 미리 확인한다. 중복이어도 200 으로 답한다."""
    value = email.strip()

    try:
        # 【문법】 TypeAdapter 는 pydantic 모델을 만들지 않고 타입 하나만 따로
        # 검증하고 싶을 때 쓴다. 여기선 EmailStr(이메일 형식) 규칙만 빌려 쓴다.
        TypeAdapter(EmailStr).validate_python(value)
    except ValidationError:
        return APIResponse.ok(data={"available": False}, message="이메일 형식을 확인해 주세요.")

    if repository.get_by(email=value):
        return APIResponse.ok(data={"available": False}, message="이미 가입된 이메일입니다.")

    return APIResponse.ok(data={"available": True}, message="사용 가능한 이메일입니다.")


@router.get('/check-nickname', response_model=APIResponse[AvailabilityResponse])
def check_nickname(
    repository: UserRepository,
    nickname: str = Query(..., description="가입에 쓸 닉네임"),
    token: str | None = Depends(oauth2_scheme),
):
    """【기능】 닉네임을 쓸 수 있는지 미리 확인한다. 중복이어도 200 으로 답한다."""
    value = nickname.strip()

    # 【판단】 길이 하한/상한은 UserCreate(2~50자)와 같은 값을 쓴다. 여기만 다르게
    # 잡으면 '중복확인은 통과했는데 가입에서 422' 가 나온다.
    if not (2 <= len(value) <= 50):
        return APIResponse.ok(data={"available": False}, message="닉네임은 2자 이상 50자 이하여야 합니다.")

    # 【판단】 로그인한 사람이면 "나"는 중복에서 뺀다. 소셜로 막 가입하면 계정이
    # 이미 만들어져 있고 닉네임도 SDK 가 준 이름으로 채워져 있는데, 그 이름을
    # 그대로 쓰려고 중복확인을 누르면 자기 자신에 걸려 "이미 사용 중"이 나왔다.
    # 【문법】 oauth2_scheme 은 auto_error=False 라 토큰이 없으면 None 을 준다.
    # 회원가입 전(토큰 없음)에도 이 API 를 그대로 쓸 수 있어야 하므로, 토큰이
    # 없거나 만료됐으면 조용히 전체를 검사하는 원래 동작으로 돌아간다.
    me = None
    if token:
        try:
            me = repository.get_by(email=verify_token(token))
        except Exception:
            me = None

    found = repository.get_by(nickname=value)
    if found is not None and (me is None or found.user_id != me.user_id):
        return APIResponse.ok(data={"available": False}, message="이미 사용 중인 닉네임입니다.")

    return APIResponse.ok(data={"available": True}, message="사용 가능한 닉네임입니다.")


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
    refresh = issue_refresh_token(repository, user.user_id)
    return APIResponse.ok(data={"access_token": token, "refresh_token": refresh, "token_type": "bearer"}, message="Login successful")

@router.post('/social-login', response_model=APIResponse[LoginResponse])
def social_login(req: SocialLoginRequest, repository: UserRepository, background_tasks: BackgroundTasks):
    if req.provider == "google":
        try:
            idinfo = verify_google_id_token(req.id_token)
        except ValueError:
            raise HTTPException(status_code=401, detail="Invalid Google token")
        email = idinfo.get("email")
        provider_user_id = idinfo.get("sub")
        nickname = idinfo.get("name") or email.split("@")[0]

    elif req.provider == "kakao":
        # 【기능】 카카오는 id_token 칸에 access_token 이 담겨 온다 (schemas.py 주석 참고)
        info = verify_kakao_access_token(req.id_token)
        email = info["email"]
        provider_user_id = info["id"]
        nickname = info["nickname"]

    else:
        raise HTTPException(status_code=400, detail="Unsupported provider")
    
    user, is_new_user = find_or_create_social_user(repository, req.provider, provider_user_id, email, nickname)
    record_daily_user_activity(repository=repository,user_id=user.user_id,)
    trigger_embedding_if_needed(user, background_tasks)
    
    token = create_access_token(data={
        "sub": user.email,
        "id": user.user_id,
        "name": user.nickname,
        "level": user.current_level,
        "xp": user.current_xp
    })
    refresh = issue_refresh_token(repository, user.user_id)
    return APIResponse.ok(data={"access_token": token, "refresh_token": refresh, "token_type": "bearer", "is_new_user": is_new_user}, message="Social login successful")



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
    # 【판단】 닉네임 중복을 여기서도 검사한다. uq_user_nickname 제약이 걸려 있어
    # 남의 닉네임을 넣으면 IntegrityError 가 그대로 터져 500 이 나간다.
    # "!= current_user.nickname" 이 핵심이다. 자기 이름을 그대로 두는 것은
    # 중복이 아니므로, 이 조건이 없으면 프로필을 저장할 때마다 자기 자신에
    # 걸려서 아무것도 못 고치게 된다.
    nickname = data.nickname.strip()
    if nickname != current_user.nickname and repository.get_by(nickname=nickname):
        raise HTTPException(status_code=400, detail="이미 사용 중인 닉네임입니다.")

    current_user.nickname = nickname
    current_user.birthday = data.birthday
    current_user.category = data.category
    current_user.active_time = data.active_time

    try:
        repository.session.commit()
    except IntegrityError:
        # 위 검사와 저장 사이에 남이 같은 닉네임을 차지한 경우.
        repository.session.rollback()
        raise HTTPException(status_code=400, detail="이미 사용 중인 닉네임입니다.")

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

@router.post("/refresh")
def refresh_access_token(
    req: RefreshRequest,
    repository: UserRepository,
):
    
    row = consume_refresh_token(repository, req.refresh_token)
    user = repository.get(row.user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="다시 로그인해 주세요.")

    token = create_access_token(data={
        "sub": user.email,
        "id": user.user_id,
        "name": user.nickname,
        "level": user.current_level,
        "xp": user.current_xp,
    })
    refresh = issue_refresh_token(repository, user.user_id)
    return APIResponse.ok(
        data={"access_token": token, "refresh_token": refresh, "token_type": "bearer"},
        message="Token refreshed",
    )


@router.post("/logout")
def logout(
    repository: UserRepository,
    current_user: User = Depends(get_current_db_user),
):
    
    count = revoke_all_refresh_tokens(repository, current_user.user_id)
    return APIResponse.ok(data={"revoked": count}, message="Logged out")