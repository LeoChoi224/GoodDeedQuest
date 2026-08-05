import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from backend.main import app
from backend.app.common.auth import get_current_user
from backend.app.common.database import SessionLocal, get_db
from backend.app.common.tests.factories import create_test_user, delete_test_user
from backend.app.quest_recommend.models import AiRecommendationLog
from backend.app.quest_recommend.service import save_recommendation_log

class TestAiRecommendationLogging(unittest.TestCase):
    def setUp(self):
        """테스트 전용 유저 생성 / 인증 의존성 Mocking / TestClient 초기화"""
        # 예전에는 "DB에 user_id=1 이 있다"고 가정했다. 그 유저가 사라지자
        # 로그 적재가 전부 외래키 위반으로 실패했다. 이제 스스로 만든다.
        self.test_user_id = create_test_user()

        app.dependency_overrides[get_current_user] = lambda: {
            "id": self.test_user_id,
            "email": "test@example.com",
            "level": 3
        }
        self.client = TestClient(app)

    def tearDown(self):
        """의존성 초기화 및 테스트 유저 정리"""
        app.dependency_overrides.clear()
        delete_test_user(self.test_user_id)

    def test_save_recommendation_log_direct_service(self):
        """service.py의 save_recommendation_log 함수에 DB 세션 주입하여 적재 테스트"""
        req_context = {
            "interests": ["VOLUNTEER", "ENVIRONMENT"],
            "latitude": 37.5665,
            "longitude": 126.9780,
            "level": 3,
            "request_message": "실내 활동 추천"
        }
        res_context = {
            "success": True,
            "message": "추천 완료",
            "data": [
                {
                    "quest_title": "지역사회 도시락 배달",
                    "quest_description": "도시락을 전달합니다.",
                    "quest_type": "VOLUNTEER",
                    "reason": "지역사회 관심사 매칭",
                    "category_name": "VOLUNTEER"
                }
            ]
        }

        with SessionLocal() as session:
            ai_log_id = save_recommendation_log(
                db=session,
                user_id=self.test_user_id,
                request_context=req_context,
                response_context=res_context
            )
            session.commit()

            self.assertIsNotNone(ai_log_id)

            saved_log = session.query(AiRecommendationLog).filter_by(ai_log_id=ai_log_id).first()
            self.assertIsNotNone(saved_log)
            self.assertEqual(saved_log.user_id, self.test_user_id)
            self.assertEqual(saved_log.request_context["interests"], ["VOLUNTEER", "ENVIRONMENT"])
            
            session.delete(saved_log)
            session.commit()

    @patch("httpx.AsyncClient.post")
    def test_recommend_api_logging_integration(self, mock_post):
        """추천 API 호출 시 get_db()를 통해 DB ai_recommendation_log 테이블에 로그가 정상 적재되는지 E2E 검증"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "message": "AI 추천 성공",
            "data": [
                {
                    "quest_title": "환경정화 플로깅",
                    "quest_description": "쓰레기를 주웁니다.",
                    "quest_type": "GOOD_DEED",
                    "reason": "환경 보호",
                    "category_name": "ENVIRONMENT"
                }
            ]
        }
        mock_post.return_value = mock_response

        payload = {
            "interests": ["ENVIRONMENT"],
            "request_message": "DB 로깅 E2E 테스트"
        }

        response = self.client.post("/api/v1/quest-recommend", json=payload)
        self.assertEqual(response.status_code, 200)

        with SessionLocal() as session:
            latest_log = session.query(AiRecommendationLog).filter_by(user_id=self.test_user_id).order_by(AiRecommendationLog.ai_log_id.desc()).first()
            self.assertIsNotNone(latest_log)
            self.assertEqual(latest_log.request_context["request_message"], "DB 로깅 E2E 테스트")

            session.delete(latest_log)
            session.commit()

if __name__ == "__main__":
    unittest.main()