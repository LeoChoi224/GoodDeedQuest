import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.app.quest_recommend.models import AiRecommendationLog

logger = logging.getLogger(__name__)

def save_recommendation_log(
    db: Session,
    user_id: int, 
    request_context: Dict[str, Any], 
    response_context: Dict[str, Any]
) -> Optional[int]:
    """
    AI 퀘스트 추천 시 수집된 요청 상황(request_context)과 
    최종 5개 추천 결과(response_context)를 AiRecommendationLog DB 테이블에 적재합니다.
    """
    logger.info(f"AI 추천 요청/응답 로그 DB 적재 시작. User ID: {user_id}")
    
    try:
        log_entry = AiRecommendationLog(
            user_id=user_id,
            request_context=request_context,
            response_context=response_context
        )
        db.add(log_entry)
        db.flush()  # 자동 생성되는 PK(ai_log_id) 획득을 위해 flush 수행
        
        logger.info(f"AI 추천 로그 DB 등록 완료. User ID: {user_id}, Generated Log ID: {log_entry.ai_log_id}")
        return log_entry.ai_log_id
            
    except Exception as e:
        logger.error(f"AI 추천 로그 DB 등록 중 예외 발생. User ID: {user_id}, 에러: {str(e)}")
        return None