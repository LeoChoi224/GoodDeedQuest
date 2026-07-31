from __future__ import annotations

# =========================================================
# [확인 및 검토할 사항]
#
# 1. 입력 데이터 형식
#    - 이 파일은 Backend Service가 만든 dict 데이터를 입력받는다.
#    - team, quest, candidate에 값이 없더라도 오류가 발생하지 않도록 기본값과 Fallback을 적용.
#
# 2. 활동 시간 점수
#    - 정확한 계산을 위해 quest["active_time"] 또는 team["active_time"]에 0·6·12·18 중 하나 이상의 값이 필요.
#    - 기준 활동 시간이 없으면 해당 점수는 0점으로 처리.
#
# 3. 지역 점수
#    - Backend가 전달한 팀 활동 지역과 후보 사용자 지역을 비교합니다.
#    - 지역 문자열이 일치하면 15점, 다르면 0점으로 계산합니다.
#    - 현재 팀 좌표가 없으므로 실제 거리 계산은 수행하지 않습니다.
#
# 4. Embedding 점수
#    - Quest와 사용자 Embedding이 모두 있을 때 코사인 유사도를 계산.
#    - 길이가 다르거나 값이 없거나 숫자가 아니면 0점으로 처리.
#
# 5. 점수 범위
#    - 각 항목별 점수는 정해진 최대 점수를 넘지 않습니다.
#    - 최종 점수는 항상 0점 이상 100점 이하로 반환.
#
# 6. 추천 이유
#    - 이 파일은 추천 이유 문장을 만들지 않습니다.
#    - 항목별 점수와 총점만 계산하고 추천 이유는 LLM 단계에서 생성.
# =========================================================

from dataclasses import asdict, dataclass
from math import sqrt
from typing import Any, Mapping, Sequence


# AI 규칙 기반 추천 점수 기준
CATEGORY_MAX_SCORE = 25.0       # 관심 카테고리
DIFFICULTY_MAX_SCORE = 15.0     # 선호 난이도
ACTIVE_TIME_MAX_SCORE = 15.0    # 활동 시간
REGION_MAX_SCORE = 15.0         # 팀 활동 지역 일치
EMBEDDING_MAX_SCORE = 10.0      # 프로필 임배딩
DAILY_STREAK_MAX_SCORE = 5.0    # 활동 지속성
USER_LEVEL_MAX_SCORE = 5.0      # 사용자 레벨
TRUST_MAX_SCORE = 10.0          # 신뢰도 점수

# 모든 항목을 합친 추천 점수의 최대값.
TOTAL_MAX_SCORE = 100.0 


# 공통 Difficulty Enum 순서에 맞춰 난이도 간 거리를 계산.
DIFFICULTY_ORDER = {
    "very_easy": 0,
    "very easy": 0,
    "veryeasy": 0,
    "easy": 1,
    "normal": 2,
    "medium": 2,
    "hard": 3,
    "very_hard": 4,
    "very hard": 4,
    "veryhard": 4,
}


@dataclass(frozen=True)
class RecommendationScore:
    """후보 사용자 한 명의 항목별 추천 점수 결과입니다."""

    category_score: float
    difficulty_score: float
    active_time_score: float
    region_score: float
    embedding_score: float
    daily_streak_score: float
    user_level_score: float
    trust_score: float
    total_score: float

    def to_dict(self) -> dict[str, float]:
        """AI State와 JSON 응답에서 사용할 일반 dict로 변환합니다."""

        return asdict(self)


def _normalize_value(value: Any) -> str | None:
    """Enum 또는 일반 값을 비교 가능한 소문자 문자열로 변환합니다."""

    if value is None:
        return None

    enum_value = getattr(value, "value", value)

    normalized = str(enum_value).strip().lower()

    if not normalized:
        return None

    return normalized


def _normalize_collection(value: Any) -> set[str]:
    """단일 값 또는 여러 값을 비교 가능한 문자열 집합으로 변환합니다."""

    if value is None:
        return set()

    if isinstance(value, (str, int, float)):
        normalized = _normalize_value(value)
        return {normalized} if normalized is not None else set()

    if not isinstance(value, Sequence):
        normalized = _normalize_value(value)
        return {normalized} if normalized is not None else set()

    normalized_values: set[str] = set()

    for item in value:
        normalized = _normalize_value(item)

        if normalized is not None:
            normalized_values.add(normalized)

    return normalized_values


def _clamp_score(
    score: float,
    *,
    max_score: float,
) -> float:
    """점수를 0점 이상 항목별 최대 점수 이하로 제한합니다."""

    return round(
        max(
            0.0,
            min(float(score), max_score),
        ),
        2,
    )


