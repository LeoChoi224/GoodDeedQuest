"""
선행퀘스트 - Badge 도메인 Pydantic 스키마

이슈 #160 대응. models.py(SQLAlchemy)의 Badge/UserBadge 모델에 대응하는 응답 스키마.

컨벤션:
- 파일명: snake_case (schemas.py)
- 클래스명: PascalCase
- 필드명: snake_case (프론트에서 camelCase 변환이 필요하면 별도 alias 처리)
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


# ─────────────────────────────────────────────
# 공통 Base
# ─────────────────────────────────────────────
class ORMBase(BaseModel):
    """DB 모델 -> 응답 스키마 변환을 위한 공통 설정"""
    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────
# Badge 스키마
# ─────────────────────────────────────────────
class BadgeResponse(ORMBase):
    """GET /badges - 전체 배지 도감(미보유 포함) 응답"""
    badge_id: int
    name: str
    description: str
    icon_url: str
    badge_category: str
    # DB 컬럼이 아님 - 서비스 로직에서 현재 유저의 보유 여부를 계산해서 채워 넣는 필드
    is_owned: bool


class MyBadgeResponse(ORMBase):
    """GET /badges/my - 내가 보유한 배지 목록 응답"""
    badge_id: int
    name: str
    description: str
    icon_url: str
    badge_category: str
    is_equipped: bool
    awarded_at: datetime
