import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List, Final

from sqlalchemy.orm import Session

from backend.app.auth.models import User
from backend.app.common.enums import Difficulty
from backend.app.quest_recommend.models import AiRecommendationLog, AiRecommendation
from backend.app.quest.models import Quest, Category
from backend.app.quest.enums import QuestTarget, QuestType, QuestSource, QuestStatus
from backend.app.quest.rewards import reward_from_intensity
from backend.app.quest.service import completed_quest_ids, started_quest_ids


logger: Final = logging.getLogger(__name__)

# created_at은 DB 서버 시계(UTC)로 저장되는데 사용자가 느끼는 '오늘'은 한국 시간이다
KST: Final = timezone(timedelta(hours=9))

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
        # flush 실패 시 세션이 롤백 대기 상태가 되어 get_db()의 commit에서 다시 터진다
        db.rollback()
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
            center_id_val = item.get("center_id")


            # 1. 실제 봉사(VOLUNTEER), 일상 선행(GOOD_DEED) 판별 로직
            # quest_type이 VOLUNTEER이거나 장소 주소(location)가 존재하면 무조건 실제 봉사(VOLUNTEER)로 처리
            if raw_type == "VOLUNTEER":
                mapped_quest_type = QuestType.VOLUNTEER
                quest_type_str = "VOLUNTEER"
                target_cat_name = "VOLUNTEER"  # 카테고리 무조건 'VOLUNTEER'(봉사) 강제 부여

                # 타입은 VOLUNTEER인데 원본 공고 연결이 없는 경우는 데이터 이상이다.
                # 저장은 진행하되(추천 자체는 유효), 버튼이 동작하지 않으므로 로그로 남긴다.
                if not center_id_val:
                    logger.warning(
                        f"VOLUNTEER 퀘스트에 center_id가 없습니다. "
                        f"'봉사활동 상세' 이동 버튼이 동작하지 않습니다. 제목: {item.get('quest_title')}"
                    )
            else:
                mapped_quest_type = QuestType.GOOD_DEED
                quest_type_str = "GOOD_DEED"
                target_cat_name = item.get("category_name", "OTHER")

            # 2. DB category 테이블에서 카테고리 객체 조회
            category_obj = db.query(Category).filter_by(name=target_cat_name).first()
            if not category_obj:
                category_obj = db.query(Category).first()
            category_id = category_obj.category_id if category_obj else 1

            # 3. AI가 준 난이도 문자열을 enum으로 변환 (알 수 없는 값이면 NORMAL로 폴백)
            #    변환에 실패해 예외가 나면 이 함수 전체가 롤백되어 추천 5개가 통째로 날아간다
            raw_difficulty = item.get("difficulty") or "NORMAL"
            try:
                mapped_difficulty = Difficulty(raw_difficulty)
            except ValueError:
                logger.warning(f"알 수 없는 난이도 값으로 NORMAL을 적용합니다. 값: {raw_difficulty}")
                mapped_difficulty = Difficulty.NORMAL

            # 4. 난이도 구간 안에서 intensity 위치에 해당하는 포인트/경험치를 산정
            #    intensity=0은 '해당 난이도의 최소'라는 유효한 값이므로 or 연산으로 기본값을 주면 안 된다
            raw_intensity = item.get("intensity")
            intensity = 50 if raw_intensity is None else raw_intensity
            reward_point, reward_exp = reward_from_intensity(mapped_difficulty, intensity)

            target_quest_id = item.get("quest_id")

            # 5. Quest 메인 원본 테이블 레코드 생성 (VOLUNTEER/GOOD_DEED 모두 quest_id 획득)
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
                    volunteer_center_id=center_id_val if mapped_quest_type == QuestType.VOLUNTEER else None,
                    difficulty=mapped_difficulty,
                    reward_point=reward_point,
                    reward_exp=reward_exp,
                    estimated_duration=item.get("estimated_duration", 15),
                    quest_status=QuestStatus.NOT_STARTED
                )
                db.add(new_quest)
                db.flush()  # 신규 생성된 quest_id 획득
                target_quest_id = new_quest.quest_id

            # 6. 추천 1:N 자식 테이블(AiRecommendation) 적재
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
        # 위와 동일. 예외를 삼키고 넘어가려면 세션도 함께 정리해야 한다
        db.rollback()
        logger.error(f"추천 퀘스트 항목 DB 영속화 중 예외 발생. Log ID: {ai_log_id}, 에러: {str(e)}")
        return []


def get_completed_quest_titles(db: Session, user_id: int, limit: int = 20) -> List[str]:
    """
    사용자가 완료한 퀘스트 제목 목록을 조회합니다.
    AI 추천 시 completed_history로 전달되어 선호 활동 강화 추천에 사용됩니다.
    """
    try:
        rows = (
            db.query(Quest.quest_title)
            .filter(
                Quest.creator_id == user_id,
                Quest.quest_status == QuestStatus.COMPLETED
            )
            .order_by(Quest.quest_id.desc())
            .limit(limit)
            .all()
        )
        return [row[0] for row in rows if row[0]]
    except Exception as e:
        logger.warning(f"완료 퀘스트 이력 조회 실패. User ID: {user_id}, 사유: {str(e)}")
        return []


def get_recent_recommended_titles(db: Session, user_id: int, limit: int = 10) -> List[str]:
    """
    사용자에게 최근 추천되었던 퀘스트 제목 목록을 조회합니다.
    AI 추천 시 exclusions(제외 목록)로 전달되어 동일 퀘스트 중복 추천을 차단합니다.
    """
    try:
        rows = (
            db.query(AiRecommendation.title)
            .join(
                AiRecommendationLog,
                AiRecommendation.ai_log_id == AiRecommendationLog.ai_log_id
            )
            .filter(AiRecommendationLog.user_id == user_id)
            .order_by(AiRecommendation.ai_rec_id.desc())
            .limit(limit)
            .all()
        )
        return [row[0] for row in rows if row[0]]
    except Exception as e:
        logger.warning(f"최근 추천 이력 조회 실패. User ID: {user_id}, 사유: {str(e)}")
        return []


