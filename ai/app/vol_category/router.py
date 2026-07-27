from __future__ import annotations

from fastapi import APIRouter, status

from ai.app.vol_category.comment_generator import generate_lacking_category_comment
from ai.app.vol_category.schemas import (
    LackingCategoryCommentRequest,
    LackingCategoryCommentResponse,
)

router = APIRouter(prefix="/ai/vol-category", tags=["AI Volunteer Category"])


@router.post(
    "/lacking-comment",
    response_model=LackingCategoryCommentResponse,
    status_code=status.HTTP_200_OK,
    summary="지역별 부족 봉사 카테고리 안내 문구 생성",
)
def generate_comment(
    request: LackingCategoryCommentRequest,
) -> LackingCategoryCommentResponse:
    comment = generate_lacking_category_comment(request)
    return LackingCategoryCommentResponse(comment=comment)