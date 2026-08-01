import logging
from typing import Dict, Any, List, Optional, Final

from sqlalchemy.orm import Session
from backend.app.common.database import SessionLocal
from ai.app.common.vector_adapter import get_vector_store_adapter
from ai.app.common.embedding import get_embedding

from ai.app.quest_recommend.state import RecommendState
from backend.app.map.models import VolunteerCenter

logger: Final = logging.getLogger(__name__)


# 봉사센터 전용 인메모리 임베딩 캐시 딕셔너리
_volunteer_embedding_cache: Dict[int, List[float]] = {}

# DB 1회 조회 상한. 이 값보다 적게 조회되면 반경 내에 아직 안 본 공고가 없다는 뜻이므로 재수색을 종료한다
VOLUNTEER_FETCH_LIMIT: Final = 10


def load_volunteer_centers_from_db(
    db: Session,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    radius_km: float = 3.0,
    exclude_ids: Optional[List[int]] = None
) -> List[Dict[str, Any]]:
    """
    유저의 위도/경도(lat, lng) 좌표 기준 3km 반경(1차) 및 6km 반경(2차) 내
    VolunteerCenter 레코드를 최대 VOLUNTEER_FETCH_LIMIT건까지만 DB에서 Geo-filtering하여 반환합니다.
    재시도(Retry) 시 이미 조회했던 공고(exclude_ids)는 notin_ 조건으로 제외하여 중복 픽업을 차단합니다.
    """
    global _volunteer_embedding_cache

    # 사용자의 위치 정보가 없을 경우 DB 조회를 하지 않고 즉시 빈 리스트 반환
    if lat is None or lng is None:
        return []

    query = db.query(VolunteerCenter)

    # 이미 조회했던 center_id 제외 조건 추가
    if exclude_ids:
        query = query.filter(VolunteerCenter.center_id.notin_(exclude_ids))

    # 1. 1차 수색: 3km 반경 위경도 델타(약 0.027도) 및 limit 적용
    delta_3km = radius_km / 111.0
    centers = query.filter(
        VolunteerCenter.latitude.between(lat - delta_3km, lat + delta_3km),
        VolunteerCenter.longitude.between(lng - delta_3km, lng + delta_3km)
    ).limit(VOLUNTEER_FETCH_LIMIT).all()

    # 2. 2차 수색: 3km 내 0건 발생 시 6km 반경(약 0.054도)으로 확장 (제외 조건 유지)
    if not centers:
        logger.info("3km 이내 봉사 공고 0건 감지 -> 6km 반경으로 2차 수색을 진행합니다.")
        delta_6km = 6.0 / 111.0
        fallback_query = db.query(VolunteerCenter)
        if exclude_ids:
            fallback_query = fallback_query.filter(VolunteerCenter.center_id.notin_(exclude_ids))

        centers = fallback_query.filter(
            VolunteerCenter.latitude.between(lat - delta_6km, lat + delta_6km),
            VolunteerCenter.longitude.between(lng - delta_6km, lng + delta_6km)
        ).limit(VOLUNTEER_FETCH_LIMIT).all()

    # 3. 6km 이내에도 없으면 빈 리스트 반환
    if not centers:
        return []

    documents = []
    db_updated = False

    # 2단계 듀얼 캐싱 (RAM 메모리 -> DB 저장소 -> OpenAI API 호출은 회당 최대 VOLUNTEER_FETCH_LIMIT회)
    for center in centers:
        title = center.vol_title or center.vol_name or "봉사활동 공고"
        act_content = center.vol_act or "상세 봉사 내용 없음"
        full_content = f"{title}\n{act_content}"

        vector = None
        cid = center.center_id

        # Tier 1: RAM 인메모리 딕셔너리 캐시
        if cid in _volunteer_embedding_cache:
            vector = _volunteer_embedding_cache[cid]

        # Tier 2: DB VolunteerCenter.embedding 영구 저장 컬럼
        elif center.embedding and isinstance(center.embedding, dict) and "vector" in center.embedding:
            vector = center.embedding["vector"]
            _volunteer_embedding_cache[cid] = vector

        # Tier 3: 신규 공고만 OpenAI API 1회 호출 후 RAM & DB 동시 적재
        else:
            logger.info(f"신규 봉사 공고(ID: {cid}) 임베딩 생성 중...")
            vector = get_embedding(full_content)
            _volunteer_embedding_cache[cid] = vector
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

    if db_updated:
        db.commit()

    logger.info(
        f"유저 맞춤 3km/6km 이내 봉사 공고 총 {len(documents)}건 DB 픽업 완료 "
        f"(제외 목록 수: {len(exclude_ids) if exclude_ids else 0}개)"
    )
    return documents



