"""
공용 Enum — 여러 도메인이 함께 쓰는 것만 여기에 둔다.
(한 도메인만 쓰는 enum은 그 도메인 폴더의 enums.py로)
"""
import enum


class Difficulty(enum.Enum):
    """퀘스트 난이도 5단계. User(auth)와 Quest(quest)가 함께 쓰므로 공용."""
    VERY_EASY = "VERY_EASY"   # 하
    EASY = "EASY"             # 중하
    NORMAL = "NORMAL"         # 중
    HARD = "HARD"             # 중상
    VERY_HARD = "VERY_HARD"   # 상
