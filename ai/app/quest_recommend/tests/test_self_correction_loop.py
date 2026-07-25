import unittest
from ai.app.quest_recommend.state import RecommendState
from ai.app.quest_recommend.nodes.validation_agent import route_validation

class TestSelfCorrectionLoop(unittest.TestCase):
    def test_route_validation_pass(self):
        """최종 합격 퀘스트가 5개 이상일 때 정상적으로 response로 통과하는지 검증"""
        mock_state: RecommendState = {
            "user_id": 1,
            "interests": [],
            "region_id": None,
            "latitude": None,
            "longitude": None,
            "level": 1,
            "history_quests": [],
            "recent_recommendations": [],
            "preferred_difficulty": "ANY",
            "request_message": None,
            "user_profile": {},
            "situation_context": {},
            "request_context": {},
            "recommendation_strategy": {},
            "retrieved_volunteers": [{"title": "봉사1"}],
            "candidate_quests": [
                {"title": "퀘스트1"}, {"title": "퀘스트2"}, {"title": "퀘스트3"},
                {"title": "퀘스트4"}, {"title": "퀘스트5"}
            ],
            "retry_count": 0,
            "recommended_quests": []
        }
        
        result = route_validation(mock_state)
        self.assertEqual(result, "response")

    def test_route_validation_max_retries(self):
        """후보가 5개 미만이더라도 재시도가 3회 이상이면 response로 탈출하여 폴백하는지 검증"""
        mock_state: RecommendState = {
            "user_id": 1,
            "interests": [],
            "region_id": None,
            "latitude": None,
            "longitude": None,
            "level": 1,
            "history_quests": [],
            "recent_recommendations": [],
            "preferred_difficulty": "ANY",
            "request_message": None,
            "user_profile": {},
            "situation_context": {},
            "request_context": {},
            "recommendation_strategy": {},
            "retrieved_volunteers": [{"title": "봉사1"}],
            "candidate_quests": [{"title": "퀘스트1"}],  # 1개뿐이지만
            "retry_count": 3,  # 3회 초과
            "recommended_quests": []
        }
        
        result = route_validation(mock_state)
        self.assertEqual(result, "response")

    def test_route_validation_insufficient_search(self):
        """후보가 부족한데 검색 결과조차 없으면 retrieval(검색 툴)로 돌아가는지 검증"""
        mock_state: RecommendState = {
            "user_id": 1,
            "interests": [],
            "region_id": None,
            "latitude": None,
            "longitude": None,
            "level": 1,
            "history_quests": [],
            "recent_recommendations": [],
            "preferred_difficulty": "ANY",
            "request_message": None,
            "user_profile": {},
            "situation_context": {},
            "request_context": {},
            "recommendation_strategy": {},
            "retrieved_volunteers": [],  # 검색 결과 없음
            "candidate_quests": [{"title": "퀘스트1"}],
            "retry_count": 0,
            "recommended_quests": []
        }
        
        result = route_validation(mock_state)
        self.assertEqual(result, "retrieval")

    def test_route_validation_low_quality(self):
        """후보가 부족하고 검색 결과는 충분했으나 비평가 탈락인 경우 planner로 회귀하는지 검증"""
        mock_state: RecommendState = {
            "user_id": 1,
            "interests": [],
            "region_id": None,
            "latitude": None,
            "longitude": None,
            "level": 1,
            "history_quests": [],
            "recent_recommendations": [],
            "preferred_difficulty": "ANY",
            "request_message": None,
            "user_profile": {},
            "situation_context": {},
            "request_context": {},
            "recommendation_strategy": {},
            "retrieved_volunteers": [{"title": "봉사1"}, {"title": "봉사2"}],  # 검색 재료는 있음
            "candidate_quests": [{"title": "퀘스트1"}],  # 비평에서 탈락하여 1개만 남음
            "retry_count": 0,
            "recommended_quests": []
        }
        
        result = route_validation(mock_state)
        self.assertEqual(result, "planner")

if __name__ == "__main__":
    unittest.main()