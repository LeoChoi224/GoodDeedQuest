import logging
from typing import Dict, Any, List, Optional

from sqlalchemy.orm import Session
from backend.app.common.database import SessionLocal
from ai.app.common.vector_adapter import get_vector_store_adapter
from ai.app.common.embedding import get_embedding

from ai.app.quest_recommend.state import RecommendState
from backend.app.map.models import VolunteerCenter

logger = logging.getLogger(__name__)


# 봉사센터 전용 인메모리 임베딩 캐시 딕셔너리
_volunteer_embedding_cache: Dict[int, List[float]] = {}

def load_volunteer_centers_from_db(
    db: Session,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    radius_km: float = 3.0
) -> List[Dict[str, Any]]:
    """
    유저의 위도/경도(lat, lng) 좌표 기준 3km 반경 내 VolunteerCenter 레코드를 
    DB에서 1차 Geo-filtering하여 랭체인 Document 매핑용 딕셔너리 리스트로 반환합니다.
    """
    query = db.query(VolunteerCenter)

    # 1. 유저 좌표가 존재할 경우 3km 반경 위경도 델타(약 0.027도) 1차 Geo-filtering
    if lat is not None and lng is not None:
        delta = radius_km / 111.0  # 1도 약 111km 기준 (3km ≒ 0.027도)
        query = query.filter(
            VolunteerCenter.latitude.between(lat - delta, lat + delta),
            VolunteerCenter.longitude.between(lng - delta, lng + delta)
        )
        logger.info(f"유저 좌표 ({lat}, {lng}) 기준 {radius_km}km 반경 내 봉사 공고 1차 DB 쿼리 필터링 가동")

    centers = query.all()

    # 2. 3km 이내 봉사 공고가 0개일 경우 10km 반경 확장 또는 전체 공고 2차 Fallback 조회
    if not centers and lat is not None and lng is not None:
        logger.warning(f"3km 이내 봉사 공고 0건 감지. 10km 반경으로 2차 안전 Fallback 확장 조회를 수행합니다.")
        fallback_delta = 10.0 / 111.0
        centers = db.query(VolunteerCenter).filter(
            VolunteerCenter.latitude.between(lat - fallback_delta, lat + fallback_delta),
            VolunteerCenter.longitude.between(lng - fallback_delta, lng + fallback_delta)
        ).all()

    # 3. 10km 범위로도 없으면 전체 공고 조회
    if not centers:
        logger.warning("주변 반경 내 봉사 공고가 없어 DB 전체 봉사 레코드를 fallback으로 가져옵니다.")
        centers = db.query(VolunteerCenter).all()

    documents = []
    db_updated = False

    for center in centers:
        title = center.vol_title or center.vol_name or "봉사활동 공고"
        act_content = center.vol_act or "상세 봉사 내용 없음"
        full_content = f"{title}\n{act_content}"

        vector = None
        cid = center.center_id

        # Tier 1: 1단계 RAM 인메모리 딕셔너리 캐시 확인 (속도: 0.0001초, API 0회)
        if cid in _volunteer_embedding_cache:
            vector = _volunteer_embedding_cache[cid]
        
        # Tier 2: 2단계 DB 영구 저장 컬럼(center.embedding) 확인 (서버 재시작 후에도 API 0회)
        elif center.embedding and isinstance(center.embedding, dict) and "vector" in center.embedding:
            vector = center.embedding["vector"]
            _volunteer_embedding_cache[cid] = vector  # RAM 캐시에도 동시 복사하여 다회차 속도 최적화
        
        # Tier 3: RAM에도 없고 DB에도 없는 완전 신규 공고만 OpenAI API 1회 호출 후 RAM & DB 동시 영구 저장!
        else:
            logger.info(f"신규 봉사 공고(ID: {cid}) 임베딩 생성 중...")
            vector = get_embedding(full_content)
            
            # RAM 캐시에 저장
            _volunteer_embedding_cache[cid] = vector
            
            # DB VolunteerCenter.embedding 컬럼에 영구 적재
            center.embedding = {"vector": vector}
            db_updated = True

        documents.append({
            "id": cid,
            "title": title,
            "content": full_content,
            "category": center.ai_category or "VOLUNTEER",
            "location": center.vol_address or "장소 미지정",
            "url": center.vms_url or "https://www.vms.or.kr",
            "is_volunteer": True,
            "vector": vector
        })

    # 신규 임베딩이 생성된 경우 DB에 영구 커밋(db.commit())
    if db_updated:
        db.commit()
        logger.info("신규 봉사 공고 임베딩 벡터가 DB VolunteerCenter.embedding 컬럼에 영구 적재(commit) 되었습니다.")
        
    logger.info(f"유저 맞춤 봉사 공고 총 {len(documents)}건 DB에서 픽업 완료")
    return documents


