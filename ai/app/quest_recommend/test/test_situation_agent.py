import unittest
from ai.app.quest_recommend.state import RecommendState
from ai.app.quest_recommend.situation_agent import analyze_situation


class TestContextAgent(unittest.TestCase):
    def test_analyze_context_default_sunny(self):
        """기본 좌표(서울) 기준 실시간 날씨 API 연동 및 결과 타입 검증"""
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
            "request_message": None,
            "user_profile": {},
            "situation_context": {},
            "request_context": {},
            "recommendation_strategy": {},
            "retrieved_volunteers": [],
            "candidate_quests": [],
            "retry_count": 0,
            "recommended_quests": []
        }

        # 노드 실행
        result = analyze_situation(mock_state)
        situation_context = result.get("situation_context")

        # 검증
        self.assertIsNotNone(situation_context)
        # 실시간 API 호출이므로 네 가지 기상 분류 중 하나가 반드시 매핑되어야 함
        self.assertIn(situation_context["today_weather"], ["sunny", "cloudy", "rainy", "snowy"])
        self.assertIn(situation_context["day_of_week_type"], ["weekday", "weekend"])
        self.assertIsInstance(situation_context["is_weekend"], bool)
        self.assertIsInstance(situation_context["is_outdoor_feasible"], bool)

    def test_analyze_context_fallback_jeju_mock(self):
        """제주 임시 테스트 ID를 활용한 가상 기상 분기 및 예외 우회 검증"""
        mock_state: RecommendState = {
            "user_id": 2,
            "interests": ["동물"],
            "region_id": 999,  # 가상의 제주 지역 매핑용 코드
            "latitude": None,
            "longitude": None,
            "level": 1,
            "history_quests": [],
            "recent_recommendations": [],
            "preferred_difficulty": "NORMAL",
            "request_message": None,
            "user_profile": {},
            "situation_context": {},
            "request_context": {},
            "recommendation_strategy": {},
            "retrieved_volunteers": [],
            "candidate_quests": [],
            "retry_count": 0,
            "recommended_quests": []
        }

        # 노드 실행
        result = analyze_situation(mock_state)
        situation_context = result.get("situation_context")

        # 검증
        self.assertIsNotNone(situation_context)
        # 주석 해제 전이므로 999 ID에 기반해 제주 대표 좌표(위도 33.499)로 들어가 실시간 날씨를 긁어오는지 확인
        self.assertIn(situation_context["today_weather"], ["sunny", "cloudy", "rainy", "snowy"])


if __name__ == "__main__":
    unittest.main()