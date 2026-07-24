from __future__ import annotations

# =========================================================
# [확인 및 검토할 사항]
#
# 1. Repository는 flush()까지만 수행.
#    최종 commit()과 오류 발생 시 rollback()은 공통 get_db()에서 처리.
#
# 2. 게시글 수정·사용자 직접 삭제 기능은 이번 프로젝트 범위에서 구현하지 않습니다.
# =========================================================

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app.auth.models import User
from backend.app.community.models import CommunityPost
from backend.app.community.repository import CommunityRepository
from backend.app.community.schema import (
    CommunityAuthorResponse,
    CommunityCommentDetailResponse,
    CommunityFeedItemResponse,
    CommunityPostCreate,
    FeedHiddenPreferenceResponse,
    PostLikeToggleResponse,
    PostLikeUserResponse,
)


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
            db=db,
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
        db=db,
        user_id=current_user.user_id,
        submission_id=request.submission_id,
        media_url=request.media_url,
        caption=request.caption,
    )

    return post


# 일반 사용자가 조회하거나 활동할 수 있는 활성 게시글인지 확인.
def _get_active_community_post(
    db: Session,
    *,
    post_id: int,
) -> CommunityPost:
    """활성 커뮤니티 게시글을 조회하거나 404 오류를 발생시킵니다."""

    # 게시글 ID로 게시글 한 건을 조회.
    post = CommunityRepository.get_post_by_id(
        db=db,
        post_id=post_id,
    )

    if post is None or not post.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="게시글을 찾을 수 없습니다.",
        )

    return post


def _build_author_response(
    user: User,
) -> CommunityAuthorResponse:
    """User 모델을 커뮤니티 작성자 응답으로 변환합니다."""

    return CommunityAuthorResponse(
        user_id=user.user_id,
        nickname=user.nickname,
        profile_image_url=user.profile_image_url,
    )

def _build_comment_response(
    *,
    comment,
    author: User,
) -> CommunityCommentDetailResponse:
    """댓글 모델과 작성자 모델을 댓글 응답으로 변환합니다."""

    return CommunityCommentDetailResponse(
        comment_id=comment.comment_id,
        post_id=comment.post_id,
        content=comment.content,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
        author=_build_author_response(author),
    )

def get_community_feed(
    db: Session,
    *,
    current_user: User,
    skip: int = 0,
    limit: int = 20,
) -> list[CommunityFeedItemResponse]:
    """최신순 기본 피드와 댓글 미리보기를 반환합니다."""

    # 게시글과 작성자, 좋아요·댓글 집계 정보를 한 번에 조회.
    feed_rows = CommunityRepository.list_feed_posts(
        db=db,
        user_id=current_user.user_id,
        skip=skip,
        limit=limit,
    )

    feed_items: list[CommunityFeedItemResponse] = []

    # 각 게시글을 피드 화면용 응답으로 변환.
    for post, author, like_count, comment_count, is_liked in feed_rows:
        # Repository는 최신 댓글부터 최대 두 개를 반환.
        preview_rows = CommunityRepository.list_comment_previews(
            db=db,
            post_id=post.post_id,
            limit=2,
        )

        # 화면에서는 오래된 댓글부터 자연스럽게 읽히도록 순서를 뒤집습니다.
        comment_previews = [
            _build_comment_response(
                comment=comment,
                author=comment_author,
            )
            for comment, comment_author in reversed(preview_rows)
        ]

        feed_items.append(
            CommunityFeedItemResponse(
                post_id=post.post_id,
                submission_id=post.submission_id,
                media_url=post.media_url,
                caption=post.caption,
                created_at=post.created_at,
                updated_at=post.updated_at,
                author=_build_author_response(author),
                like_count=like_count,
                comment_count=comment_count,
                is_liked=is_liked,
                comment_previews=comment_previews,
            )
        )

    return feed_items

