from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Optional
from backend.app.common.response import APIResponse
from backend.app.common.auth import get_current_user

router = APIRouter(prefix="/quests", tags=["Quests"])

class QuestSchema(BaseModel):
    id: int
    title: str
    description: str
    category: str
    difficulty: str
    xp_reward: int
    point_reward: int
    location: Optional[str] = None

# Mock 데이터
MOCK_QUESTS = [
    {"id": 1, "title": "플로깅(조깅하며 쓰레기 줍기)", "description": "주변 공원에서 쓰레기를 줍고 인증샷을 올리세요.", "category": "환경", "difficulty": "쉬움", "xp_reward": 50, "point_reward": 10, "location": "근처 공원"},
    {"id": 2, "title": "동네 유기동물 보호소 봉사", "description": "동네 유기동물 보호소에 방문하여 봉사활동을 진행하세요.", "category": "봉사", "difficulty": "어려움", "xp_reward": 200, "point_reward": 50, "location": "행복유기동물보호소"},
    {"id": 3, "title": "텀블러 사용하기", "description": "카페에서 일회용 컵 대신 개인 텀블러를 사용한 인증샷을 남겨주세요.", "category": "환경", "difficulty": "쉬움", "xp_reward": 30, "point_reward": 5, "location": "모든 카페"}
]

@router.get("", response_model=APIResponse[List[QuestSchema]])
def get_all_quests(user: dict = Depends(get_current_user)):
    """전체 퀘스트 목록을 조회합니다."""
    return APIResponse.ok(data=MOCK_QUESTS)

@router.get("/{quest_id}", response_model=APIResponse[QuestSchema])
def get_quest_detail(quest_id: int, user: dict = Depends(get_current_user)):
    """특정 퀘스트의 상세 정보를 조회합니다."""
    for q in MOCK_QUESTS:
        if q["id"] == quest_id:
            return APIResponse.ok(data=q)
    return APIResponse.fail(message="Quest not found")
