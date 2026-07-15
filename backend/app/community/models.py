from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Identity,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.common.database import Base


class CommunityPost(Base):
    """사용자가 커뮤니티 피드에 등록한 게시글."""

    __tablename__ = "community_post"

    post_id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(),
        primary_key=True,
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("user.user_id"),
        nullable=False,
        index=True,
    )
    submission_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("quest_submission.submission_id"),
        index=True,
    )

    media_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    caption: Mapped[str | None] = mapped_column(Text)

    is_active: Mapped[bool] = mapped_column(
    Boolean,
    nullable=False,
    server_default="true",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class PostLike(Base):
    """사용자의 게시글 좋아요."""

    __tablename__ = "post_like"

    post_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("community_post.post_id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("user.user_id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class Comment(Base):
    """커뮤니티 게시글 댓글."""

    __tablename__ = "comment"

    comment_id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(),
        primary_key=True,
    )
    post_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("community_post.post_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("user.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    content: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    # is_activate: Mapped[bool | None] = mapped_column(Boolean)
    # 댓글 신고기능없어서 활성 여부 컬럼 삭제 
    # 게시물은 신고기능이있어 관리자가 삭제 및 차단 할수있기에 필요하지만 댓글은 필요없음.
    # 게시물 주인이나 댓글 쓴 당사자가 지운다고 쳐도. 그냥 지워버리면 되는거라 DB에 활성여부 필요없음

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class FeedHiddenPreference(Base):
    """사용자가 관심없음처리."""

    __tablename__ = "feed_hidden_preference"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "post_id",
            name="uq_feed_hidden_preference_user_post",
        ),
    )

    hidden_id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(),
        primary_key=True,
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("user.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    post_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("community_post.post_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class UserActivityLog(Base):
    """사용자의 일별 접속 기록."""

    __tablename__ = "user_activity_log"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "access_date",
            name="uq_user_activity_log_user_date",
        ),
    )

    activity_id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(),
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("user.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    access_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        server_default=func.current_date(),
        index=True,
    )
