from enum import Enum

class QuestTarget(str, Enum):
    """참여 방식 ENUM (SOLO / TEAM)"""
    SOLO = "SOLO"
    TEAM = "TEAM"

class QuestType(str, Enum):
    """퀘스트 종류 ENUM (VOLUNTEER: 실제 봉사, GOOD_DEED: 선행)"""
    VOLUNTEER = "VOLUNTEER"
    GOOD_DEED = "GOOD_DEED"

class QuestSource(str, Enum):
    """등록 출처 ENUM (USER: 유저 생성, AI: AI 추천 생성, ADMIN: 관리자 등록)"""
    USER = "USER"
    AI = "AI"
    ADMIN = "ADMIN"

class QuestStatus(str, Enum):
    """퀘스트 진행 상태 ENUM"""
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
