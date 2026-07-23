from __future__ import annotations

# =========================================================
# [확인 및 검토할 사항]
#
# 1. 이 파일의 역할
#    - LangGraph 추천 흐름에서 실제 작업을 수행하는 Node를 정의합니다.
#    - DB 조회는 수행하지 않습니다.
#    - Backend에서 전달되어 schemas.py 검증을 통과한 데이터만 사용합니다.
#
# 2. 현재 포함된 Node
#    - score_candidates_node:
#      모든 후보의 규칙 기반 추천 점수를 계산합니다.
#
#    - rank_candidates_node:
#      총점이 높은 순서로 정렬하고 요청한 Top-K만 남깁니다.
#
#    - create_recommendation_reason_node:
#      추천 이유 생성기를 주입받아 LLM 추천 이유를 생성합니다.
#      생성기가 없거나 LLM 호출이 실패하면 규칙 기반 기본 이유를 사용합니다.
#
#    - build_recommendations_node:
#      점수·순위·추천 이유를 하나의 최종 후보 결과로 합칩니다.
#
#    - build_response_node:
#      Backend에 반환할 최종 TeamRecommendationResponse를 만듭니다.
#
# 3. Prompt와 LLM 연동
#    - prompts.py와 실제 LLM 호출 코드는 다음 단계에서 작성합니다.
#    - 이 파일은 RecommendationReasonGenerator Protocol을 제공하므로,
#      이후 LLM 구현체가 generate() 메서드만 맞추면 Node 수정 없이 연결할 수 있습니다.
#
# 4. Fallback 정책
#    - 규칙 기반 점수 계산 실패는 추천 자체를 만들 수 없으므로 치명적 오류입니다.
#    - LLM 추천 이유 생성 실패는 점수와 순위가 이미 있으므로 비치명적 오류입니다.
#    - LLM 실패 시 warnings를 추가하고 규칙 기반 기본 추천 이유를 사용합니다.
#
# 5. State 변경 방식
#    - Node는 State 전체를 직접 수정하지 않습니다.
#    - 변경할 필드만 새 dict로 반환합니다.
#    - warnings, errors, metadata도 기존 값을 복사한 뒤 새 값으로 교체합니다.
#
# 6. 정렬 기준
#    - 1순위: total_score 내림차순
#    - 2순위: user_id 오름차순
#    - 같은 입력은 항상 같은 순서를 반환하도록 고정합니다.
#
# 7. 개인정보와 로그
#    - llm_prompt와 llm_raw_response는 디버깅 목적으로만 State에 저장할 수 있습니다.
#    - 운영 환경에서는 개인정보 노출과 로그 용량을 고려해 저장 여부를 검토합니다.
# =========================================================

from dataclasses import dataclass, field
from typing import Any, Protocol, Sequence, runtime_checkable

from .schemas import (
    CandidateRecommendationReason,
    RecommendationResult,
    ScoredRecommendationCandidate,
    TeamRecommendationResponse,
)
from .scoring import score_candidates
from .state import (
    RecommendationMetadata,
    RecommendationState,
    has_fatal_error,
)


# LLM Fallback 시 최종 결과에 사용할 기본 문장입니다.
DEFAULT_RECOMMENDATION_REASON = (
    "팀과 퀘스트의 추천 기준을 종합했을 때 적합도가 높은 사용자입니다."
)

# 추천 이유 생성에 실패했을 때 State에 남길 공통 경고 문장입니다.
LLM_FALLBACK_WARNING = (
    "추천 이유 생성에 실패하여 규칙 기반 추천 이유를 사용했습니다."
)


@dataclass(slots=True)
class RecommendationReasonGenerationResult:
    """추천 이유 생성기가 Node에 반환하는 표준 결과입니다."""

    # 사용자별 구조화된 추천 이유입니다.
    reasons: list[CandidateRecommendationReason]

    # 실제 LLM에 전달한 Prompt입니다.
    prompt: str | None = None

    # LLM이 반환한 파싱 전 원본 응답입니다.
    raw_response: str | None = None

    # 일부 후보만 Fallback 처리한 경우 등 비치명적 경고입니다.
    warnings: list[str] = field(default_factory=list)


@runtime_checkable
class RecommendationReasonGenerator(Protocol):
    """Prompt·LLM 구현체가 따라야 하는 추천 이유 생성 인터페이스입니다."""

    def generate(
        self,
        *,
        state: RecommendationState,
        candidates: Sequence[ScoredRecommendationCandidate],
    ) -> RecommendationReasonGenerationResult:
        """정렬된 추천 후보의 사용자별 추천 이유를 생성합니다."""


def _copy_metadata(
    state: RecommendationState,
) -> RecommendationMetadata:
    """기존 Metadata를 복사하여 Node 간 직접 변경을 방지합니다."""

    return RecommendationMetadata(**state["metadata"])


