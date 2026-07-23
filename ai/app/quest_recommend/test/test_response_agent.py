import unittest
from ai.app.quest_recommend.state import RecommendState
from ai.app.quest_recommend.response_agent import format_response

class TestResponseAgent(unittest.TestCase):
    def test_format_response_sorting_and_slicing(self):
        """합격 후보군을 점수 순으로 내림차순 정렬하고 최종 5개만 골라내는지 검증"""
        mock_state: RecommendState = {
            "user_id": 1,
            "interests": [],
            "region_id": None,
            "latitude": None,
            "longitude": None,
            "level": 1,
            "history_quests": [],
            "recent_recommendations": [],
            "preferred_difficulty": "ANY",
            "request_message": None,
            "user_profile": {},
            "situation_context": {},
            "request_context": {},
            "recommendation_strategy": {},
            "retrieved_volunteers": [],
            "candidate_quests": [
                {"quest_title": "퀘스트A", "priority_score": 5},
                {"quest_title": "퀘스트B", "priority_score": 10},  # 최상위
                {"quest_title": "퀘스트C", "priority_score": 8},
                {"quest_title": "퀘스트D", "priority_score": 3},
                {"quest_title": "퀘스트E", "priority_score": 9},
                {"quest_title": "퀘스트F", "priority_score": 7}   # F와 A는 탈락 대상
            ],
            "retry_count": 0,
            "recommended_quests": []
        }
        
        result = format_response(mock_state)
        recommended = result.get("recommended_quests")
        
        self.assertIsNotNone(recommended)
        self.assertEqual(len(recommended), 5)  # 최대 5개 슬라이싱 검증
        
        # 내림차순 정렬 결과 순서 검증 (10점 -> 9점 -> 8점 -> 7점 -> 5점)
        self.assertEqual(recommended[0]["quest_title"], "퀘스트B")
        self.assertEqual(recommended[1]["quest_title"], "퀘스트E")
        self.assertEqual(recommended[2]["quest_title"], "퀘스트C")
        self.assertEqual(recommended[3]["quest_title"], "퀘스트F")
        self.assertEqual(recommended[4]["quest_title"], "퀘스트A")

    def test_format_response_empty_candidates(self):
        """합격 후보군이 없을 때 안전하게 빈 리스트를 최종 추천 결과로 반환하는지 검증"""
        mock_state: RecommendState = {
            "user_id": 2,
            "interests": [],
            "region_id": None,
            "latitude": None,
            "longitude": None,
            "level": 1,
            "history_quests": [],
            "recent_recommendations": [],
            "preferred_difficulty": "ANY",
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
        
        result = format_response(mock_state)
        recommended = result.get("recommended_quests")
        
        self.assertIsNotNone(recommended)
        self.assertEqual(len(recommended), 0)

if __name__ == "__main__":
    unittest.main()