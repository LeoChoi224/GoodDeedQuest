import unittest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.main import app
from backend.app.common.database import SessionLocal
from backend.app.common.auth import get_current_user
from backend.app.common.tests.factories import create_test_user, delete_test_user
from backend.app.auth.models import User, PointTransaction
from backend.app.auth.enums import TransactionType
from backend.app.shop.models import Purchase, Item



class TestShopE2EIntegration(unittest.TestCase):
    def setUp(self):
        # 1. get_current_user 의존성을 유저 ID 2번으로 오버라이딩
        # 예전에는 user_id=2 를 그대로 썼다. 그 유저가 없는 환경(빈 DB, CI)에서는
        # 구매 적재가 전부 외래키 위반으로 실패했다.
        self.test_user_id = create_test_user(point_balance=10000)

        app.dependency_overrides[get_current_user] = lambda: {
            "id": self.test_user_id,
            "email": "pytest@example.com",
            "name": "테스트유저",
        }
        self.client = TestClient(app)
        self.db: Session = SessionLocal()

        # 포인트 10,000P 는 create_test_user 에서 이미 넣었다.
        # 아래 삭제는 새 유저라 지울 게 없지만, 혹시 이전 실행이 남긴 게 있어도
        # 안전하도록 자식(PointTransaction) -> 부모(Purchase) 순서로 정리한다.
        self.db.query(PointTransaction).filter(PointTransaction.user_id == self.test_user_id).delete()
        self.db.query(Purchase).filter(Purchase.user_id == self.test_user_id).delete()
        self.db.commit()

    def tearDown(self):
        app.dependency_overrides.clear()
        self.db.close()
        delete_test_user(self.test_user_id)

    def test_shop_e2e_full_flow(self):
        """
        상점 전 생애주기 E2E 통합 시나리오 테스트:
        시드 확인/목록 조회 ➡️ 상세 조회 ➡️ 아이템 구매 ➡️ 잔액 차감 & 원장 정합성 DB 검증 ➡️ 구매 내역 확인 ➡️ 중복 구매 차단 예외 검증
        """
        # =========================================================================
        # 1단계: 상점 상품 목록 조회 (GET /api/v1/shop) & 시드 자동 적재 검증
        # =========================================================================
        list_response = self.client.get("/api/v1/shop")
        self.assertEqual(list_response.status_code, 200)
        list_json = list_response.json()
        self.assertTrue(list_json["success"])

        items = list_json["data"]
        self.assertGreaterEqual(len(items), 3)

        # 구매 테스트 대상 첫 번째 아이템 선택
        target_item = items[0]
        target_item_id = target_item["item_id"]
        target_price = target_item["price_point"]

        # =========================================================================
        # 2단계: 상품 상세 조회 (GET /api/v1/shop/{item_id}) 검증
        # =========================================================================
        detail_response = self.client.get(f"/api/v1/shop/{target_item_id}")
        self.assertEqual(detail_response.status_code, 200)
        detail_json = detail_response.json()
        self.assertTrue(detail_json["success"])
        self.assertEqual(detail_json["data"]["name"], target_item["name"])
        self.assertEqual(detail_json["data"]["price_point"], target_price)

        # =========================================================================
        # 3단계: 아이템 구매 실행 (POST /api/v1/shop/purchase) 검증
        # =========================================================================
        purchase_payload = {"item_id": target_item_id}
        buy_response = self.client.post("/api/v1/shop/purchase", json=purchase_payload)
        self.assertEqual(buy_response.status_code, 200)
        buy_json = buy_response.json()
        self.assertTrue(buy_json["success"])
        self.assertEqual(buy_json["data"]["user_id"], self.test_user_id)
        self.assertEqual(buy_json["data"]["item_id"], target_item_id)
        self.assertEqual(buy_json["data"]["status"], "COMPLETED")

        # =========================================================================
        # 4단계: 유저 포인트 잔액 차감 & PointTransaction 원장 DB 정합성 100% 검증
        # =========================================================================
        # DB 직조회를 통해 잔액 및 원장 데이터 확인.
        # 구매 API 가 다른 세션에서 커밋했으므로 이 세션의 캐시를 비우고 다시 읽는다.
        self.db.expire_all()
        user_in_db = self.db.get(User, self.test_user_id)
        expected_balance = 10000 - target_price
        self.assertEqual(user_in_db.point_balance, expected_balance)

        # 최신 생성된 거래 원장 레코드 조회
        latest_tx = (
            self.db.query(PointTransaction)
            .filter(PointTransaction.user_id == self.test_user_id)
            .order_by(PointTransaction.transaction_id.desc())
            .first()
        )
        self.assertIsNotNone(latest_tx)
        self.assertEqual(latest_tx.amount, target_price)
        self.assertEqual(latest_tx.type, TransactionType.SPEND)
        self.assertEqual(latest_tx.balance_after, expected_balance)

        # =========================================================================
        # 5단계: 구매 내역 조회 (GET /api/v1/shop/purchases) 연동 검증
        # =========================================================================
        history_response = self.client.get("/api/v1/shop/purchases")
        self.assertEqual(history_response.status_code, 200)
        history_json = history_response.json()
        self.assertTrue(history_json["success"])

        purchases = history_json["data"]
        self.assertGreaterEqual(len(purchases), 1)
        self.assertEqual(purchases[0]["item_id"], target_item_id)
        self.assertEqual(purchases[0]["item"]["name"], target_item["name"])

        # =========================================================================
        # 6단계: 동일 아이템 중복 구매 시도 시 400 Bad Request 예외 차단 검증
        # =========================================================================
        duplicate_response = self.client.post("/api/v1/shop/purchase", json=purchase_payload)
        self.assertEqual(duplicate_response.status_code, 400)
        self.assertIn("이미 구매하여 보유 중인 아이템입니다.", duplicate_response.json().get("detail", ""))


if __name__ == "__main__":
    unittest.main()