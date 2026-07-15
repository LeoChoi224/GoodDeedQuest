from sqlalchemy import Integer, BigInteger, String, Text, TIMESTAMP, ForeignKey, JSON, Boolean, Enum as SQLEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional, List
from backend.app.common.database import Base

from backend.app.quest.enums import QuestTarget, QuestType, QuestSource, QuestStatus
from backend.app.common.enums import Difficulty

class Category(Base):
    """퀘스트 카테고리 모델"""
    __tablename__ = "category"

    category_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="카테고리명 (예: 환경, 봉사)")
    icon_url: Mapped[str] = mapped_column(String(500), nullable=False, comment="카테고리 아이콘 이미지 URL")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, comment="카테고리 활성화 상태")

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now(), comment="생성 일시"
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False, comment="수정 일시"
    )

    # 1:N 관계 정의 (하나의 카테고리에 여러 퀘스트가 포함됨)
    quests: Mapped[List["Quest"]] = relationship("Quest", back_populates="category")

    def __repr__(self):
        return f"<Category category_id={self.category_id} name={self.name}>"


class Quest(Base):
    """퀘스트 모델 (실제 봉사 및 AI 생성 퀘스트 원본 테이블)"""
    __tablename__ = "quest"

    quest_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    
    category_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("category.category_id", ondelete="RESTRICT"), nullable=False, comment="카테고리 ID"
    )
    
    creator_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False, comment="등록한 주체 ID (AI 또는 관리자/유저)"
    )
    
    quest_title: Mapped[str] = mapped_column(String(200), nullable=False, comment="퀘스트 제목")
    quest_description: Mapped[str] = mapped_column(Text, nullable=False, comment="퀘스트 상세 설명")
    
    quest_target: Mapped[QuestTarget] = mapped_column(
        SQLEnum(QuestTarget, name="quest_target_enum"), nullable=False, default=QuestTarget.SOLO, comment="참여 방식 (SOLO / TEAM)"
    )
    quest_type: Mapped[QuestType] = mapped_column(
        SQLEnum(QuestType, name="quest_type_enum"), nullable=False, comment="퀘스트 종류 (VOLUNTEER / GOOD_DEED)"
    )
    quest_source: Mapped[QuestSource] = mapped_column(
        SQLEnum(QuestSource, name="quest_source_enum"), nullable=False, default=QuestSource.ADMIN, comment="등록 출처 (USER / AI / ADMIN)"
    )
    
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="봉사 장소 및 주소 (일상 퀘스트는 None)")
    
    # AI 보상 산정 결과 나오기 전에 퀘스트 등록을 위해 null 허용 - 추후 코드 구현하다 변경사항은 직접 수정하시면 됩니다. @yangjungun05-prog
    reward_point: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="지급 보상 포인트")
    reward_exp: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="지급 보상 경험치")
    
    difficulty: Mapped[Difficulty] = mapped_column(
        SQLEnum(Difficulty, name="quest_difficulty_enum"), nullable=False, comment="난이도 (VERY EASY ~ VERY HARD)"
    )
    
    # 벡터 검색용 퀘스트 임베딩 정보 (임베딩 데이터는 비동기로 처리되므로 생성 직후에는 Null이 허용되어야 함)
    quest_embedding: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment="벡터 검색용 퀘스트 임베딩 정보")
    
    quest_status: Mapped[QuestStatus] = mapped_column(
        SQLEnum(QuestStatus, name="quest_status_enum"), nullable=False, default=QuestStatus.NOT_STARTED, comment="진행 상태"
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now(), comment="생성 일시"
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP, nullable=True, comment="퀘스트 수행 완료 일시"
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False, comment="수정 일시"
    )
    # 관계 설정 (카테고리)
    category: Mapped["Category"] = relationship("Category", back_populates="quests")
    
    # TODO User, Team, QuestSubmission 테이블 병합 시 각각 주석 해제
    # creator: Mapped["User"] = relationship("User", back_populates="created_quests")
    # teams: Mapped[List["Team"]] = relationship("Team", back_populates="quest")
    # submissions: Mapped[List["QuestSubmission"]] = relationship("QuestSubmission", back_populates="quest")
    
    """
    순환 참조 방지를 위해 ai_recommendations 관계 필드는 제거
    ai_recommendations: Mapped[List["AiRecommendation"]] = relationship("AiRecommendation", back_populates="quest")
    """
    
    def __repr__(self):
        return f"<Quest quest_id={self.quest_id} title={self.title} source={self.source}>"