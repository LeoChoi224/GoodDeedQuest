from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated, List
from datetime import datetime, timedelta, timezone
import httpx
from backend.app.common.response import APIResponse
from backend.app.common.auth import get_current_user
from backend.app.common.config import get_setting
from backend.app.common.deps import get_repository
from backend.app.common.enums import Difficulty
from backend.app.common.repository import DatabaseRepository
from backend.app.quest.models import Quest, Category
from backend.app.quest.enums import QuestType, QuestSource
from backend.app.quest.rewards import reward_from_intensity
from backend.app.quest.schemas import QuestSchema, CreateQuestRequest, CreateQuestResponse
from backend.app.auth.router import get_current_db_user
from backend.app.auth.models import User

# 하루에 만들 수 있는 커스텀 퀘스트 수.
# 같은 활동을 여러 개 만드는 것 자체는 막지 않는다. 인증 단계에서 사진·영상
# 재사용이 걸러지므로, 여기서는 생성 횟수 상한만 둔다.
DAILY_CREATE_LIMIT = 5

# created_at은 UTC로 저장되는데 사용자가 느끼는 '오늘'은 한국 시간이다.
KST = timezone(timedelta(hours=9))

QuestRepository = Annotated[
    DatabaseRepository[Quest],
    Depends(get_repository(Quest))
]

CategoryRepository = Annotated[
    DatabaseRepository[Category],
    Depends(get_repository(Category))
]

router = APIRouter(prefix="/quests", tags=["Quests"])


def _evaluate(quest_title: str, quest_description: str, category_name: str) -> dict:
    """AI 서버에 심사를 맡긴다. 선행 여부와 난이도만 돌려받는다."""
    try:
        response = httpx.post(
            f"{get_setting().AI_SERVICE_URL}/ai/quest-create/evaluate",
            json={
                "quest_title": quest_title,
                "quest_description": quest_description,
                "category_name": category_name,
            },
            timeout=60.0,
        )
        response.raise_for_status()
        return response.json()["data"]
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="AI 심사 서버 호출에 실패했습니다.")


def _judge(req: CreateQuestRequest, category: Category) -> tuple[CreateQuestResponse, dict]:
    """심사 한 번. 미리보기와 등록이 같은 판단을 쓰도록 여기로 모았다.

    돌려주는 dict에는 저장에 필요한 재료(난이도·보상·임베딩)가 들어 있다.
    """
    result = _evaluate(req.quest_title, req.quest_description, category.name)

    if not result.get("accepted"):
        return CreateQuestResponse(accepted=False, reason=result.get("reason", "")), {}

    # 임베딩은 막는 데 쓰지 않고, 나중에 유사 퀘스트 추천 등에 쓰도록 저장만 해둔다.
    embedding = result.get("embedding")

    difficulty = Difficulty(result["difficulty"])
    point, exp = reward_from_intensity(difficulty, result["intensity"])

    response = CreateQuestResponse(
        accepted=True,
        reason=result.get("reason", ""),
        difficulty=difficulty,
        reward_point=point,
        reward_exp=exp,
    )
    return response, {"difficulty": difficulty, "point": point, "exp": exp,
                      "embedding": embedding}


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


def _load_category(category_repository: CategoryRepository, code: str) -> Category:
    category = category_repository.get_by(code=code)
    if category is None:
        raise HTTPException(status_code=400, detail="알 수 없는 카테고리입니다.")
    return category


def _created_today(quest_repository: QuestRepository, user_id: int) -> int:
    """오늘(한국 시간 기준) 내가 만든 커스텀 퀘스트 수."""
    start_kst = datetime.now(KST).replace(hour=0, minute=0, second=0, microsecond=0)
    # created_at은 시간대 정보 없는 UTC로 저장되므로 같은 형태로 맞춰 비교한다
    start_utc = start_kst.astimezone(timezone.utc).replace(tzinfo=None)
    return len(quest_repository.filter(
        Quest.creator_id == user_id,
        Quest.quest_source == QuestSource.USER,
        Quest.created_at >= start_utc,
    ))


@router.post("/preview", response_model=APIResponse[CreateQuestResponse])
def preview_quest(
    req: CreateQuestRequest,
    category_repository: CategoryRepository,
    current_user: User = Depends(get_current_db_user),
):
    """등록하기 전에 심사 결과만 미리 본다. 저장하지 않는다."""
    category = _load_category(category_repository, req.category_code)
    response, _ = _judge(req, category)
    return APIResponse.ok(data=response)


@router.post("", response_model=APIResponse[CreateQuestResponse])
def create_quest(
    req: CreateQuestRequest,
    quest_repository: QuestRepository,
    category_repository: CategoryRepository,
    current_user: User = Depends(get_current_db_user),
):
    """커스텀 퀘스트를 등록한다. 보상은 미리보기 값이 아니라 여기서 다시 판정한다."""
    category = _load_category(category_repository, req.category_code)

    # AI를 부르기 전에 횟수부터 확인한다 (막힐 요청에 비용을 쓰지 않도록)
    made_today = _created_today(quest_repository, current_user.user_id)
    if made_today >= DAILY_CREATE_LIMIT:
        return APIResponse.ok(data=CreateQuestResponse(
            accepted=False,
            reason=f"퀘스트는 하루에 {DAILY_CREATE_LIMIT}개까지 만들 수 있어요. 내일 다시 시도해 주세요.",
        ))

    response, material = _judge(req, category)

    if not response.accepted:
        return APIResponse.ok(data=response)

    quest = quest_repository.create({
        "category_id": category.category_id,
        "creator_id": current_user.user_id,
        "quest_title": req.quest_title,
        "quest_description": req.quest_description,
        # 개인 선행이므로 GOOD_DEED. VOLUNTEER는 VMS 확인서가 필요해 유저가 만들 수 없다.
        "quest_type": QuestType.GOOD_DEED,
        "quest_source": QuestSource.USER,
        "difficulty": material["difficulty"],
        "reward_point": material["point"],
        "reward_exp": material["exp"],
        # 다음 중복 검사의 재료가 된다
        "quest_embedding": material["embedding"],
    })

    response.quest_id = quest.quest_id
    return APIResponse.ok(data=response)
