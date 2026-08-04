from __future__ import annotations

# =========================================================
# [확인 및 검토할 사항]
#
# 1. Repository는 flush()까지만 수행.
#    최종 commit()과 오류 발생 시 rollback()은 공통 get_db()에서 처리.
#
# 2. 게시글 수정·사용자 직접 삭제 기능은 이번 프로젝트 범위에서 구현하지 않습니다.
# =========================================================

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from pathlib import PurePosixPath
from urllib.parse import urlparse
from uuid import uuid4

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app.auth.enums import UserRole
from backend.app.auth.models import User
from backend.app.common.s3_client import (
    CommunityVideoTranscodeTimeoutError,
    copy_s3_object,
    generate_download_presigned_url,
    transcode_s3_video_for_community,
)
from backend.app.community.models import CommunityPost
from backend.app.community.repository import (
    CommunityRepository,
    DuplicateCommunityPostError,
)
from backend.app.community.scoring import (
    CommunityRecommendationScore,
    calculate_community_recommendation_score,
)
from backend.app.community.schema import (
    CommunityAuthorResponse,
    CommunityCommentDetailResponse,
    CommunityFeedItemResponse,
    CommunityPostCreate,
    FeedHiddenPreferenceResponse,
    CommunityPostResponse,
    PostLikeToggleResponse,
    PostLikeUserResponse,
    CommunityPostUpdate,
    RecentQuestSubmissionResponse,
    CommunityReportCreate,
    CommunityReportResponse,
    CommunityUserProfileResponse,
    CommunityUserQuestAchievementResponse,
)

from backend.app.quest_verification.enums import MediaType

VIDEO_FILE_EXTENSIONS = {".mp4", ".mov", ".m4v", ".webm"}
KST = ZoneInfo("Asia/Seoul")
DEFAULT_PROFILE_TITLE = "선행 초보자"


def _to_download_url(stored_media: str) -> str:
    """DB의 S3 key를 조회용 URL로 바꾸되 기존 외부 URL은 그대로 유지합니다."""

    if stored_media.startswith(("http://", "https://")):
        return stored_media

    return generate_download_presigned_url(stored_media)

def _to_profile_image_url(
    stored_profile_image: str | None,
) -> str | None:
    """프로필 S3 key를 조회용 URL로 바꾸고 빈 값은 그대로 처리합니다."""

    if not stored_profile_image:
        return None

    return _to_download_url(stored_profile_image)

def _infer_media_type(stored_media: str) -> MediaType:
    """기존 게시글도 표시할 수 있도록 key 또는 URL 확장자에서 유형을 판별합니다."""

    media_path = urlparse(stored_media).path
    extension = PurePosixPath(media_path).suffix.lower()

    if extension in VIDEO_FILE_EXTENSIONS:
        return MediaType.VIDEO

    return MediaType.PHOTO

def _get_extra_media_keys(submission: object) -> list[str]:
    """QuestSubmission의 유효한 추가 미디어 S3 key를 순서대로 반환합니다."""

    raw_extra_media = getattr(
        submission,
        "extra_media_urls",
        None,
    )

    if not isinstance(raw_extra_media, list):
        return []

    return [
        media_key.strip()
        for media_key in raw_extra_media
        if isinstance(media_key, str) and media_key.strip()
    ]

def _build_permanent_media_key(
    *,
    user_id: int,
    submission_id: int,
    source_key: str,
    media_type: MediaType | None,
) -> str:
    """30일 만료 대상과 분리된 community/ 영구 저장 key를 만듭니다."""

    if media_type == MediaType.VIDEO:
        # 동영상은 변환 결과가 항상 MP4입니다.
        extension = ".mp4"
    else:
        extension = PurePosixPath(source_key).suffix.lower() or ".jpg"

    return (
        f"community/{user_id}/{submission_id}/"
        f"{uuid4().hex}{extension}"
    )

