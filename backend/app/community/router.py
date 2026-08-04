from __future__ import annotations

# =========================================================
# [구현 기준]
#
# 1. 모든 Community API는 /community 경로를 사용합니다.
#
# 2. 로그인 필수 기능
#    - 게시글 생성 / 기본 피드 조회 / 좋아요 토글 / 댓글 생성 / 관심 없음 기록
#
# 3. 단순 조회 기능
#    - 좋아요 사용자 목록 / 댓글 전체 목록
#
# 4. 현재 사용자 인증은 Auth의 get_current_db_user 의존성을 재사용.
#
# 5. 관심 없음 API는 게시글을 즉시 숨기지 않고 추천 알고리즘에서 사용할 기록만 생성.
#
# 6. 개인화 추천 피드
#    - 사용자의 관심 카테고리·지역과 게시글 최신성·반응도를 기준으로 정렬.
#    - 관심 없음으로 기록한 게시글은 추천 후보에서 제외.
#    - 점수가 같으면 최신 게시글과 큰 post_id를 우선.
# =========================================================

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.auth.models import User
from backend.app.auth.router import get_current_db_user
from backend.app.common.database import get_db
from backend.app.community import service
from backend.app.community.schema import (
    CommunityCommentCreate,
    CommunityCommentDetailResponse,
    CommunityFeedItemResponse,
    CommunityPostCreate,
    CommunityPostResponse,
    CommunityPostUpdate,
    FeedHiddenPreferenceResponse,
    PostLikeToggleResponse,
    PostLikeUserResponse,
    RecentQuestSubmissionResponse,
    CommunityReportCreate,
    CommunityReportResponse,
    CommunityUserProfileResponse,
    CommunityUserQuestAchievementResponse,
)

router = APIRouter(
    prefix="/community",
    tags=["Community"],
)

@router.get(
    "/users/{user_id}/profile",
    response_model=CommunityUserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="사용자 공개 프로필 조회",
)
def get_community_user_profile(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_db_user),
) -> CommunityUserProfileResponse:
    return service.get_community_user_profile(
        db=db,
        user_id=user_id,
        current_user=current_user,
    )


@router.get(
    "/users/{user_id}/quests/achievements",
    response_model=list[CommunityUserQuestAchievementResponse],
    status_code=status.HTTP_200_OK,
    summary="사용자 달성 퀘스트 타임라인 조회",
)
def get_community_user_quest_achievements(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_db_user),
) -> list[CommunityUserQuestAchievementResponse]:
    return service.get_community_user_quest_achievements(
        db=db,
        user_id=user_id,
        current_user=current_user,
    )

@router.get(
    "/quest-submissions/recent",
    response_model=list[RecentQuestSubmissionResponse],
    status_code=status.HTTP_200_OK,
    summary="최근 승인 퀘스트 인증 목록 조회",
)
def get_recent_accepted_quest_submissions(
    skip: int = Query(
        default=0,
        ge=0,
        description="건너뛸 인증 내역 수",
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="조회할 인증 내역 수",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_db_user),
) -> list[RecentQuestSubmissionResponse]:
    """커뮤니티 게시글 작성에 사용할 승인 인증 내역을 반환합니다."""

    return service.get_recent_accepted_quest_submissions(
        db=db,
        current_user=current_user,
        skip=skip,
        limit=limit,
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

    return post


@router.patch(
    "/posts/{post_id}",
    response_model=CommunityPostResponse,
    status_code=status.HTTP_200_OK,
    summary="내 커뮤니티 게시글 수정",
)
def update_community_post(
    post_id: int,
    request: CommunityPostUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_db_user),
) -> CommunityPostResponse:
    """현재 로그인 사용자가 작성한 게시글 본문을 수정합니다."""

    return service.update_community_post(
        db=db,
        post_id=post_id,
        request=request,
        current_user=current_user,
    )


@router.delete(
    "/posts/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="내 커뮤니티 게시글 삭제",
)
def delete_community_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_db_user),
) -> None:
    """현재 로그인 사용자가 작성한 게시글을 삭제합니다."""

    service.delete_community_post(
        db=db,
        post_id=post_id,
        current_user=current_user,
    )

# 로그인한 사용자에게 기본 커뮤니티 피드를 반환.
@router.get(
    "/posts",
    response_model=list[CommunityFeedItemResponse],
    summary="커뮤니티 기본 피드 조회",
)
def get_community_feed(
    # 페이지네이션 시작 위치를 입력.
    skip: int = Query(
        default=0,
        ge=0,
        description="건너뛸 게시글 수",
    ),
    # 한 번에 조회할 게시글 수를 입력.
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="조회할 게시글 수",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_db_user),
) -> list[CommunityFeedItemResponse]:
    """활성 게시글을 최신순으로 조회합니다."""

    return service.get_community_feed(
        db=db,
        current_user=current_user,
        skip=skip,
        limit=limit,
    )

