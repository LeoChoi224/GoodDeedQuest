"""난이도별 보상 범위와 계산.

AI는 난이도와 '그 안에서 얼마나 힘든지'(0~100)만 판단하고,
점수로 바꾸는 일은 여기서만 한다. AI는 점수 체계를 아예 모르므로
프롬프트를 흔들어도 보상을 조작할 수 없다.
"""
from backend.app.common.enums import Difficulty

# 난이도
REWARD_RANGES: dict[Difficulty, tuple[int, int]] = {
    Difficulty.VERY_EASY: (50, 120),
    Difficulty.EASY: (120, 280),
    Difficulty.NORMAL: (280, 450),
    Difficulty.HARD: (450, 700),
    Difficulty.VERY_HARD: (700, 1000),
}

# 포인트 기준으로 산정
EXP_RATIO = 0.4


def reward_from_intensity(difficulty: Difficulty, intensity: int) -> tuple[int, int]:
    """난이도 범위 안에서 intensity(0~100) 위치에 해당하는 보상을 구한다.

    intensity 0이면 그 난이도의 최소, 100이면 최대. 범위 밖 값은 잘라낸다.
    모르는 난이도가 오면 NORMAL로 폴백한다.
    """
    low, high = REWARD_RANGES.get(difficulty, REWARD_RANGES[Difficulty.NORMAL])
    ratio = max(0, min(100, intensity)) / 100
    point = round(low + (high - low) * ratio)
    exp = round(point * EXP_RATIO)
    return point, exp


# 난이도를 어떤 기준으로 판정할지(축·예시)는 AI가 프롬프트에 쓰는 내용이라
# ai/app/quest_create/prompts.py 에 둔다. 여기는 점수 계산만 담당한다.
