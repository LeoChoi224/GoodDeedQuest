import logging
import httpx
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session


from backend.app.common.database import get_db
from backend.app.common.response import APIResponse
from backend.app.common.auth import get_current_user
from backend.app.common.config import get_setting
from backend.app.quest_recommend.schemas import BackendQuestRecommendRequest
from backend.app.quest_recommend.service import save_recommendation_log


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/quest-recommend", tags=["Quest AI Recommendation & Coach"])

@router.post("")
async def recommend_quests(
    req: BackendQuestRecommendRequest,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    사용자의 관심사와 위치 정보를 바탕으로 AI 모델 서버(Port 8001)에 비동기 추천을 요청하고 결과를 반환합니다.
    """
    user_id = user["id"]
    logger.info(f"메인 백엔드 퀘스트 추천 요청 수신. User ID: {user_id}")

    # 기본 관심 분야 설정
    user_interests = req.interests or ["ENVIRONMENT", "SHARING"]

    # 요청 당시 수집된 Context 데이터 구성
    request_context = {
        "interests": user_interests,
        "latitude": req.latitude,
        "longitude": req.longitude,
        "level": user.get("level", 1),
        "request_message": req.request_message
    }

    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            ai_service_url = f"{get_setting().AI_SERVICE_URL}/ai/recommend"
            payload = {
                "user_id": user_id,
                **request_context
            }
            
            response = await client.post(ai_service_url, json=payload)
            
            if response.status_code == 200:
                ai_result = response.json()
                logger.info(f"AI 모델 서버 통신 성공. User ID: {user_id}")

                # get_db()에서 주입받은 단일 db 세션을 전달 (get_db 종료 시 자동 커밋됨)
                save_recommendation_log(
                    db=db,
                    user_id=user_id,
                    request_context=request_context,
                    response_context=ai_result
                )

                return APIResponse.ok(data=ai_result.get("data"), message="AI 맞춤 퀘스트 추천 성공")
            else:
                logger.warning(f"AI 모델 서버 응답 이상 (HTTP Status: {response.status_code}). User ID: {user_id}")
                return APIResponse.fail(message="AI 모델 서버 응답에 실패했습니다.")
    except Exception as e:
        logger.error(f"AI 모델 서버 통신 중 예외 발생. User ID: {user_id}, 사유: {str(e)}")

    return APIResponse.fail(message="AI 모델 서버 통신 장애로 인해 퀘스트 추천을 완료하지 못했습니다.")