from __future__ import annotations

"""커뮤니티 인증 미디어 영구 보존 로직 단위 테스트.

실행 명령:
    python -m pytest \
        backend/app/community/test/test_community_media_preservation.py \
        -v

실제 DB나 S3에는 연결하지 않습니다. Repository와 S3 호출을 Mock으로
대체해 S3 key 검증, 영구 경로 복사, 응답 URL 변환, 오류 처리를 확인합니다.
"""

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

from botocore.exceptions import ClientError
from fastapi import HTTPException, status

from backend.app.community import service
from backend.app.community.schema import CommunityPostCreate
from backend.app.quest_verification.enums import MediaType
from backend.scripts import backfill_community_media


NOW = datetime(2026, 8, 2, 0, 0, tzinfo=timezone.utc)


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


def make_submission(
    *,
    submission_id: int = 100,
    user_id: int = 1,
    quest_id: int = 10,
    media_url: str = "submission/1/10/source.jpg",
    media_type: MediaType | None = MediaType.PHOTO,
) -> SimpleNamespace:
    return SimpleNamespace(
        submission_id=submission_id,
        user_id=user_id,
        quest_id=quest_id,
        media_url=media_url,
        media_type=media_type,
        submitted_at=NOW,
    )


def make_post(
    *,
    post_id: int = 30,
    user_id: int = 1,
    submission_id: int = 100,
    media_url: str = "community/1/100/copied.jpg",
) -> SimpleNamespace:
    return SimpleNamespace(
        post_id=post_id,
        user_id=user_id,
        submission_id=submission_id,
        media_url=media_url,
        caption="퀘스트 완료 인증",
        is_active=True,
        created_at=NOW,
        updated_at=NOW,
    )


def make_request(*, submission_id: int = 100) -> CommunityPostCreate:
    return CommunityPostCreate(
        submission_id=submission_id,
        caption="퀘스트 완료 인증",
    )


class PermanentMediaKeyTest(TestCase):
    def test_builds_community_key_while_preserving_extension(self) -> None:
        with patch.object(
            service,
            "uuid4",
            return_value=SimpleNamespace(hex="fixeduuid"),
        ):
            result = service._build_permanent_media_key(
                user_id=1,
                submission_id=100,
                source_key="submission/1/10/source.jpeg",
                media_type=MediaType.PHOTO,
            )

        self.assertEqual(
            result,
            "community/1/100/fixeduuid.jpeg",
        )

    def test_uses_video_extension_when_source_has_no_extension(self) -> None:
        with patch.object(
            service,
            "uuid4",
            return_value=SimpleNamespace(hex="fixeduuid"),
        ):
            result = service._build_permanent_media_key(
                user_id=1,
                submission_id=101,
                source_key="submission/1/10/source",
                media_type=MediaType.VIDEO,
            )

        self.assertEqual(
            result,
            "community/1/101/fixeduuid.mp4",
        )


