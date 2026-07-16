import enum

class ShortFormStatus(str, enum.Enum):
    """숏폼 생성 파이프라인 진행 상태 ENUM (PascalCase)"""
    PENDING = "PENDING"
    GENERATING = "GENERATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"