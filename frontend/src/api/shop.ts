import api from './client';

export interface ShopItem {
  item_id: number;
  name: string;
  description: string;
  price_point: number;
  image_url: string;
  is_active: boolean;
  is_equipped: boolean;
  created_at: string;
  updated_at: string;
}

export interface PurchaseRecord {
  purchase_id: number;
  user_id: number;
  item_id: number;
  status: string;
  purchased_at: string;
  item: ShopItem;
}

/**
 * 상점 활성 상품 목록 조회 API (GET /api/v1/shop)
 */
export const getShopItems = async (): Promise<ShopItem[]> => {
  const response = await api.get('/shop');
  return response.data.data;
};

/**
 * 단일 상품 상세 조회 API (GET /api/v1/shop/{item_id})
 */
export const getItemDetail = async (itemId: number): Promise<ShopItem> => {
  const response = await api.get(`/shop/${itemId}`);
  return response.data.data;
};

/**
 * 아이템 구매 처리 API (POST /api/v1/shop/purchase)
 */
export const purchaseShopItem = async (itemId: number): Promise<PurchaseRecord> => {
  const response = await api.post('/shop/purchase', { item_id: itemId });
  return response.data.data;
};

/**
 * 사용자 구매 내역 목록 조회 API (GET /api/v1/shop/purchases)
 */
export const getPurchaseHistory = async (): Promise<PurchaseRecord[]> => {
  const response = await api.get('/shop/purchases');
  return response.data.data;
};