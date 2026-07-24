from __future__ import annotations

# =========================================================
# [확인 및 검토할 사항]
#
# 1. 모든 Community API는 /community 경로를 사용합니다.
#
# 2. 게시글 생성은 로그인한 사용자만 가능.
#
# 3. 현재 사용자 인증은 Auth에서 사용 중인 get_current_db_user 의존성을 재사용.
#
# =========================================================

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.auth.models import User
from backend.app.auth.router import get_current_db_user
from backend.app.common.database import get_db
from backend.app.community import service
from backend.app.community.schema import (
    CommunityPostCreate,
    CommunityPostResponse,
)

router = APIRouter(
    prefix="/community",
    tags=["Community"],
)

# 로그인한 사용자가 새 커뮤니티 게시글을 생성하는 API.
@router.post(
    "/posts",
    response_model=CommunityPostResponse,
    status_code=status.HTTP_201_CREATED,
    summary="커뮤니티 게시글 생성",
)
def create_community_post(
    request: CommunityPostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_db_user),
) -> CommunityPostResponse:
    """로그인한 사용자의 새 커뮤니티 게시글을 생성합니다."""

    # Service를 호출하여 게시글 생성과 인증 내역 검증을 처리.
    post = service.create_community_post(
        db=db,
        request=request,
        current_user=current_user,
    )

    return CommunityPostResponse.model_validate(post)