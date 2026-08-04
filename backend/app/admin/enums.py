"""
admin/enums.py

admin 기능에서 사용하는 Enum(열거형) 모음.

Enum은 정해진 값만 저장하도록 제한하는 자료형이다.
신고 관련 Enum은 모두 이 파일에서 관리한다.
"""

import enum

class UserReportStatus(str, enum.Enum):
    """유저 신고 상태"""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"

class AdminUserSort(str, enum.Enum):
    """관리자 사용자 목록 정렬 기준."""

    NEWEST = "newest"
    OLDEST = "oldest"
    LEVEL = "level"
    NICKNAME = "nickname"
    TRUST = "trust"