import unittest
from unittest.mock import patch
import openai

from ai.app.quest_recommend.state import RecommendState
from ai.app.quest_recommend.nodes.good_deed_agent import create_good_deeds
from ai.app.quest_recommend.nodes.validation_agent import validate_candidates, route_validation
from ai.app.quest_recommend.nodes.response_agent import format_response

class TestRecommendationFallbackAndPipeline(unittest.TestCase):
    """
    이슈 #17 추천 워크플로우 5대 고도화 및 100% 진성 Gemini Failover 검증 테스트
    """

    @patch("ai.app.quest_recommend.nodes.good_deed_agent.get_openai_model")
    @patch("ai.app.quest_recommend.nodes.good_deed_agent.invoke_gemini_fallback")
    def test_openai_failure_gemini_fallback(self, mock_gemini_fallback, mock_get_openai):
        """OpenAI API 장애 시 가짜 더미 데이터 대신 무소음 Gemini 백업 모델 가동 검증"""
        # get_openai_model 호출 시 즉시 openai.OpenAIError 예외 발생시킴
        mock_get_openai.side_effect = openai.OpenAIError("OpenAI API Outage Failure")

        class DummyOutput:
            quests = [
                type("Quest", (), {
                    "model_dump": lambda self: {
                        "category_name": "ENVIRONMENT",
                        "quest_title": f"Gemini 선행 {i}",
                        "quest_description": "Gemini 백업 실천 가이드",
                        "quest_target": "SOLO",
                        "quest_type": "GOOD_DEED",
                        "location": None,
                        "difficulty": "EASY",
                        "estimated_duration": 15,
                        "recommendation_reason": "Gemini 맞춤 사유",
                        "priority_score": 8
                    }
                })() for i in range(6)
            ]

        mock_gemini_fallback.return_value = DummyOutput()

        state: RecommendState = {
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
            "situation_context": {},
            "request_context": {},
            "recommendation_strategy": {},
            "retrieved_volunteers": [],
            "ai_good_deeds": [],
            "candidate_quests": [],
            "accumulated_candidates": [],
            "rejection_reasons_en": [],
            "rejection_reasons_ko": [],
            "retry_count": 0,
            "recommended_quests": []
        }

        result = create_good_deeds(state)
        ai_good_deeds = result.get("ai_good_deeds")

        self.assertIsNotNone(ai_good_deeds)
        self.assertEqual(len(ai_good_deeds), 6)
        self.assertTrue(ai_good_deeds[0]["quest_title"].startswith("Gemini"))
        mock_gemini_fallback.assert_called_once()

    def test_golden_ratio_response_selection(self):
        """실제 봉사 1개 + AI 선행 6개 중 [봉사 1개 + 선행 4개 = 총 5개] 황금 비율 응답 구성 검증"""
        target_pool = [
            {
                "category_name": "VOLUNTEER",
                "quest_title": "실제 한강 봉사활동",
                "quest_description": "봉사 실천",
                "quest_target": "SOLO",
                "quest_type": "VOLUNTEER",
                "location": "서울시 마포구",
                "difficulty": "NORMAL",
                "estimated_duration": None,
                "recommendation_reason": "실제 봉사 기회",
                "priority_score": 10
            }
        ] + [
            {
                "category_name": "ENVIRONMENT",
                "quest_title": f"AI 일상 선행 {i}",
                "quest_description": "선행 가이드",
                "quest_target": "SOLO",
                "quest_type": "GOOD_DEED",
                "location": None,
                "difficulty": "EASY",
                "estimated_duration": 15,
                "recommendation_reason": "AI 창작",
                "priority_score": 9 - i
            } for i in range(6)
        ]

        state: RecommendState = {
            "accumulated_candidates": target_pool,
            "candidate_quests": target_pool,
            "recommended_quests": []
        }

        res = format_response(state)
        recommended = res.get("recommended_quests", [])

        self.assertEqual(len(recommended), 5)
        self.assertEqual(recommended[0]["quest_type"], "VOLUNTEER")
        self.assertEqual(recommended[0]["quest_title"], "실제 한강 봉사활동")
        self.assertEqual(len([q for q in recommended if q["quest_type"] == "GOOD_DEED"]), 4)

if __name__ == "__main__":
    unittest.main()