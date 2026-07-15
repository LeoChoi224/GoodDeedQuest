"""quest_verification 도메인 전용 Enum."""
import enum


class MediaType(enum.Enum):
    PHOTO = "PHOTO"
    VIDEO = "VIDEO"


class SubmissionStatus(enum.Enum):
    PENDING = "PENDING"     # 검토 대기 (제출 직후 기본값)
    ACCEPTED = "ACCEPTED"   # 인증 통과
    REJECTED = "REJECTED"   # 거절
