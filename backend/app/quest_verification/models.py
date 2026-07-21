"""
quest_verification 도메인 - QuestSubmission 모델
(퀘스트 인증 제출 — 실제 미디어는 여기에만 저장)
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger, Integer, String, Boolean, TIMESTAMP, JSON,
    ForeignKey, func, Enum as SqlEnum,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.common.database import Base
from backend.app.quest_verification.enums import MediaType, SubmissionStatus


class QuestSubmission(Base):
    __tablename__ = "quest_submission"

    submission_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    # → User (만든 테이블이라 FK 연결)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user.user_id"), nullable=False)  # 제출자

    quest_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("quest.quest_id"), nullable=False)

    # → User (만든 테이블이라 FK 연결). 검토자, 없을 수 있어 nullable
    reviewed_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("user.user_id"), nullable=True)

    attempt_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)   # 재시도 추적
    quest_explain: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    # 인증 파일은 S3에 저장하고, DB엔 그 "주소"만 저장 (서버가 채움)
    media_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # [enum] 사진/영상 (서버가 파일 보고 판별 권장)
    media_type: Mapped[Optional[MediaType]] = mapped_column(SqlEnum(MediaType, validate_strings=True), nullable=True)

    media_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)   # 재활용 검사용 해시
    media_embedding: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)    # 도용 검사용 임베딩
    ai_verdict: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)         # Gemini Vision 판단
    ai_generated_suspicion: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    # [enum] 인증 결과 (AI/서버가 정함). 제출 직후 기본값 PENDING
    final_status: Mapped[SubmissionStatus] = mapped_column(
        SqlEnum(SubmissionStatus, validate_strings=True), nullable=False,  # validate_strings -> 파인썬 단위에서 enum 검사 혹시 ai 가 이상한 난이도 배출했을 때 방지
        default=SubmissionStatus.PENDING, server_default=SubmissionStatus.PENDING.value,
    )

    submitted_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now()
    )
