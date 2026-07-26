from typing import List
from fastapi import HTTPException, status
from backend.app.common.repository import DatabaseRepository
from backend.app.shop.models import Item


def get_active_items(item_repo: DatabaseRepository[Item]) -> List[Item]:
    """
    상점에 노출 활성화(is_active == True)된 모든 상품 목록을 조회합니다.
    """
    return item_repo.filter(Item.is_active == True)


def get_item_by_id(item_repo: DatabaseRepository[Item], item_id: int) -> Item:
    """
    단일 상품 식별자(item_id)로 상품 상세 정보를 조회하며, 없거나 비활성화된 경우 404 예외를 발생시킵니다.
    """
    item = item_repo.get_by(item_id=item_id, is_active=True)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"상품 ID {item_id}번 상품을 찾을 수 없거나 현재 판매 중이 아닙니다.",
        )
    return item