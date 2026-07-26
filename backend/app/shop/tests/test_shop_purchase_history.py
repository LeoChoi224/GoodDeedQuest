import unittest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.main import app
from backend.app.common.database import SessionLocal
from backend.app.common.auth import get_current_user
from backend.app.auth.models import PointTransaction
from backend.app.shop.models import Purchase


# 유저 ID 2번 계정을 반환하는 테스트용 의존성 오버라이드 함수
def override_get_current_user_id2():
    return {"id": 2, "email": "user2@example.com", "name": "테스트유저2"}


class TestShopPurchaseHistoryAPI(unittest.TestCase):
    def setUp(self):
        app.dependency_overrides[get_current_user] = override_get_current_user_id2
        self.client = TestClient(app)
        self.db: Session = SessionLocal()

        # 기존 유저 ID 2번 데이터 정리 (자식 PointTransaction ➡️ 부모 Purchase 순)
        self.db.query(PointTransaction).filter(PointTransaction.user_id == 2).delete()
        self.db.query(Purchase).filter(Purchase.user_id == 2).delete()
        self.db.commit()

        # 상품 동적 target_item_id 획득
        list_res = self.client.get("/api/v1/shop")
        self.assertEqual(list_res.status_code, 200)
        items = list_res.json()["data"]
        self.assertGreater(len(items), 0)
        self.target_item_id = items[0]["item_id"]

    def tearDown(self):
        app.dependency_overrides.clear()
        self.db.close()

    def test_get_my_purchases_success(self):
        """GET /api/v1/shop/purchases 구매 후 구매 내역 목록 조회 200 OK 검증"""
        # 1. 아이템 1개 구매 진행
        purchase_payload = {"item_id": self.target_item_id}
        buy_res = self.client.post("/api/v1/shop/purchase", json=purchase_payload)
        self.assertEqual(buy_res.status_code, 200)

        # 2. 구매 내역 목록 조회 API 호출
        response = self.client.get("/api/v1/shop/purchases")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data["success"])
        
        # 구매 내역 배열 및 중첩 item 데이터 존재 검증
        purchases = json_data["data"]
        self.assertGreaterEqual(len(purchases), 1)
        self.assertEqual(purchases[0]["item_id"], self.target_item_id)
        self.assertIsNotNone(purchases[0]["item"])
        self.assertEqual(purchases[0]["item"]["item_id"], self.target_item_id)

    def test_get_my_purchases_empty(self):
        """GET /api/v1/shop/purchases 구매 이력이 없을 때 빈 배열 반환 검증"""
        response = self.client.get("/api/v1/shop/purchases")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data["success"])
        self.assertEqual(len(json_data["data"]), 0)


if __name__ == "__main__":
    unittest.main()