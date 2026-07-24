from __future__ import annotations

# =========================================================
# [확인 및 검토할 사항]
#
# 1. Repository는 flush()까지만 수행.
#    최종 commit()과 오류 발생 시 rollback()은m공통 get_db()에서 처리.
#
# 2. 게시글 수정·사용자 직접 삭제 기능은
#    이번 프로젝트 범위에서 구현하지 않습니다.
# =========================================================

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app.auth.models import User
from backend.app.community.models import CommunityPost
from backend.app.community.repository import CommunityRepository
from backend.app.community.schema import CommunityPostCreate


# 커뮤니티 게시글 생성과 관련된 비즈니스 로직을 처리.
def create_community_post(
    db: Session,
    *,
    request: CommunityPostCreate,
    current_user: User,
) -> CommunityPost:
    """현재 로그인 사용자의 커뮤니티 게시글을 생성합니다."""

    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 사용자는 게시글을 작성할 수 없습니다.",
        )

    # 요청에 퀘스트 인증 ID가 포함된 경우 해당 인증 내역을 검증.
    if request.submission_id is not None:
        submission = CommunityRepository.get_accepted_submission_by_id(
            db,
            submission_id=request.submission_id,
            user_id=current_user.user_id,
        )

        if submission is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "게시글에 연결할 수 있는 승인된 "
                    "퀘스트 인증 내역이 없습니다."
                ),
            )

    # 검증이 완료된 요청 데이터로 새 커뮤니티 게시글을 생성.
    post = CommunityRepository.create_post(
        db,
        user_id=current_user.user_id,
        submission_id=request.submission_id,
        media_url=request.media_url,
        caption=request.caption,
    )

    return post