def retrieve_volunteers(state: RecommendState) -> Dict[str, Any]:
    """
    유저의 실시간 좌표 기준 3km/6km 이내 봉사 데이터를 수색하는 노드 함수입니다.
    재시도 시 이전 회차까지 조회했던 공고(searched_volunteer_ids)를 모두 제외하고 새 공고만 가져오며,
    더 가져올 공고가 없다고 판단되면 skip_volunteer_agent를 True로 반환하여
    이후 루프에서 같은 수색이 반복되지 않도록 차단합니다.
    """
    recommendation_strategy = state.get("recommendation_strategy", {})
    user_profile = state.get("user_profile", {})

    search_query = (recommendation_strategy.get("search_query") or "").strip() or "volunteer"

    latitude = user_profile.get("latitude")
    longitude = user_profile.get("longitude")

    searched_ids: List[int] = list(state.get("searched_volunteer_ids", []))

    adapter = get_vector_store_adapter()

    # 1. 누적 제외 목록을 뺀 3km/6km 이내 신규 공고만 DB에서 픽업
    with SessionLocal() as db:
        vol_docs = load_volunteer_centers_from_db(
            db, lat=latitude, lng=longitude, radius_km=3.0, exclude_ids=searched_ids
        )

        adapter.clear()
        if vol_docs:
            adapter.add_documents(vol_docs)

    # 2. 이번 회차에 픽업한 공고를 누적 목록에 반영
    searched_ids.extend(doc["id"] for doc in vol_docs)

    # 3. 신규 공고가 없으면(사용자 위치 미조회 포함) 재수색을 종료
    if not vol_docs:
        logger.info("6km 이내에 새로 조회할 봉사 공고가 없거나 사용자의 현재 위치가 확인되지 않습니다.")
        return {
            "retrieved_volunteers": [],
            "searched_volunteer_ids": searched_ids,
            "skip_volunteer_agent": True
        }

    # 4. 하이브리드 수색 (Top 5). 1차 결과가 없으면 관심사 키워드로 2차 수색
    logger.info(f"검색 쿼리 '{search_query}'로 3km/6km 맞춤 봉사 데이터 하이브리드 수색 수행")
    results = adapter.hybrid_search(query=search_query, top_k=5)

    if not results:
        interests = user_profile.get("interests", [])
        fallback_query = interests[0] if interests else "봉사"
        logger.info(f"1차 수색 결과 0건. 관심사 키워드 '{fallback_query}'로 2차 수색을 수행합니다.")
        results = adapter.hybrid_search(query=fallback_query, top_k=5)

    # 5. 공고는 있으나 수색 결과가 끝내 0건이면, 같은 조건의 재수색은 결과가 동일하므로 종료
    if not results:
        logger.warning("봉사 공고는 존재하나 하이브리드 수색 결과가 0건입니다. 재수색을 종료합니다.")
        return {
            "retrieved_volunteers": [],
            "searched_volunteer_ids": searched_ids,
            "skip_volunteer_agent": True
        }

    # 6. 조회량이 상한에 못 미치면 반경 내 공고를 모두 소진한 것이므로 다음 회차부터 재수색 생략
    is_exhausted = len(vol_docs) < VOLUNTEER_FETCH_LIMIT
    if is_exhausted:
        logger.info(
            f"반경 내 신규 봉사 공고 {len(vol_docs)}건을 모두 조회했습니다"
            f"(상한 {VOLUNTEER_FETCH_LIMIT}건 미만). 이후 재수색을 생략합니다."
        )

    logger.info(f"실제 봉사 데이터 수색 완료. 최종 후보 {len(results)}건")
    return {
        "retrieved_volunteers": results,
        "searched_volunteer_ids": searched_ids,
        "skip_volunteer_agent": is_exhausted
    }


