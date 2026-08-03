import logging

from fastapi import APIRouter

from ai.app.quest_create.schemas import EvaluateQuestRequest, EvaluateQuestResponse, EmbedQuestRequest, EmbedQuestResponse
from ai.app.quest_create.graph import run_quest_evaluation
from ai.app.quest_create.similarity import embed_quest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai/quest-create", tags=["AI Custom Quest"])


@router.post("/evaluate", response_model=dict)
def ai_evaluate_quest(req: EvaluateQuestRequest):
    """사용자가 만든 퀘스트가 선행으로 인정되는지 판정하고 난이도를 매긴다."""
    logger.info(f"커스텀 퀘스트 심사 요청: {req.quest_title}")
    result = run_quest_evaluation(
        quest_title=req.quest_title,
        quest_description=req.quest_description,
        category_name=req.category_name,
    )
    return {"success": True, "data": EvaluateQuestResponse(**result).model_dump()}

@router.post('/embed', response_model=dict)
def ai_embed_quest(req: EmbedQuestRequest):
    vector = embed_quest(req.quest_title, req.quest_description, req.category_name)
    return {"success": True, "data": EmbedQuestResponse(embedding=vector).model_dump()}
