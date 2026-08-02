from __future__ import annotations

# =========================================================
# [확인 및 검토할 사항]
#
# 1. 저장 위치
#    - ai/app/challenge_recommend/test/test_llm_reason_generator.py
#
# 2. 테스트 범위
#    - 실제 OpenAI API는 호출하지 않습니다.
#    - 정상 배열 JSON과 user_id-key 객체 JSON을 모두 검증합니다.
#    - 실제 API 장애 없이 LLM 이유가 Node에서 LLM 결과로 유지되는지 검증합니다.
#    - 잘못된 JSON과 잘못된 reasons 값은 명확한 예외로 처리합니다.
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
from ai.app.challenge_recommend.nodes import (
    create_recommendation_reason_node,
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


def test_generate_normalizes_user_id_keyed_reason_mapping() -> None:
    """실제 오류 형태의 reasons 객체가 표준 배열로 변환되는지 확인합니다."""

    fake_model = FakeChatModel(
        '''{
          "reasons": {
            "2": "환경지킴이님은 환경 분야에 관심이 있고 서울에서 활동할 수 있어 공원 정화 퀘스트를 함께하기 좋은 친구예요."
          }
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
    assert result.reasons[0].reason_source == "LLM"
    assert "공원 정화" in result.reasons[0].recommendation_reason
    assert result.reasons[0].highlights == []


def test_generate_normalizes_user_id_keyed_reason_object() -> None:
    """user_id-key 객체의 상세 이유 형식도 표준 배열로 변환합니다."""

    generator = OpenAIRecommendationReasonGenerator(
        chat_model=FakeChatModel(
            '''{
              "reasons": {
                "2": {
                  "recommendation_reason": "환경 관심사와 서울 지역 조건이 잘 맞아 공원 정화 활동을 함께하기 좋은 친구예요.",
                  "highlights": ["환경 관심", "서울 지역"]
                }
              }
            }'''
        ),
    )
    request = make_request()

    result = generator.generate(
        state=create_initial_recommendation_state(request),
        candidates=make_scored_candidates(request),
    )

    assert result.reasons[0].user_id == 2
    assert result.reasons[0].highlights == [
        "환경 관심",
        "서울 지역",
    ]


def test_reason_node_keeps_normalized_mapping_as_llm_result() -> None:
    """객체 응답이 전체 Fallback으로 바뀌지 않고 LLM 이유로 유지되는지 확인합니다."""

    generator = OpenAIRecommendationReasonGenerator(
        chat_model=FakeChatModel(
            '''{
              "reasons": {
                "2": "환경지킴이님은 환경 관심사와 오전 활동 시간이 잘 맞아 공원 정화 퀘스트에 함께하기 좋은 친구예요."
              }
            }'''
        ),
    )
    request = make_request()
    state = create_initial_recommendation_state(request)
    state["ranked_candidates"] = make_scored_candidates(request)

    result = create_recommendation_reason_node(generator)(state)
    reasons = result["recommendation_reasons"]

    assert len(reasons) == 1
    assert reasons[0].reason_source == "LLM"
    assert result["metadata"]["generated_reason_count"] == 1
    assert result["metadata"]["fallback_reason_count"] == 0
    assert result["warnings"] == []


def test_prompt_requires_reasons_array_output() -> None:
    """Prompt가 reasons 배열과 후보별 user_id를 명확히 요구하는지 확인합니다."""

    fake_model = FakeChatModel(
        '''{
          "reasons": [
            {
              "user_id": 2,
              "recommendation_reason": "환경 관심사와 활동 시간이 잘 맞는 친구예요.",
              "highlights": []
            }
          ]
        }'''
    )
    generator = OpenAIRecommendationReasonGenerator(
        chat_model=fake_model,
    )
    request = make_request()

    generator.generate(
        state=create_initial_recommendation_state(request),
        candidates=make_scored_candidates(request),
    )

    user_prompt = fake_model.received_input[1].content

    assert "reasons는 객체가 아니라 반드시" in user_prompt
    assert '"reasons": [' in user_prompt
    assert '"user_id": 2' in user_prompt


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


def test_generate_raises_error_when_reason_mapping_value_is_invalid() -> None:
    """문자열·객체가 아닌 reasons 값은 임의 보정하지 않고 차단합니다."""

    generator = OpenAIRecommendationReasonGenerator(
        chat_model=FakeChatModel(
            '''{
              "reasons": {
                "2": 123
              }
            }'''
        ),
    )
    request = make_request()

    with pytest.raises(
        RecommendationReasonLLMError,
        match="Schema와 일치하지 않습니다",
    ):
        generator.generate(
            state=create_initial_recommendation_state(request),
            candidates=make_scored_candidates(request),
        )
