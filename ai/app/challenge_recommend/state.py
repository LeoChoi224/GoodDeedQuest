from __future__ import annotations

# =========================================================
# [확인 및 검토할 사항]
#
# 1. 이 파일의 역할
#    - LangGraph 팀원 추천 워크플로우의 모든 Node가 공유하는 State를 정의합니다.
#    - Backend 요청값 자체는 schemas.py의 TeamRecommendationRequest가 검증합니다.
#    - 이 파일은 검증이 끝난 요청과 각 Node의 중간 결과를 연결합니다.
#
# 2. State 처리 원칙
#    - 각 Node는 전체 State를 다시 만들지 않고, 변경한 필드만 dict로 반환합니다.
#    - 예:
#        return {"scored_candidates": scored_candidates}
#    - LangGraph가 반환된 필드만 기존 State에 반영합니다.
#
# 3. 처리 흐름
#    - request
#      → scored_candidates
#      → ranked_candidates
#      → recommendation_reasons
#      → recommendations
#      → response
#
# 4. 오류와 경고의 차이
#    - warnings:
#      일부 기능이 Fallback으로 처리되었지만 최종 추천 결과는 반환할 수 있는 경우
#    - errors:
#      정상적인 최종 추천 결과를 만들 수 없는 치명적인 오류가 발생한 경우
#
# 5. LLM Fallback
#    - LLM 추천 이유 생성에 실패해도 규칙 기반 점수와 순위는 유지합니다.
#    - 이 경우 warnings에 내용을 추가하고 기본 추천 이유를 사용합니다.
#
# 6. 리스트 Reducer를 사용하지 않는 이유
#    - 현재 그래프는 점수 계산 → 정렬 → 추천 이유 생성 → 응답 생성의 순차 구조입니다.
#    - 각 단계의 리스트는 기존 값에 누적하지 않고 해당 Node 결과로 교체하는 것이 안전합니다.
#    - 이후 병렬 Node에서 결과를 합쳐야 한다면 Annotated와 Reducer 적용을 별도로 검토합니다.
#
# 7. TypedDict를 사용하는 이유
#    - LangGraph Node는 dict의 일부 필드만 반환하는 방식을 자연스럽게 지원합니다.
#    - Pydantic Schema는 외부 입출력 검증에 사용하고,
#      TypedDict State는 내부 워크플로우 데이터 전달에 사용합니다.
#
# 8. 초기 State
#    - create_initial_recommendation_state()를 사용하면
#      테스트와 agent.py에서 동일한 초기값을 만들 수 있습니다.
# =========================================================

from typing import Literal, NotRequired, TypedDict

from .schemas import (
    CandidateRecommendationReason,
    RecommendationResult,
    ScoredRecommendationCandidate,
    TeamRecommendationRequest,
    TeamRecommendationResponse,
)


# 추천 워크플로우가 현재 어느 단계까지 진행되었는지 나타냅니다.
RecommendationWorkflowStatus = Literal[
    "pending",
    "scoring",
    "ranking",
    "generating_reasons",
    "building_response",
    "completed",
    "failed",
]


class RecommendationMetadata(TypedDict):
    """추천 처리 과정의 운영·디버깅 정보를 저장합니다."""

    # Backend가 전달한 전체 후보 수입니다.
    candidate_count: int

    # 규칙 기반 점수 계산을 완료한 후보 수입니다.
    scored_candidate_count: int

    # Top-K 정렬 이후 남은 후보 수입니다.
    ranked_candidate_count: int

    # LLM 추천 이유가 정상적으로 생성된 후보 수입니다.
    generated_reason_count: int

    # Fallback 추천 이유를 사용한 후보 수입니다.
    fallback_reason_count: int

    # 최종 응답에 포함된 추천 후보 수입니다.
    recommendation_count: int


