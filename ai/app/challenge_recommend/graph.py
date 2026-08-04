from __future__ import annotations

# =========================================================
# [확인 및 검토할 사항]
#
# 1. 이 파일의 역할
#    - nodes.py에 작성된 LangGraph Node의 실행 순서를 연결합니다.
#    - 점수 계산, 정렬, 추천 이유 생성 로직은 직접 구현하지 않습니다.
#
# 2. 정상 실행 흐름
#    - START
#      → score_candidates
#      → rank_candidates
#      → generate_recommendation_reasons
#      → build_recommendations
#      → build_response
#      → END
#
# 3. 후보가 없는 경우
#    - rank_candidates 이후 추천 이유 생성을 생략합니다.
#    - build_recommendations와 build_response를 실행하여 빈 추천 목록을 정상 반환합니다.
#
# 4. 치명적 오류
#    - State의 errors가 존재하거나 status가 failed이면 END로 이동합니다.
#    - 최종 예외 변환은 agent.py가 담당합니다.
#
# 5. LLM Fallback
#    - reason_generator를 전달하지 않으면 nodes.py의 규칙 기반 추천 이유를 사용합니다.
# =========================================================

from typing import Literal

from langgraph.graph import END, START, StateGraph

from .nodes import (
    RecommendationReasonGenerator,
    build_recommendations_node,
    build_response_node,
    create_recommendation_reason_node,
    rank_candidates_node,
    score_candidates_node,
)
from .state import (
    RecommendationState,
    has_fatal_error,
    should_generate_recommendation_reasons,
)


SCORE_CANDIDATES_NODE = "score_candidates"
RANK_CANDIDATES_NODE = "rank_candidates"
GENERATE_REASONS_NODE = "generate_recommendation_reasons"
BUILD_RECOMMENDATIONS_NODE = "build_recommendations"
BUILD_RESPONSE_NODE = "build_response"


def route_after_scoring(
    state: RecommendationState,
) -> Literal["rank_candidates", "__end__"]:
    """점수 계산 성공 여부에 따라 정렬 단계 또는 종료로 이동합니다."""

    if has_fatal_error(state):
        return END

    return RANK_CANDIDATES_NODE


def route_after_ranking(
    state: RecommendationState,
) -> Literal[
    "generate_recommendation_reasons",
    "build_recommendations",
    "__end__",
]:
    """정렬 결과에 따라 추천 이유 생성 여부를 결정합니다."""

    if has_fatal_error(state):
        return END

    if should_generate_recommendation_reasons(state):
        return GENERATE_REASONS_NODE

    return BUILD_RECOMMENDATIONS_NODE


def route_after_reason_generation(
    state: RecommendationState,
) -> Literal["build_recommendations", "__end__"]:
    """추천 이유 생성 이후 최종 추천 결과 조립 여부를 결정합니다."""

    if has_fatal_error(state):
        return END

    return BUILD_RECOMMENDATIONS_NODE


def route_after_recommendation_build(
    state: RecommendationState,
) -> Literal["build_response", "__end__"]:
    """최종 후보 조립 이후 응답 생성 여부를 결정합니다."""

    if has_fatal_error(state):
        return END

    return BUILD_RESPONSE_NODE


def build_recommendation_graph(
    *,
    reason_generator: RecommendationReasonGenerator | None = None,
):
    """팀원 추천 LangGraph를 생성하고 실행 가능한 객체로 Compile합니다."""

    graph_builder = StateGraph(RecommendationState)

    graph_builder.add_node(
        SCORE_CANDIDATES_NODE,
        score_candidates_node,
    )
    graph_builder.add_node(
        RANK_CANDIDATES_NODE,
        rank_candidates_node,
    )
    graph_builder.add_node(
        GENERATE_REASONS_NODE,
        create_recommendation_reason_node(
            reason_generator=reason_generator,
        ),
    )
    graph_builder.add_node(
        BUILD_RECOMMENDATIONS_NODE,
        build_recommendations_node,
    )
    graph_builder.add_node(
        BUILD_RESPONSE_NODE,
        build_response_node,
    )

    graph_builder.add_edge(
        START,
        SCORE_CANDIDATES_NODE,
    )

    graph_builder.add_conditional_edges(
        SCORE_CANDIDATES_NODE,
        route_after_scoring,
        {
            RANK_CANDIDATES_NODE: RANK_CANDIDATES_NODE,
            END: END,
        },
    )

    graph_builder.add_conditional_edges(
        RANK_CANDIDATES_NODE,
        route_after_ranking,
        {
            GENERATE_REASONS_NODE: GENERATE_REASONS_NODE,
            BUILD_RECOMMENDATIONS_NODE: BUILD_RECOMMENDATIONS_NODE,
            END: END,
        },
    )

    graph_builder.add_conditional_edges(
        GENERATE_REASONS_NODE,
        route_after_reason_generation,
        {
            BUILD_RECOMMENDATIONS_NODE: BUILD_RECOMMENDATIONS_NODE,
            END: END,
        },
    )

    graph_builder.add_conditional_edges(
        BUILD_RECOMMENDATIONS_NODE,
        route_after_recommendation_build,
        {
            BUILD_RESPONSE_NODE: BUILD_RESPONSE_NODE,
            END: END,
        },
    )

    graph_builder.add_edge(
        BUILD_RESPONSE_NODE,
        END,
    )

    return graph_builder.compile()


# 실제 API Key가 있으면 OpenAI 추천 이유 생성기를 연결합니다.
# Key가 없으면 None이 전달되어 기존 규칙 기반 Fallback으로 실행됩니다.
from .llm_reason_generator import create_default_reason_generator


recommendation_graph = build_recommendation_graph(
    reason_generator=create_default_reason_generator(),
)