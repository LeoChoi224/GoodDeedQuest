import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from backend.app.quest_recommend.models import AiRecommendationLog, AiRecommendation
from backend.app.quest.models import Quest, Category
from backend.app.quest.enums import QuestTarget, QuestType, QuestSource, QuestStatus
from backend.app.common.enums import Difficulty

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

def save_recommendation_items(
    db: Session,
    ai_log_id: int,
    user_id: int,
    recommended_quests: List[Dict[str, Any]]
) -> List[AiRecommendation]:
    """
    VolunteerCenter 기반 실제 봉사(VOLUNTEER)와 AI 일상 선행(GOOD_DEED) 퀘스트 데이터를 
    Quest 원본 및 AiRecommendation 테이블에 연쇄 영속화합니다.
    """
    logger.info(f"추천 퀘스트 항목 DB 영속화 시작. Log ID: {ai_log_id}, 항목 수: {len(recommended_quests)}")
    saved_items = []

    try:
        for rank, item in enumerate(recommended_quests, start=1):
            raw_type = item.get("quest_type")
            location_val = item.get("location")

            # 1. 실제 봉사(VOLUNTEER), 일상 선행(GOOD_DEED) 판별 로직
            # quest_type이 VOLUNTEER이거나 장소 주소(location)가 존재하면 무조건 실제 봉사(VOLUNTEER)로 처리
            if raw_type == "VOLUNTEER" or (location_val and location_val.strip()):
                mapped_quest_type = QuestType.VOLUNTEER
                quest_type_str = "VOLUNTEER"
                target_cat_name = "VOLUNTEER"  # 카테고리 무조건 'VOLUNTEER'(봉사) 강제 부여
            else:
                mapped_quest_type = QuestType.GOOD_DEED
                quest_type_str = "GOOD_DEED"
                target_cat_name = item.get("category_name", "OTHER")

            # 2. DB category 테이블에서 카테고리 객체 조회
            category_obj = db.query(Category).filter_by(name=target_cat_name).first()
            if not category_obj:
                category_obj = db.query(Category).first()
            category_id = category_obj.category_id if category_obj else 1

            target_quest_id = item.get("quest_id")

            # 3. Quest 메인 원본 테이블 레코드 생성 (VOLUNTEER/GOOD_DEED 모두 quest_id 획득)
            if not target_quest_id or not db.query(Quest).filter_by(quest_id=target_quest_id).first():
                new_quest = Quest(
                    category_id=category_id,
                    creator_id=user_id,
                    quest_title=item.get("quest_title", "추천 퀘스트"),
                    quest_description=item.get("quest_description", "선행을 실천해 보세요."),
                    quest_target=QuestTarget.SOLO,
                    quest_type=mapped_quest_type,
                    quest_source=QuestSource.AI,
                    location=location_val if mapped_quest_type == QuestType.VOLUNTEER else None,
                    difficulty=Difficulty.NORMAL,
                    estimated_duration=item.get("estimated_duration", 15),
                    quest_status=QuestStatus.NOT_STARTED
                )
                db.add(new_quest)
                db.flush()  # 신규 생성된 quest_id 획득
                target_quest_id = new_quest.quest_id

            # 4. 추천 1:N 자식 테이블(AiRecommendation) 적재
            rec_reason = item.get("recommendation_reason") or item.get("reason") or "AI 맞춤 추천"
            rec_entry = AiRecommendation(
                ai_log_id=ai_log_id,
                quest_id=target_quest_id,
                title=item.get("quest_title", "추천 퀘스트"),
                description=item.get("quest_description", ""),
                recommendation_type=quest_type_str,
                score=float(item.get("priority_score", 10)),
                reason=rec_reason,
                rank=rank
            )
            db.add(rec_entry)
            saved_items.append(rec_entry)

        db.flush()
        logger.info(f"추천 퀘스트 항목 및 Quest 원본 DB 영속화 완료. Log ID: {ai_log_id}, 적재 수: {len(saved_items)}")
        return saved_items

    except Exception as e:
        logger.error(f"추천 퀘스트 항목 DB 영속화 중 예외 발생. Log ID: {ai_log_id}, 에러: {str(e)}")
        return []