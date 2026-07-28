import unittest

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.main import app
from backend.app.common.database import SessionLocal
from backend.app.common.auth import get_current_user
from backend.app.badge.models import Badge, UserBadge

# 테스트로 생성한 임시 배지를 식별/정리하기 위한 마커
TEST_BADGE_CATEGORY = "TEST_BADGE_167"

# 유저 ID 1번 계정을 강제로 반환하는 테스트용 의존성 오버라이드 함수
# (DB에 실제 존재하는 유일한 유저: user_id=1, test@naver.com)
def override_get_current_user_id1():
    return {"id": 1, "email": "test@naver.com", "name": "테스트유저1"}


class TestBadgeE2EIntegration(unittest.TestCase):
    def setUp(self):
        app.dependency_overrides[get_current_user] = override_get_current_user_id1
        self.client = TestClient(app)
        self.db: Session = SessionLocal()

        # 이전 실패한 테스트 실행 등으로 남아있을 수 있는 잔여 테스트 데이터 정리
        self._cleanup_test_data()

        # 테스트용 배지 3개 생성: A, B는 유저가 보유, C는 유저가 보유하지 않음
        self.badge_a = Badge(
            name="테스트배지A",
            description="통합 테스트용 배지 A",
            icon_url="https://example.com/badge_a.png",
            badge_category=TEST_BADGE_CATEGORY,
            # ⭐ 수정: condition_category/condition_count NOT NULL 컬럼 추가로 인한 값 지정
            condition_category=TEST_BADGE_CATEGORY,
            condition_count=1,
        )
        self.badge_b = Badge(
            name="테스트배지B",
            description="통합 테스트용 배지 B",
            icon_url="https://example.com/badge_b.png",
            badge_category=TEST_BADGE_CATEGORY,
            condition_category=TEST_BADGE_CATEGORY,
            condition_count=1,
        )
        self.badge_c = Badge(
            name="테스트배지C(미보유)",
            description="통합 테스트용 배지 C - 유저가 보유하지 않음",
            icon_url="https://example.com/badge_c.png",
            badge_category=TEST_BADGE_CATEGORY,
            condition_category=TEST_BADGE_CATEGORY,
            condition_count=1,
        )
        self.db.add_all([self.badge_a, self.badge_b, self.badge_c])
        self.db.commit()
        self.db.refresh(self.badge_a)
        self.db.refresh(self.badge_b)
        self.db.refresh(self.badge_c)

    def tearDown(self):
        self._cleanup_test_data()
        app.dependency_overrides.clear()
        self.db.close()

    def _cleanup_test_data(self):
        """TEST_BADGE_CATEGORY로 마킹된 테스트 전용 Badge/UserBadge 데이터를 정리한다."""
        test_badge_ids = [
            row.badge_id
            for row in self.db.query(Badge.badge_id)
            .filter(Badge.badge_category == TEST_BADGE_CATEGORY)
            .all()
        ]
        if test_badge_ids:
            self.db.query(UserBadge).filter(UserBadge.badge_id.in_(test_badge_ids)).delete(
                synchronize_session=False
            )
            self.db.query(Badge).filter(Badge.badge_id.in_(test_badge_ids)).delete(
                synchronize_session=False
            )
            self.db.commit()

    def test_badge_e2e_full_flow(self):
        """
        Badge 도메인 전 생애주기 E2E 통합 시나리오 테스트:
        미보유 상태 도감 조회 -> 배지 부여 후 내 배지함 조회 -> 장착 -> 재장착(자동 해제) ->
        해제 -> 존재하지 않는/미보유/미장착 배지 대상 404 검증
        """
        # =========================================================================
        # 1. 배지 미보유 상태에서 GET /badges -> 테스트 배지 3개 모두 is_owned=false
        # =========================================================================
        list_response = self.client.get("/api/v1/badges")
        self.assertEqual(list_response.status_code, 200)
        list_json = list_response.json()
        self.assertTrue(list_json["success"])

        badges_by_id = {b["badge_id"]: b for b in list_json["data"]}
        for badge_id in (self.badge_a.badge_id, self.badge_b.badge_id, self.badge_c.badge_id):
            self.assertIn(badge_id, badges_by_id)
            self.assertFalse(badges_by_id[badge_id]["is_owned"])

        # =========================================================================
        # 2. 유저(user_id=1)에게 배지 A, B를 UserBadge로 부여(테스트용) 후 GET /badges/my 확인
        #    (배지 C는 의도적으로 부여하지 않음 - 이후 "미보유 배지" 시나리오에 사용)
        # =========================================================================
        user_badge_a = UserBadge(user_id=1, badge_id=self.badge_a.badge_id, is_equipped=False)
        user_badge_b = UserBadge(user_id=1, badge_id=self.badge_b.badge_id, is_equipped=False)
        self.db.add_all([user_badge_a, user_badge_b])
        self.db.commit()

        my_response = self.client.get("/api/v1/badges/my")
        self.assertEqual(my_response.status_code, 200)
        my_json = my_response.json()
        self.assertTrue(my_json["success"])

        my_badges_by_id = {b["badge_id"]: b for b in my_json["data"]}
        self.assertIn(self.badge_a.badge_id, my_badges_by_id)
        self.assertIn(self.badge_b.badge_id, my_badges_by_id)
        self.assertNotIn(self.badge_c.badge_id, my_badges_by_id)
        self.assertFalse(my_badges_by_id[self.badge_a.badge_id]["is_equipped"])
        self.assertIsNotNone(my_badges_by_id[self.badge_a.badge_id]["awarded_at"])

        # =========================================================================
        # 3. PATCH /badges/{badge_a}/equip -> badge_a is_equipped=true
        # =========================================================================
        equip_a_response = self.client.patch(f"/api/v1/badges/{self.badge_a.badge_id}/equip")
        self.assertEqual(equip_a_response.status_code, 200)
        equip_a_json = equip_a_response.json()
        self.assertTrue(equip_a_json["success"])
        self.assertTrue(equip_a_json["data"]["is_equipped"])
        self.assertEqual(equip_a_json["data"]["badge_id"], self.badge_a.badge_id)

        self.db.refresh(user_badge_a)
        self.db.refresh(user_badge_b)
        self.assertTrue(user_badge_a.is_equipped)
        self.assertFalse(user_badge_b.is_equipped)

        # =========================================================================
        # 4. PATCH /badges/{badge_b}/equip -> badge_a는 자동 해제, badge_b만 true
        # =========================================================================
        equip_b_response = self.client.patch(f"/api/v1/badges/{self.badge_b.badge_id}/equip")
        self.assertEqual(equip_b_response.status_code, 200)
        equip_b_json = equip_b_response.json()
        self.assertTrue(equip_b_json["data"]["is_equipped"])
        self.assertEqual(equip_b_json["data"]["badge_id"], self.badge_b.badge_id)

        self.db.refresh(user_badge_a)
        self.db.refresh(user_badge_b)
        self.assertFalse(user_badge_a.is_equipped)
        self.assertTrue(user_badge_b.is_equipped)

        equipped_count = (
            self.db.query(UserBadge)
            .filter(UserBadge.user_id == 1, UserBadge.is_equipped == True)
            .count()
        )
        self.assertEqual(equipped_count, 1)

        # =========================================================================
        # 5. PATCH /badges/{badge_b}/unequip -> 완전히 미장착(0개) 상태
        # =========================================================================
        unequip_response = self.client.patch(f"/api/v1/badges/{self.badge_b.badge_id}/unequip")
        self.assertEqual(unequip_response.status_code, 200)
        unequip_json = unequip_response.json()
        self.assertFalse(unequip_json["data"]["is_equipped"])

        equipped_count_after_unequip = (
            self.db.query(UserBadge)
            .filter(UserBadge.user_id == 1, UserBadge.is_equipped == True)
            .count()
        )
        self.assertEqual(equipped_count_after_unequip, 0)

        # =========================================================================
        # 6. 존재하지 않는 badge_id로 equip/unequip 시도 -> 404
        # =========================================================================
        nonexistent_badge_id = 999_999_999
        equip_nonexistent_response = self.client.patch(
            f"/api/v1/badges/{nonexistent_badge_id}/equip"
        )
        self.assertEqual(equip_nonexistent_response.status_code, 404)

        unequip_nonexistent_response = self.client.patch(
            f"/api/v1/badges/{nonexistent_badge_id}/unequip"
        )
        self.assertEqual(unequip_nonexistent_response.status_code, 404)

        # =========================================================================
        # 7. 보유하지 않은 badge_id(badge_c)로 equip 시도 -> 404
        # =========================================================================
        equip_not_owned_response = self.client.patch(f"/api/v1/badges/{self.badge_c.badge_id}/equip")
        self.assertEqual(equip_not_owned_response.status_code, 404)
        self.assertIn("보유하지 않은 배지", equip_not_owned_response.json().get("detail", ""))

        # =========================================================================
        # 8. 미장착 상태에서 unequip 시도(badge_a: 보유하지만 현재 미장착) -> 404
        # =========================================================================
        unequip_not_equipped_response = self.client.patch(
            f"/api/v1/badges/{self.badge_a.badge_id}/unequip"
        )
        self.assertEqual(unequip_not_equipped_response.status_code, 404)
        self.assertIn("장착된 배지가 아닙니다", unequip_not_equipped_response.json().get("detail", ""))


if __name__ == "__main__":
    unittest.main()
