from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List
from backend.app.common.response import APIResponse
from backend.app.common.auth import get_current_user

router = APIRouter(prefix="/challenges", tags=["Collaborative Challenges"])

class ChallengeSchema(BaseModel):
    id: int
    title: str
    description: str
    target_xp: int
    current_xp: int
    participants_count: int
    days_left: int

MOCK_CHALLENGES = [
    {"id": 1, "title": "마포구 제로웨이스트 정복기", "description": "팀원들과 함께 환경 정화 퀘스트를 수행하여 목표 경험치를 달성하세요.", "target_xp": 1000, "current_xp": 450, "participants_count": 4, "days_left": 5},
    {"id": 2, "title": "따뜻한 연탄 나눔 챌린지", "description": "연탄 봉사 퀘스트를 성공하여 소외된 이웃에게 기부할 연탄을 모으세요.", "target_xp": 3000, "current_xp": 1200, "participants_count": 8, "days_left": 12}
]

@router.get("", response_model=APIResponse[List[ChallengeSchema]])
def get_challenges(user: dict = Depends(get_current_user)):
    """현재 활성화된 협동 챌린지 목록을 가져옵니다."""
    return APIResponse.ok(data=MOCK_CHALLENGES)

@router.post("/join/{challenge_id}")
def join_challenge(challenge_id: int, user: dict = Depends(get_current_user)):
    """협동 챌린지에 참여 신청을 합니다."""
    return APIResponse.ok(message=f"성공적으로 챌린지 {challenge_id}에 참여했습니다.")
