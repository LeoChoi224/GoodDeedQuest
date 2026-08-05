import unittest
from unittest.mock import patch

from langchain_core.runnables import RunnableLambda

from ai.app.quest_recommend.state import RecommendState
from ai.app.quest_recommend.nodes.validation_agent import validate_candidates, route_validation

class TestSelfCorrectionLoop(unittest.TestCase):
    def test_rejection_feedback_collection(self):
        """Critic 반려 시 rejection_reasons_en 및 rejection_reasons_ko 수집 및 Planner 회귀 조건 검증"""
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
            "situation_context": {"today_weather": "rainy", "is_outdoor_feasible": False},
            "request_context": {},
            "recommendation_strategy": {"strategy": "Must be indoor", "llm_constraints": ["must be indoor"]},
            "retrieved_volunteers": [
                # volunteer_agent 가 실제로 내보내는 키를 그대로 쓴다(volunteer_agent.py:152~164).
                # DB 컬럼명(vol_name/vol_act/vol_address)이 아니라 조립된 문서의 키다.
                {
                    "id": 1,
                    "title": "야외 플로깅",
                    "quest_summary": "야외 정화 활동",
                    "location": "서울시 마포구"
                }
            ],
            "ai_good_deeds": [
                {
                    "category_name": "ENVIRONMENT",
                    "quest_title": "야외 쓰레기 줍기",
                    "quest_description": "빗속 쓰레기 줍기",
                    "quest_target": "SOLO",
                    "quest_type": "GOOD_DEED",
                    "location": None,
                    "difficulty": "EASY",
                    "estimated_duration": 15,
                    "recommendation_reason": "야외 활동",
                    "priority_score": 5
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
                DummyEvaluation("야외 플로깅", False, "Violates indoor constraint", "실내 필수 제약조건 위반"),
                DummyEvaluation("야외 쓰레기 줍기", False, "Violates indoor constraint", "실내 필수 제약조건 위반")
            ]

        with patch("ai.app.quest_recommend.nodes.validation_agent.get_openai_model") as mock_get_openai:
            # 프로덕션은 `validation_prompt | structured_llm` 으로 체인을 조립한 뒤
            # 그 체인을 invoke 한다(validation_agent.py:214).
            # 따라서 with_structured_output 의 반환값은 LangChain Runnable 이어야 한다.
            # MagicMock 을 넣으면 `|` 가 만든 새 체인이 mock.invoke 를 타지 않는다.
            mock_get_openai.return_value.with_structured_output.return_value = RunnableLambda(
                lambda _: DummyReport()
            )

            result = validate_candidates(mock_state)

        rejection_en = result.get("rejection_reasons_en", [])
        rejection_ko = result.get("rejection_reasons_ko", [])
        candidate_quests = result.get("candidate_quests", [])

        # 검수 결과 반려 사유가 영문/한글 각자 정상 수집되었는지 확인
        self.assertEqual(len(candidate_quests), 0)
        self.assertEqual(len(rejection_en), 2)
        self.assertEqual(len(rejection_ko), 2)
        self.assertIn("Violates indoor constraint", rejection_en[0])
        self.assertIn("실내 필수 제약조건 위반", rejection_ko[0])

        # State에 수집된 데이터를 반영하여 라우터 분기 검증
        mock_state["retrieved_volunteers"] = [{"vol_name": "봉사1"}]  # 검색된 봉사데이터 존재 조건
        mock_state["candidate_quests"] = candidate_quests
        mock_state["accumulated_candidates"] = []
        mock_state["retry_count"] = 0

        next_node = route_validation(mock_state)
        self.assertEqual(next_node, "planner", "Critic 반려로 인해 5개 미만일 시 planner로 회귀해야 합니다.")

if __name__ == "__main__":
    unittest.main()