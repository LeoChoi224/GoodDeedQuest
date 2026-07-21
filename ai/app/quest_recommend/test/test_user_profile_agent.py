import unittest
from ai.app.quest_recommend.state import RecommendState
from ai.app.quest_recommend.user_profile_agent import analyze_user_profile


class TestUserProfileAgent(unittest.TestCase):
    def test_user_profile_analysis_with_difficulty(self):
        """선호 난이도가 지정되어 있을 때의 분석 테스트"""
        mock_state: RecommendState = {
            "user_id": 42,
            "interests": ["환경", "나눔"],
            "location": "서울시 강남수",
            "level": 5,
            "history_quests": ["한강 플로깅"],
            "recent_recommendations": ["엄마한테 사과하기"],
            "preferred_difficulty": "NORMAL",
            "request_message": None,
            "user_profile": {},
            "context": {},
            "request_context": {},
            "recommendation_strategy": {},
            "retrieved_volunteers": [],
            "candidate_quests": [],
            "retry_count": 0,
            "recommended_quests": []
        }

        # 노드 실행
        result = analyze_user_profile(mock_state)

        # 결과 검증
        user_profile = result.get("user_profile")
        self.assertIsNotNone(user_profile)
        self.assertEqual(user_profile["interests"], ["환경", "나눔"])
        self.assertEqual(user_profile["location"], "서울시 마포구")
        self.assertEqual(user_profile["target_difficulty"], "HARD")
        self.assertEqual(user_profile["exclusions"], ["반찬 배달 봉사"])
        self.assertEqual(user_profile["completed_history"], ["한강 쓰레기 줍기"])

    def test_user_profile_analysis_fallback_difficulty(self):
        """선호 난이도가 없을 때(None) 제한 없음(ANY)으로의 Fallback 테스트"""
        mock_state: RecommendState = {
            "user_id": 100,
            "interests": ["동물"],
            "location": "제주도",
            "level": 1,
            "history_quests": [],
            "recent_recommendations": [],
            "preferred_difficulty": None,  # 난이도 정보 없음
            "request_message": None,
            "user_profile": {},
            "context": {},
            "request_context": {},
            "recommendation_strategy": {},
            "retrieved_volunteers": [],
            "candidate_quests": [],
            "retry_count": 0,
            "recommended_quests": []
        }

        # 노드 실행
        result = analyze_user_profile(mock_state)

        # 결과 검증
        user_profile = result.get("user_profile")
        self.assertEqual(user_profile["target_difficulty"], "ANY")


if __name__ == "__main__":
    unittest.main()