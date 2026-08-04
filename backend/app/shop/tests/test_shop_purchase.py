import unittest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.main import app
from backend.app.common.database import SessionLocal
from backend.app.common.auth import get_current_user
from backend.app.auth.models import PointTransaction
from backend.app.shop.models import Purchase


# 유저 ID 2번 계정을 강제로 반환하는 테스트용 의존성 오버라이드 함수
def override_get_current_user_id2():
    return {"id": 2, "email": "user2@example.com", "name": "테스트유저2"}


class TestShopPurchaseAPI(unittest.TestCase):
    def setUp(self):
        # get_current_user 의존성을 유저 ID 2번으로 오버라이딩
        app.dependency_overrides[get_current_user] = override_get_current_user_id2
        self.client = TestClient(app)
        self.db: Session = SessionLocal()

        # 자식 테이블(PointTransaction) ➡️ 부모 테이블(Purchase) 순서로 안전하게 초기화
        self.db.query(PointTransaction).filter(PointTransaction.user_id == 2).delete()
        self.db.query(Purchase).filter(Purchase.user_id == 2).delete()
        self.db.commit()

        # 상점 목록 조회를 통한 동적 target_item_id 획득
        list_res = self.client.get("/api/v1/shop")
        self.assertEqual(list_res.status_code, 200)
        items = list_res.json()["data"]
        self.assertGreater(len(items), 0)
        self.target_item_id = items[0]["item_id"]

    def tearDown(self):
        app.dependency_overrides.clear()
        self.db.close()

    def test_purchase_item_success(self):
        """POST /api/v1/shop/purchase 유저 ID 2번 계정 정상 아이템 구매 200 OK 검증"""
        payload = {"item_id": self.target_item_id}
        response = self.client.post("/api/v1/shop/purchase", json=payload)

        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data["success"])
        self.assertEqual(json_data["data"]["user_id"], 2)
        self.assertEqual(json_data["data"]["item_id"], self.target_item_id)
        self.assertEqual(json_data["data"]["status"], "COMPLETED")

    def test_purchase_item_not_found_fail(self):
        """POST /api/v1/shop/purchase 존재하지 않는 item_id 99999 구매 요청 시 404 예외 검증"""
        payload = {"item_id": 99999}
        response = self.client.post("/api/v1/shop/purchase", json=payload)
        self.assertEqual(response.status_code, 404)

    def test_purchase_item_duplicate_fail(self):
        """POST /api/v1/shop/purchase 유저 ID 2번 계정 동일 아이템 중복 구매 시 400 Bad Request 예외 검증"""
        payload = {"item_id": self.target_item_id}

        # 1차 정상 구매
        first_res = self.client.post("/api/v1/shop/purchase", json=payload)
        self.assertEqual(first_res.status_code, 200)

        # 2차 동일 아이템 중복 구매 ➡️ 400 Bad Request 검증
        second_res = self.client.post("/api/v1/shop/purchase", json=payload)
        self.assertEqual(second_res.status_code, 400)
        json_data = second_res.json()
        self.assertIn("이미 구매하여 보유 중인 아이템입니다.", json_data.get("detail", ""))


if __name__ == "__main__":
    unittest.main()