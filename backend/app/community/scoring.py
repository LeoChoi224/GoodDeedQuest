from __future__ import annotations

# =========================================================
# [확인 및 검토할 사항]
#
# 1. 최종 추천 점수는 총 100점입니다.
#    - 관심 카테고리 일치: 40점
#    - 지역 일치: 15점
#    - 게시글 최신성: 25점
#    - 좋아요·댓글 반응도: 20점
#
# 2. 사용자 관심 카테고리는 User.category에 저장된 카테고리 ID 목록을 사용합니다.
#    게시글 카테고리는 CommunityPost → QuestSubmission → Quest → Category.category_id
#    연결 결과를 사용합니다.
#    숫자 또는 문자열로 저장된 ID를 모두 비교할 수 있도록 문자열로 정규화합니다.
#
# 3. 지역 점수는 사용자 지역명과 Quest.location의 문자열 포함 여부를 기준으로 계산. 
#    Region 모델의 실제 지역명 필드가 확인되면 Service에서 해당 값을 이 함수에 전달.
#
# 4. 일반 게시글은 퀘스트 카테고리와 장소가 없으므로
#    퀘스트 연결 정보가 없는 게시글은 카테고리·지역 점수를 부여하지 않고
#    최신성·반응도 점수만 계산합니다.
#
# 5. 이 파일은 DB에 접근하지 않는 순수 점수 계산 전용 파일.
#    Repository 조회, 응답 변환, 페이지네이션은 다른 계층에서 처리.
# =========================================================

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable


# 관심 카테고리 일치 시 부여할 최대 점수.
CATEGORY_MAX_SCORE = 40

# 사용자 지역과 퀘스트 장소가 일치할 때 부여할 최대 점수.
REGION_MAX_SCORE = 15

# 게시글 최신성에 부여할 최대 점수.
FRESHNESS_MAX_SCORE = 25

# 게시글 좋아요·댓글 반응도에 부여할 최대 점수.
ENGAGEMENT_MAX_SCORE = 20


@dataclass(frozen=True, slots=True)
class CommunityRecommendationScore:
    """커뮤니티 게시글의 항목별 추천 점수와 최종 점수를 보관."""

    category_score: int
    region_score: int
    freshness_score: int
    engagement_score: int

    @property
    def final_score(self) -> int:
        """항목별 점수를 합산한 최종 추천 점수를 반환."""

        return (
            self.category_score
            + self.region_score
            + self.freshness_score
            + self.engagement_score
        )


# 카테고리·지역 비교 전에 문자열의 공백과 대소문자 차이를 정리.
def normalize_text(value: str | None) -> str:
    if not value:
        return ""

    return value.strip().casefold()

# 사용자 관심 카테고리 ID와 게시글 퀘스트 카테고리 ID의 일치 점수를 계산.
def calculate_category_score(
    *,
    user_category_ids: Iterable[int | str] | None,
    quest_category_id: int | None,
) -> int:
    """사용자의 관심 카테고리에 퀘스트 카테고리가 포함되면 40점을 반환합니다."""

    # 게시글가 연결된 퀘스트 정보를 확인할 수 없으면 카테고리 점수를 부여하지 않습니다.
    if quest_category_id is None:
        return 0

    if not user_category_ids:
        return 0

    # JSON에 숫자 또는 문자열 형태로 저장돼도 비교할 수 있도록 문자열로 통일.
    normalized_user_category_ids = {
        str(category_id).strip()
        for category_id in user_category_ids
        if isinstance(category_id, (int, str))
        and str(category_id).strip()
    }

    # 현재 게시글의 퀘스트 카테고리 ID를 같은 형식으로 변환.
    normalized_quest_category_id = str(
        quest_category_id
    ).strip()

    if (
        normalized_quest_category_id
        in normalized_user_category_ids
    ):
        return CATEGORY_MAX_SCORE

    return 0


# 사용자 지역명과 퀘스트 장소 문자열의 일치 점수를 계산.
def calculate_region_score(
    *,
    user_region_name: str | None,
    quest_location: str | None,
) -> int:
    """사용자 지역명이 퀘스트 장소 문자열에 포함되면 15점을 반환합니다."""

    normalized_region = normalize_text(user_region_name)
    normalized_location = normalize_text(quest_location)

    if not normalized_region or not normalized_location:
        return 0

    # Quest에 구조화된 지역 ID가 없으므로
    # 현재는 사용자 지역명과 퀘스트 장소 문자열의 포함 여부를 비교합니다.
    if normalized_region in normalized_location:
        return REGION_MAX_SCORE

    return 0

# DB의 naive datetime과 timezone-aware datetime을 같은 기준으로 비교.
def _as_utc_datetime(value: datetime) -> datetime:
    """datetime 값을 UTC 기준 timezone-aware 값으로 변환합니다."""

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def calculate_freshness_score(
    *,
    created_at: datetime,
    reference_time: datetime | None = None,
) -> int:
    """게시글 생성 시각과 기준 시각의 차이에 따라 최대 25점을 반환."""

    current_time = _as_utc_datetime(
        reference_time or datetime.now(timezone.utc)
    )
    post_created_at = _as_utc_datetime(created_at)

    elapsed_seconds = (
        current_time - post_created_at
    ).total_seconds()

    # 서버 시간 오차나 잘못된 미래 시각은 가장 최신 게시글로 취급.
    if elapsed_seconds <= 0:
        return FRESHNESS_MAX_SCORE

    elapsed_days = elapsed_seconds / 86_400

    if elapsed_days <= 1:
        return 25

    if elapsed_days <= 3:
        return 20

    if elapsed_days <= 7:
        return 15

    if elapsed_days <= 14:
        return 10

    if elapsed_days <= 30:
        return 5

    return 0


def calculate_engagement_score(
    *,
    like_count: int,
    comment_count: int,
) -> int:
    """좋아요와 댓글 반응값에 따라 최대 20점을 반환."""

    # 비정상적인 음수 집계값은 0으로 보정.
    safe_like_count = max(like_count, 0)
    safe_comment_count = max(comment_count, 0)

    # 댓글은 좋아요보다 적극적인 반응이므로 2배 가중치를 적용.
    engagement_value = safe_like_count + safe_comment_count * 2

    if engagement_value >= 20:
        return 20

    if engagement_value >= 10:
        return 15

    if engagement_value >= 5:
        return 10

    if engagement_value >= 1:
        return 5

    return 0

def calculate_community_recommendation_score(
    *,
    user_category_ids: Iterable[int | str] | None,
    user_region_name: str | None,
    quest_category_id: int | None,
    quest_location: str | None,
    created_at: datetime,
    like_count: int,
    comment_count: int,
    reference_time: datetime | None = None,
) -> CommunityRecommendationScore:
    """커뮤니티 게시글의 항목별 점수와 최종 추천 점수를 계산합니다."""

    category_score = calculate_category_score(
        user_category_ids=user_category_ids,
        quest_category_id=quest_category_id,
    )

    region_score = calculate_region_score(
        user_region_name=user_region_name,
        quest_location=quest_location,
    )

    freshness_score = calculate_freshness_score(
        created_at=created_at,
        reference_time=reference_time,
    )

    engagement_score = calculate_engagement_score(
        like_count=like_count,
        comment_count=comment_count,
    )

    return CommunityRecommendationScore(
        category_score=category_score,
        region_score=region_score,
        freshness_score=freshness_score,
        engagement_score=engagement_score,
    )
