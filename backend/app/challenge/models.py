from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Identity,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.common.database import Base

# Team 관련 Enum import
from backend.app.challenge.enums import (
    TeamInviteStatus,
    TeamMemberRole,
    TeamStatus,
)


class Team(Base):
    """퀘스트를 함께 수행하는 팀"""

    __tablename__ = "team"

    __table_args__ = (
        CheckConstraint(
            "max_members BETWEEN 2 AND 10",
            name="ck_max_members",
        ),
    )

    team_id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(),
        primary_key=True,
    )

    leader_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("user.user_id"),
        nullable=False,
    )

    quest_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("quest.quest_id"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(100), 
        nullable=False
    )

    password_hash: Mapped[str | None] = mapped_column(
        String(255), 
        nullable=True
    )

    notification: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default="잘 부탁드립니다."
    )

    region: Mapped[str] = mapped_column(
        String(100), 
        nullable=False
    )

    is_public: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true"
    )

    max_members: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="4",
    )

    status: Mapped[TeamStatus] = mapped_column(
        SqlEnum(TeamStatus, name="team_status"),
        nullable=False,
        server_default=TeamStatus.RECRUITING.value,
    )

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class TeamInvite(Base):
    """팀 초대"""

    __tablename__ = "team_invite"

    invite_id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(),
        primary_key=True,
    )

    team_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("team.team_id"),
        nullable=False,
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("user.user_id"),
        nullable=False,
    )

    status: Mapped[TeamInviteStatus] = mapped_column(
        SqlEnum(TeamInviteStatus, name="team_invite_status"),
        nullable=False,
        server_default=TeamInviteStatus.PENDING.value,
    )

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class TeamMember(Base):
    """팀 참가 멤버"""

    __tablename__ = "team_member"

    __table_args__ = (
        UniqueConstraint(
            "team_id",
            "user_id",
            name="uq_team_member_team_user",
        ),
    )

    team_member_id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(),
        primary_key=True,
    )

    team_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("team.team_id"),
        nullable=False,
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("user.user_id"),
        nullable=False,
    )

    role_in_team: Mapped[TeamMemberRole] = mapped_column(
        SqlEnum(TeamMemberRole, name="team_member_role"),
        nullable=False,
        server_default=TeamMemberRole.MEMBER.value,
    )

    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )