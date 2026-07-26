from typing import List

from fastapi import APIRouter, Depends, status

from backend.app.common.deps import get_repository
from backend.app.common.repository import DatabaseRepository
from backend.app.common.response import APIResponse
from backend.app.shop.models import Item
from backend.app.shop.schemas import ItemResponse
from backend.app.shop.seed import seed_shop_items
from backend.app.shop.service import get_active_items, get_item_by_id

router = APIRouter(prefix="/shop", tags=["Shop"])

@router.get(
    "",
    response_model=APIResponse[List[ItemResponse]],
    status_code=status.HTTP_200_OK,
    summary="상점 상품 목록 조회",
    description="현재 판매 중인 프로필 테두리 아이템 목록을 조회합니다.",
)
def get_shop_items(
    item_repo: DatabaseRepository[Item] = Depends(get_repository(Item)),
):
    # 콜드 스타트 시드 자동 적재
    seed_shop_items(item_repo)
    items = get_active_items(item_repo)
    return APIResponse.ok(data=items, message="상점 상품 목록 조회 성공")


@router.get(
    "/{item_id}",
    response_model=APIResponse[ItemResponse],
    status_code=status.HTTP_200_OK,
    summary="상품 상세 조회",
    description="특정 아이템의 상세 정보를 조회합니다.",
)
def get_shop_item_detail(
    item_id: int,
    item_repo: DatabaseRepository[Item] = Depends(get_repository(Item)),
):
    item = get_item_by_id(item_repo, item_id)
    return APIResponse.ok(data=item, message="상품 상세 조회 성공")