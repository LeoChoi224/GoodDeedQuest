from __future__ import annotations

# =========================================================
# [확인 및 검토할 사항]
#
# 1. 최소 핵심 테스트
#    - 정상 추천 응답
#    - 후보가 없는 정상 응답
#    - 잘못된 요청의 422 처리
#    - Graph 오류의 503 변환
#
# 2. 실제 OpenAI API
#    - 호출하지 않습니다.
#    - Agent 함수를 Mock하여 HTTP 계약만 확인합니다.
#
# 3. 실행 명령어
#    - python -m pytest ai/app/challenge_recommend/test/test_router.py -v
# =========================================================

from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from ai.app.challenge_recommend.agent import RecommendationGraphError
from ai.app.challenge_recommend.router import router
from ai.app.challenge_recommend.schemas import TeamRecommendationResponse


def make_app() -> FastAPI:
    """추천 Router만 등록한 테스트용 FastAPI 앱을 생성합니다."""

    app = FastAPI()
    app.include_router(router)
    return app


def make_request_payload(
    *,
    candidates: list[dict[str, Any]] | None = None,
    top_k: int = 1,
) -> dict[str, Any]:
    """AI 추천 API 테스트용 정상 요청 Payload를 생성합니다."""

    if candidates is None:
        candidates = [
            {
                "user_id": 2,
                "nickname": "환경지킴이",
                "region": "서울",
                "preferred_categories": [5],
                "preferred_difficulty": "easy",
                "active_time": [6, 12],
                "current_level": 10,
                "daily_streak": 14,
                "profile_embedding": [1.0, 0.0, 0.0],
            }
        ]

    return {
        "requester_id": 1,
        "team": {
            "team_id": 10,
            "quest_id": 100,
            "name": "서울 환경팀",
            "region": "서울",
            "active_time": [6, 12],
            "current_members": 1,
            "max_members": 4,
        },
        "quest": {
            "quest_id": 100,
            "title": "공원 정화 활동",
            "category_id": 5,
            "category_name": "환경",
            "difficulty": "easy",
            "active_time": [6, 12],
            "description": "공원 주변 쓰레기를 수거합니다.",
            "embedding": [1.0, 0.0, 0.0],
        },
        "candidates": candidates,
        "top_k": top_k,
    }


def make_response(
    *,
    recommendations: list[dict[str, Any]] | None = None,
    requested_top_k: int = 1,
) -> TeamRecommendationResponse:
    """Router가 반환할 테스트용 AI 추천 응답을 생성합니다."""

    if recommendations is None:
        recommendations = [
            {
                "user_id": 2,
                "nickname": "환경지킴이",
                "region": "서울",
                "preferred_categories": [5],
                "preferred_difficulty": "easy",
                "active_time": [6, 12],
                "current_level": 10,
                "daily_streak": 14,
                "profile_embedding": [1.0, 0.0, 0.0],
                "score": {
                    "category_score": 30.0,
                    "difficulty_score": 15.0,
                    "active_time_score": 15.0,
                    "region_score": 15.0,
                    "embedding_score": 15.0,
                    "daily_streak_score": 5.0,
                    "user_level_score": 5.0,
                    "total_score": 100.0,
                },
                "recommendation_reason": (
                    "관심 분야와 활동 시간대가 팀의 Quest와 잘 맞습니다."
                ),
                "rank": 1,
            }
        ]

    return TeamRecommendationResponse.model_validate(
        {
            "team_id": 10,
            "quest_id": 100,
            "recommendations": recommendations,
            "requested_top_k": requested_top_k,
            "recommendation_count": len(recommendations),
            "warnings": [],
        }
    )


def test_recommend_challenge_members_returns_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """정상 요청이면 AI 추천 결과와 200 상태를 반환하는지 확인합니다."""

    received_request = None

    async def fake_run(request):
        nonlocal received_request
        received_request = request
        return make_response()

    monkeypatch.setattr(
        "ai.app.challenge_recommend.router."
        "agent.run_team_recommendation_async",
        fake_run,
    )

    client = TestClient(make_app())
    response = client.post(
        "/ai/challenge/recommend",
        json=make_request_payload(),
    )

    assert response.status_code == 200
    assert response.json()["team_id"] == 10
    assert response.json()["recommendation_count"] == 1
    assert response.json()["recommendations"][0]["user_id"] == 2
    assert received_request.requester_id == 1
    assert received_request.team.team_id == 10


def test_recommend_challenge_members_returns_empty_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """후보가 없으면 빈 추천 목록을 정상 응답으로 반환하는지 확인합니다."""

    async def fake_run(request):
        return make_response(
            recommendations=[],
            requested_top_k=request.top_k,
        )

    monkeypatch.setattr(
        "ai.app.challenge_recommend.router."
        "agent.run_team_recommendation_async",
        fake_run,
    )

    client = TestClient(make_app())
    response = client.post(
        "/ai/challenge/recommend",
        json=make_request_payload(
            candidates=[],
            top_k=5,
        ),
    )

    assert response.status_code == 200
    assert response.json()["recommendations"] == []
    assert response.json()["recommendation_count"] == 0
    assert response.json()["requested_top_k"] == 5


def test_recommend_challenge_members_rejects_invalid_payload() -> None:
    """필수 요청값이 없으면 FastAPI가 422를 반환하는지 확인합니다."""

    invalid_payload = make_request_payload()
    invalid_payload.pop("requester_id")

    client = TestClient(make_app())
    response = client.post(
        "/ai/challenge/recommend",
        json=invalid_payload,
    )

    assert response.status_code == 422


def test_recommend_challenge_members_maps_graph_error_to_503(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Graph 치명적 오류가 외부 API의 503 응답으로 변환되는지 확인합니다."""

    async def fake_run(request):
        raise RecommendationGraphError("강제 Graph 오류")

    monkeypatch.setattr(
        "ai.app.challenge_recommend.router."
        "agent.run_team_recommendation_async",
        fake_run,
    )

    client = TestClient(make_app())
    response = client.post(
        "/ai/challenge/recommend",
        json=make_request_payload(),
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "AI 팀원 추천 처리에 실패했습니다.",
    }
