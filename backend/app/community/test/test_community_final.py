from __future__ import annotations

# =========================================================
# [커뮤니티 최종 핵심 테스트]
#
# 검증 범위
# 1. 승인된 퀘스트 인증이 없는 게시글 생성 차단
# 2. 동일한 승인 인증을 여러 게시글에 재사용할 수 있는 정책
# 3. 기본 피드·추천 피드의 비활성 사용자 차단
# 4. 추천 점수와 최종 정렬·페이지네이션
# 5. 최근 승인 퀘스트 인증 목록 조회
# 6. 게시글 신고 성공·중복·본인 게시글 신고 차단
#
# 저장 위치
# backend/app/community/test/test_community_final.py
#
# 실행 명령
# python -m pytest backend/app/community/test/test_community_final.py -v
#
# 참고
# - commit()과 rollback()은 공통 get_db()가 담당하므로
#   Service 테스트에서는 직접 호출되지 않는지 확인합니다.
# - 동일 인증 재사용은 허용하므로 중복 인증 차단 테스트는 없습니다.
# =========================================================

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

from fastapi import HTTPException, status
from pydantic import ValidationError

from backend.app.community import service
from backend.app.community.schema import (
    CommunityPostCreate,
    CommunityReportCreate,
)
from backend.app.community.scoring import (
    CATEGORY_MAX_SCORE,
    ENGAGEMENT_MAX_SCORE,
    FRESHNESS_MAX_SCORE,
    REGION_MAX_SCORE,
    calculate_category_score,
    calculate_community_recommendation_score,
    calculate_engagement_score,
    calculate_freshness_score,
    calculate_region_score,
)
from backend.app.quest_verification.enums import MediaType


REFERENCE_TIME = datetime(2026, 7, 25, 12, 0, tzinfo=timezone.utc)


def make_db_mock() -> Mock:
    """공통 get_db() 트랜잭션 정책 확인용 DB Mock을 생성합니다."""

    db = Mock()
    db.commit = Mock()
    db.rollback = Mock()
    return db


def make_user(
    *,
    user_id: int = 1,
    is_active: bool = True,
    category: list[int | str] | None = None,
    region_id: int | None = 1,
    trust_score: int = 50,
) -> SimpleNamespace:
    """테스트용 사용자 객체를 생성합니다."""

    return SimpleNamespace(
        user_id=user_id,
        nickname=f"user-{user_id}",
        profile_image_url=None,
        is_active=is_active,
        category=category if category is not None else [1],
        region_id=region_id,
        # User.trust_score는 기본값 50인 필수 컬럼이다.
        # 개인화 피드가 작성자 신뢰도를 추천 점수에 반영하므로 가짜 객체에도 필요하다.
        trust_score=trust_score,
    )


def make_post(
    *,
    post_id: int = 10,
    user_id: int = 2,
    submission_id: int = 100,
    is_active: bool = True,
    created_at: datetime = REFERENCE_TIME,
) -> SimpleNamespace:
    """테스트용 커뮤니티 게시글 객체를 생성합니다."""

    return SimpleNamespace(
        post_id=post_id,
        user_id=user_id,
        submission_id=submission_id,
        media_url=f"https://example.com/{post_id}.jpg",
        caption=f"퀘스트 완료 인증-{post_id}",
        is_active=is_active,
        created_at=created_at,
        updated_at=created_at,
    )


def make_comment(
    *,
    comment_id: int,
    post_id: int = 10,
    user_id: int = 3,
    created_at: datetime = REFERENCE_TIME,
) -> SimpleNamespace:
    """테스트용 댓글 객체를 생성합니다."""

    return SimpleNamespace(
        comment_id=comment_id,
        post_id=post_id,
        user_id=user_id,
        content=f"댓글-{comment_id}",
        created_at=created_at,
        updated_at=created_at,
    )


def make_post_request(
    *,
    submission_id: int = 100,
    selected_media_index: int = 0,
) -> CommunityPostCreate:
    """승인 인증과 연결된 게시글 생성 요청을 만듭니다.

    클라이언트는 media_url을 보내지 않습니다. 어떤 미디어를 쓸지는
    selected_media_index로만 고르고, 실제 S3 key는 서버가 인증 기록에서
    찾아옵니다.
    """

    return CommunityPostCreate(
        submission_id=submission_id,
        selected_media_index=selected_media_index,
        caption="퀘스트 완료 인증",
    )


