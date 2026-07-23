from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.app.challenge.enums import TeamStatus
from backend.app.challenge.service import ChallengeRecommendationService
from ai.app.challenge_recommend.schemas import TeamRecommendationRequest


class FakeDifficulty(Enum):
    """테스트에서 Enum 문자열 변환을 확인하기 위한 임시 난이도."""

    EASY = "easy"


def make_current_user(
    *,
    user_id: int = 1,
    is_active: bool = True,
) -> SimpleNamespace:
    """추천 요청 사용자 객체를 간단히 생성합니다."""

    return SimpleNamespace(
        user_id=user_id,
        is_active=is_active,
    )


def make_context(
    *,
    leader_id: int = 1,
    team_status: TeamStatus = TeamStatus.RECRUITING,
    current_members: int = 1,
    max_members: int = 4,
) -> tuple[
    SimpleNamespace,
    SimpleNamespace,
    SimpleNamespace,
    int,
]:
    """Service 테스트에 필요한 팀·퀘스트·카테고리 문맥을 생성합니다."""

    team = SimpleNamespace(
        team_id=10,
        leader_id=leader_id,
        quest_id=100,
        name="환경 정화 팀",
        region="서울",
        status=team_status,
        expires_at=None,
        max_members=max_members,
    )

    quest = SimpleNamespace(
        quest_id=100,
        quest_title="공원 환경 정화",
        quest_description="공원 주변 쓰레기를 수거합니다.",
        difficulty=FakeDifficulty.EASY,
        active_time=[12],
        location="서울 공원",
        quest_embedding=[0.1, 0.2, 0.3],
    )

    category = SimpleNamespace(
        category_id=5,
        name="환경",
    )

    return team, quest, category, current_members


def test_normalize_enum_value() -> None:
    """Enum, 문자열, None을 AI 전달용 값으로 변환하는지 확인합니다."""

    assert (
        ChallengeRecommendationService._normalize_enum_value(
            FakeDifficulty.EASY
        )
        == "easy"
    )
    assert (
        ChallengeRecommendationService._normalize_enum_value("normal")
        == "normal"
    )
    assert (
        ChallengeRecommendationService._normalize_enum_value(None)
        is None
    )


@pytest.mark.parametrize(
    ("hour", "expected_bucket"),
    [
        (0, 0),
        (5, 0),
        (6, 6),
        (11, 6),
        (12, 12),
        (17, 12),
        (18, 18),
        (23, 18),
    ],
)
def test_get_active_time_bucket(
    hour: int,
    expected_bucket: int,
) -> None:
    """제출 시각을 네 개 활동 시간대로 구분하는지 확인합니다."""

    submitted_at = datetime(
        2026,
        7,
        23,
        hour,
        0,
        tzinfo=timezone.utc,
    )

    result = ChallengeRecommendationService._get_active_time_bucket(
        submitted_at
    )

    assert result == expected_bucket


def test_build_recent_activity_map() -> None:
    """최근 활동을 사용자별 횟수 통계로 집계하는지 확인합니다."""

    rows = [
        (
            SimpleNamespace(
                user_id=2,
                submitted_at=datetime(
                    2026,
                    7,
                    20,
                    9,
                    0,
                    tzinfo=timezone.utc,
                ),
            ),
            SimpleNamespace(difficulty=FakeDifficulty.EASY),
            SimpleNamespace(name="환경"),
        ),
        (
            SimpleNamespace(
                user_id=2,
                submitted_at=datetime(
                    2026,
                    7,
                    21,
                    14,
                    0,
                    tzinfo=timezone.utc,
                ),
            ),
            SimpleNamespace(difficulty="normal"),
            SimpleNamespace(name="환경"),
        ),
    ]

    result = ChallengeRecommendationService._build_recent_activity_map(
        rows
    )

    assert result[2] == {
        "completed_count": 2,
        "category_counts": {"환경": 2},
        "difficulty_counts": {
            "easy": 1,
            "normal": 1,
        },
        "active_time_counts": {
            "6": 1,
            "12": 1,
        },
    }


