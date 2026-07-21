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
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.common.database import Base
from backend.app.common.enums import Difficulty      # 공용 enum (auth·quest 공유)
from backend.app.auth.enums import UserRole, TransactionType           # auth 전용 enum


class User(Base):
    __tablename__ = "user"

    # 정수 primary_key는 기본으로 auto increment
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    region_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("region.region_id"), nullable=True)

    email: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)          # 'google' / 'kakao'
    provider_user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # 구글 sub / 카카오 id
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nickname: Mapped[str] = mapped_column(String(50), nullable=False)
    birthday: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    category: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)            # 관심 카테고리(멀티)
    active_time: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)         # 활동 시간대(0/6/12/18시 기준 4구간, 중복 선택 가능)

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
    
    last_embedded_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())
    # [개선] onupdate — 행이 바뀌면 updated_at 자동 갱신
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # [개선] UNIQUE 추가 (중복가입 방지). OAuth는 이메일이 없을 수도 있어 복합키가 핵심
    __table_args__ = (
        UniqueConstraint("email", name="uq_user_email"),
        UniqueConstraint("provider", "provider_user_id", name="uq_user_provider"),
    )
    user_badges = relationship("UserBadge", back_populates="user")
    shortforms = relationship("ShortForm", back_populates="user")
    purchases = relationship("Purchase", back_populates="user")

class PointTransaction(Base):
    __tablename__ = "point_transaction"

    transaction_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    # → User (만든 테이블이라 FK 연결)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user.user_id"), nullable=False)

    # [개선] NOT NULL → nullable. 적립/사용은 둘 중 하나만 채워짐
    #   EARN(적립): submission_id 만  /  SPEND(사용): purchase_id 만

    purchase_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("purchase.purchase_id"), nullable=True)

    submission_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("quest_submission.submission_id"), nullable=True)

    amount: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # [enum] 적립/사용 (서버가 정함)
    type: Mapped[Optional[TransactionType]] = mapped_column(SqlEnum(TransactionType, validate_strings=True), nullable=True)

    balance_after: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 거래 후 잔액
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())

