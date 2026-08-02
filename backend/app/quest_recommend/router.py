import logging
from typing import Final, List, Optional

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.common.auth import get_current_user
from backend.app.common.config import get_setting
from backend.app.common.database import get_db
from backend.app.common.response import APIResponse
from backend.app.quest.schemas import QuestSchema
from backend.app.quest_recommend.schemas import BackendQuestRecommendRequest
from backend.app.quest_recommend.service import (
    save_recommendation_log,
    save_recommendation_items,
    get_completed_quest_titles,
    get_recent_recommended_titles,
    get_user_coordinates,
    get_today_recommendation,
    build_quests_from_recommendations,
)


logger: Final = logging.getLogger(__name__)

router = APIRouter(prefix="/quest-recommend", tags=["Quest AI Recommendation & Coach"])

@router.get("/today", response_model=APIResponse[Optional[List[QuestSchema]]])
def get_today_recommended_quests(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    오늘 이미 생성된 추천 퀘스트 목록을 조회합니다.
    아직 생성된 적이 없으면 data에 null을 담아 반환하며, 이는 오류가 아니라 신규 생성이 필요하다는 신호입니다.
    """
    user_id = user["id"]
    quests = get_today_recommendation(db=db, user_id=user_id)

    if quests is None:
        logger.info(f"오늘 생성된 추천이 없습니다. User ID: {user_id}")
        return APIResponse.ok(data=None, message="오늘 생성된 추천이 없습니다.")

    logger.info(f"오늘의 추천 퀘스트 반환. User ID: {user_id}, 건수: {len(quests)}")
    return APIResponse.ok(
        data=[QuestSchema.from_quest(quest) for quest in quests],
        message="오늘의 추천 퀘스트 조회 성공"
    )


@router.post("")
async def recommend_quests(
    req: BackendQuestRecommendRequest, 
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    사용자의 관심사와 위치 정보를 바탕으로 AI 모델 서버(Port 8001)에 비동기 추천을 요청하고,
    수신된 결과와 퀘스트 데이터를 DB(AiRecommendationLog, AiRecommendation, Quest)에 영속화한 후 최종 반환합니다.
    """
    user_id = user["id"]
    logger.info(f"메인 백엔드 퀘스트 추천 및 DB 영속화 요청 수신. User ID: {user_id}")

    # 기본 관심 분야 설정 (영문 규격 준수)
    user_interests = req.interests if req.interests else ["VULNERABLE_GROUP", "ENVIRONMENT"]

    # 요청에 좌표가 없으면 User 테이블 저장 좌표로 폴백 
    latitude = req.latitude
    longitude = req.longitude
    if latitude is None or longitude is None:
        fallback_lat, fallback_lng = get_user_coordinates(db=db, user_id=user_id)
        latitude = latitude if latitude is not None else fallback_lat
        longitude = longitude if longitude is not None else fallback_lng
        logger.info(f"요청 좌표 누락으로 User 테이블 저장 좌표를 사용합니다. User ID: {user_id}")

    # 요청 당시 수집된 Context 데이터 구성
    request_context = {
        "interests": user_interests,
        "latitude": latitude,
        "longitude": longitude,
        "level": user.get("level", 1),
        "request_message": req.request_message
    }

    history_quests = get_completed_quest_titles(db=db, user_id=user_id)
    recent_recommendations = get_recent_recommended_titles(db=db, user_id=user_id)

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            ai_service_url = f"{get_setting().AI_SERVICE_URL}/ai/recommend"
            payload = {
                "user_id": user_id,
                **request_context,
                "history_quests": history_quests,
                "recent_recommendations": recent_recommendations,
            }
            
            response = await client.post(ai_service_url, json=payload)
            
            if response.status_code == 200:
                ai_result = response.json()
                recommended_quests = ai_result.get("data", [])
                logger.info(f"AI 모델 서버 통신 성공. User ID: {user_id}")
                
                # 1. 부모 로그 DB 적재
                ai_log_id = save_recommendation_log(
                    db=db,
                    user_id=user_id,
                    request_context=request_context,
                    response_context=ai_result
                )
                
                # 2. 추천 5개 항목 및 Quest 원본 DB 영속화 연동
                saved_items = []
                if ai_log_id and recommended_quests:
                    saved_items = save_recommendation_items(
                        db=db,
                        ai_log_id=ai_log_id,
                        user_id=user_id,
                        recommended_quests=recommended_quests
                    )

                # 3. AI 서버 응답 원본에는 quest_id가 항상 null이라 프론트가 상세 화면으로 이동할 수 없다.
                # 영속화 과정에서 생성된 quest_id를 담아 GET /today와 동일한 형태로 반환한다.
                persisted_quests = build_quests_from_recommendations(db=db, items=saved_items)

                # 4. 저장 실패 시 AI 원본을 그대로 주면 프론트가 깨지므로 실패로 처리한다
                if not persisted_quests:
                    logger.warning(f"추천 결과 DB 영속화에 실패했습니다. User ID: {user_id}")
                    return APIResponse.fail(
                        message="추천 결과를 저장하지 못했습니다. 잠시 후 다시 시도해 주세요.",
                        data=[]
                    )

                return APIResponse.ok(
                    data=[QuestSchema.from_quest(quest) for quest in persisted_quests],
                    message="AI 맞춤 퀘스트 추천 성공"
                )
            else:
                logger.warning(f"AI 모델 서버 응답 이상 (HTTP Status: {response.status_code}). User ID: {user_id}")
                return APIResponse.fail(message="AI 모델 서버 응답에 실패했습니다.")
    except Exception as e:
        logger.error(f"AI 모델 서버 통신 중 예외 발생. User ID: {user_id}, 사유: {str(e)}")

    return APIResponse.fail(message="AI 모델 서버 통신 장애로 인해 퀘스트 추천을 완료하지 못했습니다.")