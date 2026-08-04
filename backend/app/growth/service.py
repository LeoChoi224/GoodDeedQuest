"""레벨 ↔ 누적경험치(XP) 변환 공식.
growth 라우터(표시용)와 quest_verification(퀘스트 보상 지급 시 레벨업 반영) 양쪽에서
같이 써야 해서 라우터 파일이 아니라 여기(서비스 레이어)에 둔다."""


def next_level_xp(level: int) -> int:
    """레벨업에 필요한 누적 경험치.
    1레벨=1000, 이후 n레벨(n>=2)은 1000 + (100*n)*n
    (2레벨=1000+200*2=1400, 3레벨=1000+300*3=1900, ...)
    """
    if level <= 1:
        return 1000
    return 1000 + (100 * level) * level


def level_floor_xp(level: int) -> int:
    """현재 레벨에 도달하기 위해 필요했던 누적 XP(= 이전 레벨의 next_level_xp). 1레벨은 0."""
    if level <= 1:
        return 0
    return next_level_xp(level - 1)


def level_from_xp(xp: int) -> int:
    """누적 경험치로 레벨을 역산. next_level_xp(level)을 넘어설 때마다 한 레벨씩 올라간다."""
    level = 1
    while xp >= next_level_xp(level):
        level += 1
    return level