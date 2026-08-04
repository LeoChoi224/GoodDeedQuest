import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from backend.main import app
from backend.app.common.auth import get_current_user
from backend.app.common.database import SessionLocal
from backend.app.quest_recommend.models import AiRecommendationLog, AiRecommendation
from backend.app.quest.models import Quest
from backend.app.quest_recommend.service import save_recommendation_log, save_recommendation_items

class TestRecommendationPersistence(unittest.TestCase):
    def setUp(self):
        app.dependency_overrides[get_current_user] = lambda: {
            "id": 1,
            "email": "test@example.com",
            "level": 3
        }
        self.client = TestClient(app)
        self.test_user_id = 1

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_save_recommendation_items_location_based_volunteer(self):
        """location 장소 주소가 존재하는 경우 VOLUNTEER 타입 및 VOLUNTEER 카테고리로 자동 부여되는지 검증"""
        req_context = {"interests": ["ENVIRONMENT"]}
        res_context = {"success": True}
        quests_payload = [
            {
                "quest_title": "마포구 봉사센터 정화 봉사",
                "quest_description": "마포구 환경정화를 진행합니다.",
                "quest_type": "VOLUNTEER",
                "location": "서울시 마포구 월드컵북로 12",
                "recommendation_reason": "실제 봉사활동 추천",
                "category_name": "ENVIRONMENT",
                "priority_score": 10
            }
        ]

        with SessionLocal() as session:
            ai_log_id = save_recommendation_log(session, self.test_user_id, req_context, res_context)
            self.assertIsNotNone(ai_log_id)

            items = save_recommendation_items(session, ai_log_id, self.test_user_id, quests_payload)
            session.commit()

            self.assertEqual(len(items), 1)

            saved_rec = session.query(AiRecommendation).filter_by(ai_log_id=ai_log_id).first()
            self.assertIsNotNone(saved_rec)
            self.assertEqual(saved_rec.recommendation_type, "VOLUNTEER")

            saved_quest = session.query(Quest).filter_by(quest_id=saved_rec.quest_id).first()
            self.assertIsNotNone(saved_quest)
            self.assertEqual(saved_quest.quest_title, "마포구 봉사센터 정화 봉사")
            self.assertEqual(saved_quest.location, "서울시 마포구 월드컵북로 12")

            # 테스트 데이터 정돈
            session.delete(saved_rec)
            session.delete(saved_quest)
            session.query(AiRecommendationLog).filter_by(ai_log_id=ai_log_id).delete()
            session.commit()

    @patch("httpx.AsyncClient.post")
    def test_recommend_api_persistence_e2e(self, mock_post):
        """추천 API 호출 시 AiRecommendation 및 Quest 원본 DB 영속화 E2E 검증"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "message": "AI 추천 성공",
            "data": [
                {
                    "quest_title": "AI 일상 텀블러 사용",
                    "quest_description": "텀블러를 씁니다.",
                    "quest_type": "GOOD_DEED",
                    "recommendation_reason": "환경 보호",
                    "category_name": "ENVIRONMENT",
                    "priority_score": 9
                }
            ]
        }
        mock_post.return_value = mock_response

        payload = {"interests": ["ENVIRONMENT"]}
        response = self.client.post("/api/v1/quest-recommend", json=payload)
        self.assertEqual(response.status_code, 200)

        with SessionLocal() as session:
            latest_log = session.query(AiRecommendationLog).filter_by(user_id=self.test_user_id).order_by(AiRecommendationLog.ai_log_id.desc()).first()
            self.assertIsNotNone(latest_log)

            saved_recs = session.query(AiRecommendation).filter_by(ai_log_id=latest_log.ai_log_id).all()
            self.assertGreaterEqual(len(saved_recs), 1)

            # 테스트 데이터 정리
            for rec in saved_recs:
                session.query(Quest).filter_by(quest_id=rec.quest_id).delete()
                session.delete(rec)
            session.delete(latest_log)
            session.commit()

if __name__ == "__main__":
    unittest.main()