def calculate_category_score(
    *,
    quest: Mapping[str, Any],
    candidate: Mapping[str, Any],
) -> float:
    """Quest 카테고리와 후보의 선호·최근 활동을 비교해 최대 30점을 계산합니다."""

    quest_category_values = _normalize_collection(
        [
            quest.get("category_id"),
            quest.get("category_name"),
        ]
    )

    preferred_categories = _normalize_collection(
        candidate.get("preferred_categories")
    )

    # 후보가 Quest 카테고리를 관심 카테고리로 선택했다면 기본 20점을 부여합니다.
    preference_score = (
        20.0
        if quest_category_values & preferred_categories
        else 0.0
    )

    recent_activity = candidate.get("recent_activity") or {}
    category_counts = recent_activity.get("category_counts") or {}

    # 최근 수행 카테고리 중 현재 Quest 카테고리가 차지하는 비율로 최대 10점을 계산합니다.
    total_category_count = sum(
        max(float(count), 0.0)
        for count in category_counts.values()
        if isinstance(count, (int, float))
    )

    matched_category_count = 0.0

    for category_key, count in category_counts.items():
        normalized_key = _normalize_value(category_key)

        if (
            normalized_key in quest_category_values
            and isinstance(count, (int, float))
        ):
            matched_category_count += max(float(count), 0.0)

    recent_score = 0.0

    if total_category_count > 0:
        recent_score = (
            matched_category_count
            / total_category_count
            * 5.0
        )

    return _clamp_score(
        preference_score + recent_score,
        max_score=CATEGORY_MAX_SCORE,
    )


def calculate_difficulty_score(
    *,
    quest: Mapping[str, Any],
    candidate: Mapping[str, Any],
) -> float:
    """Quest 난이도와 후보 선호 난이도의 거리에 따라 최대 15점을 계산합니다."""

    quest_difficulty = _normalize_value(
        quest.get("difficulty")
    )
    preferred_difficulty = _normalize_value(
        candidate.get("preferred_difficulty")
    )

    if (
        quest_difficulty is None
        or preferred_difficulty is None
    ):
        return 0.0

    # 같은 난이도이면 최대 점수를 부여합니다.
    if quest_difficulty == preferred_difficulty:
        return DIFFICULTY_MAX_SCORE

    quest_order = DIFFICULTY_ORDER.get(
        quest_difficulty.replace("-", "_")
    )
    preferred_order = DIFFICULTY_ORDER.get(
        preferred_difficulty.replace("-", "_")
    )

    if quest_order is None or preferred_order is None:
        return 0.0

    difference = abs(quest_order - preferred_order)

    # 한 단계 차이는 10점, 두 단계 차이는 5점, 그 이상은 0점입니다.
    score_by_difference = {
        1: 10.0,
        2: 5.0,
    }

    return score_by_difference.get(difference, 0.0)


def calculate_active_time_score(
    *,
    team: Mapping[str, Any],
    quest: Mapping[str, Any],
    candidate: Mapping[str, Any],
) -> float:
    """Quest 또는 팀의 활동 시간대와 후보의 선호 시간대를 비교합니다."""

    target_active_times = _normalize_collection(
        quest.get("active_time")
        or team.get("active_time")
    )

    candidate_active_times = _normalize_collection(
        candidate.get("active_time")
    )

    if not target_active_times or not candidate_active_times:
        return 0.0

    matched_count = len(
        target_active_times & candidate_active_times
    )

    if matched_count == 0:
        return 0.0

    # 목표 시간대 중 후보와 일치한 비율만큼 최대 15점을 부여합니다.
    match_ratio = matched_count / len(target_active_times)

    return _clamp_score(
        match_ratio * ACTIVE_TIME_MAX_SCORE,
        max_score=ACTIVE_TIME_MAX_SCORE,
    )


def calculate_region_score(
    *,
    team: Mapping[str, Any],
    candidate: Mapping[str, Any],
) -> float:
    """팀 활동 지역과 후보 지역이 일치하면 15점을 부여합니다."""

    team_region = _normalize_value(
        team.get("region")
        or team.get("region_id")
    )

    candidate_region = _normalize_value(
        candidate.get("region")
    )

    if team_region is None or candidate_region is None:
        return 0.0

    if team_region == candidate_region:
        return REGION_MAX_SCORE

    return 0.0


def calculate_cosine_similarity(
    first_vector: Any,
    second_vector: Any,
) -> float:
    """두 Embedding 벡터의 코사인 유사도를 -1에서 1 사이 값으로 계산합니다."""

    if (
        not isinstance(first_vector, Sequence)
        or isinstance(first_vector, (str, bytes))
        or not isinstance(second_vector, Sequence)
        or isinstance(second_vector, (str, bytes))
    ):
        return 0.0

    if (
        not first_vector
        or not second_vector
        or len(first_vector) != len(second_vector)
    ):
        return 0.0

    try:
        first_values = [
            float(value)
            for value in first_vector
        ]
        second_values = [
            float(value)
            for value in second_vector
        ]
    except (TypeError, ValueError):
        return 0.0

    dot_product = sum(
        first * second
        for first, second in zip(
            first_values,
            second_values,
            strict=True,
        )
    )

    first_norm = sqrt(
        sum(value * value for value in first_values)
    )
    second_norm = sqrt(
        sum(value * value for value in second_values)
    )

    if first_norm == 0.0 or second_norm == 0.0:
        return 0.0

    similarity = dot_product / (
        first_norm * second_norm
    )

    return max(-1.0, min(similarity, 1.0))


