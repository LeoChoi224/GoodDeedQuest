from __future__ import annotations

# =========================================================
# [확인 및 검토할 사항]
#
# 1. 최소 핵심 테스트
#    - 전체 세부 조합을 모두 테스트하지 않습니다.
#    - 정상 추천 흐름, 빈 후보 흐름, 치명적 오류 변환만 확인합니다.
#
# 2. 저장 위치
#    - ai/app/challenge_recommend/test/test_graph.py
#
# 3. 실행 명령어
#    - python -m pytest ai/app/challenge_recommend/test/test_graph.py -v
# =========================================================

import pytest

from ai.app.challenge_recommend.agent import (
    RecommendationGraphError,
    run_team_recommendation,
)
from ai.app.challenge_recommend.schemas import (
    TeamRecommendationRequest,
)


def make_request(
    *,
    candidates: list[dict] | None = None,
    top_k: int = 2,
) -> TeamRecommendationRequest:
    """Graph 테스트에 사용할 정상 추천 요청을 생성합니다."""

    if candidates is None:
        candidates = [
            {
                "user_id": 2,
                "nickname": "환경지킴이",
                "region": "서울",
                "preferred_categories": [5],
                "preferred_difficulty": "easy",
                "active_time": [6, 12],
                "current_level": 20,
                "daily_streak": 30,
                "profile_embedding": [1.0, 0.0, 0.0],
                "recent_activity": {
                    "completed_count": 2,
                    "category_counts": {"환경": 2},
                    "difficulty_counts": {"easy": 2},
                    "active_time_counts": {"6": 1, "12": 1},
                },
            },
            {
                "user_id": 3,
                "nickname": "도움이",
                "region": "부산",
                "preferred_categories": [9],
                "preferred_difficulty": "hard",
                "active_time": [20],
                "current_level": 1,
                "daily_streak": 0,
                "profile_embedding": [0.0, 1.0, 0.0],
            },
        ]

    return TeamRecommendationRequest.model_validate(
        {
            "requester_id": 1,
            "team": {
                "team_id": 10,
                "quest_id": 100,
                "name": "서울 환경팀",
                "region": "서울",
                "active_time": [6, 12],
                "current_members": 2,
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
    )


def test_graph_returns_ranked_recommendations_with_fallback_reason() -> None:
    """LLM 생성기 없이도 규칙 기반 이유와 순위가 반환되는지 확인합니다."""

    response = run_team_recommendation(make_request())

    assert response.team_id == 10
    assert response.quest_id == 100
    assert response.recommendation_count == 2
    assert [item.rank for item in response.recommendations] == [1, 2]
    assert response.recommendations[0].user_id == 2
    assert response.recommendations[0].score.total_score == 100.0
    assert response.recommendations[0].recommendation_reason
    assert response.warnings


def test_graph_returns_empty_response_when_candidates_are_empty() -> None:
    """후보가 없으면 실패하지 않고 빈 추천 목록을 반환하는지 확인합니다."""

    response = run_team_recommendation(
        make_request(
            candidates=[],
            top_k=5,
        )
    )

    assert response.recommendations == []
    assert response.recommendation_count == 0
    assert response.requested_top_k == 5
    assert response.warnings == []


def test_agent_raises_graph_error_when_scoring_node_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """점수 계산 실패 State가 호출자용 예외로 변환되는지 확인합니다."""

    def raise_scoring_error(*args, **kwargs):
        raise RuntimeError("강제 점수 계산 오류")

    monkeypatch.setattr(
        "ai.app.challenge_recommend.nodes.score_candidates",
        raise_scoring_error,
    )

    with pytest.raises(
        RecommendationGraphError,
        match="추천 후보 점수 계산에 실패했습니다",
    ):
        run_team_recommendation(make_request())
