from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app.common.repository import DatabaseRepository
from backend.app.shop.models import Item, Purchase
from backend.app.auth.models import User, PointTransaction
from backend.app.shop.enums import PurchaseStatus
from backend.app.auth.enums import TransactionType


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


def execute_purchase(db: Session, user_id: int, item_id: int) -> Purchase:
    """
    포인트를 사용하여 상점 아이템을 구매합니다.
    중복 구매 방지 검증, 잔액 부족 검증, 포인트 차감, Purchase 레코드 생성, PointTransaction 원장 저장을
    단일 데이터베이스 트랜잭션으로 원자적(Atomic) 처리합니다.
    """
    # 1. 유저 존재 여부 검증
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="존재하지 않는 유저입니다.",
        )
    
    # 2. 상품 존재 및 활성화 상태 검증
    item = db.query(Item).filter(Item.item_id == item_id, Item.is_active == True).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"상품 ID {item_id}번 상품을 찾을 수 없거나 판매 중이 아닙니다.",
        )
    
    # 3. 중복 구매 방지 예외 검증 (이미 보유 중인 프로필 테두리인지 판별)
    existing_purchase = (
        db.query(Purchase)
        .filter(
            Purchase.user_id == user_id,
            Purchase.item_id == item_id,
            Purchase.status == PurchaseStatus.COMPLETED,
        )
        .first()
    )
    if existing_purchase:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 구매하여 보유 중인 아이템입니다.",
        )
    
    # 4. 포인트 잔액 부족 예외 검증
    if user.point_balance < item.price_point:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"포인트 잔액이 부족합니다. (보유 포인트: {user.point_balance}P, 상품 가격: {item.price_point}P)",
        )
    
    # 5. 포인트 차감 실행
    user.point_balance -= item.price_point

    # 6. Purchase 구매 이력 생성
    new_purchase = Purchase(
        user_id=user_id,
        item_id=item_id,
        status=PurchaseStatus.COMPLETED,
    )
    db.add(new_purchase)
    db.flush()  # 생성된 purchase_id PK를 획득하기 위해 flush 수행

    # 7. PointTransaction 거래 원장 기록 생성
    new_transaction = PointTransaction(
        user_id=user_id,
        purchase_id=new_purchase.purchase_id,
        amount=item.price_point,
        type=TransactionType.SPEND,
        balance_after=user.point_balance,
    )
    db.add(new_transaction)

    # 8. 최종 트랜잭션 커밋
    db.commit()
    db.refresh(new_purchase)

    return new_purchase


def get_user_purchases(db: Session, user_id: int) -> List[Purchase]:
    """
    현재 로그인한 사용자가 구매 완료(COMPLETED)한 아이템 목록을 최신순으로 조회합니다.
    """
    return (
        db.query(Purchase)
        .filter(Purchase.user_id == user_id, Purchase.status == PurchaseStatus.COMPLETED)
        .order_by(Purchase.purchased_at.desc())
        .all()
    )



