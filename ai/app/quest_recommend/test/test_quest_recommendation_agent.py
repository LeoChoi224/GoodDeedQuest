import unittest
from unittest.mock import patch # Mock 도구 임포트
from ai.app.quest_recommend.state import RecommendState
from ai.app.quest_recommend.quest_recommendation_agent import recommend_quests

class TestQuestRecommendationAgent(unittest.TestCase):
    def test_recommend_quests_normal(self):
        """정상 조건 하에서 6~7개의 맞춤형 봉사/선행 후보군 조립 및 데이터 타입 검증"""
        mock_state: RecommendState = {
            "user_id": 1,
            "interests": ["환경", "동물"],
            "region_id": 1,
            "latitude": 37.566,
            "longitude": 126.978,
            "level": 3,
            "history_quests": [],
            "recent_recommendations": [],
            "preferred_difficulty": "NORMAL",
            "request_message": None,
            "user_profile": {
                "interests": ["환경", "동물"],
                "target_difficulty": "NORMAL",
                "exclusions": [],
                "completed_history": []
            },
            "situation_context": {
                "current_date": "2026-07-21",
                "day_of_week_type": "weekend",
                "is_weekend": True,
                "today_weather": "sunny",
                "is_outdoor_feasible": True
            },
            "request_context": {},
            "recommendation_strategy": {
                "strategy": "Recommend outdoor environmental and animal tasks on a sunny weekend.",
                "search_query": "environmental cleanup and animal care",
                "llm_constraints": ["allow outdoor tasks"]
            },
            "retrieved_volunteers": [
                {
                    "id": 1001,
                    "title": "한강 시민공원 망원지구 쓰레기 줍기 플로깅",
                    "content": "한강 일대 방치된 쓰레기를 수거하고 환경 정화 활동을 펼칩니다.",
                    "category": "환경",
                    "location": "서울시 마포구",
                    "url": "https://www.1365.go.kr/nanum/prg/egvh/vnt/vntProgCode=1001",
                    "is_volunteer": True
                }
            ],
            "candidate_quests": [],
            "retry_count": 0,
            "recommended_quests": []
        }
        
        result = recommend_quests(mock_state)
        candidates = result.get("candidate_quests")
        
        self.assertIsNotNone(candidates)
        self.assertIsInstance(candidates, list)
        self.assertTrue(6 <= len(candidates) <= 7, f"Expected 6-7 candidates, got {len(candidates)}")
        
        for q in candidates:
            self.assertIn("category_name", q)
            self.assertIn("quest_title", q)
            self.assertIn("quest_description", q)
            self.assertIn("quest_target", q)
            self.assertIn("quest_type", q)
            self.assertIn(q["quest_type"], ["VOLUNTEER", "GOOD_DEED"])
            self.assertIn(q["difficulty"], ["VERY_EASY", "EASY", "NORMAL", "HARD", "VERY_HARD"])
            self.assertIsInstance(q["estimated_duration"], int)
            
            if q["quest_type"] == "GOOD_DEED":
                self.assertIsNone(q["location"])
                
    @patch("ai.app.quest_recommend.quest_recommendation_agent.get_openai_model")
    def test_recommend_quests_fallback(self, mock_get_openai):
        """API 장애를 모의(Mocking)하여 안전하게 Fallback 일상 퀘스트 리스트를 반환하는지 검증"""
        # OpenAI 호출 시 무조건 예외를 발생시키도록 세팅
        mock_get_openai.side_effect = Exception("OpenAI API Connection Timeout")

        mock_state: RecommendState = {
            "user_id": 2,
            "interests": [],
            "region_id": 1,
            "latitude": 37.566,
            "longitude": 126.978,
            "level": 1,
            "history_quests": [],
            "recent_recommendations": [],
            "preferred_difficulty": "NORMAL",
            "request_message": None,
            "user_profile": {
                "interests": ["환경"],
                "target_difficulty": "NORMAL",
                "exclusions": [],
                "completed_history": []
            },
            "situation_context": {},
            "request_context": {},
            "recommendation_strategy": {},
            "retrieved_volunteers": [],
            "candidate_quests": [],
            "retry_count": 0,
            "recommended_quests": []
        }
        
        result = recommend_quests(mock_state)
        candidates = result.get("candidate_quests")
        
        self.assertIsNotNone(candidates)
        self.assertTrue(len(candidates) > 0)
        # 예외가 성공적으로 가로채져 Fallback 퀘스트(텀블러 사용하기)가 반환되었는지 검증
        self.assertEqual(candidates[0]["quest_title"], "텀블러 사용하기")

if __name__ == "__main__":
    unittest.main()