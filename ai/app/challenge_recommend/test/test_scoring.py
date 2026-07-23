from __future__ import annotations

# =========================================================
# [확인 및 검토할 사항]
#
# 1. 최소 핵심 테스트
#    - 전체 세부 조합을 모두 테스트하지 않습니다.
#    - 최대 점수, Fallback, 핵심 부분 점수, 정렬만 확인합니다.
#
# 2. 실행 위치
#    - 프로젝트 최상위 폴더에서 아래 명령어로 실행합니다.
#      python -m pytest ai/app/challenge_recommend/test/test_scoring.py -v
#
# 3. Import 오류
#    - test 폴더와 challenge_recommend 폴더에 __init__.py가 없다면
#      프로젝트 설정에 따라 빈 __init__.py 파일이 필요할 수 있습니다.
# =========================================================

from ai.app.challenge_recommend.scoring import (
    calculate_cosine_similarity,
    calculate_recommendation_score,
    score_candidates,
)


def make_team() -> dict:
    """최대 점수 후보와 비교할 팀 데이터를 생성합니다."""

    return {
        "team_id": 10,
        "quest_id": 100,
        "region": "서울",
        "active_time": [6, 12],
    }


def make_quest() -> dict:
    """최대 점수 후보와 비교할 Quest 데이터를 생성합니다."""

    return {
        "quest_id": 100,
        "category_id": 5,
        "category_name": "환경",
        "difficulty": "easy",
        "active_time": [6, 12],
        "embedding": [1.0, 0.0, 0.0],
    }


def make_candidate(
    *,
    user_id: int = 2,
) -> dict:
    """모든 추천 기준이 일치하는 후보 데이터를 생성합니다."""

    return {
        "user_id": user_id,
        "region": "서울",
        "preferred_categories": [5],
        "preferred_difficulty": "easy",
        "active_time": [6, 12],
        "current_level": 20,
        "daily_streak": 30,
        "profile_embedding": [1.0, 0.0, 0.0],
        "recent_activity": {
            "completed_count": 2,
            "category_counts": {
                "환경": 2,
            },
            "difficulty_counts": {
                "easy": 2,
            },
            "active_time_counts": {
                "6": 1,
                "12": 1,
            },
        },
    }


def test_calculate_recommendation_score_returns_100() -> None:
    """모든 기준이 일치하면 총점과 각 항목이 최대 점수인지 확인합니다."""

    result = calculate_recommendation_score(
        team=make_team(),
        quest=make_quest(),
        candidate=make_candidate(),
    )

    assert result.category_score == 30.0
    assert result.difficulty_score == 15.0
    assert result.active_time_score == 15.0
    assert result.region_score == 15.0
    assert result.embedding_score == 15.0
    assert result.daily_streak_score == 5.0
    assert result.user_level_score == 5.0
    assert result.total_score == 100.0


def test_missing_values_use_zero_score_fallback() -> None:
    """Embedding과 선택 정보가 없어도 오류 없이 0점 Fallback을 적용합니다."""

    result = calculate_recommendation_score(
        team={},
        quest={},
        candidate={
            "user_id": 2,
            "profile_embedding": None,
            "daily_streak": None,
            "current_level": None,
        },
    )

    assert result.embedding_score == 0.0
    assert result.total_score == 0.0


def test_partial_match_calculates_core_scores() -> None:
    """난이도 한 단계 차이와 활동 시간 일부 일치를 계산하는지 확인합니다."""

    candidate = make_candidate()
    candidate["preferred_difficulty"] = "normal"
    candidate["active_time"] = [6]
    candidate["daily_streak"] = 7
    candidate["current_level"] = 10

    result = calculate_recommendation_score(
        team=make_team(),
        quest=make_quest(),
        candidate=candidate,
    )

    assert result.difficulty_score == 10.0
    assert result.active_time_score == 7.5
    assert result.daily_streak_score == 3.0
    assert result.user_level_score == 3.0
    assert 0.0 <= result.total_score <= 100.0


def test_cosine_similarity_invalid_vectors_return_zero() -> None:
    """길이가 다르거나 값이 없는 Embedding은 유사도 0으로 처리합니다."""

    assert calculate_cosine_similarity(None, [1.0]) == 0.0
    assert calculate_cosine_similarity([], []) == 0.0
    assert (
        calculate_cosine_similarity(
            [1.0, 0.0],
            [1.0],
        )
        == 0.0
    )


def test_score_candidates_sorts_by_total_score() -> None:
    """전체 후보를 총점이 높은 순서로 정렬하는지 확인합니다."""

    high_score_candidate = make_candidate(user_id=2)

    low_score_candidate = {
        "user_id": 3,
        "region": "부산",
        "preferred_categories": [],
        "preferred_difficulty": "very_hard",
        "active_time": [18],
        "current_level": 1,
        "daily_streak": 0,
        "profile_embedding": [0.0, 1.0, 0.0],
        "recent_activity": {
            "completed_count": 0,
            "category_counts": {},
            "difficulty_counts": {},
            "active_time_counts": {},
        },
    }

    result = score_candidates(
        team=make_team(),
        quest=make_quest(),
        candidates=[
            low_score_candidate,
            high_score_candidate,
        ],
    )

    assert result[0]["user_id"] == 2
    assert result[1]["user_id"] == 3
    assert (
        result[0]["score"]["total_score"]
        > result[1]["score"]["total_score"]
    )