def _append_unique_messages(
    existing: Sequence[str],
    new_messages: Sequence[str],
) -> list[str]:
    """기존 순서를 유지하면서 중복되지 않는 메시지만 추가합니다."""

    result = list(existing)
    seen = set(result)

    for message in new_messages:
        normalized = message.strip()

        if not normalized or normalized in seen:
            continue

        seen.add(normalized)
        result.append(normalized)

    return result


def _score_value(
    candidate: ScoredRecommendationCandidate,
    field_name: str,
) -> float:
    """후보 점수 항목을 안전하게 float으로 반환합니다."""

    return float(getattr(candidate.score, field_name, 0.0))


def _build_rule_based_highlights(
    candidate: ScoredRecommendationCandidate,
) -> list[str]:
    """점수가 높은 추천 항목을 사용자에게 보여줄 핵심 근거로 변환합니다."""

    score_labels = [
        (
            _score_value(candidate, "category_score"),
            "관심 카테고리 적합도가 높습니다.",
        ),
        (
            _score_value(candidate, "difficulty_score"),
            "선호 난이도가 퀘스트와 잘 맞습니다.",
        ),
        (
            _score_value(candidate, "active_time_score"),
            "활동 시간대가 팀 일정과 잘 맞습니다.",
        ),
        (
            _score_value(candidate, "region_score"),
            "활동 지역이 팀과 가깝거나 일치합니다.",
        ),
        (
            _score_value(candidate, "embedding_score"),
            "프로필과 퀘스트의 의미적 유사도가 높습니다.",
        ),
        (
            _score_value(candidate, "daily_streak_score"),
            "최근 꾸준한 활동 기록이 있습니다.",
        ),
        (
            _score_value(candidate, "user_level_score"),
            "퀘스트 수행 경험과 사용자 레벨이 충분합니다.",
        ),
    ]

    # 점수가 높은 항목부터 정렬하고 0점인 항목은 제외합니다.
    sorted_labels = sorted(
        score_labels,
        key=lambda item: -item[0],
    )

    return [
        label
        for score, label in sorted_labels
        if score > 0
    ][:3]


def build_rule_based_reason(
    candidate: ScoredRecommendationCandidate,
) -> CandidateRecommendationReason:
    """LLM 없이 점수 항목만으로 안전한 기본 추천 이유를 생성합니다."""

    highlights = _build_rule_based_highlights(candidate)

    if highlights:
        reason_text = " ".join(highlights)
    else:
        reason_text = DEFAULT_RECOMMENDATION_REASON

    return CandidateRecommendationReason(
        user_id=candidate.user_id,
        recommendation_reason=reason_text,
        highlights=highlights,
    )


def build_rule_based_reasons(
    candidates: Sequence[ScoredRecommendationCandidate],
) -> list[CandidateRecommendationReason]:
    """여러 후보의 규칙 기반 기본 추천 이유를 생성합니다."""

    return [
        build_rule_based_reason(candidate)
        for candidate in candidates
    ]


def score_candidates_node(
    state: RecommendationState,
) -> dict[str, Any]:
    """모든 추천 후보의 규칙 기반 점수를 계산합니다."""

    if has_fatal_error(state):
        return {}

    metadata = _copy_metadata(state)

    try:
        request = state["request"]

        # Pydantic 모델을 scoring.py가 사용하는 일반 dict로 변환합니다.
        scored_data = score_candidates(
            team=request.team.model_dump(),
            quest=request.quest.model_dump(),
            candidates=[
                candidate.model_dump()
                for candidate in request.candidates
            ],
        )

        # scoring.py 결과를 Pydantic Schema로 다시 검증합니다.
        scored_candidates = [
            ScoredRecommendationCandidate.model_validate(candidate)
            for candidate in scored_data
        ]

    except Exception as exc:
        errors = _append_unique_messages(
            state["errors"],
            [
                "추천 후보 점수 계산에 실패했습니다. "
                f"원인: {type(exc).__name__}: {exc}"
            ],
        )

        metadata["scored_candidate_count"] = 0

        return {
            "scored_candidates": [],
            "status": "failed",
            "errors": errors,
            "metadata": metadata,
        }

    metadata["scored_candidate_count"] = len(scored_candidates)

    return {
        "scored_candidates": scored_candidates,
        "status": "scoring",
        "metadata": metadata,
    }


