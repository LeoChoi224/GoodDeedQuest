from __future__ import annotations

"""Backend 팀 챌린지 AI 추천 연결 최소 핵심 테스트.

저장 위치:
    backend/app/challenge/test/test_ai_recommendation_integration.py

검증 범위:
- AI HTTP Client 정상 호출과 핵심 통신 예외 변환
- 후보가 없을 때 AI 서버 호출 생략
- 정상 AI 응답의 Backend Schema 검증
- 후보가 아닌 사용자 반환 차단
- 점수 합계가 잘못된 AI 응답 차단
- 추천 결과의 team_id·user_id를 기존 팀 초대 요청으로 변환
"""

from types import SimpleNamespace
from typing import Any

import httpx
import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.app.challenge.ai_client import (
    ChallengeRecommendationAIClient,
    ChallengeRecommendationConnectionError,
    ChallengeRecommendationTimeoutError,
)
from backend.app.challenge.schema import (
    TeamInviteCreate,
    TeamRecommendationResponse,
    TeamRecommendationScoreResponse,
)
from backend.app.challenge.service import ChallengeRecommendationService


# 정상 추천 응답에 사용할 항목별 점수입니다.
VALID_SCORE: dict[str, float] = {
    "category_score": 30.0,
    "difficulty_score": 15.0,
    "active_time_score": 15.0,
    "region_score": 15.0,
    "embedding_score": 10.0,
    "daily_streak_score": 4.0,
    "user_level_score": 3.0,
    "total_score": 92.0,
}


def make_candidate_payload() -> dict[str, Any]:
    """Service가 AI 서버에 전달할 최소 정상 후보 Payload를 생성합니다."""

    return {
        "requester_id": 1,
        "team": {
            "team_id": 10,
            "quest_id": 100,
            "name": "환경 지킴이",
            "region": "서울",
            "current_members": 1,
            "max_members": 4,
        },
        "quest": {
            "quest_id": 100,
            "category_id": 5,
            "category_name": "환경",
            "title": "공원 환경 정화",
            "description": "공원 주변 쓰레기를 수거합니다.",
            "difficulty": "easy",
            "active_time": [12],
            "location": "서울 공원",
            "embedding": [0.1, 0.2, 0.3],
        },
        "candidates": [
            {
                "user_id": 2,
                "nickname": "추천 후보",
                "profile_image_url": None,
                "region_id": 1,
                "region": "서울",
                "preferred_categories": [5, "환경"],
                "preferred_difficulty": "easy",
                "active_time": [12],
                "current_level": 3,
                "daily_streak": 7,
                "latitude": None,
                "longitude": None,
                "profile_embedding": [0.1, 0.2, 0.3],
                "recent_activity": {
                    "completed_count": 4,
                    "category_counts": {"환경": 3},
                    "difficulty_counts": {"easy": 2},
                    "active_time_counts": {"12": 2},
                },
            }
        ],
    }


def make_ai_response(
    *,
    user_id: int = 2,
    score: dict[str, float] | None = None,
) -> dict[str, Any]:
    """AI 서버의 최소 정상 추천 응답을 생성합니다."""

    return {
        "team_id": 10,
        "quest_id": 100,
        "recommendations": [
            {
                "rank": 1,
                "user_id": user_id,
                "nickname": "추천 후보",
                "profile_image_url": None,
                "region_id": 1,
                "region": "서울",
                "preferred_categories": [5, "환경"],
                "preferred_difficulty": "easy",
                "active_time": [12],
                "current_level": 3,
                "daily_streak": 7,
                "latitude": None,
                "longitude": None,
                "profile_embedding": [0.1, 0.2, 0.3],
                "recent_activity": {
                    "completed_count": 4,
                    "category_counts": {"환경": 3},
                    "difficulty_counts": {"easy": 2},
                    "active_time_counts": {"12": 2},
                },
                "score": score or VALID_SCORE,
                "recommendation_reason": (
                    "관심 카테고리와 활동 시간이 잘 맞는 사용자입니다."
                ),
            }
        ],
        "requested_top_k": 5,
        "recommendation_count": 1,
        "warnings": [],
    }


