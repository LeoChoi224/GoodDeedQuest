import unittest
from unittest.mock import patch

import httpx
import openai
import pytest

from ai.app.quest_recommend.state import RecommendState
from ai.app.quest_recommend.nodes.good_deed_agent import create_good_deeds

class TestQuestRecommendationAgent(unittest.TestCase):
    # 이 메서드만 실제 LLM 을 호출한다(실측 12초).
    # 같은 클래스의 Gemini 폴백 테스트는 목을 쓰므로 CI 에서 계속 돈다.
    @pytest.mark.live_llm
    def test_create_good_deeds_normal(self):
        """정상 조건 하에서 6개의 순수 AI 일상 선행(GOOD_DEED) 창작 및 스키마/점수/카테고리 검증"""
        mock_state: RecommendState = {
            "user_id": 1,
            "interests": ["ENVIRONMENT", "ANIMAL"],
            "region_id": 1,
            "latitude": 37.566,
            "longitude": 126.978,
            "level": 3,
            "history_quests": [],
            "recent_recommendations": [],
            "preferred_difficulty": "NORMAL",
            "request_message": None,
            "user_profile": {
                "interests": ["ENVIRONMENT", "ANIMAL"],
                "target_difficulty": "NORMAL",
                "recently_recommended": [],
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
            "retrieved_volunteers": [],
            "ai_good_deeds": [],
            "candidate_quests": [],
            "accumulated_candidates": [],
            "rejection_reasons_en": [],
            "rejection_reasons_ko": [],
            "retry_count": 0,
            "recommended_quests": []
        }
        
        result = create_good_deeds(mock_state)
        ai_good_deeds = result.get("ai_good_deeds")
        
        self.assertIsNotNone(ai_good_deeds)
        self.assertIsInstance(ai_good_deeds, list)
        
        if ai_good_deeds:
            self.assertEqual(len(ai_good_deeds), 6, f"Expected exactly 6 AI good deeds, got {len(ai_good_deeds)}")
            
            for q in ai_good_deeds:
                self.assertIn("category_name", q)
                self.assertIn(q["category_name"], ["ENVIRONMENT", "SHARING", "ANIMAL", "COMMUNITY", "OTHER"])
                self.assertIn("quest_title", q)
                self.assertIn("quest_description", q)
                self.assertIn("quest_target", q)
                self.assertEqual(q["quest_type"], "GOOD_DEED")
                self.assertIsNone(q["location"])
                self.assertIn("recommendation_reason", q)
                self.assertIn("priority_score", q)
                self.assertIsInstance(q["priority_score"], int)
                self.assertTrue(1 <= q["priority_score"] <= 10)
                self.assertIn(q["difficulty"], ["VERY_EASY", "EASY", "NORMAL", "HARD", "VERY_HARD"])
                self.assertIsInstance(q["estimated_duration"], int)

    @patch("ai.app.quest_recommend.nodes.good_deed_agent.get_openai_model")
    @patch("ai.app.quest_recommend.nodes.good_deed_agent.invoke_gemini_fallback")
    def test_create_good_deeds_fallback_to_gemini(self, mock_gemini_fallback, mock_get_openai):
        """OpenAI API 예외 발생 시 무소음 Gemini 백업 모델이 가동되어 6개 후보를 반환하는지 검증"""
        # 실제 연결 시간 초과는 openai.APITimeoutError(= OpenAIError 하위)로 올라온다.
        # good_deed_agent 는 OpenAIError 계열만 잡아서 Gemini 로 넘기므로(good_deed_agent.py:183),
        # 맨 Exception 을 던지면 현실에 없는 경로를 검증하게 된다.
        mock_get_openai.side_effect = openai.APITimeoutError(
            request=httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
        )
        
        class DummyOutput:
            quests = [
                type("Quest", (), {
                    "model_dump": lambda self: {
                        "category_name": "ENVIRONMENT",
                        "quest_title": "Gemini 텀블러 사용하기",
                        "quest_description": "일회용 컵 대신 개인 텀블러를 사용하여 환경 보호 실천하기",
                        "quest_target": "SOLO",
                        "quest_type": "GOOD_DEED",
                        "location": None,
                        "difficulty": "EASY",
                        "estimated_duration": 15,
                        "recommendation_reason": "Gemini 백업 모델 추천 사유",
                        "priority_score": 9
                    }
                })() for _ in range(6)
            ]

        mock_gemini_fallback.return_value = DummyOutput()

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
            "user_profile": {"interests": ["ENVIRONMENT"], "target_difficulty": "NORMAL", "recently_recommended": [], "completed_history": []},
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
        
        result = create_good_deeds(mock_state)
        ai_good_deeds = result.get("ai_good_deeds")
        
        self.assertIsNotNone(ai_good_deeds)
        self.assertEqual(len(ai_good_deeds), 6)
        self.assertEqual(ai_good_deeds[0]["quest_title"], "Gemini 텀블러 사용하기")
        mock_gemini_fallback.assert_called_once()

if __name__ == "__main__":
    unittest.main()