@router.get(
    "/posts/mine",
    response_model=list[CommunityFeedItemResponse],
    status_code=status.HTTP_200_OK,
    summary="내 커뮤니티 게시글 조회",
)
def get_my_community_posts(
    skip: int = Query(
        default=0,
        ge=0,
        description="건너뛸 내 게시글 수",
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="조회할 내 게시글 수",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_db_user),
) -> list[CommunityFeedItemResponse]:
    """현재 로그인 사용자가 작성한 활성 게시글을 최신순으로 반환합니다."""

    return service.get_my_community_posts(
        db=db,
        current_user=current_user,
        skip=skip,
        limit=limit,
    )

# 로그인한 사용자의 관심 정보와 게시글 반응을 반영한 추천 피드를 반환.
@router.get(
    "/posts/recommended",
    response_model=list[CommunityFeedItemResponse],
    status_code=status.HTTP_200_OK,
    summary="커뮤니티 개인화 추천 피드 조회",
)
def get_personalized_community_feed(
    skip: int = Query(
        default=0,
        ge=0,
        description="건너뛸 추천 게시글 수",
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="조회할 추천 게시글 수",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_db_user),
) -> list[CommunityFeedItemResponse]:
    """현재 사용자의 관심 정보가 반영된 추천 피드를 반환합니다."""

    return service.get_personalized_community_feed(
        db=db,
        current_user=current_user,
        skip=skip,
        limit=limit,
    )

@router.post(
    "/posts/{post_id}/likes/toggle",
    response_model=PostLikeToggleResponse,
    summary="게시글 좋아요 토글",
)
def toggle_post_like(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_db_user),
) -> PostLikeToggleResponse:
    """좋아요가 없으면 생성하고 있으면 취소합니다."""

    return service.toggle_post_like(
        db=db,
        post_id=post_id,
        current_user=current_user,
    )


@router.get(
    "/posts/{post_id}/likes",
    response_model=list[PostLikeUserResponse],
    summary="게시글 좋아요 사용자 목록 조회",
)
def get_post_like_users(
    post_id: int,
    skip: int = Query(
        default=0,
        ge=0,
        description="건너뛸 사용자 수",
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="조회할 사용자 수",
    ),
    db: Session = Depends(get_db),
) -> list[PostLikeUserResponse]:
    """게시글을 좋아요 한 사용자 목록을 반환합니다."""

    return service.get_post_like_users(
        db=db,
        post_id=post_id,
        skip=skip,
        limit=limit,
    )

@router.post(
    "/posts/{post_id}/comments",
    response_model=CommunityCommentDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="커뮤니티 댓글 생성",
)
def create_post_comment(
    post_id: int,
    request: CommunityCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_db_user),
) -> CommunityCommentDetailResponse:
    """로그인한 사용자의 새 댓글을 생성합니다."""

    return service.create_post_comment(
        db=db,
        post_id=post_id,
        content=request.content,
        current_user=current_user,
    )

@router.get(
    "/posts/{post_id}/comments",
    response_model=list[CommunityCommentDetailResponse],
    summary="커뮤니티 댓글 전체 조회",
)
def get_post_comments(
    post_id: int,
    skip: int = Query(
        default=0,
        ge=0,
        description="건너뛸 댓글 수",
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
        description="조회할 댓글 수",
    ),
    db: Session = Depends(get_db),
) -> list[CommunityCommentDetailResponse]:
    """댓글을 오래된 순서부터 조회합니다."""

    return service.get_post_comments(
        db=db,
        post_id=post_id,
        skip=skip,
        limit=limit,
    )

@router.post(
    "/posts/{post_id}/not-interested",
    response_model=FeedHiddenPreferenceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="커뮤니티 게시글 관심 없음 처리",
)
def hide_post_from_recommendation(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_db_user),
) -> FeedHiddenPreferenceResponse:
    """게시글을 추천 알고리즘용 관심 없음 데이터로 기록합니다."""

    return service.hide_post_from_recommendation(
        db=db,
        post_id=post_id,
        current_user=current_user,
    )

@router.post(
    "/posts/{post_id}/reports",
    response_model=CommunityReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="커뮤니티 게시글 신고",
)
def create_community_report(
    post_id: int,
    request: CommunityReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_db_user),
) -> CommunityReportResponse:
    """커뮤니티 게시글 신고를 접수합니다."""

    return service.create_community_report(
        db=db,
        post_id=post_id,
        request=request,
        current_user=current_user,
    )