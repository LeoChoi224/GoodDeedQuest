import unittest
from ai.app.quest_recommend.state import RecommendState
from ai.app.quest_recommend.request_agent import analyze_request

class TestRequestAgent(unittest.TestCase):
    def test_analyze_request_empty(self):
        """요청 메시지가 없을 때 LLM 호출 없이 빈 딕셔너리를 즉시 리턴하는지 검증"""
        mock_state: RecommendState = {
            "user_id": 1,
            "interests": ["환경"],
            "region_id": 1,
            "latitude": 37.566,
            "longitude": 126.978,
            "level": 3,
            "history_quests": [],
            "recent_recommendations": [],
            "preferred_difficulty": "NORMAL",
            "request_message": None,  # 메시지 없음 (None 상황)
            "user_profile": {},
            "context": {},
            "request_context": {},
            "recommendation_strategy": {},
            "retrieved_volunteers": [],
            "candidate_quests": [],
            "retry_count": 0,
            "recommended_quests": []
        }
        
        result = analyze_request(mock_state)
        self.assertEqual(result, {"request_context": {}})

    def test_analyze_request_custom(self):
        """구체적인 커스텀 요구사항 메시지가 전달되었을 때 영문 제약 조건들이 정상 추출되는지 실시간 API 검증"""
        mock_state: RecommendState = {
            "user_id": 2,
            "interests": ["환경"],
            "region_id": 1,
            "latitude": 37.566,
            "longitude": 126.978,
            "level": 3,
            "history_quests": [],
            "recent_recommendations": [],
            "preferred_difficulty": "NORMAL",
            "request_message": "퇴근하고 실외에서 가볍게 20분 정도 쓰레기 줍고 싶어",
            "user_profile": {},
            "context": {},
            "request_context": {},
            "recommendation_strategy": {},
            "retrieved_volunteers": [],
            "candidate_quests": [],
            "retry_count": 0,
            "recommended_quests": []
        }
        
        result = analyze_request(mock_state)
        request_context = result.get("request_context")
        
        # 검증
        self.assertIsNotNone(request_context)
        self.assertEqual(request_context["indoor_outdoor_preference"], "outdoor")
        self.assertEqual(request_context["duration_preference"], "short")
        self.assertIn(request_context["time_preference"], ["evening", "night", "any"])
        
        # 쓰레기 줍기 행동 키워드가 정상 추출되었는지 검증 (영단어 매핑 체크)
        keywords = request_context.get("additional_keywords", [])
        expected_keywords = ["trash", "cleanup", "litter", "waste", "cleaning"]
        self.assertTrue(any(word.lower() in expected_keywords for word in keywords))

if __name__ == "__main__":
    unittest.main()