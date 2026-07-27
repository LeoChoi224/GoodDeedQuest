from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated, List
from backend.app.common.response import APIResponse
from backend.app.common.auth import get_current_user
from backend.app.common.deps import get_repository
from backend.app.common.repository import DatabaseRepository
from backend.app.quest.models import Quest
from backend.app.quest.schemas import QuestSchema

QuestRepository = Annotated[
    DatabaseRepository[Quest],
    Depends(get_repository(Quest))
]

router = APIRouter(prefix="/quests", tags=["Quests"])


@router.get("", response_model=APIResponse[List[QuestSchema]])
def get_all_quests(
    quest_repository: QuestRepository,
    user: dict = Depends(get_current_user),
):
    """전체 퀘스트 목록을 조회합니다."""
    quests = quest_repository.filter()
    return APIResponse.ok(data=[QuestSchema.from_quest(q) for q in quests])


@router.get("/{quest_id}", response_model=APIResponse[QuestSchema])
def get_quest_detail(
    quest_id: int,
    quest_repository: QuestRepository,
    user: dict = Depends(get_current_user),
):
    """특정 퀘스트의 상세 정보를 조회합니다."""
    quest = quest_repository.get(quest_id)
    if quest is None:
        raise HTTPException(status_code=404, detail="Quest not found")
    return APIResponse.ok(data=QuestSchema.from_quest(quest))
