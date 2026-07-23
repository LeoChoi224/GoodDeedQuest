from __future__ import annotations

# =========================================================
# [확인 및 검토할 사항]
#
# 1. 저장 위치
#    - ai/app/challenge_recommend/test/test_llm_reason_generator.py
#
# 2. 테스트 범위
#    - 실제 OpenAI API는 호출하지 않습니다.
#    - 정상 JSON 파싱과 잘못된 JSON 예외 처리만 최소 검증합니다.
#    - 실제 API 장애 시 Graph Fallback은 test_graph.py에서 추가 검증합니다.
#
# 3. 실행 명령어
#    - python -m pytest /
#      ai/app/challenge_recommend/test/test_llm_reason_generator.py -v
# =========================================================

from types import SimpleNamespace
from typing import Any

import pytest

from ai.app.challenge_recommend.llm_reason_generator import (
    OpenAIRecommendationReasonGenerator,
    RecommendationReasonLLMError,
)
from ai.app.challenge_recommend.schemas import (
    TeamRecommendationRequest,
)
from ai.app.challenge_recommend.scoring import score_candidates
from ai.app.challenge_recommend.schemas import (
    ScoredRecommendationCandidate,
)
from ai.app.challenge_recommend.state import (
    create_initial_recommendation_state,
)


class FakeChatModel:
    """미리 정한 응답을 반환하는 테스트용 Chat Model입니다."""

    def __init__(self, response_content: str) -> None:
        self.response_content = response_content
        self.received_input: Any = None

    def invoke(self, input: Any, **kwargs: Any) -> Any:
        self.received_input = input
        return SimpleNamespace(content=self.response_content)


def make_request() -> TeamRecommendationRequest:
    """LLM 생성기 테스트용 정상 요청을 생성합니다."""

    return TeamRecommendationRequest.model_validate(
        {
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
            "candidates": [
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
            ],
            "top_k": 1,
        }
    )


def make_scored_candidates(
    request: TeamRecommendationRequest,
) -> list[ScoredRecommendationCandidate]:
    """요청 후보를 기존 scoring.py로 점수 계산합니다."""

    scored_data = score_candidates(
        team=request.team.model_dump(),
        quest=request.quest.model_dump(),
        candidates=[
            candidate.model_dump()
            for candidate in request.candidates
        ],
    )

    return [
        ScoredRecommendationCandidate.model_validate(item)
        for item in scored_data
    ]


def test_generate_returns_valid_recommendation_reasons() -> None:
    """정상 JSON 응답이 표준 생성 결과로 변환되는지 확인합니다."""

    fake_model = FakeChatModel(
        '''{
          "reasons": [
            {
              "user_id": 2,
              "recommendation_reason": "환경 관심사와 활동 시간이 잘 맞는 후보입니다.",
              "highlights": ["환경 카테고리 일치", "활동 시간대 일치"]
            }
          ]
        }'''
    )
    generator = OpenAIRecommendationReasonGenerator(
        chat_model=fake_model,
    )
    request = make_request()
    state = create_initial_recommendation_state(request)
    candidates = make_scored_candidates(request)

    result = generator.generate(
        state=state,
        candidates=candidates,
    )

    assert len(result.reasons) == 1
    assert result.reasons[0].user_id == 2
    assert "환경 관심사" in result.reasons[0].recommendation_reason
    assert result.raw_response is not None
    assert result.prompt is not None
    assert fake_model.received_input is not None


def test_generate_raises_error_when_llm_returns_invalid_json() -> None:
    """잘못된 LLM 문자열은 Node가 Fallback할 수 있도록 예외가 발생해야 합니다."""

    generator = OpenAIRecommendationReasonGenerator(
        chat_model=FakeChatModel("JSON이 아닌 응답"),
    )
    request = make_request()
    state = create_initial_recommendation_state(request)
    candidates = make_scored_candidates(request)

    with pytest.raises(
        RecommendationReasonLLMError,
        match="유효한 JSON",
    ):
        generator.generate(
            state=state,
            candidates=candidates,
        )