# 추천 점수가 계산된 게시글 후보를 Service 내부에서 관리.
class _ScoredCommunityFeedCandidate:
    """점수 계산이 완료된 커뮤니티 추천 후보."""
    def __init__(
        self,
        *,
        post: CommunityPost,
        author: User,
        like_count: int,
        comment_count: int,
        is_liked: bool,
        recommendation_score: CommunityRecommendationScore,
    ) -> None:
        self.post = post
        self.author = author
        self.like_count = like_count
        self.comment_count = comment_count
        self.is_liked = is_liked
        self.recommendation_score = recommendation_score

# 게시글 생성 시각을 추천 정렬에 사용할 UTC timestamp로 변환.
def _get_feed_sort_timestamp(created_at: datetime) -> float:
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    else:
        created_at = created_at.astimezone(timezone.utc)

    return created_at.timestamp()

def _get_viewable_user(
    db: Session,
    *,
    user_id: int,
    current_user: User,
) -> User:
    """일반 사용자는 활성 사용자만, 관리자는 전체 사용자를 조회합니다."""

    user = CommunityRepository.get_user_by_id(
        db=db,
        user_id=user_id,
    )

    is_admin = current_user.role == UserRole.ADMIN

    if user is None or (not user.is_active and not is_admin):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다.",
        )

    return user


def _compute_daily_streak(
    db: Session,
    *,
    user_id: int,
) -> int:
    """실제 접속 기록을 기준으로 연속 접속일을 계산합니다."""

    activity_dates = CommunityRepository.list_user_activity_dates(
        db=db,
        user_id=user_id,
    )

    if not activity_dates:
        return 0

    today = datetime.now(KST).date()

    expected = (
        today
        if activity_dates[0] == today
        else today - timedelta(days=1)
    )

    if activity_dates[0] != expected:
        return 0

    streak = 0

    for activity_date in activity_dates:
        if activity_date != expected:
            break

        streak += 1
        expected -= timedelta(days=1)

    return streak


def get_community_user_profile(
    db: Session,
    *,
    user_id: int,
    current_user: User,
) -> CommunityUserProfileResponse:
    """다른 사용자 상세 화면에 필요한 공개 프로필을 반환합니다."""

    user = _get_viewable_user(
        db=db,
        user_id=user_id,
        current_user=current_user,
    )

    title = CommunityRepository.get_equipped_badge_name(
        db=db,
        user_id=user_id,
    )

    border_image_url = (
        CommunityRepository.get_equipped_border_image_url(
            db=db,
            user_id=user_id,
        )
    )

    return CommunityUserProfileResponse(
        nickname=user.nickname,
        title=title or DEFAULT_PROFILE_TITLE,
        current_level=user.current_level,
        daily_streak=_compute_daily_streak(
            db=db,
            user_id=user_id,
        ),
        profile_image_url=_to_profile_image_url(
            user.profile_image_url,
        ),
        equipped_border_image_url=border_image_url,
    )


def get_community_user_quest_achievements(
    db: Session,
    *,
    user_id: int,
    current_user: User,
) -> list[CommunityUserQuestAchievementResponse]:
    """다른 사용자의 공개 퀘스트 달성 내역을 반환합니다."""

    _get_viewable_user(
        db=db,
        user_id=user_id,
        current_user=current_user,
    )

    rows = CommunityRepository.list_user_quest_achievements(
        db=db,
        user_id=user_id,
    )

    return [
        CommunityUserQuestAchievementResponse(
            submission_id=submission.submission_id,
            quest_id=quest.quest_id,
            title=quest.quest_title,
            description=quest.quest_description,
            category_code=category_code,
            completed_at=submission.submitted_at,
            reward_point=quest.reward_point,
            reward_exp=quest.reward_exp,
        )
        for submission, quest, category_code in rows
    ]

