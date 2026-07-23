from __future__ import annotations

"""AI 팀원 추천 Repository 최소 핵심 단위 테스트.

실제 DB에는 연결하지 않고 Session과 조회 결과를 Mock으로 대체합니다.

중요:
- list_recommendation_candidates()는 이제 result.scalars().all()이 아니라
  result.all()을 사용합니다.
- 반환 형식은 User 단독 목록이 아니라 (User, region_name) 튜플 목록입니다.
"""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock

from backend.app.challenge.repository import (
    ChallengeRecommendationRepository,
)


def test_get_team_recommendation_context_returns_joined_data() -> None:
    """팀·Quest·Category·현재 인원을 함께 반환하는지 확인합니다."""

    session = Mock()

    team = SimpleNamespace(team_id=10, quest_id=100)
    quest = SimpleNamespace(quest_id=100, category_id=1)
    category = SimpleNamespace(category_id=1, name="환경")
    expected = (team, quest, category, 3)

    result_mock = Mock()
    result_mock.one_or_none.return_value = expected
    session.execute.return_value = result_mock

    result = (
        ChallengeRecommendationRepository
        .get_team_recommendation_context(
            session,
            team_id=10,
        )
    )

    assert result == expected
    session.execute.assert_called_once()
    result_mock.one_or_none.assert_called_once_with()


def test_get_team_recommendation_context_returns_none() -> None:
    """조회할 추천 문맥이 없으면 None을 반환하는지 확인합니다."""

    session = Mock()

    result_mock = Mock()
    result_mock.one_or_none.return_value = None
    session.execute.return_value = result_mock

    result = (
        ChallengeRecommendationRepository
        .get_team_recommendation_context(
            session,
            team_id=999,
        )
    )

    assert result is None
    session.execute.assert_called_once()
    result_mock.one_or_none.assert_called_once_with()


def test_list_recommendation_candidates_returns_users_and_region() -> None:
    """추천 후보 사용자와 지역 이름을 튜플 형태로 반환하는지 확인합니다."""

    session = Mock()

    candidate = SimpleNamespace(
        user_id=2,
        nickname="추천 후보",
    )
    expected = [
        (
            candidate,
            "서울",
        )
    ]

    # Repository 구현이 result.all()을 호출하므로
    # scalars()가 아닌 all()의 반환값을 설정합니다.
    result_mock = Mock()
    result_mock.all.return_value = expected
    session.execute.return_value = result_mock

    rejected_since = (
        datetime.now(UTC)
        - timedelta(days=7)
    )

    result = (
        ChallengeRecommendationRepository
        .list_recommendation_candidates(
            session,
            requester_id=1,
            team_id=10,
            quest_id=100,
            rejected_since=rejected_since,
        )
    )

    assert result == expected
    session.execute.assert_called_once()
    result_mock.all.assert_called_once_with()


def test_candidate_query_is_executed_with_required_values() -> None:
    """후보가 없어도 추천 후보 조회 Query가 정상 실행되는지 확인합니다."""

    session = Mock()

    # Repository 구현이 result.all()을 호출하므로
    # 빈 후보 결과도 all()에 설정합니다.
    result_mock = Mock()
    result_mock.all.return_value = []
    session.execute.return_value = result_mock

    rejected_since = datetime(
        2026,
        7,
        1,
        tzinfo=UTC,
    )

    result = (
        ChallengeRecommendationRepository
        .list_recommendation_candidates(
            session,
            requester_id=1,
            team_id=10,
            quest_id=100,
            rejected_since=rejected_since,
        )
    )

    assert result == []
    session.execute.assert_called_once()
    result_mock.all.assert_called_once_with()
    assert session.execute.call_args.args[0] is not None


def test_recent_activities_returns_accepted_submission_rows() -> None:
    """최근 승인 활동 조회 결과를 그대로 반환하는지 확인합니다."""

    session = Mock()

    submission = SimpleNamespace(
        submission_id=1,
        user_id=2,
        quest_id=100,
    )
    quest = SimpleNamespace(
        quest_id=100,
        category_id=1,
    )
    category = SimpleNamespace(
        category_id=1,
        name="환경",
    )
    expected = [
        (
            submission,
            quest,
            category,
        )
    ]

    result_mock = Mock()
    result_mock.all.return_value = expected
    session.execute.return_value = result_mock

    since = (
        datetime.now(UTC)
        - timedelta(days=30)
    )

    result = (
        ChallengeRecommendationRepository
        .list_recent_candidate_activities(
            session,
            candidate_user_ids=[2],
            since=since,
        )
    )

    assert result == expected
    session.execute.assert_called_once()
    result_mock.all.assert_called_once_with()


def test_recent_activity_query_is_executed_for_candidates() -> None:
    """후보 사용자 ID가 있으면 최근 활동 조회 Query를 실행하는지 확인합니다."""

    session = Mock()

    result_mock = Mock()
    result_mock.all.return_value = []
    session.execute.return_value = result_mock

    since = datetime(
        2026,
        6,
        1,
        tzinfo=UTC,
    )

    result = (
        ChallengeRecommendationRepository
        .list_recent_candidate_activities(
            session,
            candidate_user_ids=[2, 3],
            since=since,
        )
    )

    assert result == []
    session.execute.assert_called_once()
    result_mock.all.assert_called_once_with()
    assert session.execute.call_args.args[0] is not None


def test_recent_activities_skips_query_when_candidates_are_empty() -> None:
    """후보 사용자 ID가 없으면 최근 활동 DB 조회를 생략하는지 확인합니다."""

    session = Mock()

    result = (
        ChallengeRecommendationRepository
        .list_recent_candidate_activities(
            session,
            candidate_user_ids=[],
            since=(
                datetime.now(UTC)
                - timedelta(days=30)
            ),
        )
    )

    assert result == []
    session.execute.assert_not_called()
