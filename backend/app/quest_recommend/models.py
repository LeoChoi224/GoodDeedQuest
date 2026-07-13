from sqlalchemy import Integer, BigInteger, String, Text, DateTime, ForeignKey, JSON, Float, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional, List
from backend.app.common.database import Base

class AiRecommendationLog(Base):
    """AI 추천 요청 및 응답 로그 모델"""
    __tablename__ = "ai_recommendation_log"

    ai_log_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="사용자 ID")
    
    # 추천 요청 당시 상황 (관심사, 위치, 요일, 날씨, 레벨 등) - 필수값
    request_context: Mapped[dict] = mapped_column(
        JSON, nullable=False, comment="추천 요청 당시 수집된 Context JSON"
    )
    
    # AI 응답 결과 전체 로그 - 응답이 실패할 수도 있으므로 Nullable 허용
    response_context: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True, comment="AI가 반환한 최종 추천 결과 데이터 JSON"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="로그 생성 일시"
    )
    
    # 생성 시에는 created_at과 동일한 값이 들어가고, 수정 시 자동 갱신되는 NOT NULL 구조
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False, 
        comment="로그 수정 일시"
    )

    # 1:N 관계 정의 (한 로그에 여러 개의 추천 결과가 딸림)
    recommendations: Mapped[List["AiRecommendation"]] = relationship(
        "AiRecommendation", back_populates="log", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<AiRecommendationLog ai_log_id={self.ai_log_id} user_id={self.user_id} created_at={self.created_at}>"


class AiRecommendation(Base):
    """개별 추천 결과 모델"""
    __tablename__ = "ai_recommendation"

    ai_rec_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    
    # 로그 테이블과의 외래키(FK) 연결 (테이블명 소문자 매칭)
    ai_log_id: Mapped[int] = mapped_column(
        BigInteger, 
        ForeignKey("ai_recommendation_log.ai_log_id", ondelete="CASCADE"), 
        nullable=False, 
        comment="추천 로그 ID"
    )
    
    # 추천된 퀘스트 ID (실제 퀘스트 테이블과 조인용, Nullable)
    quest_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, comment="Quest DB 연동 ID")
    
    # 추천 점수 (유사도 매칭 점수 등, Nullable)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="추천 유사도 점수")
    
    # 추천 사유
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="AI 추천 사유")
    
    # 추천 순위 (1~5등)
    rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="추천 순위")
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="생성 일시"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False, 
        comment="수정 일시"
    )

    # 관계 설정
    log: Mapped["AiRecommendationLog"] = relationship("AiRecommendationLog", back_populates="recommendations")

    def __repr__(self):
        return f"<AiRecommendation ai_rec_id={self.ai_rec_id} rank={self.rank} score={self.score}>"