def get_recent_accepted_quest_submissions(
    db: Session,
    *,
    current_user: User,
    skip: int = 0,
    limit: int = 20,
) -> list[RecentQuestSubmissionResponse]:
    """게시글 작성에 사용할 최근 승인 인증 내역을 반환합니다."""

    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "비활성화된 사용자는 "
                "퀘스트 인증 내역을 조회할 수 없습니다."
            ),
        )

    submissions = CommunityRepository.list_recent_quest_submissions(
        db=db,
        user_id=current_user.user_id,
        skip=skip,
        limit=limit,
    )

    return [
        RecentQuestSubmissionResponse(
            submission_id=submission.submission_id,
            quest_id=submission.quest_id,
            media_url=(
                _to_download_url(submission.media_url)
                if submission.media_url
                else None
            ),
            extra_media_urls=[
                _to_download_url(extra_media_key)
                for extra_media_key in _get_extra_media_keys(
                    submission,
                )
            ],
            media_type=(
                submission.media_type
                or _infer_media_type(submission.media_url)
                if submission.media_url
                else None
            ),
            submitted_at=submission.submitted_at,
        )
        for submission in submissions
    ]

# 커뮤니티 게시글 생성과 관련된 비즈니스 로직을 처리.
def create_community_post(
    db: Session,
    *,
    request: CommunityPostCreate,
    current_user: User,
) -> CommunityPostResponse:
    """현재 로그인 사용자의 커뮤니티 게시글을 생성합니다."""

    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 사용자는 게시글을 작성할 수 없습니다.",
        )

    try:
        submission = CommunityRepository.get_accepted_submission_by_id(
            db=db,
            submission_id=request.submission_id,
            user_id=current_user.user_id,
        )
    except DuplicateCommunityPostError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 커뮤니티에 등록한 퀘스트 인증입니다.",
        ) from exc

    if submission is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "게시글에 연결할 수 있는 승인된 "
                "퀘스트 인증 내역이 없습니다."
            ),
        )

    primary_media_key = (submission.media_url or "").strip()

    if not primary_media_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="인증 대표 미디어의 S3 경로가 올바르지 않습니다.",
        )

    available_media_keys = [
        primary_media_key,
        *_get_extra_media_keys(submission),
    ]

    if request.selected_media_index >= len(available_media_keys):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="선택한 인증 미디어를 찾을 수 없습니다.",
        )

    source_key = available_media_keys[
        request.selected_media_index
    ]

    expected_prefix = (
        f"submission/{current_user.user_id}/{submission.quest_id}/"
    )

    if (
        not source_key.startswith(expected_prefix)
        or ".." in source_key
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="인증 미디어의 S3 경로가 올바르지 않습니다.",
        )

    if (
        request.selected_media_index == 0
        and submission.media_type is not None
    ):
        media_type = submission.media_type
    else:
        # extra_media_urls는 PhotoPicker에서 업로드된 이미지입니다.
        media_type = _infer_media_type(source_key)

    permanent_key = _build_permanent_media_key(
        user_id=current_user.user_id,
        submission_id=submission.submission_id,
        source_key=source_key,
        media_type=media_type,
    )

    try:
        if media_type == MediaType.VIDEO:
            # 동영상은 커뮤니티 재생용 480p MP4로 변환합니다.
            transcode_s3_video_for_community(
                source_key=source_key,
                destination_key=permanent_key,
            )
        else:
            # 사진은 기존처럼 S3 내부 복사만 수행합니다.
            copy_s3_object(
                source_key=source_key,
                destination_key=permanent_key,
            )
    except CommunityVideoTranscodeTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="커뮤니티 동영상 최적화 시간이 초과되었습니다.",
        ) from exc
    except (BotoCoreError, ClientError, RuntimeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "인증 미디어를 커뮤니티용으로 "
                "저장하거나 최적화하지 못했습니다."
            ),
        ) from exc

    post = CommunityRepository.create_post(
        db=db,
        user_id=current_user.user_id,
        submission_id=request.submission_id,
        media_url=permanent_key,
        caption=request.caption,
    )

    return CommunityPostResponse(
        post_id=post.post_id,
        user_id=post.user_id,
        submission_id=post.submission_id,
        media_url=_to_download_url(post.media_url),
        media_type=media_type,
        caption=post.caption,
        is_active=post.is_active,
        created_at=post.created_at,
        updated_at=post.updated_at,
    )