def calculate_embedding_score(
    *,
    quest: Mapping[str, Any],
    candidate: Mapping[str, Any],
) -> float:
    """Quest와 후보 프로필 Embedding 유사도를 최대 15점으로 변환합니다."""

    similarity = calculate_cosine_similarity(
        quest.get("embedding"),
        candidate.get("profile_embedding"),
    )

    # 음수 유사도는 추천 점수에 반영하지 않고 0점으로 처리합니다.
    positive_similarity = max(similarity, 0.0)

    return _clamp_score(
        positive_similarity * EMBEDDING_MAX_SCORE,
        max_score=EMBEDDING_MAX_SCORE,
    )


def calculate_daily_streak_score(
    *,
    candidate: Mapping[str, Any],
) -> float:
    """연속 활동 일수를 기준으로 최대 5점을 계산합니다."""

    streak_value = candidate.get("daily_streak", 0)

    if not isinstance(streak_value, (int, float)):
        return 0.0

    streak = max(float(streak_value), 0.0)

    if streak >= 30:
        return 5.0

    if streak >= 14:
        return 4.0

    if streak >= 7:
        return 3.0

    if streak >= 3:
        return 2.0

    if streak >= 1:
        return 1.0

    return 0.0


def calculate_user_level_score(
    *,
    candidate: Mapping[str, Any],
) -> float:
    """사용자 현재 레벨을 기준으로 최대 5점을 계산합니다."""

    level_value = candidate.get("current_level", 0)

    if not isinstance(level_value, (int, float)):
        return 0.0

    level = max(float(level_value), 0.0)

    if level >= 20:
        return 5.0

    if level >= 15:
        return 4.0

    if level >= 10:
        return 3.0

    if level >= 5:
        return 2.0

    if level >= 1:
        return 1.0

    return 0.0

def calculate_trust_score(
    *,
    candidate: Mapping[str, Any],
) -> float:
    """사용자 신뢰도 0~100점을 추천 점수 0~10점으로 환산합니다."""

    trust_value = candidate.get("trust_score", 0)

    if (
        isinstance(trust_value, bool)
        or not isinstance(trust_value, (int, float))
    ):
        return 0.0

    normalized_trust = max(
        0.0,
        min(float(trust_value), 100.0),
    )

    return _clamp_score(
        normalized_trust / 100.0 * TRUST_MAX_SCORE,
        max_score=TRUST_MAX_SCORE,
    )

def calculate_recommendation_score(
    *,
    team: Mapping[str, Any],
    quest: Mapping[str, Any],
    candidate: Mapping[str, Any],
) -> RecommendationScore:
    """후보 사용자 한 명의 규칙 기반 추천 점수를 계산합니다."""

    category_score = calculate_category_score(
        quest=quest,
        candidate=candidate,
    )

    difficulty_score = calculate_difficulty_score(
        quest=quest,
        candidate=candidate,
    )

    active_time_score = calculate_active_time_score(
        team=team,
        quest=quest,
        candidate=candidate,
    )

    region_score = calculate_region_score(
        team=team,
        candidate=candidate,
    )

    embedding_score = calculate_embedding_score(
        quest=quest,
        candidate=candidate,
    )

    daily_streak_score = calculate_daily_streak_score(
        candidate=candidate,
    )

    user_level_score = calculate_user_level_score(
        candidate=candidate,
    )

    trust_score = calculate_trust_score(
        candidate=candidate,
    )

    total_score = _clamp_score(
        category_score
        + difficulty_score
        + active_time_score
        + region_score
        + embedding_score
        + daily_streak_score
        + user_level_score,
        + trust_score,
        max_score=TOTAL_MAX_SCORE,
    )

    return RecommendationScore(
        category_score=category_score,
        difficulty_score=difficulty_score,
        active_time_score=active_time_score,
        region_score=region_score,
        embedding_score=embedding_score,
        daily_streak_score=daily_streak_score,
        user_level_score=user_level_score,
        trust_score=trust_score,
        total_score=total_score,
    )


def score_candidates(
    *,
    team: Mapping[str, Any],
    quest: Mapping[str, Any],
    candidates: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """전체 후보의 점수를 계산하고 높은 점수순으로 정렬합니다."""

    scored_candidates: list[dict[str, Any]] = []

    for candidate in candidates:
        score = calculate_recommendation_score(
            team=team,
            quest=quest,
            candidate=candidate,
        )

        scored_candidate = dict(candidate)
        scored_candidate["score"] = score.to_dict()

        scored_candidates.append(scored_candidate)

    # 총점이 같으면 user_id가 작은 후보가 먼저 오도록 정렬 결과를 고정합니다.
    scored_candidates.sort(
        key=lambda item: (
            -float(item["score"]["total_score"]),
            int(item.get("user_id", 0)),
        )
    )

    return scored_candidates
