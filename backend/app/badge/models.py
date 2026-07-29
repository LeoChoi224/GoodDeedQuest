"""
badge 도메인 - Badge, UserBadge 모델
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Integer, String, Boolean, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.common.database import Base


class Badge(Base):
    """뱃지 테이블 - 뱃지 종류/정의를 저장"""
    __tablename__ = "badge"

    badge_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    icon_url: Mapped[str] = mapped_column(String(500), nullable=False)
    badge_category: Mapped[str] = mapped_column(String(30), nullable=False)
    # ⭐ 수정: 카테고리 기반 자동 지급 조건 (Category.code 값과 매핑, 완료 횟수)
    condition_category: Mapped[str] = mapped_column(String(30), nullable=False)
    condition_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    user_badges: Mapped[list["UserBadge"]] = relationship("UserBadge", back_populates="badge")


class UserBadge(Base):
    """뱃지 부여 기록 테이블 - 유저가 획득한 뱃지 이력"""
    __tablename__ = "user_badge"

    user_badge_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user.user_id"), nullable=False)
    badge_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("badge.badge_id"), nullable=False)
    is_equipped: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    awarded_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    badge: Mapped["Badge"] = relationship("Badge", back_populates="user_badges")
    user: Mapped["User"] = relationship("User", back_populates="user_badges")