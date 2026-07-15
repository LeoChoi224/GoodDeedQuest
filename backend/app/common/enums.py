"""
공용 Enum — 여러 도메인이 함께 쓰는 것만 여기에 둔다.
(한 도메인만 쓰는 enum은 그 도메인 폴더의 enums.py로)
"""
from enum import Enum

class Difficulty(str, Enum):
    """퀘스트 난이도 ENUM (EASY / NORMAL / HARD)"""
    VERY_EASY = "VERY_EASY"   # 매우 쉬움
    EASY = "EASY"             # 쉬움
    NORMAL = "NORMAL"         # 보통
    HARD = "HARD"             # 어려움
    VERY_HARD = "VERY_HARD"   # 매우 어려움