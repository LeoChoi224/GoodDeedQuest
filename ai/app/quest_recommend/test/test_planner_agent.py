import unittest
from ai.app.quest_recommend.state import RecommendState
from ai.app.quest_recommend.planner_agent import analyze_strategy

class TestPlannerAgent(unittest.TestCase):
    def test_analyze_strategy_sunny_weekend(self):
        """맑은 주말, 특별한 추가 요구사항이 없을 때의 일반 전략 및 쿼리 도출 검증"""
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
                "current_date": "2026-07-20",
                "day_of_week_type": "weekend",
                "is_weekend": True,
                "today_weather": "sunny",
                "is_outdoor_feasible": True
            },
            "request_context": {},  # 빈 요구사항 상황
            "recommendation_strategy": {},
            "retrieved_volunteers": [],
            "candidate_quests": [],
            "retry_count": 0,
            "recommended_quests": []
        }
        
        result = analyze_strategy(mock_state)
        strategy = result.get("recommendation_strategy")
        
        # 검증
        self.assertIsNotNone(strategy)
        self.assertTrue(len(strategy["strategy"]) > 0)
        self.assertTrue(len(strategy["search_query"]) > 0)
        self.assertIsInstance(strategy["llm_constraints"], list)
        
    def test_analyze_strategy_rainy_weekday_with_request(self):
        """비 오는 날씨(야외 불가)와 챗봇 컴퓨터 요청이 들어왔을 때 실내 제약조건 형성 검증"""
        mock_state: RecommendState = {
            "user_id": 2,
            "interests": ["교육"],
            "region_id": 1,
            "latitude": 37.566,
            "longitude": 126.978,
            "level": 1,
            "history_quests": [],
            "recent_recommendations": [],
            "preferred_difficulty": "NORMAL",
            "request_message": "가볍게 컴퓨터로 할 수 있는 거 추천해줘",
            "user_profile": {
                "interests": ["교육"],
                "target_difficulty": "NORMAL",
                "exclusions": [],
                "completed_history": []
            },
            "situation_context": {
                "current_date": "2026-07-20",
                "day_of_week_type": "weekday",
                "is_weekend": False,
                "today_weather": "rainy",
                "is_outdoor_feasible": False  # 비가 옴 -> 야외 불가능 상황
            },
            "request_context": {
                "time_preference": "any",
                "duration_preference": "short",
                "indoor_outdoor_preference": "indoor",
                "additional_keywords": ["computer", "easy"]
            },
            "recommendation_strategy": {},
            "retrieved_volunteers": [],
            "candidate_quests": [],
            "retry_count": 0,
            "recommended_quests": []
        }
        
        result = analyze_strategy(mock_state)
        strategy = result.get("recommendation_strategy")
        
        self.assertIsNotNone(strategy)
        # 생성 규칙 리스트에 실내(indoor) 혹은 비대면(online) 등의 키워드 조건이 강제되었는지 단언 검증
        constraints = [c.lower() for c in strategy["llm_constraints"]]
        self.assertTrue(
            any("indoor" in c or "computer" in c or "online" in c or "virtual" in c for c in constraints),
            f"Expected indoor or computer related constraints, but got: {strategy['llm_constraints']}"
        )

if __name__ == "__main__":
    unittest.main()