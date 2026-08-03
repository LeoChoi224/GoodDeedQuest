from pydantic import BaseModel, Field
from typing import Optional
from backend.app.quest.enums import QuestType, QuestStatus, QuestSource
from backend.app.common.enums import Difficulty


class CreateQuestRequest(BaseModel):
    """사용자가 직접 만드는 퀘스트. 보상은 서버가 정하므로 받지 않는다."""
    quest_title: str = Field(min_length=1, max_length=200)
    quest_description: str = Field(min_length=1, max_length=1000)
    category_code: str


class CreateQuestResponse(BaseModel):
    """심사 결과. 거절이면 reason만 채워지고 나머지는 비어 있다."""
    accepted: bool
    reason: str
    difficulty: Optional[Difficulty] = None
    reward_point: Optional[int] = None
    reward_exp: Optional[int] = None
    quest_id: Optional[int] = None


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
    volunteer_center_id: Optional[int] = None

    @classmethod
    def from_quest(cls, quest, viewer_id: Optional[int] = None,
                   started_ids: Optional[set] = None,
                   done_ids: Optional[set] = None) -> "QuestSchema":
        """viewer_id 를 주면 quest_status 를 그 사람 기준으로 계산한다.

        quest.quest_status 는 퀘스트당 하나뿐인 전역 컬럼이라, 한 사람이
        시작하면 모두에게 진행중으로 보인다. 목록은 만든 사람으로 거르지 않고
        전부 돌려주므로(quest/router.py) 남이 만든 커스텀 퀘스트까지 내
        진행중 목록에 뜬다. 그래서 보는 사람 기준으로 다시 계산한다.

        진행중으로 보는 것: 내가 만든 커스텀 퀘스트 · 내가 인증을 낸 적 있는 퀘스트.
        """
        category = quest.category
        status = quest.quest_status
        if viewer_id is not None:
            if done_ids and quest.quest_id in done_ids:
                # 【판단】 완료가 가장 강하다. 내가 만든 퀘스트를 내가 완료했으면
                #        진행중이 아니라 완료다. 컬럼(quest.quest_status)에 COMPLETED 를
                #        써넣으면 퀘스트당 값이 하나뿐이라 남에게도 완료로 보인다.
                status = QuestStatus.COMPLETED
            else:
                mine = (quest.quest_source is QuestSource.USER
                        and quest.creator_id == viewer_id)
                started = bool(started_ids) and quest.quest_id in started_ids
                status = QuestStatus.IN_PROGRESS if (mine or started) else QuestStatus.NOT_STARTED

        return cls(
            quest_id=quest.quest_id,
            quest_title=quest.quest_title,
            quest_description=quest.quest_description,
            quest_type=quest.quest_type,
            quest_status=status,
            category_code=category.code if category else "other",
            category_name=category.name if category else "기타",
            difficulty=quest.difficulty,
            reward_point=quest.reward_point,
            reward_exp=quest.reward_exp,
            location=quest.location,
            estimated_duration=quest.estimated_duration,
            volunteer_center_id=quest.volunteer_center_id,
        )

class DeleteQuestResponse(BaseModel):
    
    deleted: bool