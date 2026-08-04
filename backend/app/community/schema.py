from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.app.quest_verification.enums import MediaType


class CommunityPostCreate(BaseModel):
    """커뮤니티 게시글 생성 요청."""

    submission_id: int = Field(
        ...,
        gt=0,
        description="게시글과 연결할 승인된 퀘스트 인증 ID",
    )

    selected_media_index: int = Field(
        default=0,
        ge=0,
        le=4,
        description=(
            "커뮤니티 게시글에 사용할 인증 미디어 순서. "
            "0은 대표 미디어, 1~4는 extra_media_urls입니다."
        ),
    )

    caption: str | None = Field(
        default=None,
        max_length=5000,
        description="게시글 내용",
    )

    @field_validator("caption")
    @classmethod
    def validate_caption_not_blank(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        stripped_value = value.strip()

        if not stripped_value:
            raise ValueError("게시글 내용은 공백일 수 없습니다.")

        return stripped_value

class CommunityPostUpdate(BaseModel):
    """커뮤니티 게시글 수정 요청."""

    caption: str | None = Field(
        ...,
        max_length=5000,
        description="수정할 게시글 내용. null이면 내용을 비웁니다.",
    )

    @field_validator("caption")
    @classmethod
    def validate_caption_not_blank(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        stripped_value = value.strip()

        if not stripped_value:
            raise ValueError("게시글 내용은 공백일 수 없습니다.")

        return stripped_value

class RecentQuestSubmissionResponse(BaseModel):
    """커뮤니티 게시글 작성에 사용할 최근 승인 인증 응답."""

    model_config = ConfigDict(from_attributes=True)

    submission_id: int
    quest_id: int
    media_url: str | None
    extra_media_urls: list[str] = Field(
        default_factory=list,
        description="AI 인증에 사용된 추가 사진 조회 URL 목록",
    )
    media_type: MediaType | None
    submitted_at: datetime


class CommunityPostStatusUpdate(BaseModel):
    """관리자가 게시글 활성 상태를 변경할 때 사용하는 요청."""

    is_active: bool = Field(
        ...,
        description="게시글 활성 여부",
    )


class CommunityPostResponse(BaseModel):
    """커뮤니티 게시글 조회 응답."""

    model_config = ConfigDict(from_attributes=True)

    post_id: int
    user_id: int
    submission_id: int
    media_url: str
    media_type: MediaType
    caption: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

class CommunityAuthorResponse(BaseModel):
    """커뮤니티 작성자 요약 응답."""

    user_id: int
    nickname: str
    profile_image_url: str | None

class CommunityUserProfileResponse(BaseModel):
    """다른 사용자 상세 화면에 표시할 공개 프로필 응답."""

    nickname: str
    title: str
    current_level: int
    daily_streak: int
    profile_image_url: str | None
    equipped_border_image_url: str | None = None


class CommunityUserQuestAchievementResponse(BaseModel):
    """다른 사용자의 공개 퀘스트 달성 타임라인 응답."""

    submission_id: int
    quest_id: int
    title: str
    description: str
    category_code: str
    completed_at: datetime
    reward_point: int | None
    reward_exp: int | None

class CommunityCommentDetailResponse(BaseModel):
    """작성자 정보가 포함된 댓글 응답."""

    comment_id: int
    post_id: int
    content: str
    created_at: datetime
    updated_at: datetime
    author: CommunityAuthorResponse

class CommunityFeedItemResponse(BaseModel):
    """기본 커뮤니티 피드 게시글 응답."""

    post_id: int
    submission_id: int
    media_url: str
    media_type: MediaType
    caption: str | None
    created_at: datetime
    updated_at: datetime

    author: CommunityAuthorResponse

    like_count: int = Field(
        ...,
        ge=0,
        description="게시글 좋아요 수",
    )

    comment_count: int = Field(
        ...,
        ge=0,
        description="게시글 댓글 수",
    )

    is_liked: bool = Field(
        ...,
        description="현재 사용자의 좋아요 여부",
    )

    comment_previews: list[CommunityCommentDetailResponse] = Field(
        default_factory=list,
        description="피드에 표시할 최근 댓글 미리보기",
    )


class PostLikeToggleResponse(BaseModel):
    """게시글 좋아요 토글 결과."""

    post_id: int
    is_liked: bool

    like_count: int = Field(
        ...,
        ge=0,
        description="토글 처리 후 게시글 좋아요 수",
    )


class PostLikeUserResponse(BaseModel):
    """게시글을 좋아요 한 사용자 응답."""

    user_id: int
    nickname: str
    profile_image_url: str | None


class CommunityCommentCreate(BaseModel):
    """게시글 댓글 생성 요청."""

    content: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="댓글 내용",
    )

    @field_validator("content")
    @classmethod
    def validate_community_comment_not_blank(cls, value: str) -> str:
        stripped_value = value.strip()

        if not stripped_value:
            raise ValueError("댓글 내용은 공백일 수 없습니다.")

        return stripped_value



class PostLikeCreate(BaseModel):
    """게시글 좋아요 생성 요청."""

    post_id: int = Field(
        ...,
        gt=0,
        description="좋아요를 누를 게시글 ID",
    )


class PostLikeResponse(BaseModel):
    """게시글 좋아요 조회 응답."""

    model_config = ConfigDict(from_attributes=True)

    post_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime



class CommentCreate(BaseModel):
    """댓글 생성 요청."""

    post_id: int = Field(
        ...,
        gt=0,
        description="댓글을 작성할 게시글 ID",
    )

    content: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="댓글 내용",
    )

    @field_validator("content")
    @classmethod
    def validate_content_not_blank(cls, value: str) -> str:
        stripped_value = value.strip()

        if not stripped_value:
            raise ValueError("댓글 내용은 공백일 수 없습니다.")

        return stripped_value


class CommentResponse(BaseModel):
    """댓글 조회 응답."""

    model_config = ConfigDict(from_attributes=True)

    comment_id: int
    post_id: int
    user_id: int
    content: str
    created_at: datetime
    updated_at: datetime



class FeedHiddenPreferenceCreate(BaseModel):
    """사용자가 게시글을 관심 없음으로 처리할 때 사용하는 요청."""

    post_id: int = Field(
        ...,
        gt=0,
        description="관심 없음으로 처리할 게시글 ID",
    )


class FeedHiddenPreferenceResponse(BaseModel):
    """관심 없음 처리 기록 조회 응답."""

    model_config = ConfigDict(from_attributes=True)

    hidden_id: int
    user_id: int
    post_id: int
    created_at: datetime
    updated_at: datetime



class UserActivityLogCreate(BaseModel):
    """접속 기록 생성 요청.

    user_id와 access_date는 서버에서 자동 처리한다.
    """

    pass


class UserActivityLogResponse(BaseModel):
    """사용자의 일별 접속 기록 조회 응답."""

    model_config = ConfigDict(from_attributes=True)

    activity_id: int
    user_id: int
    access_date: date

class CommunityReportCreate(BaseModel):
    """커뮤니티 게시글 신고 요청."""

    reason: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="게시글 신고 사유",
    )

    @field_validator("reason")
    @classmethod
    def validate_reason_not_blank(cls, value: str) -> str:
        stripped_value = value.strip()

        if not stripped_value:
            raise ValueError("신고 사유는 공백일 수 없습니다.")

        return stripped_value


class CommunityReportResponse(BaseModel):
    """커뮤니티 게시글 신고 접수 응답."""

    model_config = ConfigDict(from_attributes=True)

    report_id: int
    reporter_id: int
    post_id: int | None
    reason: str
    status: str
    created_at: datetime