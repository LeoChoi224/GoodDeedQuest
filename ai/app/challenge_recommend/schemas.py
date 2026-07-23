from __future__ import annotations

# =========================================================
# [확인 및 검토할 사항]
#
# 1. 이 파일의 역할
#    - Backend가 AI 서버에 전달하는 추천 요청 데이터와
#      AI 서버가 Backend에 반환하는 추천 응답 데이터의 형식을 정의합니다.
#    - LangGraph의 State 자체는 다음 단계의 state.py에서 별도로 정의합니다.
#
# 2. 현재 scoring.py와의 호환성
#    - scoring.py가 사용하는 team, quest, candidate의 모든 키를 포함합니다.
#    - model_dump() 결과를 scoring.py에 그대로 전달할 수 있습니다.
#
# 3. 누락값 처리
#    - 추천 점수 계산에서 Fallback이 가능한 값은 대부분 Optional 또는 기본값으로 둡니다.
#    - 단, 추천 대상을 식별하는 team_id, quest_id, candidate.user_id는 필수입니다.
#
# 4. Enum 사용 여부
#    - Backend Enum 값이 문자열로 직렬화되어 전달되는 구조를 고려해
#      category, difficulty, active_time 관련 값은 문자열 또는 정수를 허용합니다.
#    - AI 서버가 Backend Enum 모듈을 직접 import하지 않으므로 서비스 간 결합을 줄입니다.
#
# 5. Embedding
#    - Quest embedding과 candidate profile_embedding은 없을 수 있습니다.
#    - 값이 없거나 벡터 길이가 다르면 scoring.py에서 0점 Fallback을 적용합니다.
#
# 6. 추천 이유
#    - 규칙 기반 scoring.py는 점수만 계산합니다.
#    - recommendation_reason은 이후 LLM 노드에서 생성하여 최종 응답에 포함합니다.
#
# 7. Pydantic 버전
#    - 현재 requirements.txt의 Pydantic v2 문법을 기준으로 작성했습니다.
# =========================================================

from typing import TypeAlias

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


# 카테고리 ID, 카테고리 이름, 시간대 값처럼
# Backend에서 정수 또는 문자열로 전달될 수 있는 값을 공통 타입으로 정의합니다.
ComparableValue: TypeAlias = int | str


class RecommendationSchema(BaseModel):
    """AI 팀원 추천 Schema가 공통으로 사용하는 기본 설정입니다."""

    # 문자열 앞뒤 공백을 제거하고, 정의되지 않은 추가 필드는 무시합니다.
    # 추가 필드를 무시하면 Backend Payload에 필드가 추가되어도
    # AI 서버가 즉시 깨지는 문제를 줄일 수 있습니다.
    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
    )


class RecentActivitySummary(RecommendationSchema):
    """후보 사용자의 최근 승인 완료 활동을 집계한 정보입니다."""

    # 최근 조회 기간 안에 승인 완료된 Quest 수입니다.
    completed_count: int = Field(
        default=0,
        ge=0,
        description="최근 기간 동안 승인 완료된 Quest 수",
    )

    # 카테고리별 완료 횟수입니다.
    category_counts: dict[str, int] = Field(
        default_factory=dict,
        description="최근 활동의 카테고리별 완료 횟수",
    )

    # 난이도별 완료 횟수입니다.
    difficulty_counts: dict[str, int] = Field(
        default_factory=dict,
        description="최근 활동의 난이도별 완료 횟수",
    )

    # 활동 시간대별 완료 횟수입니다.
    active_time_counts: dict[str, int] = Field(
        default_factory=dict,
        description="최근 활동의 시간대별 완료 횟수",
    )

    @field_validator(
        "category_counts",
        "difficulty_counts",
        "active_time_counts",
        mode="before",
    )
    @classmethod
    def normalize_count_mapping(
        cls,
        value: object,
    ) -> dict[str, int]:
        """집계 dict의 Key를 문자열로 통일하고 음수 횟수를 차단합니다."""

        if value is None:
            return {}

        if not isinstance(value, dict):
            raise ValueError("활동 집계 값은 dict 형식이어야 합니다.")

        normalized: dict[str, int] = {}

        for raw_key, raw_count in value.items():
            key = str(raw_key).strip()

            if not key:
                continue

            # bool은 int의 하위 타입이므로 횟수 값으로 사용하지 않습니다.
            if isinstance(raw_count, bool) or not isinstance(raw_count, int):
                raise ValueError("활동 횟수는 0 이상의 정수여야 합니다.")

            if raw_count < 0:
                raise ValueError("활동 횟수는 음수일 수 없습니다.")

            normalized[key] = raw_count

        return normalized


