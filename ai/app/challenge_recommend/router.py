from __future__ import annotations

# =========================================================
# [AI 팀원 추천 Router 구현 기준]
#
# 1. API 경로
#    - POST /ai/challenge/recommend
#
# 2. 처리 흐름
#    - 요청 Schema 검증
#    - LangGraph 비동기 실행
#    - 최종 추천 응답 반환
#
# 3. 오류 처리
#    - 요청 형식 오류는 FastAPI가 422로 처리합니다.
#    - Graph 내부 치명적 오류는 503으로 변환합니다.
#    - LLM 오류는 규칙 기반 추천 이유로 대체하므로
#      점수와 순위를 포함한 정상 응답을 반환할 수 있습니다.
# =========================================================

from fastapi import APIRouter, HTTPException, status

from . import agent
from .schemas import (
    TeamRecommendationRequest,
    TeamRecommendationResponse,
)


router = APIRouter(
    prefix="/ai/challenge",
    tags=["AI Challenge Recommendation"],
)


@router.post(
    "/recommend",
    response_model=TeamRecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="팀 챌린지 추천 사용자 조회",
)
async def recommend_challenge_members(
    request: TeamRecommendationRequest,
) -> TeamRecommendationResponse:
    """팀과 Quest에 적합한 추천 사용자 목록을 반환합니다."""

    try:
        return await agent.run_team_recommendation_async(request)

    except agent.RecommendationGraphError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI 팀원 추천 처리에 실패했습니다.",
        ) from exc
