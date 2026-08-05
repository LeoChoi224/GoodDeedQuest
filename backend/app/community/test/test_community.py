from __future__ import annotations

# =========================================================
# [검토 및 확인할 내용]
#
# 1. Community 일반 기능의 Service 로직을 Mock 기반으로 검증합니다.
# 2. 실제 DB 연결 없이 성공 흐름, 핵심 예외, 응답 변환만 확인합니다.
# 3. Repository는 flush()까지만 수행하며 Service는 commit/rollback을 호출하지 않습니다.
# 4. 실행 명령:
#    python -m pytest backend/app/community/test/test_community.py -v
# =========================================================

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

from fastapi import HTTPException, status

from backend.app.community import service


NOW = datetime.now(timezone.utc)


def make_db_mock() -> Mock:
    db = Mock()
    db.commit = Mock()
    db.rollback = Mock()
    return db


def make_user(*, user_id: int = 1, is_active: bool = True) -> SimpleNamespace:
    return SimpleNamespace(
        user_id=user_id,
        nickname=f"user-{user_id}",
        profile_image_url=None,
        is_active=is_active,
    )


def make_post(*, post_id: int = 10, user_id: int = 2, is_active: bool = True) -> SimpleNamespace:
    return SimpleNamespace(
        post_id=post_id,
        user_id=user_id,
        # 게시글은 승인된 퀘스트 인증과 반드시 연결된다.
        # CommunityFeedItemResponse.submission_id 가 int 필수라 None 이면 검증에 걸린다.
        submission_id=100,
        media_url="https://example.com/post.jpg",
        caption="게시글",
        is_active=is_active,
        created_at=NOW,
        updated_at=NOW,
    )


def make_comment(*, comment_id: int = 1, post_id: int = 10, user_id: int = 1) -> SimpleNamespace:
    return SimpleNamespace(
        comment_id=comment_id,
        post_id=post_id,
        user_id=user_id,
        content=f"댓글-{comment_id}",
        created_at=NOW,
        updated_at=NOW,
    )


class CommunityFeedServiceTest(TestCase):
    def test_get_feed_returns_post_with_comment_previews(self) -> None:
        db = make_db_mock()
        post = make_post()
        author = make_user(user_id=2)
        preview_author = make_user(user_id=3)
        older = make_comment(comment_id=1, user_id=3)
        newer = make_comment(comment_id=2, user_id=3)

        with (
            patch.object(
                service.CommunityRepository,
                "list_feed_posts",
                return_value=[(post, author, 4, 2, True)],
            ),
            patch.object(
                service.CommunityRepository,
                "list_comment_previews",
                return_value=[(newer, preview_author), (older, preview_author)],
            ),
        ):
            result = service.get_community_feed(
                db=db,
                current_user=make_user(),
                skip=0,
                limit=20,
            )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].post_id, 10)
        self.assertEqual(result[0].like_count, 4)
        self.assertTrue(result[0].is_liked)
        self.assertEqual(
            [item.comment_id for item in result[0].comment_previews],
            [1, 2],
        )


class CommunityLikeServiceTest(TestCase):
    def test_toggle_like_creates_like_when_missing(self) -> None:
        db = make_db_mock()
        current_user = make_user()
        post = make_post()

        with (
            patch.object(service.CommunityRepository, "get_post_by_id", return_value=post),
            patch.object(service.CommunityRepository, "get_post_like", return_value=None),
            patch.object(service.CommunityRepository, "create_post_like") as create_like,
            patch.object(service.CommunityRepository, "count_post_likes", return_value=1),
        ):
            result = service.toggle_post_like(
                db=db,
                post_id=10,
                current_user=current_user,
            )

        self.assertTrue(result.is_liked)
        self.assertEqual(result.like_count, 1)
        create_like.assert_called_once_with(db=db, post_id=10, user_id=1)
        db.commit.assert_not_called()
        db.rollback.assert_not_called()

    def test_toggle_like_deletes_existing_like(self) -> None:
        db = make_db_mock()
        existing_like = SimpleNamespace(post_id=10, user_id=1)

        with (
            patch.object(service.CommunityRepository, "get_post_by_id", return_value=make_post()),
            patch.object(service.CommunityRepository, "get_post_like", return_value=existing_like),
            patch.object(service.CommunityRepository, "delete_post_like") as delete_like,
            patch.object(service.CommunityRepository, "count_post_likes", return_value=0),
        ):
            result = service.toggle_post_like(
                db=db,
                post_id=10,
                current_user=make_user(),
            )

        self.assertFalse(result.is_liked)
        self.assertEqual(result.like_count, 0)
        delete_like.assert_called_once_with(db=db, post_like=existing_like)

    def test_like_user_list_raises_404_for_missing_post(self) -> None:
        db = make_db_mock()

        with patch.object(service.CommunityRepository, "get_post_by_id", return_value=None):
            with self.assertRaises(HTTPException) as error:
                service.get_post_like_users(
                    db=db,
                    post_id=999,
                    skip=0,
                    limit=20,
                )

        self.assertEqual(error.exception.status_code, status.HTTP_404_NOT_FOUND)


