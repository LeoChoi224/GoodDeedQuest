from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class RecommendedFacility(BaseModel):
    """다른 지역의 추천 시설 정보 (문구 생성용 최소 정보만 포함)."""

    vol_name: str = Field(..., description="추천 시설(기관)명")
    region_name: str = Field(..., description="추천 시설이 위치한 지역명")


class LackingCategoryCommentRequest(BaseModel):
    """부족 카테고리 안내 문구 생성 요청."""

    region_name: str = Field(..., description="부족 카테고리를 판단한 기준 지역명")
    lacking_category: str = Field(..., description="가장 부족한 봉사 카테고리")
    recommended_facilities: List[RecommendedFacility] = Field(
        default_factory=list,
        description="다른 지역에서 찾은 같은 카테고리 추천 시설 목록 (없을 수도 있음)",
    )


class LackingCategoryComment(BaseModel):
    """LLM structured output 스키마 (chain.invoke()의 반환 타입)."""

    comment: str = Field(..., description="사용자에게 보여줄 자연어 안내 문구 (1~2문장)")


class LackingCategoryCommentResponse(BaseModel):
    """API 응답 최상위 스키마."""

    comment: str