import enum
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    BigInteger, Column, DateTime, ForeignKey, Integer, String, func
)
# PostgreSQL 전용 JSONB 및 ENUM 사용을 위한 임포트
from sqlalchemy.dialects.postgresql import JSONB, ENUM as PGEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from backend.app.common.database import Base

class ShortFormStatus(str, enum.Enum):
    """숏폼 생성 파이프라인 진행 상태 ENUM (PascalCase)"""
    PENDING = "PENDING"
    GENERATING = "GENERATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class BackgroundMusic(Base):
    """배경음악 목록 테이블"""
    __tablename__ = 'background_music'  # 소문자 snake_case 규칙 반영

    bgm_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # 무드 필터링 및 RAG 매칭을 위한 태그 데이터 (조회 속도 향상을 위한 index 추가)
    mood_tag: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # 풀 URL 주소 대신 S3 오브젝트 Key만 보관하는 아키텍처 규칙 반영
    s3_key: Mapped[str] = mapped_column(String(512), nullable=False)
    
    # 출처 불명 음원이 있을 수 있으므로 nullable 유지
    source_info: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # DB 서버 타임스탬프 기준 자동 생성/수정
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )

    # 1:N 양방향 관계 맺기
    shortforms: Mapped[List["ShortForm"]] = relationship("ShortForm", back_populates="background_music")


class ShortForm(Base):
    """숏폼 프로젝트 결과물 테이블"""
    __tablename__ = 'shortform'  # 소문자 snake_case 규칙 반영

    shorts_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # User 테이블(전체 스키마 기준 PK가 user_id BIGINT이므로 BigInteger 매핑)을 참조하는 외래키
    # TODO: 추후 backend/app/users/models.py가 생성되면 실제 테이블명 및 PK 컬럼명 재확인 필수
    # user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('user.user_id'), nullable=False, index=True)

    # TODO: User 모델이 생성되면 ForeignKey('user.user_id') 추가 + Alembic 마이그레이션 필요 (User 테이블 생성완료시 아래 코드 삭제하고 위코드 주석풀면됨)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)

    # 배경음악 없이는 숏폼 생성 불가 → 필수
    bgm_id: Mapped[int] = mapped_column(Integer, ForeignKey('background_music.bgm_id'), nullable=False, index=True)
    
    # 숏폼 생성 시 제목 필수 입력
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # 일반 JSON 대신 PostgreSQL 전용 고성능 JSONB 타입 적용
    ai_generated_captions: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # 최종 생성된 비디오의 S3 오브젝트 Key 저장
    final_video_s3_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    
    # PostgreSQL 네이티브 ENUM 타입 생성 및 기본값 자동 할당
    status: Mapped[ShortFormStatus] = mapped_column(
        PGEnum(ShortFormStatus, name="shortform_status_enum", native_enum=True),
        nullable=False,
        default=ShortFormStatus.PENDING,
        server_default=ShortFormStatus.PENDING.value
    )
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )

    # 관계 설정
    background_music: Mapped[Optional["BackgroundMusic"]] = relationship("BackgroundMusic", back_populates="shortforms")