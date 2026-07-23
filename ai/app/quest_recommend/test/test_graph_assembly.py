import unittest
from ai.app.quest_recommend.state import RecommendState
from ai.app.quest_recommend.quest_recommend_graph import run_recommendation_flow

class TestGraphAssembly(unittest.TestCase):
    def test_full_recommendation_flow_e2e(self):
        """전체 랭그래프 조립 워크플로우의 E2E 통합 실행 및 최종 5개 퀘스트 반환 검증"""
        mock_initial_state: RecommendState = {
            "user_id": 1,
            "interests": ["ENVIRONMENT", "SHARING"],
            "region_id": 1,
            "latitude": 37.566,
            "longitude": 126.978,
            "level": 3,
            "history_quests": ["텀블러 사용하기"],
            "recent_recommendations": [],
            "preferred_difficulty": "NORMAL",
            "request_message": "비 오는 날 실내에서 할 수 있는 쉬운 봉사활동 추천해줘",
            "user_profile": {},
            "situation_context": {},
            "request_context": {},
            "recommendation_strategy": {},
            "retrieved_volunteers": [],  # 초기 상태는 빈 리스트 -> recommendation에서 LLM 스킵 후 retrieval 자동 호출
            "candidate_quests": [],
            "retry_count": 0,
            "recommended_quests": []
        }

        # 전체 랭그래프 워크플로우 가동 (E2E 실행)
        result_state = run_recommendation_flow(mock_initial_state)

        # 1. 반환 상태 검증
        self.assertIsNotNone(result_state)
        
        # 2. 각 단계별 에이전트 생성물 정합성 확인
        self.assertIn("user_profile", result_state)
        self.assertIn("situation_context", result_state)
        self.assertIn("request_context", result_state)
        self.assertIn("recommendation_strategy", result_state)
        self.assertTrue(len(result_state.get("retrieved_volunteers", [])) > 0, "Volunteer retrieval should be triggered safely")
        
        # 3. 최종 recommended_quests가 정확히 5개 배출되었는지 검증
        recommended = result_state.get("recommended_quests")
        self.assertIsNotNone(recommended)
        self.assertIsInstance(recommended, list)
        self.assertEqual(len(recommended), 5, f"Expected 5 recommended quests, got {len(recommended)}")

        # 4. 각 퀘스트 필수 필드 및 점수 검증
        for quest in recommended:
            self.assertIn("quest_title", quest)
            self.assertIn("category_name", quest)
            self.assertIn("recommendation_reason", quest)
            self.assertIn("priority_score", quest)
            self.assertIsInstance(quest["priority_score"], int)

if __name__ == "__main__":
    unittest.main()
