from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import List

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