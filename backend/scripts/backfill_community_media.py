from __future__ import annotations

import argparse
from pathlib import PurePosixPath

from sqlalchemy import select

import backend.app.models_registry  # noqa: F401
from backend.app.common.database import SessionLocal
from backend.app.common.s3_client import copy_s3_object
from backend.app.community.models import CommunityPost


def _build_destination_key(post: CommunityPost) -> str:
    source_key = post.media_url
    extension = PurePosixPath(source_key).suffix.lower() or ".jpg"
    submission_part = post.submission_id or "legacy"

    return (
        f"community/{post.user_id}/{submission_part}/"
        f"existing-{post.post_id}{extension}"
    )


def backfill(*, apply_changes: bool) -> None:
    with SessionLocal() as db:
        posts = list(
            db.scalars(
                select(CommunityPost)
                .where(CommunityPost.media_url.like("submission/%"))
                .order_by(CommunityPost.post_id.asc())
            ).all()
        )

        print(f"보정 대상 게시글: {len(posts)}개")

        for post in posts:
            source_key = post.media_url
            destination_key = _build_destination_key(post)

            if not apply_changes:
                print(
                    f"[DRY-RUN] post_id={post.post_id} "
                    f"{source_key} -> {destination_key}"
                )
                continue

            try:
                copy_s3_object(
                    source_key=source_key,
                    destination_key=destination_key,
                )
                post.media_url = destination_key
                db.commit()
            except Exception as exc:
                db.rollback()
                print(
                    f"[실패] post_id={post.post_id} "
                    f"{type(exc).__name__}: {exc}"
                )
                continue

            print(f"[완료] post_id={post.post_id} -> {destination_key}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "기존 커뮤니티 게시글의 submission/ 미디어를 "
            "community/ 영구 경로로 복사합니다."
        )
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="실제 S3 복사와 DB 갱신을 수행합니다.",
    )
    args = parser.parse_args()

    backfill(apply_changes=args.apply)