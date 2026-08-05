import unittest

# User.badges 같은 문자열 참조 relationship을 해석하려면 전체 모델이 먼저 등록돼야 한다
import backend.app.models_registry  # noqa: F401

from fastapi.testclient import TestClient

from backend.main import app
from backend.app.common.auth import get_current_user
from backend.app.common.database import SessionLocal
from backend.app.common.tests.factories import create_test_user, delete_test_user
from backend.app.common.enums import Difficulty
from backend.app.auth.models import User
from backend.app.auth.router import get_current_db_user
from backend.app.quest.enums import QuestSource, QuestStatus, QuestTarget, QuestType
from backend.app.quest.models import Category, Quest, QuestStart
from backend.app.quest.service import started_quest_ids


class TestQuestStart(unittest.TestCase):
    def setUp(self):
        """인증 의존성 Mocking / 검증용 퀘스트 1건 생성"""
        self.session = SessionLocal()
        self.created_quest_ids = []

        # 예전에는 DB에 아무 유저나 있으면 그걸 쓰고, 없으면 skipTest 로 넘어갔다.
        # 빈 DB(팀원 노트북, CI)에서는 조용히 건너뛰어서 아무것도 검증하지 못했다.
        # 이제 테스트가 자기 유저를 만든다.
        self.test_user_id = create_test_user()
        self.test_user = self.session.get(User, self.test_user_id)

        category = self.session.query(Category).first()
        if not category:
            self.session.close()
            delete_test_user(self.test_user_id)
            self.fail(
                "Category 시드가 없습니다. "
                "python -m backend.app.quest.seed_category 를 먼저 실행하세요."
            )

        quest = Quest(
            category_id=category.category_id,
            creator_id=self.test_user_id,
            quest_title="시작 검증용 퀘스트",
            quest_description="테스트용 설명입니다.",
            quest_target=QuestTarget.SOLO,
            quest_type=QuestType.GOOD_DEED,
            quest_source=QuestSource.AI,
            difficulty=Difficulty.NORMAL,
            reward_point=365,
            reward_exp=146,
            quest_status=QuestStatus.NOT_STARTED,
        )
        self.session.add(quest)
        self.session.commit()
        self.created_quest_ids.append(quest.quest_id)
        self.quest_id = quest.quest_id

        app.dependency_overrides[get_current_user] = lambda: {
            "id": self.test_user_id,
            "email": self.test_user.email,
            "level": 3
        }
        app.dependency_overrides[get_current_db_user] = lambda: self.test_user
        self.client = TestClient(app)

    def tearDown(self):
        """생성한 시작 기록과 퀘스트 정리 및 의존성 초기화"""
        if not hasattr(self, "created_quest_ids"):
            return

        for quest_id in self.created_quest_ids:
            for row in self.session.query(QuestStart).filter_by(quest_id=quest_id).all():
                self.session.delete(row)
            quest = self.session.query(Quest).filter_by(quest_id=quest_id).first()
            if quest:
                self.session.delete(quest)
        self.session.commit()
        self.session.close()
        app.dependency_overrides.clear()
        delete_test_user(self.test_user_id)

    def test_start_creates_record_and_returns_in_progress(self):
        """시작 요청이 quest_start에 기록을 남기고 IN_PROGRESS를 반환하는지 검증"""
        response = self.client.post(f"/api/v1/quests/{self.quest_id}/start")

        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data.get("success"))
        self.assertEqual(json_data["data"]["quest_status"], "IN_PROGRESS")

        row = (
            self.session.query(QuestStart)
            .filter_by(user_id=self.test_user_id, quest_id=self.quest_id)
            .first()
        )
        self.assertIsNotNone(row)

    def test_start_twice_is_idempotent(self):
        """같은 퀘스트를 두 번 시작해도 오류 없이 기록이 1건만 남는지 검증"""
        self.client.post(f"/api/v1/quests/{self.quest_id}/start")
        response = self.client.post(f"/api/v1/quests/{self.quest_id}/start")

        self.assertEqual(response.status_code, 200)
        rows = (
            self.session.query(QuestStart)
            .filter_by(user_id=self.test_user_id, quest_id=self.quest_id)
            .all()
        )
        self.assertEqual(len(rows), 1)

    def test_start_unknown_quest_returns_404(self):
        """존재하지 않는 퀘스트를 시작하면 404를 반환하는지 검증"""
        response = self.client.post("/api/v1/quests/99999999/start")
        self.assertEqual(response.status_code, 404)

    def test_started_quest_ids_includes_start_record(self):
        """인증 제출이 없어도 시작 기록만으로 진행중 집합에 포함되는지 검증"""
        self.client.post(f"/api/v1/quests/{self.quest_id}/start")

        result = started_quest_ids(self.session, self.test_user_id)
        self.assertIn(self.quest_id, result)


if __name__ == "__main__":
    unittest.main()