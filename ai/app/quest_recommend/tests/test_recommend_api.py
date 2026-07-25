import unittest
from fastapi.testclient import TestClient

from ai.main import app

class TestQuestRecommendAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_recommend_quests_api_success(self):
        """/ai/recommend 엔드포인트 정상 작동 테스트 (VOLUNTEER 영문 규격 검증)"""
        payload = {
            "user_id": 1,
            "interests": ["VOLUNTEER", "ENVIRONMENT"],
            "region_id": 1,
            "latitude": 37.5665,
            "longitude": 126.9780,
            "level": 3,
            "history_quests": [],
            "recent_recommendations": [],
            "preferred_difficulty": "NORMAL",
            "request_message": "실내 퀘스트 원해"
        }

        response = self.client.post("/ai/recommend", json=payload)
        self.assertEqual(response.status_code, 200)
        
        json_data = response.json()
        self.assertTrue(json_data.get("success"))
        self.assertIsNotNone(json_data.get("data"))
        self.assertGreaterEqual(len(json_data.get("data")), 1)
        
        # 필드명 검증 (quest_title, quest_description)
        first_quest = json_data["data"][0]
        self.assertIn("quest_title", first_quest)
        self.assertIn("quest_description", first_quest)

    def test_recommend_quests_validation_error(self):
        """user_id 누락 시 422 validation error 검증"""
        invalid_payload = {"interests": ["VOLUNTEER"]}
        response = self.client.post("/ai/recommend", json=invalid_payload)
        self.assertEqual(response.status_code, 422)

if __name__ == "__main__":
    unittest.main()