def toggle_post_like(
    db: Session,
    *,
    post_id: int,
    current_user: User,
) -> PostLikeToggleResponse:
    """좋아요가 없으면 생성하고 있으면 취소합니다."""

    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 사용자는 좋아요를 처리할 수 없습니다.",
        )

    # 존재하며 활성 상태인 게시글인지 확인.
    _get_active_community_post(
        db=db,
        post_id=post_id,
    )

    # 현재 사용자의 기존 좋아요 기록을 조회.
    existing_like = CommunityRepository.get_post_like(
        db=db,
        post_id=post_id,
        user_id=current_user.user_id,
    )

    # 좋아요가 이미 있으면 삭제하여 취소.
    if existing_like is not None:
        CommunityRepository.delete_post_like(
            db=db,
            post_like=existing_like,
        )
        is_liked = False

    # 좋아요가 없으면 새 기록을 생성.
    else:
        CommunityRepository.create_post_like(
            db=db,
            post_id=post_id,
            user_id=current_user.user_id,
        )
        is_liked = True

    # 토글 이후의 최신 좋아요 수를 조회.
    like_count = CommunityRepository.count_post_likes(
        db=db,
        post_id=post_id,
    )

    return PostLikeToggleResponse(
        post_id=post_id,
        is_liked=is_liked,
        like_count=like_count,
    )

def get_post_like_users(
    db: Session,
    *,
    post_id: int,
    skip: int = 0,
    limit: int = 20,
) -> list[PostLikeUserResponse]:
    """게시글 좋아요 사용자 목록을 최신 좋아요순으로 반환합니다."""

    # 존재하며 활성 상태인 게시글인지 확인합니다.
    _get_active_community_post(
        db=db,
        post_id=post_id,
    )

    users = CommunityRepository.list_post_like_users(
        db=db,
        post_id=post_id,
        skip=skip,
        limit=limit,
    )

    return [
        PostLikeUserResponse(
            user_id=user.user_id,
            nickname=user.nickname,
            profile_image_url=user.profile_image_url,
        )
        for user in users
    ]

def create_post_comment(
    db: Session,
    *,
    post_id: int,
    content: str,
    current_user: User,
) -> CommunityCommentDetailResponse:
    """현재 사용자의 새 댓글을 생성합니다."""

    # 비활성 사용자는 댓글을 작성할 수 없습니다.
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 사용자는 댓글을 작성할 수 없습니다.",
        )

    _get_active_community_post(
        db=db,
        post_id=post_id,
    )

    comment = CommunityRepository.create_comment(
        db=db,
        post_id=post_id,
        user_id=current_user.user_id,
        content=content,
    )

    return _build_comment_response(
        comment=comment,
        author=current_user,
    )


def get_post_comments(
    db: Session,
    *,
    post_id: int,
    skip: int = 0,
    limit: int = 50,
) -> list[CommunityCommentDetailResponse]:
    """게시글 댓글을 오래된 댓글부터 시간순으로 반환합니다."""

    _get_active_community_post(
        db=db,
        post_id=post_id,
    )

    comment_rows = CommunityRepository.list_post_comments(
        db=db,
        post_id=post_id,
        skip=skip,
        limit=limit,
    )

    return [
        _build_comment_response(
            comment=comment,
            author=author,
        )
        for comment, author in comment_rows
    ]


# 게시글을 사용자의 관심 없음 데이터로 기록.
def hide_post_from_recommendation(
    db: Session,
    *,
    post_id: int,
    current_user: User,
) -> FeedHiddenPreferenceResponse:

    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 사용자는 관심 없음 처리를 할 수 없습니다.",
        )

    _get_active_community_post(
        db=db,
        post_id=post_id,
    )

    # 동일한 관심 없음 기록이 이미 있는지 확인.
    hidden_preference = CommunityRepository.get_hidden_preference(
        db=db,
        user_id=current_user.user_id,
        post_id=post_id,
    )

    # 기존 기록이 없을 때만 새 기록을 생성.
    if hidden_preference is None:
        hidden_preference = CommunityRepository.create_hidden_preference(
            db=db,
            user_id=current_user.user_id,
            post_id=post_id,
        )

    # 이미 처리된 요청도 오류 없이 동일한 기록을 반환.
    return FeedHiddenPreferenceResponse.model_validate(
        hidden_preference
    )