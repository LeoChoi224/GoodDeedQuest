from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict

from backend.app.shop.enums import PurchaseStatus

class ItemResponse(BaseModel):
    """단일 상품 상세 조회 응답 DTO"""
    model_config = ConfigDict(from_attributes=True)
    item_id: int
    name: str
    description: str
    price_point: int
    image_url: str
    is_active: bool
    is_equipped: bool
    created_at: datetime
    updated_at: datetime

class ItemListResponse(BaseModel):
    """상점 상품 목록 조회 응답 DTO"""
    items: List[ItemResponse]
    total_count: int

class PurchaseCreate(BaseModel):
    """아이템 구매 요청 DTO"""
    item_id: int

class PurchaseResponse(BaseModel):
    """아이템 구매 완료 응답 DTO"""
    model_config = ConfigDict(from_attributes=True)
    purchase_id: int
    user_id: int
    item_id: int
    status: PurchaseStatus
    purchased_at: datetime
    item: ItemResponse

    
