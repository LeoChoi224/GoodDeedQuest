# 관리자 요청/응답 모델
from __future__ import annotations
"""
Python은 원래 타입을 '지금' 확인한다.
from __future__ import annotations를 쓰면
'지금 확인하지 말고 나중에 확인해.'
"""

from datetime import datetime, date
from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.app.admin.enums import UserReportStatus
from backend.app.auth.enums import UserRole
from typing import Literal

"""
- reporter_id, reviewed_by, reviewed_at은 
사용자가 임의로 조작하면 안 되는 정보이므로 서버에서 자동 처리

상세 이유
- 보안(Security): 사용자가 다른 사람의 ID나 처리 시간을 마음대로 넣지 못하게 함.
- 데이터 무결성(Data Integrity): 실제 신고자, 실제 처리 관리자, 실제 처리 시간이 정확하게 저장되도록 보장함.
"""

# 사용자가 게시글을 신고할 때 전달하는 데이터
class ReportCreate(BaseModel):
    post_id: int = Field(
        ...,
        gt=0,
        description="신고 대상 게시글 ID",
    )

    reason: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="신고 사유",
    )

    @field_validator("reason")
    @classmethod
    def validate_reason_not_blank(cls, value: str) -> str:
        stripped_value = value.strip()

        if not stripped_value:
            raise ValueError("신고 사유는 공백일 수 없습니다.")

        return stripped_value

# 관리자가 신고 상태를 변경할 때 사용하는 데이터
class ReportReviewUpdate(BaseModel):
    """관리자의 신고 검토 요청."""

    status: Literal[
        UserReportStatus.APPROVED,
        UserReportStatus.REJECTED,
    ] = Field(
        ...,
        description="관리자 신고 처리 결과",
    )

# 클라이언트에게 신고 정보를 반환할 때 사용하는 모델
class ReportResponse(BaseModel):
    # SQLAlchemy Model 객체를 그대로 Response로 변환할 수 있게 해주는 설정
    model_config = ConfigDict(from_attributes=True)

    report_id: int
    reporter_id: int
    reviewed_by: int | None
    post_id: int | None
    reason: str
    status: UserReportStatus
    created_at: datetime
    reviewed_at: datetime | None
    updated_at: datetime


"""관리자 사용자 관리 요청/응답 Schema"""

# 관리자가 사용자 활성 상태를 변경할 때 전달하는 요청 데이터.
class UserActiveStatusUpdate(BaseModel):
    # true이면 활성, false이면 비활성 상태로 변경.
    is_active: bool = Field(
        ...,
        description="변경할 사용자 활성 상태",
    )

# 관리자 사용자 목록에서 한 명의 사용자 정보를 반환하는 응답.
class AdminUserListResponse(BaseModel):
    # SQLAlchemy User 객체를 Pydantic 응답으로 변환합니다.
    model_config = ConfigDict(from_attributes=True)
    user_id: int
    email: str
    nickname: str
    profile_image_url: str | None
    is_active: bool
    role: UserRole
    trust_score: int
    current_level: int
    created_at: datetime
    updated_at: datetime

# 관리자 사용자 상세 화면에 사용자 정보를 반환하는 응답.
class AdminUserDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: int
    region_id: int | None
    email: str
    provider: str | None
    nickname: str
    birthday: date | None
    category: list | None
    active_time: list | None
    profile_image_url: str | None
    trust_score: int
    point_balance: int
    current_xp: int
    current_level: int
    daily_streak: int
    is_active: bool
    role: UserRole
    created_at: datetime
    updated_at: datetime



# 관리자 대시보드 오늘의 요약 정보를 반환하는 응답.
class AdminDashboardSummaryResponse(BaseModel):
    """관리자 대시보드 오늘의 요약 응답."""

    total_user_count: int = Field(
        ...,
        ge=0,
        description="전체 사용자 수",
    )

    active_user_count: int = Field(
        ...,
        ge=0,
        description="활성 상태인 사용자 수",
    )

    inactive_user_count: int = Field(
        ...,
        ge=0,
        description="비활성 상태인 사용자 수",
    )

    today_access_user_count: int = Field(
        ...,
        ge=0,
        description="오늘 접속한 사용자 수",
    )

    pending_report_count: int = Field(
        ...,
        ge=0,
        description="처리 대기 상태인 신고 수",
    )


# 관리자 대시보드 주요 알림 한 건을 반환하는 응답.
class AdminDashboardAlertResponse(BaseModel):
    """관리자 대시보드 주요 알림 응답."""

    type: str = Field(
        ...,
        description="알림 종류",
    )

    level: str = Field(
        ...,
        description="알림 표시 수준",
    )

    title: str = Field(
        ...,
        description="알림 제목",
    )

    message: str = Field(
        ...,
        description="관리자 화면에 표시할 알림 문구",
    )

    count: int = Field(
        ...,
        ge=0,
        description="알림 관련 데이터 개수",
    )  


# 관리자 대시보드 최근 7일 활동 추이의 날짜별 데이터를 반환하는 응답.
class AdminDashboardActivityTrendResponse(BaseModel):
    """관리자 대시보드 날짜별 접속 사용자 수 응답."""

    access_date: date = Field(
        ...,
        description="접속 사용자 수를 집계한 날짜",
    )

    user_count: int = Field(
        ...,
        ge=0,
        description="해당 날짜에 접속한 사용자 수",
    )