class RecommendationState(TypedDict):
    """LangGraph 팀원 추천 워크플로우 전체가 공유하는 State입니다."""

    # ---------------------------------------------------------
    # 1. 입력 단계
    # ---------------------------------------------------------

    # schemas.py에서 검증을 완료한 추천 요청입니다.
    request: TeamRecommendationRequest

    # ---------------------------------------------------------
    # 2. 규칙 기반 점수 계산 단계
    # ---------------------------------------------------------

    # 모든 후보에게 규칙 기반 점수를 계산한 결과입니다.
    scored_candidates: list[ScoredRecommendationCandidate]

    # ---------------------------------------------------------
    # 3. 정렬 및 Top-K 단계
    # ---------------------------------------------------------

    # 총점 내림차순으로 정렬하고 Top-K만 남긴 후보 목록입니다.
    ranked_candidates: list[ScoredRecommendationCandidate]

    # ---------------------------------------------------------
    # 4. LLM 추천 이유 생성 단계
    # ---------------------------------------------------------

    # LLM이 생성한 사용자별 추천 이유입니다.
    recommendation_reasons: list[CandidateRecommendationReason]

    # LLM에 실제 전달한 Prompt입니다.
    # 운영 환경에서는 개인정보나 긴 Prompt가 로그에 남지 않도록 저장 여부를 검토합니다.
    llm_prompt: NotRequired[str | None]

    # LLM의 원본 응답입니다.
    # 구조화 파싱 오류를 분석할 때만 사용하고 외부 API 응답에는 포함하지 않습니다.
    llm_raw_response: NotRequired[str | None]

    # ---------------------------------------------------------
    # 5. 최종 추천 결과 조립 단계
    # ---------------------------------------------------------

    # 점수·순위·추천 이유를 합친 최종 후보 목록입니다.
    recommendations: list[RecommendationResult]

    # Backend에 반환할 최종 Pydantic 응답 객체입니다.
    response: TeamRecommendationResponse | None

    # ---------------------------------------------------------
    # 6. 공통 상태 및 오류 처리
    # ---------------------------------------------------------

    # 현재 워크플로우 진행 단계입니다.
    status: RecommendationWorkflowStatus

    # 처리 중 발생한 비치명적 경고입니다.
    warnings: list[str]

    # 처리 중 발생한 치명적 오류입니다.
    errors: list[str]

    # 후보 수와 Fallback 수 등 처리 메타데이터입니다.
    metadata: RecommendationMetadata


def create_initial_recommendation_state(
    request: TeamRecommendationRequest,
) -> RecommendationState:
    """검증된 추천 요청으로 LangGraph 초기 State를 생성합니다.

    이 함수는 agent.py와 테스트에서 동일한 초기값을 사용하도록 하여
    필드 누락과 초기값 불일치를 방지합니다.
    """

    return RecommendationState(
        request=request,
        scored_candidates=[],
        ranked_candidates=[],
        recommendation_reasons=[],
        recommendations=[],
        response=None,
        status="pending",
        warnings=[],
        errors=[],
        metadata=RecommendationMetadata(
            candidate_count=len(request.candidates),
            scored_candidate_count=0,
            ranked_candidate_count=0,
            generated_reason_count=0,
            fallback_reason_count=0,
            recommendation_count=0,
        ),
    )


def has_fatal_error(
    state: RecommendationState,
) -> bool:
    """State에 치명적인 오류가 존재하는지 확인합니다.

    graph.py의 조건부 Edge에서 다음 Node로 이동할지,
    오류 종료 Node로 이동할지 판단할 때 사용할 수 있습니다.
    """

    return bool(state["errors"]) or state["status"] == "failed"


def should_generate_recommendation_reasons(
    state: RecommendationState,
) -> bool:
    """LLM 추천 이유 생성 단계를 실행할 수 있는지 확인합니다.

    치명적인 오류가 없고 정렬된 후보가 한 명 이상 있을 때만
    추천 이유 생성 Node로 이동합니다.
    """

    return (
        not has_fatal_error(state)
        and bool(state["ranked_candidates"])
    )