def rank_candidates_node(
    state: RecommendationState,
) -> dict[str, Any]:
    """점수 계산 결과를 정렬하고 요청된 Top-K 후보만 선택합니다."""

    if has_fatal_error(state):
        return {}

    metadata = _copy_metadata(state)

    try:
        top_k = state["request"].top_k

        # scoring.py도 정렬하지만 Node 책임을 명확히 하기 위해 다시 정렬합니다.
        ranked_candidates = sorted(
            state["scored_candidates"],
            key=lambda candidate: (
                -float(candidate.score.total_score),
                candidate.user_id,
            ),
        )[:top_k]

    except Exception as exc:
        errors = _append_unique_messages(
            state["errors"],
            [
                "추천 후보 정렬에 실패했습니다. "
                f"원인: {type(exc).__name__}: {exc}"
            ],
        )

        metadata["ranked_candidate_count"] = 0

        return {
            "ranked_candidates": [],
            "status": "failed",
            "errors": errors,
            "metadata": metadata,
        }

    metadata["ranked_candidate_count"] = len(ranked_candidates)

    return {
        "ranked_candidates": ranked_candidates,
        "status": "ranking",
        "metadata": metadata,
    }


def _validate_generated_reasons(
    *,
    candidates: Sequence[ScoredRecommendationCandidate],
    reasons: Sequence[CandidateRecommendationReason],
) -> tuple[
    list[CandidateRecommendationReason],
    int,
    list[str],
]:
    """LLM 이유를 후보 목록과 대조하고 누락·중복 결과를 Fallback으로 보완합니다."""

    warnings: list[str] = []
    candidate_by_user_id = {
        candidate.user_id: candidate
        for candidate in candidates
    }

    valid_reason_by_user_id: dict[int, CandidateRecommendationReason] = {}

    for reason in reasons:
        user_id = reason.user_id

        if user_id not in candidate_by_user_id:
            warnings.append(
                f"후보 목록에 없는 user_id={user_id}의 추천 이유를 무시했습니다."
            )
            continue

        if user_id in valid_reason_by_user_id:
            warnings.append(
                f"user_id={user_id}의 중복 추천 이유를 하나만 사용했습니다."
            )
            continue

        valid_reason_by_user_id[user_id] = reason

    normalized_reasons: list[CandidateRecommendationReason] = []
    fallback_count = 0

    # 최종 추천 순서를 유지하기 위해 후보 순서대로 이유를 다시 구성합니다.
    for candidate in candidates:
        generated_reason = valid_reason_by_user_id.get(candidate.user_id)

        if generated_reason is not None:
            normalized_reasons.append(generated_reason)
            continue

        fallback_count += 1
        normalized_reasons.append(
            build_rule_based_reason(candidate)
        )
        warnings.append(
            f"user_id={candidate.user_id}의 추천 이유가 없어 "
            "규칙 기반 추천 이유를 사용했습니다."
        )

    return (
        normalized_reasons,
        fallback_count,
        warnings,
    )


def create_recommendation_reason_node(
    reason_generator: RecommendationReasonGenerator | None = None,
):
    """추천 이유 생성기를 주입받아 LangGraph Node 함수를 생성합니다.

    다음 단계에서 prompts.py와 LLM 구현체를 작성하면 아래처럼 연결할 수 있습니다.

    reason_node = create_recommendation_reason_node(
        reason_generator=llm_reason_generator,
    )

    생성기를 전달하지 않으면 모든 후보에게 규칙 기반 추천 이유를 사용합니다.
    """

    def generate_recommendation_reasons_node(
        state: RecommendationState,
    ) -> dict[str, Any]:
        """LLM 추천 이유를 생성하고 실패 시 규칙 기반 이유로 대체합니다."""

        if has_fatal_error(state):
            return {}

        candidates = state["ranked_candidates"]
        metadata = _copy_metadata(state)

        # 추천 후보가 없으면 LLM을 호출하지 않고 정상적으로 다음 단계로 이동합니다.
        if not candidates:
            metadata["generated_reason_count"] = 0
            metadata["fallback_reason_count"] = 0

            return {
                "recommendation_reasons": [],
                "llm_prompt": None,
                "llm_raw_response": None,
                "status": "generating_reasons",
                "metadata": metadata,
            }

        # LLM 구현체가 아직 없거나 비활성화된 경우 전체 후보를 Fallback 처리합니다.
        if reason_generator is None:
            fallback_reasons = build_rule_based_reasons(candidates)
            warnings = _append_unique_messages(
                state["warnings"],
                [LLM_FALLBACK_WARNING],
            )

            metadata["generated_reason_count"] = 0
            metadata["fallback_reason_count"] = len(fallback_reasons)

            return {
                "recommendation_reasons": fallback_reasons,
                "llm_prompt": None,
                "llm_raw_response": None,
                "status": "generating_reasons",
                "warnings": warnings,
                "metadata": metadata,
            }

        try:
            generation_result = reason_generator.generate(
                state=state,
                candidates=candidates,
            )

            (
                normalized_reasons,
                fallback_count,
                validation_warnings,
            ) = _validate_generated_reasons(
                candidates=candidates,
                reasons=generation_result.reasons,
            )

            warnings = _append_unique_messages(
                state["warnings"],
                [
                    *generation_result.warnings,
                    *validation_warnings,
                ],
            )

            generated_reason_count = (
                len(normalized_reasons) - fallback_count
            )

            metadata["generated_reason_count"] = generated_reason_count
            metadata["fallback_reason_count"] = fallback_count

            return {
                "recommendation_reasons": normalized_reasons,
                "llm_prompt": generation_result.prompt,
                "llm_raw_response": generation_result.raw_response,
                "status": "generating_reasons",
                "warnings": warnings,
                "metadata": metadata,
            }

        except Exception as exc:
            fallback_reasons = build_rule_based_reasons(candidates)

            warnings = _append_unique_messages(
                state["warnings"],
                [
                    LLM_FALLBACK_WARNING,
                    "추천 이유 생성 오류: "
                    f"{type(exc).__name__}: {exc}",
                ],
            )

            metadata["generated_reason_count"] = 0
            metadata["fallback_reason_count"] = len(fallback_reasons)

            return {
                "recommendation_reasons": fallback_reasons,
                "llm_prompt": None,
                "llm_raw_response": None,
                "status": "generating_reasons",
                "warnings": warnings,
                "metadata": metadata,
            }

    return generate_recommendation_reasons_node


