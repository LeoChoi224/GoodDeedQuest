from typing import Dict, Any, List
import logging

from ai.app.quest_recommend.state import RecommendState
from ai.app.common.vector_adapter import get_vector_store_adapter, get_dummy_volunteer_data

logger = logging.getLogger(__name__)

def retrieve_volunteers(state: RecommendState) -> Dict[str, Any]:
    """
    플래너가 수립한 검색어(search_query)를 바탕으로 
    벡터 DB에서 하이브리드 검색을 수행하여 연관 봉사활동(retrieved_volunteers)을 수집하는 노드 함수입니다.
    """
    recommendation_strategy = state.get("recommendation_strategy")
    search_query = recommendation_strategy["search_query"]

    # 쿼리가 비어 있는 경우 기본 검색어인 "volunteer"(봉사활동)로 대치하여 검색 오류 방어
    if not search_query or not search_query.strip():
        search_query = "volunteer"
    
    # 싱글톤 벡터 스토어 어댑터 획득
    adapter = get_vector_store_adapter()

    # 콜드 스타트(Cold-Start) 방어 - 인덱싱된 데이터가 없을 경우 가상 데이터 즉시 자동 적재
    if adapter.db is None or not adapter.documents_list:
        logger.info("Vector DB index is empty. Indexing dummy volunteer data for Cold-Start prevention...")
        dummy_docs = get_dummy_volunteer_data()
        adapter.add_documents(dummy_docs)

    # 하이브리드 검색 (Top 5 추출)
    logger.info(f"Performing Hybrid Search in Vector DB with query: '{search_query}'")
    results = adapter.hybrid_search(query=search_query, top_k=5)
    
    return {"retrieved_volunteers": results}