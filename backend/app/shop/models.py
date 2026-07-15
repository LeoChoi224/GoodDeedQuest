from sqlalchemy import Integer, BigInteger, String, Text, DateTime, ForeignKey, Boolean, Enum as SQLEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from backend.app.common.database import Base
from backend.app.shop.enums import PurchaseStatus

class Item(Base):
    """상점 판매 상품(아이템) 모델"""
    __tablename__ = "item"

    item_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    
    # 테두리/칭호 등의 장착 아이템인 경우의 장착 여부 (기본값 False)
    is_equipped: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="장착 상태 여부")
    
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="상품 이름")
    description: Mapped[str] = mapped_column(Text, nullable=False, comment="상품 상세 설명")
    price_point: Mapped[int] = mapped_column(Integer, nullable=False, comment="상품 가격 (포인트 단위)")
    
    image_url: Mapped[str] = mapped_column(String(500), nullable=False, comment="상품 이미지 URL")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, comment="상점 노출 여부")

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="등록 일시"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="수정 일시"
    )

    def __repr__(self):
        return f"<Item item_id={self.item_id} name={self.name} price={self.price_point}>"


class Purchase(Base):
    """상품 구매 및 주문 이력 모델"""
    __tablename__ = "purchase"

    purchase_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False, comment="구매한 유저 ID"
    )
    
    # 동일 모듈 내 상품 정보 연결 (ondelete="RESTRICT"로 판매 상품이 이력 존재 시 강제 삭제되는 것을 방지)
    item_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("item.item_id", ondelete="RESTRICT"), nullable=False, comment="구매한 상품 ID"
    )
    
    status: Mapped[PurchaseStatus] = mapped_column(
        SQLEnum(PurchaseStatus, name="purchase_status_enum"),
        nullable=False, 
        efault=PurchaseStatus.COMPLETED,
        comment="구매 진행 상태 (COMPLETED / REFUNDED)"
    )

    purchased_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="구매 일시"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="수정 일시"
    )

    #  테이블과의 단방향 관계 설정 (Item은 이 존재를 몰라도 됨)
    item: Mapped["Item"] = relationship("Item")
    
    user: Mapped["User"] = relationship("User", back_populates="purchases")

    def __repr__(self):
        return f"<Purchase purchase_id={self.purchase_id} user_id={self.user_id} item_id={self.item_id} status={self.status}>"