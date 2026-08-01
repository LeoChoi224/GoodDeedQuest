from __future__ import annotations

# =========================================================
# [Challenge Schema 구현 기준]
#
# 1. 팀 요청·응답
#    - Team 응답에는 보안상 password_hash를 포함하지 않습니다.
#    - 공개 팀은 비밀번호를 사용할 수 없고,
#      비공개 팀은 비밀번호를 반드시 입력해야 합니다.
#
# 2. 팀 초대
#    - 초대 생성 요청은 team_id와 user_id를 전달합니다.
#    - 사용자 초대 응답 요청은 ACCEPTED와 REJECTED만 허용합니다.
#    - PENDING과 EXPIRED 상태는 서버 로직이 관리합니다.
#
# 3. AI 추천 응답
#    - AI 서버 응답의 정의되지 않은 추가 필드를 허용하지 않습니다.
#    - 항목별 추천 점수는 확정된 100점 배점 범위로 검증합니다.
#    - total_score가 각 항목 점수의 합계와 일치하는지 확인합니다.
#    - 추천 수, requested_top_k, 순차적인 rank와 사용자 중복을 검증합니다.
#
# 4. 서비스 간 추가 검증
#    - 응답의 팀 ID, Quest ID, 요청한 top_k와 후보 사용자 여부는
#      ChallengeRecommendationService가 추가로 검증합니다.
# =========================================================

from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from backend.app.challenge.enums import (
    TeamInviteStatus,
    TeamMemberRole,
    TeamStatus,
)



class TeamCreate(BaseModel):
    """팀 생성 요청."""

    quest_id: int = Field(
        ...,
        gt=0,
        description="팀이 수행할 퀘스트 ID",
    )

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="팀 이름",
    )

    # 클라이언트에서는 비밀번호 원문을 전달하고,
    # 서비스 계층에서 해시 처리한 뒤 password_hash 컬럼에 저장한다.
    password: str | None = Field(
        default=None,
        min_length=4,
        max_length=20,
        description="비공개 팀 입장 비밀번호",
    )

    notification: str = Field(
        default="잘 부탁드립니다.",
        min_length=1,
        max_length=2000,
        description="팀 공지사항",
    )

    region: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="팀 활동 지역",
    )

    is_public: bool = Field(
        default=True,
        description="팀 공개 여부",
    )

    max_members: int = Field(
        default=4,
        ge=2,
        le=10,
        description="팀 최대 인원",
    )

    expires_at: datetime | None = Field(
        default=None,
        description="팀 활동 만료 시각",
    )

    # 팀 이름, 공지사항, 활동 지역에 공백만 입력하는 것을 방지하고
    # 문자열 앞뒤의 불필요한 공백을 제거한다.
    @field_validator(
        "name",
        "notification",
        "region",
    )
    @classmethod
    def validate_not_blank(cls, value: str) -> str:
        stripped_value = value.strip()

        if not stripped_value:
            raise ValueError("공백만 입력할 수 없습니다.")

        return stripped_value

    # 공개 팀은 비밀번호를 사용할 수 없고,
    # 비공개 팀은 비밀번호를 반드시 입력해야 한다.
    @model_validator(mode="after")
    def validate_team_password(self) -> TeamCreate:
        if self.is_public and self.password is not None:
            raise ValueError(
                "공개 팀에는 비밀번호를 설정할 수 없습니다."
            )

        if not self.is_public and not self.password:
            raise ValueError(
                "비공개 팀은 비밀번호를 입력해야 합니다."
            )

        if self.password is not None and not self.password.strip():
            raise ValueError(
                "비밀번호는 공백만 입력할 수 없습니다."
            )

        return self


class TeamPasswordVerify(BaseModel):
    """비공개 팀 입장 비밀번호 확인 요청."""

    password: str = Field(
        ...,
        min_length=4,
        max_length=20,
        description="비공개 팀 입장 비밀번호",
    )

    @field_validator("password")
    @classmethod
    def validate_password_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("비밀번호는 공백만 입력할 수 없습니다.")

        return value

class TeamResponse(BaseModel):
    """팀 조회 응답."""

    # password_hash는 보안상 응답 Schema에 포함하지 않는다.
    model_config = ConfigDict(from_attributes=True)

    team_id: int
    leader_id: int
    quest_id: int
    name: str
    notification: str
    region: str
    is_public: bool
    max_members: int
    status: TeamStatus
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime

# 팀 목록 화면에서 팀 기본 정보와 현재 참가 인원을 반환.
class TeamListItemResponse(TeamResponse):

    current_members: int = Field(
        ...,
        ge=0,
        description="현재 팀 참가 인원",
    )

# 팀 상세 화면에서 팀 기본 정보와 현재 참가 인원을 반환.
class TeamDetailResponse(TeamResponse):

    current_members: int = Field(
        ...,
        ge=0,
        description="현재 팀 참가 인원",
    )


