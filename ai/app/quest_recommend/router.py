import logging
from fastapi import APIRouter, HTTPException, status

from ai.app.quest_recommend.schemas import QuestRecommendRequest, QuestRecommendResponse
from ai.app.quest_recommend.graph import run_recommendation_flow

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai/recommend", tags=["AI Quest Recommendation"])

@router.post("", response_model=QuestRecommendResponse)
async def recommend_quests(req: QuestRecommendRequest) -> QuestRecommendResponse:
    """
    LangGraph 추천 워크플로우를 실행하여 사용자 맞춤형 5개 퀘스트를 반환합니다.
    """
    logger.info(f"AI 퀘스트 추천 요청 수신. 사용자 ID: {req.user_id}")

    try:
        # Pydantic 객체를 RecommendState 딕셔너리로 직렬화
        initial_state = req.model_dump()

        # LangGraph 8개 노드 워크플로우 실행
        final_state = run_recommendation_flow(initial_state)

        recommended_quests = final_state.get("recommended_quests", [])
        logger.info(f"AI 퀘스트 추천 워크플로우 정상 완료. 사용자 ID: {req.user_id}, 퀘스트 수: {len(recommended_quests)}")
        
        return QuestRecommendResponse(
            success=True,
            message="추천 퀘스트 생성이 완료되었습니다.",
            data=recommended_quests
        )
    
    except Exception as e:
        logger.error(f"AI 퀘스트 추천 연산 중 예외 발생. 사용자 ID: {req.user_id}, 에러: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI 퀘스트 추천 처리 중 내부 오류가 발생했습니다."
        )

