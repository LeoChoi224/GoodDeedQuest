from __future__ import annotations

# =========================================================
# [확인 및 검토할 사항]
#
# 1. 이 파일의 역할
#    - 외부 요청 데이터를 TeamRecommendationRequest로 검증합니다.
#    - 초기 State를 생성한 뒤 graph.py의 LangGraph를 실행합니다.
#    - 완료된 TeamRecommendationResponse만 호출자에게 반환합니다.
#
# 2. 입력 형식
#    - TeamRecommendationRequest 객체 또는 일반 dict를 받을 수 있습니다.
#
# 3. 오류 처리
#    - 입력 검증 오류는 Pydantic ValidationError가 그대로 발생합니다.
#    - Graph 내부 치명적 오류는 RecommendationGraphError로 변환합니다.
#
# 4. 비동기 실행
#    - 현재 Node가 동기 함수이지만 LangGraph의 ainvoke도 사용할 수 있습니다.
# =========================================================

from typing import Any, Mapping

from .graph import recommendation_graph
from .schemas import (
    TeamRecommendationRequest,
    TeamRecommendationResponse,
)
from .state import (
    RecommendationState,
    create_initial_recommendation_state,
    has_fatal_error,
)


class RecommendationGraphError(RuntimeError):
    """LangGraph 추천 처리 중 치명적 오류가 발생했음을 나타냅니다."""


def _validate_request(
    request: TeamRecommendationRequest | Mapping[str, Any],
) -> TeamRecommendationRequest:
    """입력값을 최종 추천 요청 Schema로 검증합니다."""

    if isinstance(request, TeamRecommendationRequest):
        return request

    return TeamRecommendationRequest.model_validate(request)


def _extract_response(
    final_state: RecommendationState,
) -> TeamRecommendationResponse:
    """최종 State에서 정상 응답을 꺼내고 실패 State는 예외로 변환합니다."""

    if has_fatal_error(final_state):
        error_message = "; ".join(final_state["errors"]).strip()

        raise RecommendationGraphError(
            error_message or "팀원 추천 처리에 실패했습니다."
        )

    response = final_state.get("response")

    if response is None:
        raise RecommendationGraphError(
            "추천 Graph가 완료되었지만 최종 응답이 생성되지 않았습니다."
        )

    return response


def run_team_recommendation(
    request: TeamRecommendationRequest | Mapping[str, Any],
) -> TeamRecommendationResponse:
    """팀원 추천 Graph를 동기 방식으로 실행합니다."""

    validated_request = _validate_request(request)
    initial_state = create_initial_recommendation_state(
        validated_request
    )

    final_state = recommendation_graph.invoke(initial_state)

    return _extract_response(final_state)


async def run_team_recommendation_async(
    request: TeamRecommendationRequest | Mapping[str, Any],
) -> TeamRecommendationResponse:
    """팀원 추천 Graph를 비동기 방식으로 실행합니다."""

    validated_request = _validate_request(request)
    initial_state = create_initial_recommendation_state(
        validated_request
    )

    final_state = await recommendation_graph.ainvoke(initial_state)

    return _extract_response(final_state)