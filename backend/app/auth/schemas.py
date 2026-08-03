from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from backend.app.common.enums import Difficulty
from backend.app.auth.enums import UserRole, TransactionType

class UserBase(BaseModel):
    nickname: str
    email: EmailStr | None = None # EmailStr을 사용하여 이메일 골뱅이(@) 및 도메인 형식을 자동 검증
                                    # pip install pydantic[email]

    @field_validator('email', mode="before")
    @classmethod
    def allow_empty_string_for_email(cls, v):
        if v == "":
            return None

        return v 

# ═══════════════════════════════════════
# ① 회원가입
# ═══════════════════════════════════════
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)   # 평문 → 서버에서 해싱 후 password_hash로 저장
    nickname: str = Field(..., min_length=2, max_length=50)
    birthday: date = Field(...)
    active_time: Optional[list[str]] = None
    category: Optional[list[str]] = None
    
    # 소셜 로그인 시에만 채워짐 (일반 가입이면 둘 다 None)
    provider: Optional[str] = None
    provider_user_id: Optional[str] = None


# ═══════════════════════════════════════
# ①-1 중복확인 (이메일 · 닉네임)
# ═══════════════════════════════════════
class AvailabilityResponse(BaseModel):
    """【기능】 가입 전에 이메일/닉네임을 쓸 수 있는지 미리 알려준다.

    available=False 여도 200 으로 응답한다. 400/409 로 주면 프론트의 axios 가
    에러로 던져 버려서, '중복이라 못 쓴다'와 '서버가 죽었다'를 구분할 수 없다.
    """
    available: bool


# ═══════════════════════════════════════
# ② 소셜 로그인 (OAuth)
# ═══════════════════════════════════════
class SocialLoginRequest(BaseModel):
    provider: str        # 'google','kakao'
    id_token: str


# ═══════════════════════════════════════
# ③ 로그인
# ═══════════════════════════════════════
class LoginRequest(BaseModel):
    email: EmailStr
    password: str                    # 검증용 평문, DB의 password_hash와 bcrypt.checkpw()로 비교


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    is_new_user: bool = False
    # password_hash 등 유저 정보는 응답에 절대 포함하지 않음


# ═══════════════════════════════════════
# ④ 온보딩 (관심사 설정)
# ═══════════════════════════════════════
class OnboardingRequest(BaseModel):
    category: list[str]
    active_time: str
    preferred_difficulty: Difficulty


# ═══════════════════════════════════════
# ⑤ 내 프로필 조회 (마이페이지)
# ═══════════════════════════════════════
class MyProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    nickname: str
    profile_image_url: Optional[str] = None
    trust_score: int
    point_balance: int
    current_xp: int
    current_level: int
    daily_streak: int



# ═══════════════════════════════════════
# ⑥ 공개 프로필 조회 (남이 보는 내 정보)
# ═══════════════════════════════════════
class PublicProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    nickname: str
    profile_image_url: Optional[str] = None
    current_level: int
    daily_streak: int
    # trust_score, point_balance는 의도적으로 제외 (비공개)


# ═══════════════════════════════════════
# ⑦ 프로필 수정
# ═══════════════════════════════════════
class ProfileUpdateRequest(BaseModel):
    nickname: Optional[str] = Field(None, min_length=2, max_length=50)
    profile_image_url: Optional[str] = None
    category: Optional[list[str]] = None
    active_time: Optional[str] = None
    # email, password는 여기 없음 → 별도 API(/auth/change-email, /auth/change-password)로 분리


# ═══════════════════════════════════════
# ⑧ 위치 기반 퀘스트 추천
# ═══════════════════════════════════════
class LocationUpdateRequest(BaseModel):
    current_latitude: Decimal = Field(..., max_digits=10, decimal_places=7)
    current_longitude: Decimal = Field(..., max_digits=10, decimal_places=7)


class NearbyQuestQueryParams(BaseModel):
    region_id: int
    current_latitude: Decimal
    current_longitude: Decimal
    # profile_embedding은 클라이언트가 보내는 게 아니라 서버 내부에서 AI 추천 계산에만 사용


# ═══════════════════════════════════════
# ⑨ 포인트 내역 조회
# ═══════════════════════════════════════
class PointTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    transaction_id: int
    amount: Optional[int] = None
    type: Optional[TransactionType] = None
    balance_after: Optional[int] = None
    created_at: datetime


class PointTransactionListResponse(BaseModel):
    transactions: list[PointTransactionResponse]
    total_count: int


# ═══════════════════════════════════════
# ⑩ 관리자용 유저 목록
# ═══════════════════════════════════════
class AdminUserListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    email: str
    nickname: str
    role: UserRole
    is_active: bool
    created_at: datetime
    
class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    user_id: int

    point_balance: int = 0
    current_level: int = 1
    current_xp: int = 0

    created_at: datetime

class TokenData(BaseModel):
    username: str | None = None

class ProfileCompleteRequest(BaseModel):
    nickname: str
    birthday: date
    category: Optional[list[str]] = None
    active_time: Optional[list[str]] = None
    
class RefreshRequest(BaseModel):
    refresh_token: str