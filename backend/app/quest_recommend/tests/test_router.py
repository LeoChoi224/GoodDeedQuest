import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from backend.main import app
from backend.app.common.auth import get_current_user
from backend.app.common.tests.factories import create_test_user, delete_test_user

class TestBackendQuestRecommendRouter(unittest.TestCase):
    def setUp(self):
        # 라우터가 응답을 돌려주면서 추천 로그를 DB에 남긴다.
        # 존재하지 않는 user_id 면 그 적재가 외래키 위반으로 실패한다.
        self.test_user_id = create_test_user()

        app.dependency_overrides[get_current_user] = lambda: {
            "id": self.test_user_id,
            "email": "test@example.com",
            "level": 3
        }
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()
        delete_test_user(self.test_user_id)

    @patch("httpx.AsyncClient.post")
    def test_recommend_quests_success(self, mock_post):
        """AI 서비스 연동 성공 시 정상 200 OK 및 success: True 검증"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "message": "Quest recommendations successfully generated.",
            "data": [
                {
                    # quest_id 를 넣지 않는다. 값을 넣으면 service 가
                    # "그 ID의 퀘스트가 이미 있으면 재사용"하는 분기를 타서
                    # (service.py:167) DB에 우연히 같은 ID가 있을 때
                    # 그 퀘스트의 제목이 응답에 실려 나온다.
                    "quest_title": "Vulnerable Group Support",
                    "quest_description": "Delivering food packages for elderly people.",
                    "quest_type": "VOLUNTEER",
                    "reason": "Matches user interest in vulnerable groups",
                    "category_name": "VOLUNTEER"
                }
            ]
        }
        mock_post.return_value = mock_response

        payload = {"interests": ["VOLUNTEER"]}
        response = self.client.post("/api/v1/quest-recommend", json=payload)
        
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data.get("success"))
        self.assertEqual(json_data["data"][0]["quest_title"], "Vulnerable Group Support")

    @patch("httpx.AsyncClient.post")
    def test_recommend_quests_failure(self, mock_post):
        """AI 서비스 연동 에러 시 APIResponse.fail (success: False) 리턴 검증"""
        mock_post.side_effect = Exception("Connection Timeout")

        payload = {"interests": ["ENVIRONMENT"]}
        response = self.client.post("/api/v1/quest-recommend", json=payload)
        
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        # AI 서버 연결 실패 시 success: False 반환 확인
        self.assertFalse(json_data.get("success"))
        self.assertIn("장애", json_data.get("message"))

if __name__ == "__main__":
    unittest.main()