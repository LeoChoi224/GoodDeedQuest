import unittest
from ai.app.common.vector_adapter import get_vector_store_adapter
from backend.app.common.database import SessionLocal

from ai.app.quest_recommend.state import RecommendState
from ai.app.quest_recommend.nodes.volunteer_agent import (
    retrieve_volunteers,
    load_volunteer_centers_from_db,
    _volunteer_embedding_cache
)


class TestVolunteerDualCaching(unittest.TestCase):
    """
    2단계 듀얼 캐싱 (RAM 메모리 + DB VolunteerCenter.embedding 영구 저장) 및 Planner 쿼리 수색 테스트
    """

    def setUp(self):
        """테스트 전 매번 싱글톤 벡터 어댑터를 초기화하여 깨끗한 상태 유지"""
        adapter = get_vector_store_adapter()
        adapter.clear()

    def test_dual_caching_and_db_persistence(self):
        """1회 임베딩 후 RAM 캐시와 DB VolunteerCenter.embedding 컬럼 2곳에 동시 영구 저장되는지 검증"""
        with SessionLocal() as db:
            docs = load_volunteer_centers_from_db(db, lat=35.574, lng=129.241, radius_km=3.0)
            
            self.assertTrue(len(docs) > 0, "실제 DB에서 3km 이내 봉사 공고가 최소 1개 이상 로드되어야 합니다.")
            cid = docs[0]["id"]
            
            # 1. Tier 1: RAM 메모리 캐시에 벡터 저장 여부 검증
            self.assertIn(cid, _volunteer_embedding_cache, "RAM 인메모리 딕셔너리에 임베딩 벡터가 캐싱되어야 합니다.")
            
            # 2. Tier 2: DB VolunteerCenter.embedding 컬럼에 영구 적재(db.commit) 여부 검증
            from backend.app.map.models import VolunteerCenter
            center_in_db = db.get(VolunteerCenter, cid)
            self.assertIsNotNone(center_in_db.embedding, "DB VolunteerCenter.embedding 컬럼에 벡터가 영구 적재되어야 합니다.")
            self.assertIn("vector", center_in_db.embedding)

    def test_retrieve_volunteers_with_planner_query(self):
        """Planner 전략 쿼리(search_query)로 2단계 듀얼 캐시 적용 수색이 정상 실행되는지 검증"""
        mock_state: RecommendState = {
            "user_id": 1,
            "interests": ["어르신"],
            "latitude": 35.250,
            "longitude": 128.667,
            "user_profile": {"latitude": 35.250, "longitude": 128.667, "interests": ["어르신"]},
            # Planner Agent가 수립한 실제 전략 쿼리
            "recommendation_strategy": {
                "strategy": "창원시 요양병원 이미용 봉사 수색 전략",
                "search_query": "성미카엘요양병원 이미용 봉사자",
                "llm_constraints": []
            },
            "retrieved_volunteers": [],
            "candidate_quests": [],
            "retry_count": 0,
            "recommended_quests": []
        }
        
        result = retrieve_volunteers(mock_state)
        retrieved = result.get("retrieved_volunteers", [])
        
        self.assertIsNotNone(retrieved)
        self.assertTrue(len(retrieved) > 0, "유사도 수색 결과가 최소 1개 이상 배출되어야 합니다.")


if __name__ == "__main__":
    unittest.main()


