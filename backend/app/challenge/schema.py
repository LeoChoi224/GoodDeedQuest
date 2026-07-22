from __future__ import annotations

# =========================================================
# [반드시 확인 및 검토할 사항]
#
# 1. 팀 목록에 퀘스트 제목, 카테고리 아이콘, 장소, 시행 일자까지 표시하려면
#    - Quest 모델 구조가 확정된 뒤 Repository JOIN과 응답 Schema 필드를 추가.
#
# 2. TeamMemberResponse는 현재 TeamMember 테이블 정보만 반환합니다.
#    - 닉네임과 프로필 이미지가 필요하면 User 모델 JOIN이 추가로 필요.
# =========================================================

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from backend.app.challenge.enums import (
    TeamInviteStatus,
    TeamMemberRole,
    TeamStatus,
)
from typing import Literal



class TeamCreate(BaseModel):
    """팀 생성 요청."""

    quest_id: int = Field(
        ...,
        gt=0,
        description="팀이 수행할 퀘스트 ID",
    )

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="팀 이름",
    )

    # 클라이언트에서는 비밀번호 원문을 전달하고,
    # 서비스 계층에서 해시 처리한 뒤 password_hash 컬럼에 저장한다.
    password: str | None = Field(
        default=None,
        min_length=4,
        max_length=20,
        description="비공개 팀 입장 비밀번호",
    )

    notification: str = Field(
        default="잘 부탁드립니다.",
        min_length=1,
        max_length=2000,
        description="팀 공지사항",
    )

    region: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="팀 활동 지역",
    )

    is_public: bool = Field(
        default=True,
        description="팀 공개 여부",
    )

    max_members: int = Field(
        default=4,
        ge=2,
        le=10,
        description="팀 최대 인원",
    )

    expires_at: datetime | None = Field(
        default=None,
        description="팀 활동 만료 시각",
    )

    # 팀 이름, 공지사항, 활동 지역에 공백만 입력하는 것을 방지하고
    # 문자열 앞뒤의 불필요한 공백을 제거한다.
    @field_validator(
        "name",
        "notification",
        "region",
    )
    @classmethod
    def validate_not_blank(cls, value: str) -> str:
        stripped_value = value.strip()

        if not stripped_value:
            raise ValueError("공백만 입력할 수 없습니다.")

        return stripped_value

    # 공개 팀은 비밀번호를 사용할 수 없고,
    # 비공개 팀은 비밀번호를 반드시 입력해야 한다.
    @model_validator(mode="after")
    def validate_team_password(self) -> TeamCreate:
        if self.is_public and self.password is not None:
            raise ValueError(
                "공개 팀에는 비밀번호를 설정할 수 없습니다."
            )

        if not self.is_public and not self.password:
            raise ValueError(
                "비공개 팀은 비밀번호를 입력해야 합니다."
            )

        if self.password is not None and not self.password.strip():
            raise ValueError(
                "비밀번호는 공백만 입력할 수 없습니다."
            )

        return self


class TeamPasswordVerify(BaseModel):
    """비공개 팀 입장 비밀번호 확인 요청."""

    password: str = Field(
        ...,
        min_length=4,
        max_length=20,
        description="비공개 팀 입장 비밀번호",
    )

    @field_validator("password")
    @classmethod
    def validate_password_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("비밀번호는 공백만 입력할 수 없습니다.")

        return value

class TeamResponse(BaseModel):
    """팀 조회 응답."""

    # password_hash는 보안상 응답 Schema에 포함하지 않는다.
    model_config = ConfigDict(from_attributes=True)

    team_id: int
    leader_id: int
    quest_id: int
    name: str
    notification: str
    region: str
    is_public: bool
    max_members: int
    status: TeamStatus
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime

# 팀 목록 화면에서 팀 기본 정보와 현재 참가 인원을 반환.
class TeamListItemResponse(TeamResponse):

    current_members: int = Field(
        ...,
        ge=0,
        description="현재 팀 참가 인원",
    )

# 팀 상세 화면에서 팀 기본 정보와 현재 참가 인원을 반환.
class TeamDetailResponse(TeamResponse):

    current_members: int = Field(
        ...,
        ge=0,
        description="현재 팀 참가 인원",
    )


class TeamInviteCreate(BaseModel):
    """팀 초대 생성 요청."""

    team_id: int = Field(
        ...,
        gt=0,
        description="초대할 팀 ID",
    )

    user_id: int = Field(
        ...,
        gt=0,
        description="초대받을 사용자 ID",
    )

    expires_at: datetime | None = Field(
        default=None,
        description="초대 만료 시각",
    )


class TeamInviteStatusUpdate(BaseModel):
    """사용자가 팀 초대를 수락하거나 거절할 때 사용하는 요청 Schema.

    PENDING은 초대 생성 시 서버가 설정하고,
    EXPIRED는 만료 처리 로직과 Celery Task가 관리하므로
    클라이언트 요청값으로 허용하지 않습니다.
    """

    status: Literal[
        TeamInviteStatus.ACCEPTED,
        TeamInviteStatus.REJECTED,
    ] = Field(
        ...,
        description="초대 처리 상태: ACCEPTED 또는 REJECTED만 가능",
    )


class TeamInviteResponse(BaseModel):
    """팀 초대 조회 응답."""

    model_config = ConfigDict(from_attributes=True)

    invite_id: int
    team_id: int
    user_id: int
    status: TeamInviteStatus
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime


class TeamMemberResponse(BaseModel):
    """팀 멤버 조회 응답."""

    model_config = ConfigDict(from_attributes=True)

    team_member_id: int
    team_id: int
    user_id: int
    role_in_team: TeamMemberRole
    joined_at: datetime
    updated_at: datetime