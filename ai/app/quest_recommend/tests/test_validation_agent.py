import unittest
from unittest.mock import patch
from ai.app.quest_recommend.state import RecommendState
from ai.app.quest_recommend.nodes.validation_agent import validate_candidates

class TestValidationAgent(unittest.TestCase):
    def test_validate_candidates_lcel_critic_success(self):
        """실제 비평가 LLM이 제약조건에 맞춰 실외 퀘스트를 올바르게 필터링하는지 검증"""
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
            "user_profile": {
                "interests": ["환경"],
                "target_difficulty": "NORMAL"
            },
            "situation_context": {
                "today_weather": "rainy",
                "is_outdoor_feasible": False  # 야외 불가 상황
            },
            "request_context": {},
            "recommendation_strategy": {
                "strategy": "Suggest indoor tasks due to rain.",
                "llm_constraints": ["must be indoor", "실내 활동 필수"]
            },
            "retrieved_volunteers": [],
            "candidate_quests": [
                # 1. 실내 환경 선행 (통과 대상)
                {
                    "category_name": "환경",
                    "quest_title": "일회용 컵 대신 개인 텀블러 사용하기",
                    "quest_description": "카페 방문 시 텀블러를 사용하여 플라스틱을 절약합니다.",
                    "quest_target": "SOLO",
                    "quest_type": "GOOD_DEED",
                    "location": None,
                    "difficulty": "VERY_EASY",
                    "estimated_duration": 5
                },
                # 2. 야외 공원 청소 봉사 (location이 있고 야외 활동이므로 반려 대상)
                {
                    "category_name": "환경",
                    "quest_title": "공원 환경 미화 쓰레기 줍기 봉사",
                    "quest_description": "야외 한강 공원에서 집게로 쓰레기를 수거합니다.",
                    "quest_target": "SOLO",
                    "quest_type": "VOLUNTEER",
                    "location": "서울시 마포구 한강공원",
                    "difficulty": "NORMAL",
                    "estimated_duration": 120
                }
            ],
            "retry_count": 0,
            "recommended_quests": []
        }
        
        result = validate_candidates(mock_state)
        valid = result.get("candidate_quests")
        
        self.assertIsNotNone(valid)
        self.assertIsInstance(valid, list)
        # 야외 봉사활동 1개는 반려되고 실내 텀블러 1개만 합격해야 함
        self.assertEqual(len(valid), 1)
        self.assertEqual(valid[0]["quest_title"], "일회용 컵 대신 개인 텀블러 사용하기")

    @patch("ai.app.quest_recommend.validation_agent.get_openai_model")
    def test_validate_candidates_lcel_critic_fallback(self, mock_get_openai):
        """비평가 API 통신 에러 발생 시, 1차 기계적 필터링 결과물로 안전하게 대체되는지 검증"""
        mock_get_openai.side_effect = Exception("OpenAI Server Error")
        
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
            "request_message": None,
            "user_profile": {},
            "situation_context": {},
            "request_context": {},
            "recommendation_strategy": {},
            "retrieved_volunteers": [],
            "candidate_quests": [
                {
                    "category_name": "환경",
                    "quest_title": "방 불 끄기",
                    "quest_description": "안 쓰는 방 불을 꺼 에너지를 절약합니다.",
                    "quest_target": "SOLO",
                    "quest_type": "GOOD_DEED",
                    "location": None,
                    "difficulty": "VERY_EASY",
                    "estimated_duration": 5
                }
            ],
            "retry_count": 0,
            "recommended_quests": []
        }
        
        result = validate_candidates(mock_state)
        valid = result.get("candidate_quests")
        
        self.assertIsNotNone(valid)
        # API 오류가 나더라도 Fallback으로 1차 필터링된 원본 퀘스트 1개가 반환되어야 함
        self.assertEqual(len(valid), 1)
        self.assertEqual(valid[0]["quest_title"], "방 불 끄기")

if __name__ == "__main__":
    unittest.main()