class TeamRecommendationInfo(RecommendationSchema):
    """팀원 추천의 기준이 되는 팀 정보입니다."""

    # 추천을 요청한 팀의 식별자입니다.
    team_id: int = Field(
        ...,
        gt=0,
        description="추천 대상 팀 ID",
    )

    # 팀이 수행할 Quest의 식별자입니다.
    quest_id: int = Field(
        ...,
        gt=0,
        description="팀이 수행할 Quest ID",
    )

    # 추천 이유 생성 시 사용할 팀 이름입니다.
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="팀 이름",
    )

    # 팀 활동 지역 이름입니다.
    region: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="팀 활동 지역 이름",
    )

    # 지역 이름을 조회하지 못했을 때 참고할 지역 식별자입니다.
    region_id: int | None = Field(
        default=None,
        gt=0,
        description="팀 활동 지역 ID",
    )

    # 팀이 선호하거나 예정한 활동 시간대입니다.
    active_time: list[ComparableValue] = Field(
        default_factory=list,
        description="팀의 활동 시간대 목록",
    )

    # 현재 팀원 수입니다.
    current_members: int = Field(
        default=0,
        ge=0,
        description="현재 팀원 수",
    )

    # 팀 최대 인원입니다.
    max_members: int | None = Field(
        default=None,
        ge=1,
        description="팀 최대 인원",
    )

    @model_validator(mode="after")
    def validate_member_count(
        self,
    ) -> TeamRecommendationInfo:
        """현재 인원이 최대 인원보다 큰 비정상 입력을 차단합니다."""

        if (
            self.max_members is not None
            and self.current_members > self.max_members
        ):
            raise ValueError(
                "현재 팀원 수는 최대 팀원 수보다 클 수 없습니다."
            )

        return self


class QuestRecommendationInfo(RecommendationSchema):
    """팀이 수행할 Quest의 추천 기준 정보입니다."""

    # 추천 기준 Quest의 식별자입니다.
    quest_id: int = Field(
        ...,
        gt=0,
        description="추천 기준 Quest ID",
    )

    # 추천 이유 생성에 사용할 Quest 제목입니다.
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="Quest 제목",
    )

    # 카테고리 식별자입니다.
    category_id: int | None = Field(
        default=None,
        gt=0,
        description="Quest 카테고리 ID",
    )

    # 카테고리 이름입니다.
    category_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Quest 카테고리 이름",
    )

    # Quest 난이도 문자열입니다.
    difficulty: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
        description="Quest 난이도",
    )

    # Quest가 요구하거나 권장하는 활동 시간대입니다.
    active_time: list[ComparableValue] = Field(
        default_factory=list,
        description="Quest 활동 시간대 목록",
    )

    # Quest 설명 또는 Embedding 생성의 원문입니다.
    description: str | None = Field(
        default=None,
        max_length=5000,
        description="Quest 설명",
    )

    # Quest 의미 벡터입니다.
    embedding: list[float] | None = Field(
        default=None,
        description="Quest Embedding 벡터",
    )