class TeamInviteCreate(BaseModel):
    """팀 초대 생성 요청."""

    team_id: int = Field(
        ...,
        gt=0,
        description="초대할 팀 ID",
    )

    user_id: int = Field(
        ...,
        gt=0,
        description="초대받을 사용자 ID",
    )

    expires_at: datetime | None = Field(
        default=None,
        description="초대 만료 시각",
    )


class TeamInviteStatusUpdate(BaseModel):
    """사용자가 팀 초대를 수락하거나 거절할 때 사용하는 요청 Schema.

    PENDING은 초대 생성 시 서버가 설정하고,
    EXPIRED는 만료 처리 로직과 Celery Task가 관리하므로
    클라이언트 요청값으로 허용하지 않습니다.
    """

    status: Literal[
        TeamInviteStatus.ACCEPTED,
        TeamInviteStatus.REJECTED,
    ] = Field(
        ...,
        description="초대 처리 상태: ACCEPTED 또는 REJECTED만 가능",
    )


class TeamInviteResponse(BaseModel):
    """팀 초대 조회 응답."""

    model_config = ConfigDict(from_attributes=True)

    invite_id: int
    team_id: int
    user_id: int
    status: TeamInviteStatus
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime

class TeamInviteCandidateResponse(BaseModel):
    """팀 초대 검색 결과에 표시할 공개 사용자 정보."""

    user_id: int = Field(..., gt=0)
    nickname: str = Field(..., min_length=1, max_length=50)
    profile_image_url: str | None = None
    region_id: int | None = None
    region: str | None = None
    current_level: int = Field(default=1, ge=0)
    daily_streak: int = Field(default=0, ge=0)

class TeamMemberResponse(BaseModel):
    """팀 멤버 조회 응답."""

    model_config = ConfigDict(from_attributes=True)

    team_member_id: int
    team_id: int
    user_id: int
    role_in_team: TeamMemberRole
    joined_at: datetime
    updated_at: datetime


# AI 추천 Schema에서 카테고리 ID와 이름처럼
# 정수 또는 문자열로 전달될 수 있는 값을 공통 타입으로 정의.
RecommendationComparableValue = int | str


class TeamRecommendationRecentActivityResponse(BaseModel):
    """추천 사용자의 최근 승인 완료 활동 집계 응답."""

    # AI 서버가 정의하지 않은 응답 필드를 반환하면 계약 오류로 처리.
    model_config = ConfigDict(extra="forbid")

    completed_count: int = Field(
        default=0,
        ge=0,
        description="최근 기간 동안 승인 완료된 Quest 수",
    )

    category_counts: dict[str, int] = Field(
        default_factory=dict,
        description="카테고리별 승인 완료 횟수",
    )

    difficulty_counts: dict[str, int] = Field(
        default_factory=dict,
        description="난이도별 승인 완료 횟수",
    )

    active_time_counts: dict[str, int] = Field(
        default_factory=dict,
        description="활동 시간대별 승인 완료 횟수",
    )

    @field_validator(
        "category_counts",
        "difficulty_counts",
        "active_time_counts",
    )
    @classmethod
    def validate_activity_counts(
        cls,
        value: dict[str, int],
    ) -> dict[str, int]:
        """활동 집계에 음수 또는 잘못된 값이 포함되는 것을 차단."""

        for key, count in value.items():
            if not key.strip():
                raise ValueError(
                    "활동 집계 항목 이름은 비어 있을 수 없습니다."
                )

            # bool은 int의 하위 타입이므로 별도로 차단.
            if isinstance(count, bool) or count < 0:
                raise ValueError(
                    "활동 집계 횟수는 0 이상의 정수여야 합니다."
                )

        return value


class TeamRecommendationScoreResponse(BaseModel):
    """추천 사용자의 규칙 기반 항목별 점수 응답."""

    model_config = ConfigDict(extra="forbid")

    category_score: float = Field(
        ...,
        ge=0,
        le=25,
        description="관심 카테고리 점수",
    )

    difficulty_score: float = Field(
        ...,
        ge=0,
        le=15,
        description="선호 난이도 점수",
    )

    active_time_score: float = Field(
        ...,
        ge=0,
        le=15,
        description="활동 시간대 점수",
    )

    region_score: float = Field(
        ...,
        ge=0,
        le=15,
        description="지역 일치 점수",
    )

    embedding_score: float = Field(
        ...,
        ge=0,
        le=10,
        description="Embedding 유사도 점수",
    )

    trust_score: float = Field(
        ...,
        ge=0,
        le=10,
        description="사용자 신뢰도 점수",
    )

    daily_streak_score: float = Field(
        ...,
        ge=0,
        le=5,
        description="연속 활동 점수",
    )

    user_level_score: float = Field(
        ...,
        ge=0,
        le=5,
        description="사용자 레벨 점수",
    )

    total_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="전체 추천 점수",
    )

    @model_validator(mode="after")
    def validate_total_score(
        self,
    ) -> TeamRecommendationScoreResponse:
        """총점이 항목별 점수 합계와 일치하는지 검증."""

        calculated_total = round(
            self.category_score
            + self.difficulty_score
            + self.active_time_score
            + self.region_score
            + self.embedding_score
            + self.daily_streak_score
            + self.user_level_score
            + self.trust_score,
            2,
        )

        if abs(self.total_score - calculated_total) > 0.01:
            raise ValueError(
                "total_score는 항목별 추천 점수 합계와 일치해야 합니다."
            )

        return self


