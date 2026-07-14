"""auth 도메인 전용 Enum."""
import enum


class UserRole(enum.Enum):
    ADMIN = "ADMIN"
    USER = "USER"
