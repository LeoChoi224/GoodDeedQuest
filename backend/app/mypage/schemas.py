"""
backend/app/mypage/schemas.py

MyPage 도메인 Pydantic 스키마 (읽기 전용 집계 레이어, 자체 테이블 없음).
Quest/QuestSubmission(quest_verification) 모델을 조회해서 조립한 응답만 정의한다.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ORMBase(BaseModel):
    """DB 모델 -> 응답 스키마 변환을 위한 공통 설정"""
    model_config = ConfigDict(from_attributes=True)


class MyQuestAchievementResponse(ORMBase):
    """GET /mypage/quests/achievements - 내가 달성한 퀘스트 타임라인/상세 응답"""
    # ⭐ 수정: 같은 퀘스트를 여러 번 완료할 수 있어 quest_id만으로는 항목이 유일하지 않음 -
    # 프론트 리스트 key 등 항목 식별용으로 제출(QuestSubmission) 단위 PK를 추가
    submission_id: int
    quest_id: int
    title: str
    description: str
    # DB 컬럼 이름이 아님 - 프론트 아이콘 매칭용으로 Quest.category에서 조회해 채워 넣는 필드
    category_code: str
    completed_at: datetime
    reward_point: Optional[int]
    reward_exp: Optional[int]


# ⭐ 수정: 마이페이지 상단 프로필 헤더(이름/칭호/레벨/연속접속일/프로필이미지)
class MyProfileResponse(ORMBase):
    """GET /mypage/profile - 마이페이지 상단 프로필 헤더 응답"""
    nickname: str
    title: str  # 현재 장착 중인 칭호(Badge.name) - User 컬럼이 아니라 badge 도메인에서 조회
    current_level: int
    # DB 컬럼(User.daily_streak)이 아님 - user_activity_log 기준으로 매 요청마다 계산
    daily_streak: int
    profile_image_url: Optional[str]


class ProfileImagePresignRequest(BaseModel):
    content_type: str


class ProfileImagePresignResponse(BaseModel):
    upload_url: str
    s3_key: str


class ProfileImageConfirmRequest(BaseModel):
    s3_key: str
