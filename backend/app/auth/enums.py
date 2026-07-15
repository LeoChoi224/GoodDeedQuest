"""auth 도메인 전용 Enum."""
import enum


class UserRole(enum.Enum):
    ADMIN = "ADMIN"
    USER = "USER"


class TransactionType(enum.Enum):
    EARN = "EARN"    # 적립 (퀘스트 인증 통과)
    SPEND = "SPEND"  # 사용 (상점 구매)
