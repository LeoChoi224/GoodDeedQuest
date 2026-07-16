# 관리자 요청/응답 모델
from __future__ import annotations
"""
Python은 원래 타입을 '지금' 확인한다.
from __future__ import annotations를 쓰면
'지금 확인하지 말고 나중에 확인해.'
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.app.admin.enums import UserReportStatus
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