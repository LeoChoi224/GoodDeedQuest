from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.common.database import get_db
from backend.app.common.auth import get_current_user
from backend.app.common.deps import get_repository
from backend.app.common.repository import DatabaseRepository
from backend.app.common.response import APIResponse
from backend.app.shop.models import Item
from backend.app.shop.schemas import ItemResponse, PurchaseCreate, PurchaseResponse
from backend.app.shop.seed import seed_shop_items
from backend.app.shop.service import (
    get_active_items,
    get_item_by_id,
    execute_purchase,
    get_user_purchases,
    equip_item,
    unequip_item,
)

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
    "/purchases",
    response_model=APIResponse[List[PurchaseResponse]],
    status_code=status.HTTP_200_OK,
    summary="사용자 구매 내역 조회",
    description="현재 로그인한 사용자가 구매 완료한 아이템 이력 목록을 최신순으로 조회합니다.",
)
def get_my_purchases(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = current_user.get("id") or current_user.get("user_id")
    purchases = get_user_purchases(db, user_id=user_id)
    return APIResponse.ok(data=purchases, message="사용자 구매 내역 조회 성공")


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


@router.post(
    "/purchase",
    response_model=APIResponse[PurchaseResponse],
    status_code=status.HTTP_200_OK,
    summary="아이템 구매 처리",
    description="포인트를 차감하여 아이템을 구매하고 거래 원장을 기록합니다.",
)
def purchase_item(
    req: PurchaseCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = current_user.get("id") or current_user.get("user_id")
    purchase = execute_purchase(db, user_id=user_id, item_id=req.item_id)
    return APIResponse.ok(data=purchase, message="아이템 구매가 성공적으로 완료되었습니다.")


# ⭐ 수정: 보유 아이템 장착 / 해제 (badge 도메인 /badges/{id}/equip,unequip과 동일한 패턴)
@router.patch(
    "/{item_id}/equip",
    response_model=APIResponse[PurchaseResponse],
    status_code=status.HTTP_200_OK,
    summary="보유 아이템 장착",
    description="구매(보유)한 아이템을 장착합니다. 유저당 최대 1개만 장착 가능하며, 기존에 장착 중이던 아이템은 자동으로 해제됩니다.",
)
def equip_item_endpoint(
    item_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = current_user.get("id") or current_user.get("user_id")
    purchase = equip_item(db, user_id=user_id, item_id=item_id)
    return APIResponse.ok(data=purchase, message="아이템 장착 성공")


@router.patch(
    "/{item_id}/unequip",
    response_model=APIResponse[PurchaseResponse],
    status_code=status.HTTP_200_OK,
    summary="보유 아이템 장착 해제",
    description="장착 중인 아이템을 해제합니다.",
)
def unequip_item_endpoint(
    item_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = current_user.get("id") or current_user.get("user_id")
    purchase = unequip_item(db, user_id=user_id, item_id=item_id)
    return APIResponse.ok(data=purchase, message="아이템 장착 해제 성공")


