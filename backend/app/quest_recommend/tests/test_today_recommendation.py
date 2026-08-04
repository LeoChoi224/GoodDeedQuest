import unittest
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from backend.main import app
from backend.app.common.auth import get_current_user
from backend.app.common.database import SessionLocal
from backend.app.common.enums import Difficulty
from backend.app.quest.enums import QuestSource, QuestStatus, QuestTarget, QuestType
from backend.app.quest.models import Category, Quest
from backend.app.quest_recommend.models import AiRecommendation, AiRecommendationLog
from backend.app.quest_recommend.service import get_today_recommendation

TEST_USER_ID = 2


class TestTodayRecommendation(unittest.TestCase):
    def setUp(self):
        """인증 의존성 Mocking / TestClient 및 DB 세션 초기화"""
        app.dependency_overrides[get_current_user] = lambda: {
            "id": TEST_USER_ID,
            "email": "user@example.com",
            "level": 3
        }
        self.client = TestClient(app)
        self.session = SessionLocal()
        self.created_quest_ids = []
        self.created_log_ids = []

        category = self.session.query(Category).first()
        self.category_id = category.category_id if category else 1

    def tearDown(self):
        """테스트에서 생성한 로그/퀘스트 정리 및 의존성 초기화"""
        # AiRecommendation은 cascade="all, delete-orphan"으로 로그와 함께 삭제된다
        for log_id in self.created_log_ids:
            log = self.session.query(AiRecommendationLog).filter_by(ai_log_id=log_id).first()
            if log:
                self.session.delete(log)
        self.session.commit()

        for quest_id in self.created_quest_ids:
            quest = self.session.query(Quest).filter_by(quest_id=quest_id).first()
            if quest:
                self.session.delete(quest)
        self.session.commit()

        self.session.close()
        app.dependency_overrides.clear()

    def _create_quest(self, title):
        """검증용 Quest 레코드를 생성하고 정리 대상에 등록하는 헬퍼"""
        quest = Quest(
            category_id=self.category_id,
            creator_id=TEST_USER_ID,
            quest_title=title,
            quest_description="테스트용 추천 퀘스트입니다.",
            quest_target=QuestTarget.SOLO,
            quest_type=QuestType.GOOD_DEED,
            quest_source=QuestSource.AI,
            difficulty=Difficulty.NORMAL,
            estimated_duration=15,
            quest_status=QuestStatus.NOT_STARTED
        )
        self.session.add(quest)
        self.session.flush()
        self.created_quest_ids.append(quest.quest_id)
        return quest

    def _utc_now(self):
        """created_at은 DB 서버 시계(UTC)로 저장되므로 테스트도 동일한 형태로 맞춘다"""
        return datetime.now(timezone.utc).replace(tzinfo=None)

    def _create_log(self, created_at):
        """지정한 생성 일시로 AiRecommendationLog를 적재하는 헬퍼"""
        log = AiRecommendationLog(
            user_id=TEST_USER_ID,
            request_context={"interests": ["ENVIRONMENT"]},
            response_context={"success": True},
            created_at=created_at
        )
        self.session.add(log)
        self.session.flush()
        self.created_log_ids.append(log.ai_log_id)
        return log

    def _create_item(self, ai_log_id, quest, rank):
        """추천 항목(AiRecommendation)을 지정한 순위로 적재하는 헬퍼"""
        item = AiRecommendation(
            ai_log_id=ai_log_id,
            quest_id=quest.quest_id,
            title=quest.quest_title,
            description=quest.quest_description,
            recommendation_type="GOOD_DEED",
            score=10.0,
            reason="테스트 추천 사유",
            rank=rank
        )
        self.session.add(item)
        self.session.flush()

    def test_returns_none_when_user_has_no_log(self):
        """추천 이력이 없는 사용자는 None을 반환하여 신규 생성을 유도하는지 검증"""
        result = get_today_recommendation(db=self.session, user_id=99999999)
        self.assertIsNone(result)

    def test_returns_none_when_latest_log_is_yesterday(self):
        """마지막 추천이 어제 생성된 경우 None을 반환하는지 검증"""
        log = self._create_log(self._utc_now() - timedelta(days=1))
        quest = self._create_quest("어제 추천된 퀘스트")
        self._create_item(log.ai_log_id, quest, rank=1)
        self.session.commit()

        result = get_today_recommendation(db=self.session, user_id=TEST_USER_ID)
        self.assertIsNone(result)

    def test_returns_quests_in_rank_order(self):
        """오늘 추천이 존재하면 rank 오름차순 순서 그대로 반환하는지 검증"""
        log = self._create_log(self._utc_now())
        first = self._create_quest("추천 1순위")
        second = self._create_quest("추천 2순위")
        third = self._create_quest("추천 3순위")

        # 순위와 반대 순서로 적재하여 IN 절 조회 후 재정렬이 실제로 동작하는지 확인한다
        self._create_item(log.ai_log_id, third, rank=3)
        self._create_item(log.ai_log_id, first, rank=1)
        self._create_item(log.ai_log_id, second, rank=2)
        self.session.commit()

        result = get_today_recommendation(db=self.session, user_id=TEST_USER_ID)

        self.assertIsNotNone(result)
        self.assertEqual(
            [quest.quest_title for quest in result],
            ["추천 1순위", "추천 2순위", "추천 3순위"]
        )

    def test_returns_none_when_all_quests_deleted(self):
        """오늘 로그는 있으나 연결된 퀘스트가 전부 삭제된 경우 None을 반환하는지 검증"""
        log = self._create_log(self._utc_now())
        quest = self._create_quest("삭제 처리될 퀘스트")
        self._create_item(log.ai_log_id, quest, rank=1)
        quest.is_deleted = True
        self.session.commit()

        result = get_today_recommendation(db=self.session, user_id=TEST_USER_ID)
        self.assertIsNone(result)

    def test_api_returns_quest_schema_with_quest_id(self):
        """GET /today 응답이 QuestSchema 형태이며 quest_id가 채워져 있는지 E2E 검증"""
        log = self._create_log(self._utc_now())
        quest = self._create_quest("API 응답 검증용 퀘스트")
        self._create_item(log.ai_log_id, quest, rank=1)
        self.session.commit()

        response = self.client.get("/api/v1/quest-recommend/today")

        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data.get("success"))
        self.assertIsNotNone(json_data.get("data"))

        titles = [item["quest_title"] for item in json_data["data"]]
        self.assertIn("API 응답 검증용 퀘스트", titles)

        # 프론트가 상세 화면으로 이동하려면 quest_id가 반드시 있어야 한다
        for item in json_data["data"]:
            self.assertIsNotNone(item["quest_id"])
            self.assertIn("category_code", item)
            self.assertIn("difficulty", item)


if __name__ == "__main__":
    unittest.main()