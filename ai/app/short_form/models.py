"""
AI 서버 쪽 읽기 전용 BackgroundMusic 미러 모델

backend/app/short_form/models.py의 BackgroundMusic과 같은 테이블(background_music)을
가리키지만, AI 서버는 이 테이블을 읽기만 하므로(RAG 매칭용) 별도 Base에 필요한
컬럼만 매핑한다. 스키마는 backend 쪽 모델이 원본(source of truth)이며,
컬럼이 추가/변경되면 이 파일도 함께 갱신해야 한다.
"""
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..common.database import Base


class BackgroundMusic(Base):
    __tablename__ = "background_music"

    bgm_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    mood_tag: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    s3_key: Mapped[str] = mapped_column(String(512), nullable=False)
