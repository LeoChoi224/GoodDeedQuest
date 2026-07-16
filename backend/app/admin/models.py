from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Identity,
    Text,
    UniqueConstraint,
    func,
)

from sqlalchemy.orm import Mapped, mapped_column

from backend.app.common.database import Base
from backend.app.admin.enums import UserReportStatus


class Report(Base):
    """커뮤니티 게시글 신고 및 관리자 검토 기록."""

    __tablename__ = "report"

    __table_args__ = (
        UniqueConstraint(
            "reporter_id",
            "post_id",
            name="uq_report_reporter_post",
        ),
    )

    report_id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(), # PostgreSQL 에서 숫자 자동 상승.
        primary_key=True,
    )
    reporter_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("user.user_id"),
        nullable=False,
        index=True, # 검색 속도를 빠르게 하기 위해 인덱스를 만든다 (?)
    )
    
    """
    신고가 처음 접수될 때는 아직 관리자가 검토하지 않았으므로 reviewed_by는 필수값이면 안됨.
    신고 생성 직후에는 : 
    reviewed_by = NULL
    reviewed_at = NULL
    status = PENDING
    관리자가 처리하면 그때 관리자 ID와 처리 시간이 들어가는 구조가 자연스러움

    ondelete="SET NULL"
    SET NULL은 부모 데이터가 삭제되면 FK 값을 NULL로 바꿈
    """
    reviewed_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("user.user_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    post_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("community_post.post_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    # ******** status 기존 str 타입에서 enum 으로 변경 (erd 수정완료) ********
    status: Mapped[UserReportStatus] = mapped_column(
        SqlEnum(UserReportStatus, name="report_status"),
        nullable=False,
        server_default=UserReportStatus.PENDING.value,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), # 시간(Timezone) 정보까지 함께 저장하는 날짜/시간 타입. ex) 2026-07-14 15:30:12+09:00
        nullable=False,
        server_default=func.now(),
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(), # 데이터가 수정될 때마다 현재 시간으로 자동 변경해주는 옵션
    )