# LLM 구현체를 전달하지 않는 기본 Node입니다.
# graph.py에서 Fallback 전용 실행 또는 초기 개발 단계에 사용할 수 있습니다.
generate_recommendation_reasons_node = (
    create_recommendation_reason_node()
)


def build_recommendations_node(
    state: RecommendationState,
) -> dict[str, Any]:
    """정렬된 후보와 추천 이유를 합쳐 최종 후보 결과를 생성합니다."""

    if has_fatal_error(state):
        return {}

    metadata = _copy_metadata(state)

    try:
        reason_by_user_id = {
            reason.user_id: reason
            for reason in state["recommendation_reasons"]
        }

        recommendations: list[RecommendationResult] = []
        warnings_to_add: list[str] = []
        fallback_count = metadata["fallback_reason_count"]

        for rank, candidate in enumerate(
            state["ranked_candidates"],
            start=1,
        ):
            reason = reason_by_user_id.get(candidate.user_id)

            if reason is None:
                reason = build_rule_based_reason(candidate)
                fallback_count += 1
                warnings_to_add.append(
                    f"user_id={candidate.user_id}의 추천 이유가 누락되어 "
                    "최종 조립 단계에서 규칙 기반 이유를 사용했습니다."
                )

            # 후보 원본 정보와 점수를 유지한 채 추천 이유·순위를 추가합니다.
            recommendation_data = candidate.model_dump()
            recommendation_data.update(
                {
                    "recommendation_reason": (
                        reason.recommendation_reason
                    ),
                    "rank": rank,
                }
            )

            recommendations.append(
                RecommendationResult.model_validate(
                    recommendation_data
                )
            )

        warnings = _append_unique_messages(
            state["warnings"],
            warnings_to_add,
        )

    except Exception as exc:
        errors = _append_unique_messages(
            state["errors"],
            [
                "최종 추천 후보 조립에 실패했습니다. "
                f"원인: {type(exc).__name__}: {exc}"
            ],
        )

        metadata["recommendation_count"] = 0

        return {
            "recommendations": [],
            "status": "failed",
            "errors": errors,
            "metadata": metadata,
        }

    metadata["fallback_reason_count"] = fallback_count
    metadata["recommendation_count"] = len(recommendations)

    return {
        "recommendations": recommendations,
        "status": "building_response",
        "warnings": warnings,
        "metadata": metadata,
    }


def build_response_node(
    state: RecommendationState,
) -> dict[str, Any]:
    """현재 State를 Backend 반환용 최종 응답 Schema로 변환합니다."""

    if has_fatal_error(state):
        return {}

    metadata = _copy_metadata(state)

    try:
        request = state["request"]
        recommendations = state["recommendations"]

        response = TeamRecommendationResponse(
            team_id=request.team.team_id,
            quest_id=request.quest.quest_id,
            recommendations=recommendations,
            requested_top_k=request.top_k,
            recommendation_count=len(recommendations),
            warnings=state["warnings"],
        )

    except Exception as exc:
        errors = _append_unique_messages(
            state["errors"],
            [
                "최종 추천 응답 생성에 실패했습니다. "
                f"원인: {type(exc).__name__}: {exc}"
            ],
        )

        metadata["recommendation_count"] = 0

        return {
            "response": None,
            "status": "failed",
            "errors": errors,
            "metadata": metadata,
        }

    metadata["recommendation_count"] = len(recommendations)

    return {
        "response": response,
        "status": "completed",
        "metadata": metadata,
    }