def retrieve_volunteers(state: RecommendState) -> Dict[str, Any]:
    """
    유저의 실시간 좌표(latitude, longitude) 기준 3km 반경 내 봉사 공고를 
    2단계 듀얼 캐싱 기반으로 하이브리드 수색하는 노드 함수입니다.
    """
    recommendation_strategy = state.get("recommendation_strategy")
    user_profile = state.get("user_profile", {})
    search_query = recommendation_strategy["search_query"]

    # 쿼리가 비어 있는 경우 기본 검색어인 "volunteer"(봉사활동)로 대치하여 검색 오류 방어
    if not search_query or not search_query.strip():
        search_query = "volunteer"

    latitude = user_profile.get("latitude")
    longitude = user_profile.get("longitude")

    # 싱글톤 벡터 스토어 어댑터 획득
    adapter = get_vector_store_adapter()

    logger.info(f"유저 좌표(lat={latitude}, lng={longitude}) 기반 3km 맞춤 봉사 데이터를 DB에서 픽업합니다.")

    with SessionLocal() as db:
        vol_docs = load_volunteer_centers_from_db(db, lat=latitude, lng=longitude, radius_km=3.0)
        
        # 어댑터 인덱스를 3km 맞춤 공고로 새로 갱신
        adapter.clear()
        if vol_docs:
            adapter.add_documents(vol_docs)
        else:
            logger.warning("픽업된 맞춤 봉사 공고가 존재하지 않습니다.")

    # 1. 하이브리드 검색 (Top 5 추출)
    logger.info(f"검색 쿼리 '{search_query}'로 3km 맞춤 봉사 데이터 하이브리드 수색을 수행합니다.")
    results = adapter.hybrid_search(query=search_query, top_k=5)

    # 2. 1차 수색 결과가 0개일 경우, 관심 키워드로 2차 수색 (Fall-back Broad Search)
    if not results or len(results) == 0:
        interests = user_profile.get("interests", [])
        fallback_query = interests[0] if interests else "봉사"
        logger.warning(f"1차 봉사 수색 결과 0개 감지. 키워드 단순화 2차 수색 가동: '{fallback_query}'")
        results = adapter.hybrid_search(query=fallback_query, top_k=5)
        
    logger.info(f"실제 봉사 데이터 수색 최종 완료. 수집 개수: {len(results)}개")
    return {"retrieved_volunteers": results}


def route_validation_result(state: RecommendState) -> str:
    """
    Validation Agent의 검증 결과를 바탕으로 다음 목적지 노드를 결정하는 조건부 라우터 함수입니다.
    """
    retry_count = state.get("retry_count", 0)
    retrieved_volunteers = state.get("retrieved_volunteers", [])
    
    # 1. 1차 수색된 봉사 데이터가 0개이면 바로 수색 노드로 되돌아감
    if not retrieved_volunteers:
        logger.warning("[Router] 수집된 봉사 데이터 0개 감지 -> retrieval 노드로 재수색 루프 실행")
        return "retrieval"
    
    # 2. 루프 횟수 가드 (최대 3회: 0, 1, 2)
    if retry_count >= 2:
        logger.warning(f"[Router] 최대 재시도 횟수 초과(retry_count={retry_count}) -> response 노드로 강제 이동")
        return "response"
    
    # 3. Validation Agent의 검증 판단 결과 분기
    candidate_quests = state.get("candidate_quests", [])
    if len(candidate_quests) >= 5:
        logger.info(f"[Router] 검증 승인 (후보군 {len(candidate_quests)}개 충족) -> response 노드로 이동")
        return "response"
    else:
        logger.info(f"[Router] 검증 실패 (후보군 {len(candidate_quests)}개 부족) -> planner 노드로 재루프 수립")
        return "planner"


    