def test_get_recommendation_candidates_rejects_non_leader(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """팀장이 아닌 사용자의 추천 요청을 차단하는지 확인합니다."""

    context = make_context(leader_id=99)

    monkeypatch.setattr(
        "backend.app.challenge.service."
        "ChallengeRecommendationRepository."
        "get_team_recommendation_context",
        lambda session, *, team_id: context,
    )

    with pytest.raises(HTTPException) as exc_info:
        ChallengeRecommendationService.get_recommendation_candidates(
            SimpleNamespace(spec=Session),
            team_id=10,
            current_user=make_current_user(user_id=1),
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "팀장만 팀원 추천을 요청할 수 있습니다."


def test_no_candidates_returns_empty_and_skips_activity_query(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """추천 후보가 없으면 빈 목록을 반환하고 활동 조회를 생략하는지 확인합니다."""

    context = make_context()
    activity_query_called = False

    monkeypatch.setattr(
        "backend.app.challenge.service."
        "ChallengeRecommendationRepository."
        "get_team_recommendation_context",
        lambda session, *, team_id: context,
    )
    monkeypatch.setattr(
        "backend.app.challenge.service."
        "ChallengeRecommendationRepository."
        "list_recommendation_candidates",
        lambda session, **kwargs: [],
    )

    def fake_activity_query(session, **kwargs):
        nonlocal activity_query_called
        activity_query_called = True
        return []

    monkeypatch.setattr(
        "backend.app.challenge.service."
        "ChallengeRecommendationRepository."
        "list_recent_candidate_activities",
        fake_activity_query,
    )

    result = ChallengeRecommendationService.get_recommendation_candidates(
        SimpleNamespace(spec=Session),
        team_id=10,
        current_user=make_current_user(),
    )

    assert result["requester_id"] == 1
    assert result["team"]["team_id"] == 10
    assert result["quest"]["category_name"] == "환경"
    assert result["quest"]["active_time"] == [12]
    assert result["candidates"] == []

    validated_request = TeamRecommendationRequest.model_validate(result)

    assert validated_request.requester_id == 1
    assert validated_request.quest.active_time == [12]
    assert activity_query_called is False


def test_get_recommendation_candidates_builds_candidate_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """후보 정보와 최근 활동 통계를 AI 전달 형태로 구성하는지 확인합니다."""

    context = make_context()

    candidate = SimpleNamespace(
        user_id=2,
        nickname="추천후보",
        profile_image_url="https://example.com/profile.png",
        region_id=11,
        category=[5, 7],
        preferred_difficulty=FakeDifficulty.EASY,
        active_time=[6, 12],
        current_level=4,
        daily_streak=8,
        current_latitude=37.5,
        current_longitude=127.0,
        profile_embedding=[0.4, 0.5, 0.6],
    )

    activity_rows = [
        (
            SimpleNamespace(
                user_id=2,
                submitted_at=datetime(
                    2026,
                    7,
                    22,
                    10,
                    0,
                    tzinfo=timezone.utc,
                ),
            ),
            SimpleNamespace(difficulty=FakeDifficulty.EASY),
            SimpleNamespace(name="환경"),
        )
    ]

    monkeypatch.setattr(
        "backend.app.challenge.service."
        "ChallengeRecommendationRepository."
        "get_team_recommendation_context",
        lambda session, *, team_id: context,
    )
    monkeypatch.setattr(
        "backend.app.challenge.service."
        "ChallengeRecommendationRepository."
        "list_recommendation_candidates",
        lambda session, **kwargs: [
            (
                candidate,
                "서울",
            )
        ],
    )
    monkeypatch.setattr(
        "backend.app.challenge.service."
        "ChallengeRecommendationRepository."
        "list_recent_candidate_activities",
        lambda session, **kwargs: activity_rows,
    )

    result = ChallengeRecommendationService.get_recommendation_candidates(
        SimpleNamespace(spec=Session),
        team_id=10,
        current_user=make_current_user(),
    )

    candidate_result = result["candidates"][0]
    validated_request = TeamRecommendationRequest.model_validate(result)

    assert result["requester_id"] == 1
    assert result["quest"]["active_time"] == [12]
    assert validated_request.requester_id == 1
    assert validated_request.quest.active_time == [12]
    assert len(validated_request.candidates) == 1

    assert candidate_result["region"] == "서울"
    assert candidate_result["user_id"] == 2
    assert candidate_result["preferred_difficulty"] == "easy"
    assert candidate_result["latitude"] == 37.5
    assert candidate_result["longitude"] == 127.0
    assert candidate_result["recent_activity"] == {
        "completed_count": 1,
        "category_counts": {"환경": 1},
        "difficulty_counts": {"easy": 1},
        "active_time_counts": {"6": 1},
    }