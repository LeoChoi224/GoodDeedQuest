from enum import Enum

class PurchaseStatus(str, Enum):
    """아이템 구매 상태 ENUM (COMPLETED: 완료, REFUNDED: 환불)"""
    COMPLETED = "COMPLETED"
    REFUNDED = "REFUNDED"