def make_submission(
    *,
    submission_id: int = 100,
    user_id: int = 1,
    quest_id: int = 50,
) -> SimpleNamespace:
    """게시글에 연결할 승인된 퀘스트 인증 객체를 만듭니다.

    media_url은 URL이 아니라 S3 key여야 합니다. 서비스가
    submission/{user_id}/{quest_id}/ 로 시작하는지 검사해서, 남의 인증
    미디어를 가져다 쓰는 것을 막기 때문입니다.
    """

    return SimpleNamespace(
        submission_id=submission_id,
        user_id=user_id,
        quest_id=quest_id,
        media_url=f"submission/{user_id}/{quest_id}/verify.jpg",
        media_type=MediaType.PHOTO,
        extra_media_urls=[],
    )


class CommunityPostPolicyTest(TestCase):
    """커뮤니티 게시글 생성 정책을 검증합니다."""

    def test_submission_id_is_required(self) -> None:
        """인증 ID 없이 게시글 요청을 만들 수 없습니다."""

        with self.assertRaises(ValidationError):
            CommunityPostCreate(
                media_url="https://example.com/post.jpg",
                caption="인증 없는 게시글",
            )

    def test_inactive_user_cannot_create_post(self) -> None:
        """비활성 사용자는 게시글을 작성할 수 없습니다."""

        with self.assertRaises(HTTPException) as error:
            service.create_community_post(
                db=make_db_mock(),
                request=make_post_request(),
                current_user=make_user(is_active=False),
            )

        self.assertEqual(
            error.exception.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_unaccepted_submission_cannot_create_post(self) -> None:
        """본인의 승인된 인증이 아니면 게시글 생성을 차단합니다."""

        db = make_db_mock()

        with patch.object(
            service.CommunityRepository,
            "get_accepted_submission_by_id",
            return_value=None,
        ):
            with self.assertRaises(HTTPException) as error:
                service.create_community_post(
                    db=db,
                    request=make_post_request(submission_id=999),
                    current_user=make_user(),
                )

        self.assertEqual(
            error.exception.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_accepted_submission_creates_post(self) -> None:
        """본인의 승인 인증으로 게시글을 생성합니다.

        게시글의 media_url은 요청에서 오지 않습니다. 인증 기록의 S3 key를
        community/ 아래로 복사한 결과가 쓰입니다. 인증 원본은 30일 뒤
        만료되지만 게시글은 남아야 하기 때문입니다.
        """

        db = make_db_mock()
        request = make_post_request()
        created_post = make_post(
            post_id=30,
            user_id=1,
            submission_id=100,
        )
        submission = make_submission()

        with (
            patch.object(
                service.CommunityRepository,
                "get_accepted_submission_by_id",
                return_value=submission,
            ),
            patch.object(service, "copy_s3_object") as copy_object,
            patch.object(
                service.CommunityRepository,
                "create_post",
                return_value=created_post,
            ) as create_post,
        ):
            result = service.create_community_post(
                db=db,
                request=request,
                current_user=make_user(),
            )

        self.assertEqual(result.post_id, 30)

        # 원본은 인증 key, 사본은 community/{user_id}/{submission_id}/ 아래로 간다.
        copy_object.assert_called_once()
        copy_kwargs = copy_object.call_args.kwargs
        self.assertEqual(copy_kwargs["source_key"], submission.media_url)
        self.assertTrue(
            copy_kwargs["destination_key"].startswith("community/1/100/")
        )
        self.assertTrue(copy_kwargs["destination_key"].endswith(".jpg"))

        # 게시글에는 요청값이 아니라 복사된 영구 key가 저장된다.
        create_post.assert_called_once()
        create_kwargs = create_post.call_args.kwargs
        self.assertEqual(create_kwargs["db"], db)
        self.assertEqual(create_kwargs["user_id"], 1)
        self.assertEqual(create_kwargs["submission_id"], 100)
        self.assertEqual(
            create_kwargs["media_url"], copy_kwargs["destination_key"]
        )
        self.assertEqual(create_kwargs["caption"], "퀘스트 완료 인증")

        db.commit.assert_not_called()
        db.rollback.assert_not_called()

    def test_other_users_media_key_is_rejected(self) -> None:
        """남의 경로를 가리키는 인증 미디어는 거부합니다."""

        db = make_db_mock()
        submission = make_submission()
        # 로그인 사용자는 1번인데 미디어 key는 2번 사용자 경로다.
        submission.media_url = "submission/2/50/verify.jpg"

        with (
            patch.object(
                service.CommunityRepository,
                "get_accepted_submission_by_id",
                return_value=submission,
            ),
            patch.object(service, "copy_s3_object") as copy_object,
        ):
            with self.assertRaises(HTTPException) as error:
                service.create_community_post(
                    db=db,
                    request=make_post_request(),
                    current_user=make_user(),
                )

        self.assertEqual(
            error.exception.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        copy_object.assert_not_called()

    def test_same_submission_can_be_used_for_multiple_posts(self) -> None:
        """동일 승인 인증으로 여러 게시글을 작성할 수 있습니다."""

        db = make_db_mock()
        request = make_post_request(submission_id=100)

        with (
            patch.object(
                service.CommunityRepository,
                "get_accepted_submission_by_id",
                return_value=make_submission(),
            ) as get_submission,
            patch.object(service, "copy_s3_object") as copy_object,
            patch.object(
                service.CommunityRepository,
                "create_post",
                side_effect=[
                    make_post(
                        post_id=30,
                        user_id=1,
                        submission_id=100,
                    ),
                    make_post(
                        post_id=31,
                        user_id=1,
                        submission_id=100,
                    ),
                ],
            ) as create_post,
        ):
            first_result = service.create_community_post(
                db=db,
                request=request,
                current_user=make_user(),
            )
            second_result = service.create_community_post(
                db=db,
                request=request,
                current_user=make_user(),
            )

        self.assertEqual(first_result.post_id, 30)
        self.assertEqual(second_result.post_id, 31)
        self.assertEqual(get_submission.call_count, 2)
        self.assertEqual(create_post.call_count, 2)

        # 같은 인증을 재사용해도 사본 key는 매번 달라야 한다.
        # 같으면 두 번째 게시글이 첫 번째 파일을 덮어써 버린다.
        first_key = copy_object.call_args_list[0].kwargs["destination_key"]
        second_key = copy_object.call_args_list[1].kwargs["destination_key"]
        self.assertNotEqual(first_key, second_key)


class CommunityScoringTest(TestCase):
    """개인화 추천 점수 계산을 검증합니다."""

    def test_category_score_matches_numeric_and_string_ids(self) -> None:
        """카테고리 ID의 숫자·문자열 표현을 동일하게 비교합니다."""

        self.assertEqual(
            calculate_category_score(
                user_category_ids=[1, "2"],
                quest_category_id=2,
            ),
            CATEGORY_MAX_SCORE,
        )

    def test_category_score_is_zero_when_not_matched(self) -> None:
        """관심 카테고리와 일치하지 않으면 0점입니다."""

        self.assertEqual(
            calculate_category_score(
                user_category_ids=[1, 2],
                quest_category_id=3,
            ),
            0,
        )

    def test_region_score_matches_location_substring(self) -> None:
        """사용자 지역명이 퀘스트 장소에 포함되면 최고점입니다."""

        self.assertEqual(
            calculate_region_score(
                user_region_name=" 서울 ",
                quest_location="서울특별시 강남구",
            ),
            REGION_MAX_SCORE,
        )

    def test_region_score_is_zero_without_region(self) -> None:
        """사용자 지역 정보가 없으면 지역 점수는 0점입니다."""

        self.assertEqual(
            calculate_region_score(
                user_region_name=None,
                quest_location="서울특별시 강남구",
            ),
            0,
        )

    def test_freshness_score_is_max_within_one_day(self) -> None:
        """등록 후 1일 이내 게시글은 최신성 최고점입니다."""

        self.assertEqual(
            calculate_freshness_score(
                created_at=REFERENCE_TIME - timedelta(hours=12),
                reference_time=REFERENCE_TIME,
            ),
            FRESHNESS_MAX_SCORE,
        )

    def test_freshness_score_is_zero_after_thirty_days(self) -> None:
        """등록 후 30일을 초과한 게시글은 최신성 0점입니다."""

        self.assertEqual(
            calculate_freshness_score(
                created_at=REFERENCE_TIME - timedelta(days=31),
                reference_time=REFERENCE_TIME,
            ),
            0,
        )

    def test_engagement_score_applies_comment_weight(self) -> None:
        """댓글 가중치를 반영하여 반응도 점수를 계산합니다."""

        # 좋아요 1 + 댓글 2×2 = 5 → 5점 이상 구간이므로 8점.
        # (같은 반응 수라도 좋아요만 3개면 3 → 4점 구간에 머문다)
        self.assertEqual(
            calculate_engagement_score(
                like_count=1,
                comment_count=2,
            ),
            8,
        )

    def test_engagement_score_caps_at_maximum(self) -> None:
        """반응도 점수는 최대 점수를 넘지 않습니다."""

        self.assertEqual(
            calculate_engagement_score(
                like_count=100,
                comment_count=100,
            ),
            ENGAGEMENT_MAX_SCORE,
        )

    def test_negative_engagement_counts_are_zero(self) -> None:
        """비정상적인 음수 집계값은 0으로 보정합니다."""

        self.assertEqual(
            calculate_engagement_score(
                like_count=-10,
                comment_count=-5,
            ),
            0,
        )

    def test_total_recommendation_score_is_100(self) -> None:
        """모든 항목의 최고점을 합산하면 100점입니다."""

        result = calculate_community_recommendation_score(
            user_category_ids=[1],
            user_region_name="서울",
            quest_category_id=1,
            quest_location="서울특별시 종로구",
            created_at=REFERENCE_TIME,
            like_count=100,
            comment_count=100,
            # 작성자 신뢰도 100 → 신뢰 점수 15점 만점
            author_trust_score=100,
            reference_time=REFERENCE_TIME,
        )

        self.assertEqual(result.category_score, CATEGORY_MAX_SCORE)
        self.assertEqual(result.region_score, REGION_MAX_SCORE)
        self.assertEqual(result.freshness_score, FRESHNESS_MAX_SCORE)
        self.assertEqual(result.engagement_score, ENGAGEMENT_MAX_SCORE)
        self.assertEqual(result.final_score, 100)


class CommunityFeedServiceTest(TestCase):
    """기본 피드와 개인화 추천 피드 Service를 검증합니다."""

    def test_inactive_user_cannot_get_basic_feed(self) -> None:
        """비활성 사용자는 기본 피드를 조회할 수 없습니다."""

        with self.assertRaises(HTTPException) as error:
            service.get_community_feed(
                db=make_db_mock(),
                current_user=make_user(is_active=False),
            )

        self.assertEqual(
            error.exception.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_basic_feed_comment_previews_are_oldest_first(self) -> None:
        """최근 댓글을 조회한 뒤 화면에는 오래된 댓글부터 표시합니다."""

        db = make_db_mock()
        post = make_post()
        author = make_user(user_id=2)
        comment_author = make_user(user_id=3)

        older_comment = make_comment(
            comment_id=1,
            created_at=REFERENCE_TIME - timedelta(minutes=2),
        )
        newer_comment = make_comment(
            comment_id=2,
            created_at=REFERENCE_TIME - timedelta(minutes=1),
        )

        with (
            patch.object(
                service.CommunityRepository,
                "list_feed_posts",
                return_value=[
                    (post, author, 4, 2, True),
                ],
            ),
            patch.object(
                service.CommunityRepository,
                "list_comment_previews",
                return_value=[
                    (newer_comment, comment_author),
                    (older_comment, comment_author),
                ],
            ),
        ):
            result = service.get_community_feed(
                db=db,
                current_user=make_user(),
            )

        self.assertEqual(len(result), 1)
        self.assertEqual(
            [
                comment.comment_id
                for comment in result[0].comment_previews
            ],
            [1, 2],
        )
        self.assertEqual(result[0].like_count, 4)
        self.assertTrue(result[0].is_liked)

    def test_inactive_user_cannot_get_personalized_feed(self) -> None:
        """비활성 사용자는 개인화 추천 피드를 조회할 수 없습니다."""

        with self.assertRaises(HTTPException) as error:
            service.get_personalized_community_feed(
                db=make_db_mock(),
                current_user=make_user(is_active=False),
                skip=0,
                limit=20,
            )

        self.assertEqual(
            error.exception.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_personalized_feed_sorts_by_score_descending(self) -> None:
        """개인화 피드는 최종 추천 점수 내림차순으로 정렬합니다."""

        db = make_db_mock()
        user = make_user(category=[1], region_id=1)
        author = make_user(user_id=2)

        high_score_post = make_post(
            post_id=20,
            created_at=REFERENCE_TIME - timedelta(days=1),
        )
        low_score_post = make_post(
            post_id=10,
            created_at=REFERENCE_TIME - timedelta(days=31),
        )

        candidate_rows = [
            (
                low_score_post,
                author,
                2,
                "부산광역시",
                0,
                0,
                False,
            ),
            (
                high_score_post,
                author,
                1,
                "서울특별시",
                20,
                0,
                True,
            ),
        ]

        with (
            patch.object(
                service.CommunityRepository,
                "get_region_name_by_id",
                return_value="서울",
            ),
            patch.object(
                service.CommunityRepository,
                "list_personalized_feed_candidates",
                return_value=candidate_rows,
            ),
            patch.object(
                service.CommunityRepository,
                "list_comment_previews",
                return_value=[],
            ),
            patch.object(service, "datetime") as datetime_mock,
        ):
            datetime_mock.now.return_value = REFERENCE_TIME

            result = service.get_personalized_community_feed(
                db=db,
                current_user=user,
                skip=0,
                limit=20,
            )

        self.assertEqual(
            [item.post_id for item in result],
            [20, 10],
        )

    def test_personalized_feed_uses_tie_breakers(self) -> None:
        """동점이면 최신 작성 시각, 큰 post_id 순으로 정렬합니다."""

        db = make_db_mock()
        user = make_user(category=[1], region_id=1)
        author = make_user(user_id=2)

        older_post = make_post(
            post_id=50,
            created_at=REFERENCE_TIME - timedelta(days=2),
        )
        newer_low_id_post = make_post(
            post_id=40,
            created_at=REFERENCE_TIME - timedelta(days=1),
        )
        newer_high_id_post = make_post(
            post_id=60,
            created_at=REFERENCE_TIME - timedelta(days=1),
        )

        candidate_rows = [
            (older_post, author, 1, "서울", 0, 0, False),
            (newer_low_id_post, author, 1, "서울", 0, 0, False),
            (newer_high_id_post, author, 1, "서울", 0, 0, False),
        ]

        with (
            patch.object(
                service.CommunityRepository,
                "get_region_name_by_id",
                return_value="서울",
            ),
            patch.object(
                service.CommunityRepository,
                "list_personalized_feed_candidates",
                return_value=candidate_rows,
            ),
            patch.object(
                service.CommunityRepository,
                "list_comment_previews",
                return_value=[],
            ),
            patch.object(service, "datetime") as datetime_mock,
        ):
            datetime_mock.now.return_value = REFERENCE_TIME

            result = service.get_personalized_community_feed(
                db=db,
                current_user=user,
                skip=0,
                limit=20,
            )

        self.assertEqual(
            [item.post_id for item in result],
            [60, 40, 50],
        )

    def test_personalized_feed_applies_skip_and_limit(self) -> None:
        """점수 정렬 이후 skip과 limit을 적용합니다."""

        db = make_db_mock()
        user = make_user(category=[1], region_id=1)
        author = make_user(user_id=2)

        candidate_rows = [
            (
                make_post(
                    post_id=post_id,
                    created_at=REFERENCE_TIME,
                ),
                author,
                1,
                "서울",
                0,
                0,
                False,
            )
            for post_id in [1, 2, 3]
        ]

        with (
            patch.object(
                service.CommunityRepository,
                "get_region_name_by_id",
                return_value="서울",
            ),
            patch.object(
                service.CommunityRepository,
                "list_personalized_feed_candidates",
                return_value=candidate_rows,
            ),
            patch.object(
                service.CommunityRepository,
                "list_comment_previews",
                return_value=[],
            ),
            patch.object(service, "datetime") as datetime_mock,
        ):
            datetime_mock.now.return_value = REFERENCE_TIME

            result = service.get_personalized_community_feed(
                db=db,
                current_user=user,
                skip=1,
                limit=1,
            )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].post_id, 2)


class RecentAcceptedSubmissionServiceTest(TestCase):
    """최근 승인 퀘스트 인증 목록 조회를 검증합니다."""

    def test_inactive_user_cannot_get_recent_submissions(self) -> None:
        """비활성 사용자는 승인 인증 목록을 조회할 수 없습니다."""

        with self.assertRaises(HTTPException) as error:
            service.get_recent_accepted_quest_submissions(
                db=make_db_mock(),
                current_user=make_user(is_active=False),
                skip=0,
                limit=20,
            )

        self.assertEqual(
            error.exception.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_recent_submissions_are_converted_to_response(self) -> None:
        """Repository 결과를 최근 승인 인증 응답으로 변환합니다."""

        db = make_db_mock()
        submission = SimpleNamespace(
            submission_id=100,
            quest_id=50,
            media_url="https://example.com/submission.jpg",
            # 응답 변환 시 media_type을 읽는다(service.py:336).
            # None이면 media_url 확장자로 종류를 추론한다.
            media_type=None,
            submitted_at=REFERENCE_TIME,
        )

        with patch.object(
            service.CommunityRepository,
            "list_recent_quest_submissions",
            return_value=[submission],
        ) as list_submissions:
            result = service.get_recent_accepted_quest_submissions(
                db=db,
                current_user=make_user(),
                skip=0,
                limit=20,
            )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].submission_id, 100)
        self.assertEqual(result[0].quest_id, 50)

        list_submissions.assert_called_once_with(
            db=db,
            user_id=1,
            skip=0,
            limit=20,
        )


class CommunityReportServiceTest(TestCase):
    """커뮤니티 게시글 신고 Service를 검증합니다."""

    def test_inactive_user_cannot_report_post(self) -> None:
        """비활성 사용자는 게시글을 신고할 수 없습니다."""

        with self.assertRaises(HTTPException) as error:
            service.create_community_report(
                db=make_db_mock(),
                post_id=10,
                request=CommunityReportCreate(
                    reason="부적절한 게시글입니다.",
                ),
                current_user=make_user(is_active=False),
            )

        self.assertEqual(
            error.exception.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_user_cannot_report_own_post(self) -> None:
        """본인이 작성한 게시글은 신고할 수 없습니다."""

        db = make_db_mock()

        with patch.object(
            service,
            "_get_active_community_post",
            return_value=make_post(
                post_id=10,
                user_id=1,
            ),
        ):
            with self.assertRaises(HTTPException) as error:
                service.create_community_report(
                    db=db,
                    post_id=10,
                    request=CommunityReportCreate(
                        reason="신고 사유",
                    ),
                    current_user=make_user(user_id=1),
                )

        self.assertEqual(
            error.exception.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_duplicate_report_is_rejected(self) -> None:
        """동일 사용자의 동일 게시글 중복 신고를 차단합니다."""

        db = make_db_mock()

        with (
            patch.object(
                service,
                "_get_active_community_post",
                return_value=make_post(
                    post_id=10,
                    user_id=2,
                ),
            ),
            patch.object(
                service.CommunityRepository,
                "get_report_by_reporter_and_post",
                return_value=SimpleNamespace(report_id=1),
            ),
        ):
            with self.assertRaises(HTTPException) as error:
                service.create_community_report(
                    db=db,
                    post_id=10,
                    request=CommunityReportCreate(
                        reason="중복 신고",
                    ),
                    current_user=make_user(user_id=1),
                )

        self.assertEqual(
            error.exception.status_code,
            status.HTTP_409_CONFLICT,
        )

    def test_report_is_created_successfully(self) -> None:
        """유효한 게시글 신고를 생성합니다."""

        db = make_db_mock()
        created_report = SimpleNamespace(
            report_id=1,
            reporter_id=1,
            post_id=10,
            reason="부적절한 게시글입니다.",
            status="PENDING",
            created_at=REFERENCE_TIME,
        )

        with (
            patch.object(
                service,
                "_get_active_community_post",
                return_value=make_post(
                    post_id=10,
                    user_id=2,
                ),
            ),
            patch.object(
                service.CommunityRepository,
                "get_report_by_reporter_and_post",
                return_value=None,
            ),
            patch.object(
                service.CommunityRepository,
                "create_report",
                return_value=created_report,
            ) as create_report,
        ):
            result = service.create_community_report(
                db=db,
                post_id=10,
                request=CommunityReportCreate(
                    reason="  부적절한 게시글입니다.  ",
                ),
                current_user=make_user(user_id=1),
            )

        self.assertEqual(result.report_id, 1)
        self.assertEqual(result.reporter_id, 1)
        self.assertEqual(result.post_id, 10)
        self.assertEqual(result.reason, "부적절한 게시글입니다.")

        create_report.assert_called_once_with(
            db=db,
            reporter_id=1,
            post_id=10,
            reason="부적절한 게시글입니다.",
        )

        db.commit.assert_not_called()
        db.rollback.assert_not_called()