def update_community_post(
    db: Session,
    *,
    post_id: int,
    request: CommunityPostUpdate,
    current_user: User,
) -> CommunityPostResponse:
    """현재 로그인 사용자가 작성한 게시글 본문을 수정합니다."""

    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 사용자는 게시글을 수정할 수 없습니다.",
        )

    post = _get_active_community_post(
        db=db,
        post_id=post_id,
    )

    if post.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="본인이 작성한 게시글만 수정할 수 있습니다.",
        )

    updated_post = CommunityRepository.update_post_caption(
        db=db,
        post=post,
        caption=request.caption,
    )

    return CommunityPostResponse(
        post_id=updated_post.post_id,
        user_id=updated_post.user_id,
        submission_id=updated_post.submission_id,
        media_url=_to_download_url(updated_post.media_url),
        media_type=_infer_media_type(updated_post.media_url),
        caption=updated_post.caption,
        is_active=updated_post.is_active,
        created_at=updated_post.created_at,
        updated_at=updated_post.updated_at,
    )


def delete_community_post(
    db: Session,
    *,
    post_id: int,
    current_user: User,
) -> None:
    """현재 로그인 사용자가 작성한 게시글을 삭제합니다."""

    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 사용자는 게시글을 삭제할 수 없습니다.",
        )

    post = _get_active_community_post(
        db=db,
        post_id=post_id,
    )

    if post.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="본인이 작성한 게시글만 삭제할 수 있습니다.",
        )

    CommunityRepository.delete_post(
        db=db,
        post=post,
    )

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
        profile_image_url=_to_profile_image_url(
            user.profile_image_url,
        ),
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

# 게시글과 집계 데이터를 피드 화면 응답으로 변환.
def _build_feed_item_response(
    db: Session,
    *,
    post: CommunityPost,
    author: User,
    like_count: int,
    comment_count: int,
    is_liked: bool,
) -> CommunityFeedItemResponse:
    # Repository에서 최신 댓글부터 최대 미리보기 두 개를 조회.
    preview_rows = CommunityRepository.list_comment_previews(
        db=db,
        post_id=post.post_id,
        limit=2,
    )

    # 화면에서는 오래된 댓글부터 읽을 수 있도록 조회 결과를 뒤집음.
    comment_previews = [
        _build_comment_response(
            comment=comment,
            author=comment_author,
        )
        for comment, comment_author in reversed(preview_rows)
    ]

    return CommunityFeedItemResponse(
        post_id=post.post_id,
        submission_id=post.submission_id,
        media_url=_to_download_url(post.media_url),
        media_type=_infer_media_type(post.media_url),
        caption=post.caption,
        created_at=post.created_at,
        updated_at=post.updated_at,
        author=_build_author_response(author),
        like_count=like_count,
        comment_count=comment_count,
        is_liked=is_liked,
        comment_previews=comment_previews,
    )

def get_community_feed(
    db: Session,
    *,
    current_user: User,
    skip: int = 0,
    limit: int = 20,
) -> list[CommunityFeedItemResponse]:

    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 사용자는 커뮤니티 피드를 조회할 수 없습니다.",
        )

    """최신순 기본 피드와 댓글 미리보기를 반환합니다."""
    # 게시글과 작성자, 좋아요·댓글 집계 정보를 한 번에 조회.
    feed_rows = CommunityRepository.list_feed_posts(
        db=db,
        user_id=current_user.user_id,
        skip=skip,
        limit=limit,
    )


    # 각 게시글을 공통 피드 응답 변환 함수로 변환.
    return [
        _build_feed_item_response(
            db=db,
            post=post,
            author=author,
            like_count=like_count,
            comment_count=comment_count,
            is_liked=is_liked,
        )
        for post, author, like_count, comment_count, is_liked in feed_rows
    ]

def get_my_community_posts(
    db: Session,
    *,
    current_user: User,
    skip: int = 0,
    limit: int = 20,
) -> list[CommunityFeedItemResponse]:
    """현재 로그인 사용자가 작성한 활성 게시글을 최신순으로 반환합니다."""

    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 사용자는 자신의 게시글을 조회할 수 없습니다.",
        )

    feed_rows = CommunityRepository.list_feed_posts(
        db=db,
        user_id=current_user.user_id,
        author_id=current_user.user_id,
        skip=skip,
        limit=limit,
    )

    return [
        _build_feed_item_response(
            db=db,
            post=post,
            author=author,
            like_count=like_count,
            comment_count=comment_count,
            is_liked=is_liked,
        )
        for post, author, like_count, comment_count, is_liked in feed_rows
    ]

