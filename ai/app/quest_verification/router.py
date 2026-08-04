import logging

from fastapi import APIRouter

from ai.app.quest_verification.schemas import VerifyQuestRequest, VerifyChallengeRequest
from ai.app.quest_verification.graph import run_verification_flow
from ai.app.quest_verification.challenge import verify_challenge

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Quest Verification"])


@router.post("/verify-quest")
def ai_verify_quest(req: VerifyQuestRequest):
    """제출된 동영상(또는 봉사활동 확인서)이 퀘스트 수행 증거로 적합한지 판정합니다."""
    logger.info(f"인증 판정 요청. 퀘스트 ID: {req.quest_id}, 동영상 여부: {req.is_video}")
    result = run_verification_flow(
        quest_id=req.quest_id,
        quest_title=req.quest_title,
        quest_description=req.quest_description,
        media_urls=req.media_urls,
        is_video=req.is_video,
    )
    return {"success": True, "data": result}


@router.post("/verify-challenge")
def ai_verify_challenge(req: VerifyChallengeRequest):
    """진위가 의심스러울 때 발급한 코드를 손으로 적어 올렸는지 확인합니다."""
    result = verify_challenge(media_url=req.media_url, code=req.code)
    return {"success": True, "data": result}