class CommunityCommentServiceTest(TestCase):
    def test_create_comment_returns_comment_with_author(self) -> None:
        db = make_db_mock()
        user = make_user()
        comment = make_comment()

        with (
            patch.object(service.CommunityRepository, "get_post_by_id", return_value=make_post()),
            patch.object(service.CommunityRepository, "create_comment", return_value=comment),
        ):
            result = service.create_post_comment(
                db=db,
                post_id=10,
                content="댓글-1",
                current_user=user,
            )

        self.assertEqual(result.comment_id, 1)
        self.assertEqual(result.author.user_id, 1)

    def test_get_comments_preserves_oldest_first_order(self) -> None:
        db = make_db_mock()
        author = make_user()
        first = make_comment(comment_id=1)
        second = make_comment(comment_id=2)

        with (
            patch.object(service.CommunityRepository, "get_post_by_id", return_value=make_post()),
            patch.object(
                service.CommunityRepository,
                "list_post_comments",
                return_value=[(first, author), (second, author)],
            ),
        ):
            result = service.get_post_comments(
                db=db,
                post_id=10,
                skip=0,
                limit=50,
            )

        self.assertEqual([item.comment_id for item in result], [1, 2])

    def test_inactive_user_cannot_create_comment(self) -> None:
        db = make_db_mock()

        with self.assertRaises(HTTPException) as error:
            service.create_post_comment(
                db=db,
                post_id=10,
                content="댓글",
                current_user=make_user(is_active=False),
            )

        self.assertEqual(error.exception.status_code, status.HTTP_403_FORBIDDEN)


class CommunityHiddenPreferenceServiceTest(TestCase):
    def test_hidden_preference_returns_existing_record_without_duplicate(self) -> None:
        db = make_db_mock()
        existing = SimpleNamespace(
            hidden_id=1,
            user_id=1,
            post_id=10,
            created_at=NOW,
            updated_at=NOW,
        )

        with (
            patch.object(service.CommunityRepository, "get_post_by_id", return_value=make_post()),
            patch.object(service.CommunityRepository, "get_hidden_preference", return_value=existing),
            patch.object(service.CommunityRepository, "create_hidden_preference") as create_hidden,
        ):
            result = service.hide_post_from_recommendation(
                db=db,
                post_id=10,
                current_user=make_user(),
            )

        self.assertEqual(result.hidden_id, 1)
        create_hidden.assert_not_called()

    def test_hidden_preference_creates_record_when_missing(self) -> None:
        db = make_db_mock()
        created = SimpleNamespace(
            hidden_id=1,
            user_id=1,
            post_id=10,
            created_at=NOW,
            updated_at=NOW,
        )

        with (
            patch.object(service.CommunityRepository, "get_post_by_id", return_value=make_post()),
            patch.object(service.CommunityRepository, "get_hidden_preference", return_value=None),
            patch.object(
                service.CommunityRepository,
                "create_hidden_preference",
                return_value=created,
            ) as create_hidden,
        ):
            result = service.hide_post_from_recommendation(
                db=db,
                post_id=10,
                current_user=make_user(),
            )

        self.assertEqual(result.post_id, 10)
        create_hidden.assert_called_once_with(db=db, user_id=1, post_id=10)