class FakeAIClient:
    """Service 테스트에서 실제 HTTP 요청을 대체하는 가짜 Client입니다."""

    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.called = False
        self.received_payload: dict[str, Any] | None = None

    def request_recommendations(
        self,
        *,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        self.called = True
        self.received_payload = payload
        return self.response


def test_ai_client_posts_expected_payload_and_returns_json() -> None:
    """Client가 정해진 주소로 Payload를 전송하고 JSON을 반환하는지 확인합니다."""

    payload = make_candidate_payload()

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert str(request.url) == (
            "http://ai-server:8001/ai/challenge/recommend"
        )
        assert request.headers["accept"] == "application/json"
        assert request.headers["content-type"] == "application/json"
        assert request.read()

        return httpx.Response(
            status_code=200,
            json=make_ai_response(),
        )

    client = ChallengeRecommendationAIClient(
        base_url="http://ai-server:8001/",
        transport=httpx.MockTransport(handler),
    )

    result = client.request_recommendations(payload=payload)

    assert result["team_id"] == 10
    assert result["recommendation_count"] == 1


@pytest.mark.parametrize(
    ("raised_error", "expected_exception"),
    [
        (
            httpx.ReadTimeout("AI server timeout"),
            ChallengeRecommendationTimeoutError,
        ),
        (
            httpx.ConnectError("AI server connection failed"),
            ChallengeRecommendationConnectionError,
        ),
    ],
)
def test_ai_client_converts_core_network_errors(
    raised_error: httpx.RequestError,
    expected_exception: type[Exception],
) -> None:
    """Timeout과 연결 실패를 Client 전용 예외로 구분하는지 확인합니다."""

    def handler(request: httpx.Request) -> httpx.Response:
        raise raised_error

    client = ChallengeRecommendationAIClient(
        base_url="http://ai-server:8001",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(expected_exception):
        client.request_recommendations(
            payload=make_candidate_payload(),
        )


def test_service_skips_ai_call_when_no_candidates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """후보가 없으면 AI Client를 호출하지 않고 검증된 빈 응답을 반환합니다."""

    empty_payload = make_candidate_payload()
    empty_payload["candidates"] = []

    monkeypatch.setattr(
        ChallengeRecommendationService,
        "get_recommendation_candidates",
        staticmethod(lambda session, *, team_id, current_user: empty_payload),
    )

    fake_client = FakeAIClient(make_ai_response())

    result = (
        ChallengeRecommendationService
        .get_team_member_recommendations(
            SimpleNamespace(spec=Session),
            team_id=10,
            current_user=SimpleNamespace(user_id=1, is_active=True),
            top_k=5,
            ai_client=fake_client,
        )
    )

    assert isinstance(result, TeamRecommendationResponse)
    assert result.team_id == 10
    assert result.recommendations == []
    assert result.recommendation_count == 0
    assert fake_client.called is False


def test_service_returns_validated_ai_recommendation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """정상 AI 응답을 Backend Schema로 검증해 반환하는지 확인합니다."""

    payload = make_candidate_payload()

    monkeypatch.setattr(
        ChallengeRecommendationService,
        "get_recommendation_candidates",
        staticmethod(lambda session, *, team_id, current_user: payload),
    )

    fake_client = FakeAIClient(make_ai_response())

    result = (
        ChallengeRecommendationService
        .get_team_member_recommendations(
            SimpleNamespace(spec=Session),
            team_id=10,
            current_user=SimpleNamespace(user_id=1, is_active=True),
            top_k=5,
            ai_client=fake_client,
        )
    )

    assert isinstance(result, TeamRecommendationResponse)
    assert result.recommendations[0].user_id == 2
    assert result.recommendations[0].score.total_score == 92.0
    assert fake_client.called is True
    assert fake_client.received_payload is not None
    assert fake_client.received_payload["top_k"] == 5


def test_service_rejects_user_not_in_candidate_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Backend가 전달하지 않은 사용자를 AI가 추천하면 502로 차단합니다."""

    payload = make_candidate_payload()

    monkeypatch.setattr(
        ChallengeRecommendationService,
        "get_recommendation_candidates",
        staticmethod(lambda session, *, team_id, current_user: payload),
    )

    fake_client = FakeAIClient(
        make_ai_response(user_id=999)
    )

    with pytest.raises(HTTPException) as exc_info:
        ChallengeRecommendationService.get_team_member_recommendations(
            SimpleNamespace(spec=Session),
            team_id=10,
            current_user=SimpleNamespace(user_id=1, is_active=True),
            top_k=5,
            ai_client=fake_client,
        )

    assert exc_info.value.status_code == 502
    assert (
        exc_info.value.detail
        == "AI 추천 서버가 후보가 아닌 사용자를 반환했습니다."
    )


def test_score_schema_rejects_wrong_total_score() -> None:
    """총점과 항목별 점수 합계가 다르면 응답 Schema가 차단하는지 확인합니다."""

    invalid_score = {
        **VALID_SCORE,
        "total_score": 99.0,
    }

    with pytest.raises(ValueError):
        TeamRecommendationScoreResponse.model_validate(
            invalid_score
        )


def test_recommendation_result_converts_to_existing_invite_request() -> None:
    """추천 결과의 식별자를 기존 TeamInviteCreate 요청으로 연결합니다."""

    recommendation = TeamRecommendationResponse.model_validate(
        make_ai_response()
    )

    invite_request = TeamInviteCreate(
        team_id=recommendation.team_id,
        user_id=recommendation.recommendations[0].user_id,
    )

    assert invite_request.team_id == 10
    assert invite_request.user_id == 2
    assert invite_request.expires_at is None
