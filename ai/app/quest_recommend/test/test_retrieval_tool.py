import unittest
from ai.app.quest_recommend.state import RecommendState
from ai.app.quest_recommend.retrieval_tool import retrieve_volunteers
from ai.app.common.vector_adapter import get_vector_store_adapter

class TestRetrievalTool(unittest.TestCase):
    def setUp(self):
        """테스트 전 매번 싱글톤 어댑터를 초기화하여 깨끗한 상태로 유지"""
        adapter = get_vector_store_adapter()
        adapter.clear()

    def test_retrieve_volunteers_cold_start_and_search(self):
        """인덱스가 비어 있을 때 콜드 스타트 방어 로직이 더미 데이터를 자동 적재하고 하이브리드 검색을 수행하는지 검증"""
        mock_state: RecommendState = {
            "user_id": 1,
            "interests": ["ENVIRONMENT"],
            "region_id": 1,
            "latitude": 37.566,
            "longitude": 126.978,
            "level": 3,
            "history_quests": [],
            "recent_recommendations": [],
            "preferred_difficulty": "NORMAL",
            "request_message": None,
            "user_profile": {},
            "situation_context": {},
            "request_context": {},
            "recommendation_strategy": {
                "strategy": "Plan to search for environment cleanup tasks",
                "search_query": "쓰레기 줍기 플로깅 환경 정화",
                "llm_constraints": ["must be outdoor"]
            },
            "retrieved_volunteers": [],
            "candidate_quests": [],
            "retry_count": 0,
            "recommended_quests": []
        }
        
        result = retrieve_volunteers(mock_state)
        retrieved = result.get("retrieved_volunteers")
        
        # 검증
        self.assertIsNotNone(retrieved)
        self.assertIsInstance(retrieved, list)
        self.assertTrue(len(retrieved) > 0)
        
        # 1순위 결과에 플로깅/환경 관련 글이 잘 수집되었는지 확인 (더미 중 1001번 한강 쓰레기 줍기 매칭)
        top_result = retrieved[0]
        self.assertEqual(top_result["id"], 1001)
        self.assertEqual(top_result["category"], "ENVIRONMENT")

    def test_retrieve_volunteers_fallback_query(self):
        """플래너의 쿼리가 누락되었을 때 기본 검색어로 폴백하여 검색을 정상 수행하는지 검증"""
        mock_state: RecommendState = {
            "user_id": 2,
            "interests": ["ANIMAL"],
            "region_id": 1,
            "latitude": 37.566,
            "longitude": 126.978,
            "level": 1,
            "history_quests": [],
            "recent_recommendations": [],
            "preferred_difficulty": "NORMAL",
            "request_message": None,
            "user_profile": {},
            "situation_context": {},
            "request_context": {},
            "recommendation_strategy": {
                "strategy": "Empty strategy",
                "search_query": "",  # 쿼리 누락 상황
                "llm_constraints": []
            },
            "retrieved_volunteers": [],
            "candidate_quests": [],
            "retry_count": 0,
            "recommended_quests": []
        }
        
        result = retrieve_volunteers(mock_state)
        retrieved = result.get("retrieved_volunteers")
        
        # 검증
        self.assertIsNotNone(retrieved)
        self.assertTrue(len(retrieved) > 0)
        
        # 쿼리가 비어 있어도 폴백되어 모든 더미 데이터 범위 내에서 검색이 완료되었는지 확인
        ids = [doc["id"] for doc in retrieved]
        self.assertTrue(any(doc_id in [1001, 1002, 1003, 1004, 1005] for doc_id in ids))

if __name__ == "__main__":
    unittest.main()