from pydantic import BaseModel
from typing import Optional
from backend.app.quest.enums import QuestType, QuestStatus
from backend.app.common.enums import Difficulty


class QuestSchema(BaseModel):
    """퀘스트 조회 응답. 카테고리는 프론트 아이콘 매칭용 code와 표시용 name을 함께 준다."""
    quest_id: int
    quest_title: str
    quest_description: str
    quest_type: QuestType
    quest_status: QuestStatus
    category_code: str
    category_name: str
    difficulty: Difficulty
    reward_point: Optional[int] = None
    reward_exp: Optional[int] = None
    location: Optional[str] = None
    estimated_duration: Optional[int] = None

    @classmethod
    def from_quest(cls, quest) -> "QuestSchema":
        category = quest.category
        return cls(
            quest_id=quest.quest_id,
            quest_title=quest.quest_title,
            quest_description=quest.quest_description,
            quest_type=quest.quest_type,
            quest_status=quest.quest_status,
            category_code=category.code if category else "other",
            category_name=category.name if category else "기타",
            difficulty=quest.difficulty,
            reward_point=quest.reward_point,
            reward_exp=quest.reward_exp,
            location=quest.location,
            estimated_duration=quest.estimated_duration,
        )
