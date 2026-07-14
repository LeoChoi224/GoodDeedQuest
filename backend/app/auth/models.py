"""
auth 도메인 - User 모델
"""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    BigInteger, Integer, String, Boolean, Date, TIMESTAMP,
    Numeric, JSON, UniqueConstraint, ForeignKey, func, Enum as SqlEnum,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.common.database import Base
from backend.app.common.enums import Difficulty      # 공용 enum (auth·quest 공유)
from backend.app.auth.enums import UserRole           # auth 전용 enum


class User(Base):
    __tablename__ = "user"

    # 정수 primary_key는 기본으로 auto increment
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    # → Region (아직 안 만든 테이블이라 FK는 주석)
    region_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    # region_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("Region.region_id"), nullable=False)

    email: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)          # 'google' / 'kakao'
    provider_user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # 구글 sub / 카카오 id
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nickname: Mapped[str] = mapped_column(String(50), nullable=False)
    birthday: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    category: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)            # 관심 카테고리(멀티)
    active_time: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # [enum] 선호 난이도 5단계 (공용 Difficulty, 사용자가 회원가입 때 선택)
    preferred_difficulty: Mapped[Optional[Difficulty]] = mapped_column(SqlEnum(Difficulty, validate_strings=True), nullable=True)

    profile_embedding: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)   # AI 추천용 임베딩
    profile_image_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    trust_score: Mapped[int] = mapped_column(Integer, default=0)
    point_balance: Mapped[int] = mapped_column(Integer, default=0)
    current_xp: Mapped[int] = mapped_column(Integer, default=0)
    current_level: Mapped[int] = mapped_column(Integer, default=1)
    daily_streak: Mapped[int] = mapped_column(Integer, default=0)

    # [개선] is_activate → is_active (이름 통일)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # [enum] 권한 (서버가 정함). 기본값 USER
    role: Mapped[UserRole] = mapped_column(
        SqlEnum(UserRole, validate_strings=True), nullable=False,
        default=UserRole.USER, server_default=UserRole.USER.value,
    )

    current_latitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7), nullable=True)
    current_longitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7), nullable=True)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())
    # [개선] onupdate — 행이 바뀌면 updated_at 자동 갱신
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now()
    )

    # [개선] UNIQUE 추가 (중복가입 방지). OAuth는 이메일이 없을 수도 있어 복합키가 핵심
    __table_args__ = (
        UniqueConstraint("email", name="uq_user_email"),
        UniqueConstraint("provider", "provider_user_id", name="uq_user_provider"),
    )
