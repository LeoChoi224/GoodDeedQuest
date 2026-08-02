from typing import List, Optional
from pydantic import BaseModel, Field

class QuestRecommendRequest(BaseModel):
    """AI 퀘스트 추천 요청 DTO"""
    user_id: int = Field(
        ...,
        # "사용자 식별 ID"
        description="User unique identification ID"
    )
    interests: List[str] = Field(
        default_factory=list,
        # "사용자 관심사 카테고리 목록 (예: VOLUNTEER, ENVIRONMENT 등)"
        description="List of user interest categories (e.g. VOLUNTEER, ENVIRONMENT)"
    )
    region_id: Optional[int] = Field(
        default=None,
        # "지역 식별 ID"
        description="Region identification ID"
    )
    latitude: Optional[float] = Field(
        default=None,
        # "현재위치 위도"
        description="Current latitude coordinate"
    )
    longitude: Optional[float] = Field(
        default=None,
        # "현재위치 경도"
        description="Current longitude coordinate"
    )
    level: int = Field(
        default=1,
        # "사용자 레벨"
        description="User level"
    )
    history_quests: List[str] = Field(
        default_factory=list,
        # "이전 완료 퀘스트 이력"
        description="Titles of previously completed quests"
    )
    recent_recommendations: List[str] = Field(
        default_factory=list,
        # "최근 추천 이력"
        description="Titles of recently recommended quests for deduplication"
    )
    preferred_difficulty: str = Field(
        default="NORMAL",
        # "선호 난이도 (VERY_EASY, EASY, NORMAL, HARD, VERY_HARD)"
        description="Preferred difficulty: VERY_EASY, EASY, NORMAL, HARD, VERY_HARD"
    )
    request_message: Optional[str] = Field(
        default=None,
        # "유저 추가 요청 사항"
        description="Additional user request or prompt message"
    )

class QuestItemSchema(BaseModel):
    """추천 퀘스트 개별 항목 DTO"""
    quest_id: Optional[int] = Field(
        default=None,
        # "퀘스트 DB 식별자"
        description="Quest database primary key ID"
    )
    quest_title: str = Field(
        ...,
        # "퀘스트 제목"
        description="Title of the quest"
    )
    quest_description: str = Field(
        ...,
        # "퀘스트 상세 내용 및 이행 지침"
        description="Detailed description and execution guide of the quest"
    )
    quest_type: str = Field(
        ...,
        # "퀘스트 유형 (VOLUNTEER 또는 GOOD_DEED)"
        description="Quest type: 'VOLUNTEER' for real volunteer works, 'GOOD_DEED' for AI-created daily good deeds"
    )
    recommendation_reason: str = Field(
        ...,
        # "AI 맞춤 추천 사유"
        description="AI recommendation reason explaining why this quest was selected"
    )
    category_name: Optional[str] = Field(
        default=None,
        # "카테고리명 (VOLUNTEER, ENVIRONMENT 등)"
        description="Category name (e.g., VOLUNTEER, ENVIRONMENT, SHARING)"
    )
    location: Optional[str] = Field(
        default=None,
        # "실제 봉사 장소 주소 (GOOD_DEED는 null)"
        description="Real volunteer activity address. Null for GOOD_DEED quests."
    )
    center_id: Optional[int] = Field(
        default=None,
        # "원본 봉사 공고 ID (GOOD_DEED는 null)"
        description="Source VolunteerCenter ID used to open the original posting screen. Null for GOOD_DEED quests."
    )
    quest_target: Optional[str] = Field(
        default="SOLO",
        # "참여 방식 (SOLO / TEAM)"
        description="Participation mode: 'SOLO' or 'TEAM'"
    )
    difficulty: Optional[str] = Field(
        default="NORMAL",
        # "체감 난이도 (VERY_EASY, EASY, NORMAL, HARD, VERY_HARD)"
        description="Quest difficulty: VERY_EASY, EASY, NORMAL, HARD, VERY_HARD"
    )
    estimated_duration: Optional[int] = Field(
        default=15,
        # "분 단위 예상 소요 시간"
        description="Estimated duration in minutes"
    )
    priority_score: Optional[int] = Field(
        default=10,
        # "추천 적합도 점수 (1~10)"
        description="Priority score from 1 to 10 indicating suitability"
    )

class QuestRecommendResponse(BaseModel):
    """AI 퀘스트 추천 응답 DTO"""
    success: bool = Field(
        default=True,
        # "결과 메시지"
        description="Indicates if the API request was successfully processed"
    )
    message: str = Field(
        default="추천 퀘스트가 성공적으로 생성되었습니다.",
        # "결과 메시지"
        description="Response summary message"
    )
    data: List[QuestItemSchema] = Field(
        ...,
        # "최종 5개 추천 퀘스트 리스트"
        description="List of top 5 recommended quest objects"
    )