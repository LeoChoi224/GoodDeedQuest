import unittest
from fastapi.testclient import TestClient
from backend.main import app


class TestShopItemListAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_get_shop_items_success(self):
        """GET /api/v1/shop 상품 목록 조회 및 시드 자동적재 200 OK 검증"""
        response = self.client.get("/api/v1/shop")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data["success"])
        self.assertGreaterEqual(len(json_data["data"]), 3)

    def test_get_shop_item_detail_success(self):
        """GET /api/v1/shop/{item_id} 동적 ID 추출을 통한 단일 상품 상세 조회 200 OK 검증"""
        # 1. 목록 조회를 실행하여 시드 데이터 획득 및 동적 PK 추출
        list_response = self.client.get("/api/v1/shop")
        self.assertEqual(list_response.status_code, 200)
        items = list_response.json()["data"]
        self.assertGreater(len(items), 0)

        # 2. 첫 번째 실제 상품의 PK로 상세 조회 수행
        target_id = items[0]["item_id"]
        response = self.client.get(f"/api/v1/shop/{target_id}")

        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data["success"])
        self.assertEqual(json_data["data"]["item_id"], target_id)

    def test_get_shop_item_detail_not_found(self):
        """GET /api/v1/shop/99999 존재하지 않는 ID 조회 시 404 예외 검증"""
        response = self.client.get("/api/v1/shop/99999")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()