class RecommendationCandidate(RecommendationSchema):
    """추천 점수를 계산할 후보 사용자 한 명의 정보입니다."""

    # 추천 후보 사용자의 식별자입니다.
    user_id: int = Field(
        ...,
        gt=0,
        description="추천 후보 사용자 ID",
    )

    # 최종 추천 결과 화면에 표시할 닉네임입니다.
    nickname: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="추천 후보 닉네임",
    )

    # 최종 추천 결과 화면에 표시할 프로필 이미지 주소입니다.
    profile_image_url: str | None = Field(
        default=None,
        max_length=2048,
        description="추천 후보 프로필 이미지 URL",
    )

    # 후보 사용자의 지역 식별자입니다.
    region_id: int | None = Field(
        default=None,
        gt=0,
        description="후보 사용자 지역 ID",
    )

    # 팀 지역과 문자열 비교할 후보 사용자의 지역 이름입니다.
    region: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="후보 사용자 지역 이름",
    )

    # 사용자가 선택한 관심 카테고리 ID 또는 이름 목록입니다.
    preferred_categories: list[ComparableValue] = Field(
        default_factory=list,
        description="후보 사용자의 선호 카테고리 목록",
    )

    # 사용자가 선택한 선호 Quest 난이도입니다.
    preferred_difficulty: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
        description="후보 사용자의 선호 난이도",
    )

    # 사용자가 선호하는 활동 시간대입니다.
    active_time: list[ComparableValue] = Field(
        default_factory=list,
        description="후보 사용자의 선호 활동 시간대 목록",
    )

    # 후보 사용자의 현재 레벨입니다.
    current_level: int = Field(
        default=0,
        ge=0,
        description="후보 사용자의 현재 레벨",
    )

    # 후보 사용자의 연속 활동 일수입니다.
    daily_streak: int = Field(
        default=0,
        ge=0,
        description="후보 사용자의 연속 활동 일수",
    )

    # 후보 사용자의 위도입니다.
    latitude: float | None = Field(
        default=None,
        ge=-90,
        le=90,
        description="후보 사용자의 위도",
    )

    # 후보 사용자의 경도입니다.
    longitude: float | None = Field(
        default=None,
        ge=-180,
        le=180,
        description="후보 사용자의 경도",
    )

    # 사용자 프로필 의미 벡터입니다.
    profile_embedding: list[float] | None = Field(
        default=None,
        description="후보 사용자 프로필 Embedding 벡터",
    )

    # 최근 승인 완료 활동 집계입니다.
    recent_activity: RecentActivitySummary = Field(
        default_factory=RecentActivitySummary,
        description="후보 사용자의 최근 활동 집계",
    )


class TeamRecommendationRequest(RecommendationSchema):
    """Backend가 AI 서버에 전달하는 팀원 추천 요청입니다."""

    # 추천을 요청한 사용자 식별자입니다.
    requester_id: int = Field(
        ...,
        gt=0,
        description="팀원 추천을 요청한 사용자 ID",
    )

    # 추천 기준 팀 정보입니다.
    team: TeamRecommendationInfo = Field(
        ...,
        description="추천 기준 팀 정보",
    )

    # 추천 기준 Quest 정보입니다.
    quest: QuestRecommendationInfo = Field(
        ...,
        description="추천 기준 Quest 정보",
    )

    # 제외 조건을 통과한 추천 후보 목록입니다.
    candidates: list[RecommendationCandidate] = Field(
        default_factory=list,
        description="추천 점수를 계산할 후보 사용자 목록",
    )

    # 최종적으로 반환할 추천 사용자 수입니다.
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="최종 추천 결과 수",
    )

    @model_validator(mode="after")
    def validate_request_relations(
        self,
    ) -> TeamRecommendationRequest:
        """팀·Quest 관계와 후보 중복 여부를 검증합니다."""

        if self.team.quest_id != self.quest.quest_id:
            raise ValueError(
                "team.quest_id와 quest.quest_id가 일치해야 합니다."
            )

        candidate_user_ids = [
            candidate.user_id
            for candidate in self.candidates
        ]

        if len(candidate_user_ids) != len(set(candidate_user_ids)):
            raise ValueError(
                "추천 후보 목록에 같은 user_id가 중복될 수 없습니다."
            )

        if self.requester_id in candidate_user_ids:
            raise ValueError(
                "추천 요청자는 추천 후보 목록에 포함될 수 없습니다."
            )

        return self


