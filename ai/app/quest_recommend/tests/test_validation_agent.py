import unittest
from unittest.mock import patch
from ai.app.quest_recommend.state import RecommendState
from ai.app.quest_recommend.nodes.validation_agent import validate_candidates, route_validation

class TestValidationAgent(unittest.TestCase):
    def test_validate_candidates_success(self):
        """실제 봉사(retrieved_volunteers)와 AI 선행(ai_good_deeds)의 1차 매핑/검수 및 2차 LLM 검수 통과 테스트"""
        mock_state: RecommendState = {
            "user_id": 1,
            "interests": ["ENVIRONMENT"],
            "region_id": 1,
            "latitude": 37.566,
            "longitude": 126.978,
            "level": 1,
            "history_quests": [],
            "recent_recommendations": [],
            "preferred_difficulty": "NORMAL",
            "request_message": None,
            "user_profile": {"interests": ["ENVIRONMENT"]},
            "situation_context": {"today_weather": "sunny", "is_outdoor_feasible": True},
            "request_context": {},
            "recommendation_strategy": {"strategy": "Allow outdoor tasks", "llm_constraints": []},
            "retrieved_volunteers": [
                {
                    "vol_name": "한강 플로깅 쓰레기 수거",
                    "vol_act": "한강 수변 환경 정화 활동",
                    "vol_address": "서울시 마포구"
                }
            ],
            "ai_good_deeds": [
                {
                    "category_name": "ENVIRONMENT",
                    "quest_title": "텀블러 실천하기",
                    "quest_description": "개인 텀블러 사용",
                    "quest_target": "SOLO",
                    "quest_type": "GOOD_DEED",
                    "location": None,
                    "difficulty": "EASY",
                    "estimated_duration": 15,
                    "recommendation_reason": "환경 보호",
                    "priority_score": 9
                }
            ],
            "candidate_quests": [],
            "accumulated_candidates": [],
            "rejection_reasons_en": [],
            "rejection_reasons_ko": [],
            "retry_count": 0,
            "recommended_quests": []
        }

        class DummyEvaluation:
            def __init__(self, title, is_valid, reason, reason_ko):
                self.quest_title = title
                self.is_valid = is_valid
                self.reason = reason
                self.reason_ko = reason_ko

        class DummyReport:
            evaluations = [
                DummyEvaluation("한강 플로깅 쓰레기 수거", True, "Approved", "승인됨"),
                DummyEvaluation("텀블러 실천하기", True, "Approved", "승인됨")
            ]

        with patch("ai.app.quest_recommend.nodes.validation_agent.get_openai_model") as mock_get_openai:
            mock_chain = unittest.mock.MagicMock()
            mock_chain.invoke.return_value = DummyReport()
            mock_get_openai.return_value.with_structured_output.return_value = mock_chain

            result = validate_candidates(mock_state)

        candidate_quests = result.get("candidate_quests", [])
        accumulated_candidates = result.get("accumulated_candidates", [])

        self.assertIsNotNone(candidate_quests)
        self.assertEqual(len(candidate_quests), 2)
        self.assertEqual(len(accumulated_candidates), 2)
        self.assertEqual(candidate_quests[0]["quest_type"], "VOLUNTEER")
        self.assertEqual(candidate_quests[1]["quest_type"], "GOOD_DEED")

    def test_route_validation_decisions(self):
        """라우터 함수 분기 판단 테스트 (봉사 데이터 누락: retrieval / 5개 이상: response / 3회 초과: response)"""
        # 1. 봉사 데이터 아예 누락 시 핀포인트 retrieval 수색 회귀 1순위 테스트
        state_no_volunteers: RecommendState = {
            "retrieved_volunteers": [],
            "accumulated_candidates": [{"quest_title": f"Q{i}"} for i in range(6)],
            "retry_count": 0
        }
        self.assertEqual(route_validation(state_no_volunteers), "retrieval")

        # 2. 봉사 데이터 존재 및 최종 후보 5개 이상 확보 시 response 진입 테스트
        state_pass: RecommendState = {
            "retrieved_volunteers": [{"vol_name": "봉사1"}],
            "accumulated_candidates": [{"quest_title": f"Q{i}"} for i in range(5)],
            "retry_count": 0
        }
        self.assertEqual(route_validation(state_pass), "response")

        # 3. 최대 3회 연산(retry_count >= 2) 초과 시 response 폴백 강제 종료 테스트
        state_max_retry: RecommendState = {
            "retrieved_volunteers": [{"vol_name": "봉사1"}],
            "accumulated_candidates": [{"quest_title": "Q1"}],
            "retry_count": 2
        }
        self.assertEqual(route_validation(state_max_retry), "response")

if __name__ == "__main__":
    unittest.main()