class CommunityMediaPreservationServiceTest(TestCase):
    def test_accepted_submission_is_copied_and_permanent_key_is_saved(self) -> None:
        db = make_db_mock()
        submission = make_submission()
        post = make_post()

        with (
            patch.object(
                service.CommunityRepository,
                "get_accepted_submission_by_id",
                return_value=submission,
            ),
            patch.object(
                service,
                "_build_permanent_media_key",
                return_value="community/1/100/copied.jpg",
            ),
            patch.object(service, "copy_s3_object") as copy_s3_object,
            patch.object(
                service.CommunityRepository,
                "create_post",
                return_value=post,
            ) as create_post,
            patch.object(
                service,
                "generate_download_presigned_url",
                return_value="https://download.example/copied.jpg",
            ) as generate_download_url,
        ):
            result = service.create_community_post(
                db=db,
                request=make_request(),
                current_user=make_user(),
            )

        copy_s3_object.assert_called_once_with(
            source_key="submission/1/10/source.jpg",
            destination_key="community/1/100/copied.jpg",
        )
        create_post.assert_called_once_with(
            db=db,
            user_id=1,
            submission_id=100,
            media_url="community/1/100/copied.jpg",
            caption="퀘스트 완료 인증",
        )
        generate_download_url.assert_called_once_with(
            "community/1/100/copied.jpg"
        )
        self.assertEqual(
            result.media_url,
            "https://download.example/copied.jpg",
        )
        self.assertEqual(result.media_type, MediaType.PHOTO)
        db.commit.assert_not_called()
        db.rollback.assert_not_called()

    def test_invalid_submission_s3_key_is_rejected_before_copy(self) -> None:
        db = make_db_mock()
        submission = make_submission(
            media_url="submission/999/10/other-user.jpg",
        )

        with (
            patch.object(
                service.CommunityRepository,
                "get_accepted_submission_by_id",
                return_value=submission,
            ),
            patch.object(service, "copy_s3_object") as copy_s3_object,
            patch.object(
                service.CommunityRepository,
                "create_post",
            ) as create_post,
        ):
            with self.assertRaises(HTTPException) as error:
                service.create_community_post(
                    db=db,
                    request=make_request(),
                    current_user=make_user(),
                )

        self.assertEqual(
            error.exception.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        copy_s3_object.assert_not_called()
        create_post.assert_not_called()

    def test_path_traversal_s3_key_is_rejected_before_copy(self) -> None:
        db = make_db_mock()
        submission = make_submission(
            media_url="submission/1/10/../private.jpg",
        )

        with (
            patch.object(
                service.CommunityRepository,
                "get_accepted_submission_by_id",
                return_value=submission,
            ),
            patch.object(service, "copy_s3_object") as copy_s3_object,
            patch.object(
                service.CommunityRepository,
                "create_post",
            ) as create_post,
        ):
            with self.assertRaises(HTTPException) as error:
                service.create_community_post(
                    db=db,
                    request=make_request(),
                    current_user=make_user(),
                )

        self.assertEqual(
            error.exception.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        copy_s3_object.assert_not_called()
        create_post.assert_not_called()

    def test_s3_copy_failure_returns_502_and_does_not_create_post(self) -> None:
        db = make_db_mock()
        client_error = ClientError(
            error_response={
                "Error": {
                    "Code": "AccessDenied",
                    "Message": "Access denied",
                }
            },
            operation_name="CopyObject",
        )

        with (
            patch.object(
                service.CommunityRepository,
                "get_accepted_submission_by_id",
                return_value=make_submission(),
            ),
            patch.object(
                service,
                "_build_permanent_media_key",
                return_value="community/1/100/copied.jpg",
            ),
            patch.object(
                service,
                "copy_s3_object",
                side_effect=client_error,
            ),
            patch.object(
                service.CommunityRepository,
                "create_post",
            ) as create_post,
        ):
            with self.assertRaises(HTTPException) as error:
                service.create_community_post(
                    db=db,
                    request=make_request(),
                    current_user=make_user(),
                )

        self.assertEqual(
            error.exception.status_code,
            status.HTTP_502_BAD_GATEWAY,
        )
        create_post.assert_not_called()

    def test_recent_submission_key_is_returned_as_presigned_url(self) -> None:
        db = make_db_mock()
        submission = make_submission(
            media_url="submission/1/10/source.mp4",
            media_type=MediaType.VIDEO,
        )

        with (
            patch.object(
                service.CommunityRepository,
                "list_recent_quest_submissions",
                return_value=[submission],
            ),
            patch.object(
                service,
                "generate_download_presigned_url",
                return_value="https://download.example/source.mp4",
            ) as generate_download_url,
        ):
            result = service.get_recent_accepted_quest_submissions(
                db=db,
                current_user=make_user(),
            )

        self.assertEqual(len(result), 1)
        self.assertEqual(
            result[0].media_url,
            "https://download.example/source.mp4",
        )
        self.assertEqual(result[0].media_type, MediaType.VIDEO)
        generate_download_url.assert_called_once_with(
            "submission/1/10/source.mp4"
        )


class CommunityMediaBackfillTest(TestCase):
    def test_builds_deterministic_destination_key_for_existing_post(self) -> None:
        post = make_post(
            post_id=77,
            user_id=3,
            submission_id=200,
            media_url="submission/3/20/original.mp4",
        )

        result = backfill_community_media._build_destination_key(post)

        self.assertEqual(
            result,
            "community/3/200/existing-77.mp4",
        )

    def test_dry_run_does_not_copy_or_update_existing_post(self) -> None:
        post = make_post(
            post_id=77,
            user_id=3,
            submission_id=200,
            media_url="submission/3/20/original.jpg",
        )
        db = Mock()
        db.scalars.return_value.all.return_value = [post]
        session_context = Mock()
        session_context.__enter__ = Mock(return_value=db)
        session_context.__exit__ = Mock(return_value=False)

        with (
            patch.object(
                backfill_community_media,
                "SessionLocal",
                return_value=session_context,
            ),
            patch.object(
                backfill_community_media,
                "copy_s3_object",
            ) as copy_s3_object,
        ):
            backfill_community_media.backfill(apply_changes=False)

        copy_s3_object.assert_not_called()
        self.assertEqual(
            post.media_url,
            "submission/3/20/original.jpg",
        )
        db.commit.assert_not_called()
        db.rollback.assert_not_called()

    def test_apply_copies_existing_post_and_updates_database_key(self) -> None:
        post = make_post(
            post_id=77,
            user_id=3,
            submission_id=200,
            media_url="submission/3/20/original.jpg",
        )
        db = Mock()
        db.scalars.return_value.all.return_value = [post]
        session_context = Mock()
        session_context.__enter__ = Mock(return_value=db)
        session_context.__exit__ = Mock(return_value=False)

        with (
            patch.object(
                backfill_community_media,
                "SessionLocal",
                return_value=session_context,
            ),
            patch.object(
                backfill_community_media,
                "copy_s3_object",
            ) as copy_s3_object,
        ):
            backfill_community_media.backfill(apply_changes=True)

        copy_s3_object.assert_called_once_with(
            source_key="submission/3/20/original.jpg",
            destination_key="community/3/200/existing-77.jpg",
        )
        self.assertEqual(
            post.media_url,
            "community/3/200/existing-77.jpg",
        )
        db.commit.assert_called_once_with()
        db.rollback.assert_not_called()