# 현재 사용자의 관심 정보와 게시글 반응을 이용한 개인화 피드(알고리즘)를 반환.
def get_personalized_community_feed(
    db: Session,
    *,
    current_user: User,
    skip: int = 0,
    limit: int = 20,
    candidate_limit: int = 200,
) -> list[CommunityFeedItemResponse]:

    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 사용자는 추천 피드를 조회할 수 없습니다.",
        )

    # 현재 사용자의 region_id를 이용해 추천 점수용 실제 지역명을 조회.
    user_region_name = CommunityRepository.get_region_name_by_id(
        db=db,
        region_id=current_user.region_id,
    )

    # Repository에서 관심 없음 게시글이 제외된 추천 후보를 조회.
    candidate_rows = CommunityRepository.list_personalized_feed_candidates(
        db=db,
        user_id=current_user.user_id,
        candidate_limit=candidate_limit,
    )

    # 같은 요청 안에서 모든 게시글의 최신성 기준 시간을 동일하게 사용.
    reference_time = datetime.now(timezone.utc)

    scored_candidates: list[_ScoredCommunityFeedCandidate] = []

    # 각 추천 후보에 카테고리·지역·최신성·반응도·작성자 신뢰도 점수를 계산.
    for (
        post,
        author,
        quest_category_id,
        quest_location,
        like_count,
        comment_count,
        is_liked,
    ) in candidate_rows:
        recommendation_score = calculate_community_recommendation_score(
            # User.category의 JSON 카테고리 ID 목록을 전달.
            user_category_ids=(
                current_user.category
                if isinstance(current_user.category, list)
                else None
            ),
            user_region_name=user_region_name,
            quest_category_id=quest_category_id,
            quest_location=quest_location,
            created_at=post.created_at,
            like_count=like_count,
            comment_count=comment_count,
            author_trust_score=author.trust_score,
            reference_time=reference_time,
        )

        scored_candidates.append(
            _ScoredCommunityFeedCandidate(
                post=post,
                author=author,
                like_count=like_count,
                comment_count=comment_count,
                is_liked=is_liked,
                recommendation_score=recommendation_score,
            )
        )

    # 최종 점수, 생성 시각, 게시글 ID를 모두 내림차순으로 정렬.
    scored_candidates.sort(
        key=lambda candidate: (
            candidate.recommendation_score.final_score,
            _get_feed_sort_timestamp(candidate.post.created_at),
            candidate.post.post_id,
        ),
        reverse=True,
    )

    # 점수 정렬이 완료된 전체 후보에서 요청한 페이지 범위만 추출.
    paginated_candidates = scored_candidates[
        skip : skip + limit
    ]

    return [
        _build_feed_item_response(
            db=db,
            post=candidate.post,
            author=candidate.author,
            like_count=candidate.like_count,
            comment_count=candidate.comment_count,
            is_liked=candidate.is_liked,
        )
        for candidate in paginated_candidates
    ]


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
            profile_image_url=_to_profile_image_url(
                user.profile_image_url,
            ),
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

def create_community_report(
    db: Session,
    *,
    post_id: int,
    request: CommunityReportCreate,
    current_user: User,
) -> CommunityReportResponse:
    """현재 사용자의 커뮤니티 게시글 신고를 접수합니다."""

    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 사용자는 게시글을 신고할 수 없습니다.",
        )

    post = _get_active_community_post(
        db=db,
        post_id=post_id,
    )

    if post.user_id == current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="본인이 작성한 게시글은 신고할 수 없습니다.",
        )

    existing_report = (
        CommunityRepository.get_report_by_reporter_and_post(
            db=db,
            reporter_id=current_user.user_id,
            post_id=post_id,
        )
    )

    if existing_report is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 신고한 게시글입니다.",
        )

    report = CommunityRepository.create_report(
        db=db,
        reporter_id=current_user.user_id,
        post_id=post_id,
        reason=request.reason,
    )

    return CommunityReportResponse.model_validate(report)