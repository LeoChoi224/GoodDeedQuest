import unittest
from ai.app.quest_recommend.state import RecommendState
from ai.app.quest_recommend.nodes.volunteer_agent import (
    retrieve_volunteers,
    load_volunteer_centers_from_db,
    _volunteer_embedding_cache
)
from ai.app.common.vector_adapter import get_vector_store_adapter
from backend.app.common.database import SessionLocal


class TestVolunteerAgentUnit(unittest.TestCase):
    """
    3km/6km DB Geo-filtering, exclude_ids 제외 픽업, volunteer_retry_count 상태 반환 검증 테스트
    """

    def setUp(self):
        """테스트 전 매번 싱글톤 어댑터를 초기화하여 깨끗한 상태 유지"""
        adapter = get_vector_store_adapter()
        adapter.clear()

    def test_load_volunteer_centers_with_exclude_ids(self):
        """재시도 시 이전 픽업된 center_id(exclude_ids)가 DB 쿼리에서 notin_으로 제외되는지 검증"""
        with SessionLocal() as db:
            # 1차 픽업
            docs_1st = load_volunteer_centers_from_db(db, lat=35.574, lng=129.241, radius_km=3.0)
            
            if docs_1st:
                first_ids = [d["id"] for d in docs_1st]
                # 2차 픽업 시 이전 1차 id들을 exclude_ids로 전달
                docs_2nd = load_volunteer_centers_from_db(
                    db, lat=35.574, lng=129.241, radius_km=3.0, exclude_ids=first_ids
                )
                
                second_ids = [d["id"] for d in docs_2nd]
                # 1차 픽업된 id가 2차 픽업 결과에 단 하나도 포함되지 않음을 검증
                for fid in first_ids:
                    self.assertNotIn(fid, second_ids, "이전 픽업된 공고 ID는 2차 픽업에서 중복 제외(notin_)되어야 합니다.")

    def test_retrieve_volunteers_no_location(self):
        """유저 실시간 좌표가 없을 때 volunteer_retry_count: -1 이 반환되는지 검증"""
        mock_state: RecommendState = {
            "user_id": 1,
            "interests": ["어르신"],
            "latitude": None,  # 위치 미조회
            "longitude": None,
            "user_profile": {"interests": ["어르신"]},
            "recommendation_strategy": {
                "strategy": "봉사 수색",
                "search_query": "어르신 봉사",
                "llm_constraints": []
            },
            "retrieved_volunteers": [],
            "candidate_quests": [],
            "retry_count": 0,
            "volunteer_retry_count": 0,
            "recommended_quests": []
        }
        
        result = retrieve_volunteers(mock_state)
        
        self.assertEqual(result.get("retrieved_volunteers"), [])
        self.assertEqual(result.get("volunteer_retry_count"), -1, "위치 미조회 시 volunteer_retry_count는 -1이 반환되어야 합니다.")

    def test_dual_caching_and_search(self):
        """정상 위치 입력 시 RAM + DB 듀얼 캐싱과 함께 volunteer_retry_count: 1 이 반환되는지 검증"""
        mock_state: RecommendState = {
            "user_id": 1,
            "interests": ["어르신"],
            "latitude": 35.250,
            "longitude": 128.667,
            "user_profile": {"latitude": 35.250, "longitude": 128.667, "interests": ["어르신"]},
            "recommendation_strategy": {
                "strategy": "창원시 요양병원 이미용 봉사 수색",
                "search_query": "요양병원 이미용 봉사자",
                "llm_constraints": []
            },
            "retrieved_volunteers": [],
            "candidate_quests": [],
            "retry_count": 0,
            "volunteer_retry_count": 0,
            "recommended_quests": []
        }
        
        result = retrieve_volunteers(mock_state)
        retrieved = result.get("retrieved_volunteers", [])
        
        self.assertIsNotNone(retrieved)
        self.assertEqual(result.get("volunteer_retry_count"), 1, "정상 수색 성공 시 volunteer_retry_count는 1로 설정되어야 합니다.")


if __name__ == "__main__":
    unittest.main()