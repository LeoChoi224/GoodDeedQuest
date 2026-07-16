"""
challenge/enums.py

Challenge 기능에서 사용하는 Enum(열거형) 모음.

Enum은 정해진 값만 저장하도록 제한하는 자료형이다.
Team 관련 Enum은 모두 이 파일에서 관리한다.
"""

import enum


class TeamStatus(str, enum.Enum):
    """팀 진행 상태"""

    RECRUITING = "RECRUITING"
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    DISBANDED = "DISBANDED"


class TeamInviteStatus(str, enum.Enum):
    """팀 초대 상태"""

    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class TeamMemberRole(str, enum.Enum):
    """팀 내 역할"""

    LEADER = "LEADER"
    MEMBER = "MEMBER"