class RecommendationScoreSchema(RecommendationSchema):
    """규칙 기반 추천 점수의 항목별 결과입니다."""

    category_score: float = Field(
        ...,
        ge=0,
        le=30,
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
        description="활동 시간 점수",
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
        le=15,
        description="Embedding 유사도 점수",
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
    ) -> RecommendationScoreSchema:
        """총점이 항목별 점수 합계와 일치하는지 확인합니다."""

        calculated_total = round(
            self.category_score
            + self.difficulty_score
            + self.active_time_score
            + self.region_score
            + self.embedding_score
            + self.daily_streak_score
            + self.user_level_score,
            2,
        )

        if abs(self.total_score - calculated_total) > 0.01:
            raise ValueError(
                "total_score는 항목별 추천 점수 합계와 일치해야 합니다."
            )

        return self


class ScoredRecommendationCandidate(RecommendationCandidate):
    """규칙 기반 점수 계산을 완료한 추천 후보입니다."""

    # scoring.py의 RecommendationScore.to_dict() 결과가 들어갑니다.
    score: RecommendationScoreSchema = Field(
        ...,
        description="후보 사용자의 항목별 추천 점수",
    )


class CandidateRecommendationReason(RecommendationSchema):
    """LLM이 후보 한 명에게 생성한 추천 이유입니다."""

    # 추천 이유가 연결될 후보 사용자 식별자입니다.
    user_id: int = Field(
        ...,
        gt=0,
        description="추천 이유 대상 사용자 ID",
    )

    # 사용자 화면에 표시할 자연어 추천 이유입니다.
    recommendation_reason: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="LLM이 생성한 추천 이유",
    )

    # 선택적으로 화면에 표시하거나 로그에서 활용할 핵심 근거입니다.
    highlights: list[str] = Field(
        default_factory=list,
        max_length=5,
        description="추천 이유의 핵심 근거 목록",
    )

    @field_validator("highlights")
    @classmethod
    def validate_highlights(
        cls,
        value: list[str],
    ) -> list[str]:
        """빈 핵심 근거와 중복 핵심 근거를 제거합니다."""

        normalized: list[str] = []
        seen: set[str] = set()

        for item in value:
            stripped = item.strip()

            if not stripped or stripped in seen:
                continue

            seen.add(stripped)
            normalized.append(stripped)

        return normalized


class RecommendationResult(ScoredRecommendationCandidate):
    """점수와 추천 이유를 모두 포함한 최종 후보 한 명의 결과입니다."""

    # LLM 호출 실패 시에도 규칙 기반 결과를 반환할 수 있도록 기본 문장을 허용합니다.
    recommendation_reason: str = Field(
        default="추천 기준과의 종합 적합도가 높은 사용자입니다.",
        min_length=1,
        max_length=500,
        description="후보 사용자 추천 이유",
    )

    # 추천 목록에서의 순위입니다.
    rank: int = Field(
        ...,
        ge=1,
        description="최종 추천 순위",
    )


class TeamRecommendationResponse(RecommendationSchema):
    """AI 서버가 Backend에 반환하는 최종 팀원 추천 응답입니다."""

    # 추천 대상 팀 식별자입니다.
    team_id: int = Field(
        ...,
        gt=0,
        description="추천 대상 팀 ID",
    )

    # 추천 기준 Quest 식별자입니다.
    quest_id: int = Field(
        ...,
        gt=0,
        description="추천 기준 Quest ID",
    )

    # 최종 추천 후보 목록입니다.
    recommendations: list[RecommendationResult] = Field(
        default_factory=list,
        description="점수와 추천 이유가 포함된 최종 추천 후보 목록",
    )

    # 요청된 추천 수입니다.
    requested_top_k: int = Field(
        ...,
        ge=1,
        le=20,
        description="요청된 추천 결과 수",
    )

    # 실제 반환된 추천 수입니다.
    recommendation_count: int = Field(
        default=0,
        ge=0,
        description="실제 반환된 추천 결과 수",
    )

    # 일부 후보 처리 실패나 LLM Fallback 정보를 담습니다.
    warnings: list[str] = Field(
        default_factory=list,
        description="추천 처리 중 발생한 비치명적 경고 목록",
    )

    @model_validator(mode="after")
    def validate_response(
        self,
    ) -> TeamRecommendationResponse:
        """추천 수와 순위가 응답 내용과 일치하는지 검증합니다."""

        actual_count = len(self.recommendations)

        if self.recommendation_count != actual_count:
            raise ValueError(
                "recommendation_count는 recommendations 길이와 일치해야 합니다."
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

        return self