def get_user_coordinates(db: Session, user_id: int) -> tuple:
    """
    User 테이블에 저장된 사용자의 마지막 위치 좌표를 조회합니다.
    프론트엔드가 실시간 좌표를 보내지 못한 경우의 폴백 값으로 사용됩니다.
    """
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            return None, None

        # DB 컬럼이 Numeric 타입이라 Decimal로 반환되므로 JSON 직렬화를 위해 float으로 변환
        lat = float(user.current_latitude) if user.current_latitude is not None else None
        lng = float(user.current_longitude) if user.current_longitude is not None else None
        return lat, lng
    except Exception as e:
        logger.warning(f"사용자 좌표 조회 실패. User ID: {user_id}, 사유: {str(e)}")
        return None, None


def build_quests_from_recommendations(db: Session, items: List[AiRecommendation]) -> List[Quest]:
    """
    추천 항목(AiRecommendation)에 연결된 Quest 원본을 추천 순위 그대로 조회하는 헬퍼 함수입니다.
    오늘의 추천 조회(GET)와 신규 추천 생성(POST)이 동일한 응답 형태를 반환하도록 두 곳에서 함께 사용합니다.
    """
    # 1. quest_id는 ondelete="SET NULL"이라 원본 퀘스트가 지워지면 비어 있을 수 있어 걸러낸다
    quest_ids = [item.quest_id for item in items if item.quest_id is not None]
    if not quest_ids:
        return []

    # 2. 항목마다 조회하면 5회 왕복하므로 IN 절로 한 번에 가져온다
    rows = (
        db.query(Quest)
        .filter(
            Quest.quest_id.in_(quest_ids),
            Quest.is_deleted == False,
        )
        .all()
    )

    # 3. IN 절 조회는 순서를 보장하지 않아 1순위가 3번째에 나올 수 있으므로 순위대로 다시 정렬한다
    quest_map = {row.quest_id: row for row in rows}
    return [quest_map[quest_id] for quest_id in quest_ids if quest_id in quest_map]


def get_today_recommendation(db: Session, user_id: int) -> Optional[List[Quest]]:
    """
    오늘 생성된 추천 결과를 조회합니다. LLM은 호출하지 않고 DB 조회만 수행합니다.
    홈 화면 진입 시 사용되며, 오늘 생성된 결과가 없으면 None을 반환하여 프론트가 신규 생성을 요청하도록 합니다.
    """
    try:
        # 1. 가장 최근 로그 1건 조회 (created_at은 초 단위라 동시 생성 시 순서가 흔들리므로 PK 기준 정렬)
        latest_log = (
            db.query(AiRecommendationLog)
            .filter(AiRecommendationLog.user_id == user_id)
            .order_by(AiRecommendationLog.ai_log_id.desc())
            .first()
        )
        if not latest_log:
            logger.info(f"추천 이력이 없는 사용자입니다. User ID: {user_id}")
            return None

        # 2. 오늘(한국 시간 기준) 생성된 로그인지 판정 (어제 것이면 새로 만들어야 한다)
        start_kst = datetime.now(KST).replace(hour=0, minute=0, second=0, microsecond=0)
        start_utc = start_kst.astimezone(timezone.utc).replace(tzinfo=None)
        if not latest_log.created_at or latest_log.created_at < start_utc:
            logger.info(f"마지막 추천이 오늘 생성된 것이 아닙니다. User ID: {user_id}")
            return None

        # 3. 딸린 추천 항목을 순위대로 조회 (rank는 nullable이라 ai_rec_id를 2차 정렬 키로 고정)
        items = (
            db.query(AiRecommendation)
            .filter(AiRecommendation.ai_log_id == latest_log.ai_log_id)
            .order_by(
                AiRecommendation.rank.asc(),
                AiRecommendation.ai_rec_id.asc(),
            )
            .all()
        )

        # 4. Quest 원본 조회 및 순위 정렬
        quests = build_quests_from_recommendations(db=db, items=items)

        # 5. 이미 시작했거나 완료한 퀘스트는 추천 목록에서 뺀다.
        #    진행중인 것은 홈 상단 캐러셀에 이미 있어 아래 목록에 또 두면 중복이고,
        #    완료한 것은 다시 추천할 이유가 없다 (전체 목록 조회와 같은 기준).
        excluded_ids = (
            completed_quest_ids(db, user_id) | started_quest_ids(db, user_id)
        )
        if excluded_ids:
            before_count = len(quests)
            quests = [quest for quest in quests if quest.quest_id not in excluded_ids]
            if before_count != len(quests):
                logger.info(
                    f"진행중/완료 퀘스트를 추천 목록에서 제외했습니다. "
                    f"User ID: {user_id}, {before_count}건 -> {len(quests)}건"
                )

        # 6. 오늘 로그는 있으나 퀘스트가 전부 사라진 경우(AI 빈 응답 / 전량 삭제)
        #    빈 목록 대신 None을 반환해야 프론트가 새로 생성한다
        if not quests:
            logger.warning(f"오늘 추천 로그는 있으나 표시할 퀘스트가 없습니다. User ID: {user_id}")
            return None

        logger.info(f"오늘의 추천 퀘스트 조회 완료. User ID: {user_id}, 건수: {len(quests)}")
        return quests

    except Exception as e:
        logger.warning(f"오늘의 추천 조회 실패. User ID: {user_id}, 사유: {str(e)}")
        return None


    