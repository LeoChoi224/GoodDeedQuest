import unittest

# User.badges 같은 문자열 참조 relationship을 해석하려면 전체 모델이 먼저 등록돼야 한다
import backend.app.models_registry  # noqa: F401

from backend.app.common.database import SessionLocal
from backend.app.common.tests.factories import create_test_user, delete_test_user
from backend.app.common.enums import Difficulty
from backend.app.quest.models import Category, Quest
from backend.app.quest_recommend.models import AiRecommendation, AiRecommendationLog
from backend.app.quest_recommend.service import save_recommendation_items


class TestRewardFill(unittest.TestCase):
    def setUp(self):
        """DB 세션 초기화 및 검증용 부모 로그 1건 생성"""
        self.session = SessionLocal()
        self.created_quest_ids = []
        self.created_log_ids = []

        # 예전에는 DB에 아무 유저나 있으면 쓰고 없으면 skipTest 로 넘어갔다.
        # 빈 DB(팀원 노트북, CI)에서는 조용히 건너뛰어 아무것도 검증하지 못했다.
        self.test_user_id = create_test_user()

        category = self.session.query(Category).first()
        if not category:
            self.session.close()
            delete_test_user(self.test_user_id)
            self.fail(
                "Category 시드가 없습니다. "
                "python -m backend.app.quest.seed_category 를 먼저 실행하세요."
            )

        log = AiRecommendationLog(
            user_id=self.test_user_id,
            request_context={"interests": ["ENVIRONMENT"]},
            response_context={"success": True}
        )
        self.session.add(log)
        self.session.flush()
        self.created_log_ids.append(log.ai_log_id)
        self.ai_log_id = log.ai_log_id

    def tearDown(self):
        """테스트에서 생성한 로그/퀘스트 정리"""
        if not hasattr(self, "created_log_ids"):
            return

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
        delete_test_user(self.test_user_id)

    def _save_and_fetch(self, items):
        """추천 항목을 저장하고 생성된 Quest 목록을 순서대로 반환하는 헬퍼"""
        saved = save_recommendation_items(
            db=self.session,
            ai_log_id=self.ai_log_id,
            user_id=self.test_user_id,
            recommended_quests=items
        )
        self.session.commit()

        quests = []
        for rec in saved:
            quest = self.session.query(Quest).filter_by(quest_id=rec.quest_id).first()
            self.created_quest_ids.append(quest.quest_id)
            quests.append(quest)
        return quests

    def test_good_deed_reward_from_difficulty_and_intensity(self):
        """EASY 난이도 + 강도 50이면 200P / 80EXP가 저장되는지 검증"""
        quests = self._save_and_fetch([{
            "quest_title": "보상 검증용 일상 선행",
            "quest_description": "테스트용 설명입니다.",
            "quest_type": "GOOD_DEED",
            "category_name": "ENVIRONMENT",
            "difficulty": "EASY",
            "intensity": 50,
            "estimated_duration": 15,
        }])

        self.assertEqual(quests[0].difficulty, Difficulty.EASY)
        self.assertEqual(quests[0].reward_point, 200)
        self.assertEqual(quests[0].reward_exp, 80)

    def test_volunteer_reward_uses_fixed_intensity(self):
        """봉사(NORMAL + 강도 70)는 399P / 160EXP로 저장되는지 검증"""
        quests = self._save_and_fetch([{
            "quest_title": "보상 검증용 봉사활동",
            "quest_description": "테스트용 봉사 요약입니다.",
            "quest_type": "VOLUNTEER",
            "category_name": "VOLUNTEER",
            "location": "서울시 어딘가",
            "center_id": None,
            "difficulty": "NORMAL",
            "intensity": 70,
            "estimated_duration": 180,
        }])

        self.assertEqual(quests[0].difficulty, Difficulty.NORMAL)
        self.assertEqual(quests[0].reward_point, 399)
        self.assertEqual(quests[0].reward_exp, 160)

    def test_unknown_difficulty_falls_back_to_normal(self):
        """AI가 enum에 없는 난이도를 보내도 저장이 롤백되지 않고 NORMAL로 처리되는지 검증"""
        quests = self._save_and_fetch([{
            "quest_title": "알 수 없는 난이도 퀘스트",
            "quest_description": "테스트용 설명입니다.",
            "quest_type": "GOOD_DEED",
            "category_name": "OTHER",
            "difficulty": "MEDIUM",
            "intensity": 50,
        }])

        self.assertEqual(quests[0].difficulty, Difficulty.NORMAL)
        self.assertEqual(quests[0].reward_point, 365)

    def test_intensity_zero_is_not_treated_as_missing(self):
        """강도 0은 유효한 값이므로 기본값 50으로 바뀌지 않고 구간 최솟값이 나오는지 검증"""
        quests = self._save_and_fetch([{
            "quest_title": "강도 0 퀘스트",
            "quest_description": "테스트용 설명입니다.",
            "quest_type": "GOOD_DEED",
            "category_name": "OTHER",
            "difficulty": "NORMAL",
            "intensity": 0,
        }])

        self.assertEqual(quests[0].reward_point, 280)

    def test_missing_intensity_uses_default(self):
        """intensity 필드가 아예 없으면 기본값 50이 적용되는지 검증"""
        quests = self._save_and_fetch([{
            "quest_title": "강도 없는 퀘스트",
            "quest_description": "테스트용 설명입니다.",
            "quest_type": "GOOD_DEED",
            "category_name": "OTHER",
            "difficulty": "NORMAL",
        }])

        self.assertEqual(quests[0].reward_point, 365)


if __name__ == "__main__":
    unittest.main()