class TeamRecommendedUserResponse(BaseModel):
    """AI가 점수와 추천 이유를 생성한 사용자 한 명의 응답."""

    model_config = ConfigDict(extra="forbid")

    user_id: int = Field(
        ...,
        gt=0,
        description="추천 사용자 ID",
    )

    nickname: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="추천 사용자 닉네임",
    )

    profile_image_url: str | None = Field(
        default=None,
        max_length=2048,
        description="추천 사용자 프로필 이미지 URL",
    )

    region_id: int | None = Field(
        default=None,
        gt=0,
        description="추천 사용자 지역 ID",
    )

    region: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="추천 사용자 지역 이름",
    )

    preferred_categories: list[
        RecommendationComparableValue
    ] = Field(
        default_factory=list,
        description="추천 사용자의 관심 카테고리 목록",
    )

    preferred_difficulty: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
        description="추천 사용자의 선호 난이도",
    )

    active_time: list[
        RecommendationComparableValue
    ] = Field(
        default_factory=list,
        description="추천 사용자의 선호 활동 시간대",
    )

    current_level: int = Field(
        default=0,
        ge=0,
        description="추천 사용자의 현재 레벨",
    )

    daily_streak: int = Field(
        default=0,
        ge=0,
        description="추천 사용자의 연속 활동 일수",
    )

    trust_score: int = Field(
        default=0,
        ge=0,
        le=100,
        description="추천 사용자의 원본 신뢰도",
    )

    latitude: float | None = Field(
        default=None,
        ge=-90,
        le=90,
        description="추천 사용자의 위도",
    )

    longitude: float | None = Field(
        default=None,
        ge=-180,
        le=180,
        description="추천 사용자의 경도",
    )

    profile_embedding: list[float] | None = Field(
        default=None,
        description="추천 사용자 프로필 Embedding",
    )

    recent_activity: (
        TeamRecommendationRecentActivityResponse
    ) = Field(
        default_factory=TeamRecommendationRecentActivityResponse,
        description="추천 사용자의 최근 승인 활동 집계",
    )

    score: TeamRecommendationScoreResponse = Field(
        ...,
        description="추천 사용자의 항목별 추천 점수",
    )

    recommendation_reason: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="사용자 추천 이유",
    )

    reason_source: Literal["LLM", "FALLBACK"] = Field(
        default="FALLBACK",
        description="추천 이유 생성 출처",
    )

    rank: int = Field(
        ...,
        ge=1,
        description="추천 결과 순위",
    )


class TeamRecommendationResponse(BaseModel):
    """AI 서버에서 반환한 최종 팀원 추천 응답."""

    model_config = ConfigDict(extra="forbid")

    team_id: int = Field(
        ...,
        gt=0,
        description="추천 대상 팀 ID",
    )

    quest_id: int = Field(
        ...,
        gt=0,
        description="추천 기준 Quest ID",
    )

    recommendations: list[
        TeamRecommendedUserResponse
    ] = Field(
        default_factory=list,
        description="최종 추천 사용자 목록",
    )

    requested_top_k: int = Field(
        ...,
        ge=1,
        le=5,
        description="요청한 최대 추천 사용자 수",
    )

    recommendation_count: int = Field(
        default=0,
        ge=0,
        description="실제로 반환된 추천 사용자 수",
    )

    warnings: list[str] = Field(
        default_factory=list,
        description="추천 처리 중 발생한 비치명적 경고",
    )

    @model_validator(mode="after")
    def validate_recommendation_response(
        self,
    ) -> TeamRecommendationResponse:
        """추천 개수·순위·사용자 중복을 검증."""

        actual_count = len(self.recommendations)

        if self.recommendation_count != actual_count:
            raise ValueError(
                "recommendation_count는 recommendations 길이와 "
                "일치해야 합니다."
            )

        if actual_count > self.requested_top_k:
            raise ValueError(
                "추천 결과 수는 requested_top_k를 초과할 수 없습니다."
            )

        expected_ranks = list(
            range(
                1,
                actual_count + 1,
            )
        )

        actual_ranks = [
            recommendation.rank
            for recommendation in self.recommendations
        ]

        if actual_ranks != expected_ranks:
            raise ValueError(
                "추천 결과의 rank는 1부터 순서대로 이어져야 합니다."
            )

        recommended_user_ids = [
            recommendation.user_id
            for recommendation in self.recommendations
        ]

        if len(recommended_user_ids) != len(
            set(recommended_user_ids)
        ):
            raise ValueError(
                "같은 사용자가 추천 결과에 중복될 수 없습니다."
            )

        return self