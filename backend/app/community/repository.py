from __future__ import annotations

# =========================================================
# [확인 및 검토 사항]
#
# 1. QuestSubmission
#    - 실제 import 경로와 컬럼명(user_id, final_status 등) 확인
#
# 2. 피드 응답
#    - list_feed_posts() 반환값은 Service에서 화면용 Schema로 변환
#
# 3. 신고 기능
#    - 신고 생성은 Community Repository
#    - 신고 검토 및 게시글 삭제는 Admin Repository
#
# 4. 트랜잭션 처리
#    - Repository는 flush()까지만 수행
#    - commit()/rollback()은 Service에서 처리
# =========================================================

from datetime import datetime, timedelta

from sqlalchemy import Select, exists, func, select

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.auth.models import User
from backend.app.admin.models import Report

from backend.app.community.models import (
    Comment,
    CommunityPost,
    FeedHiddenPreference,
    PostLike,
)

# TODO: 퀘스트 인증 담당 팀원의 실제 모델 경로 검토 필요.
from backend.app.quest.models import QuestSubmission


# 커뮤니티 DB 조회와 생성 작업을 모아 관리하는 Repository 클래스.
class CommunityRepository:
    """커뮤니티 게시글, 좋아요, 댓글, 관심 없음 기록을 관리."""

    @staticmethod
    # 사용자가 작성한 새 커뮤니티 게시글을 DB에 생성.
    async def create_post(
        db: AsyncSession,
        *,
        user_id: int,
        submission_id: int | None,
        media_url: str,
        caption: str | None,
    ) -> CommunityPost:
        # 전달받은 값으로 새 게시글 모델 객체를 만듭니다.
        post = CommunityPost(
            user_id=user_id,
            submission_id=submission_id,
            media_url=media_url,
            caption=caption,
        )

        db.add(post)

        await db.flush()
        await db.refresh(post)

        return post

    @staticmethod
    # 게시글 ID로 커뮤니티 게시글 한 건을 조회.
    async def get_post_by_id(
        db: AsyncSession,
        *,
        post_id: int,
    ) -> CommunityPost | None:

        # 관리자 승인으로 삭제된 게시글은 DB에 존재하지 않으므로 게시글 ID만으로 조회.
        query: Select[tuple[CommunityPost]] = select(CommunityPost).where(
            CommunityPost.post_id == post_id,
        )

        result = await db.execute(query)

        return result.scalar_one_or_none()

    @staticmethod
    # 메인 화면에 표시할 커뮤니티 피드 목록을 조회.
    async def list_feed_posts(
        db: AsyncSession,
        *,
        user_id: int,
        skip: int = 0,
        limit: int = 20,
    # 게시글, 작성자, 좋아요 수, 댓글 수, 좋아요 여부의 튜플 목록을 반환.
    ) -> list[tuple[CommunityPost, User, int, int, bool]]:
        """현재 사용자에게 표시할 활성 피드 목록을 최신순으로 조회."""

        # 각 게시글의 좋아요 개수를 계산하는 연관 서브쿼리.
        like_count_query = (
            select(func.count(PostLike.user_id))
            .where(PostLike.post_id == CommunityPost.post_id)
            # CommunityPost와 연결된 서브쿼리라는 것을 SQLAlchemy에 알려줍니다.
            .correlate(CommunityPost)
            # SELECT 결과를 하나의 값처럼 사용할 수 있도록 변환합니다.
            .scalar_subquery()
        )

        # 각 게시글의 댓글 개수를 계산하는 연관 서브쿼리.
        comment_count_query = (
            select(func.count(Comment.comment_id))
            .where(Comment.post_id == CommunityPost.post_id)
            .correlate(CommunityPost)
            .scalar_subquery()
        )

        # 현재 사용자가 해당 게시글에 좋아요를 눌렀는지 확인하는 조건.
        current_user_liked_query = exists(
            # 존재 여부 확인을 위해 값 1을 조회하는 서브쿼리.
            select(1).where(
                PostLike.post_id == CommunityPost.post_id,
                PostLike.user_id == user_id,
            )
        )

        # 현재 사용자가 해당 게시글을 관심 없음 처리했는지 확인하는 조건.
        current_user_hidden_query = exists(
            # 존재 여부 확인을 위해 값 1을 조회하는 서브쿼리.
            select(1).where(
                FeedHiddenPreference.post_id == CommunityPost.post_id,
                FeedHiddenPreference.user_id == user_id,
            )
        )

        # 피드 화면에 필요한 정보를 한 번에 가져오는 쿼리.
        query = (
            # 게시글, 작성자, 좋아요 수, 댓글 수, 좋아요 여부를 함께 조회.
            select(
                # 게시글 모델 전체를 조회.
                CommunityPost,
                # 게시글 작성자 모델 전체를 조회.
                User,
                like_count_query.label("like_count"),
                comment_count_query.label("comment_count"),
                current_user_liked_query.label("is_liked"),
            )
            .join(
                User,
                User.user_id == CommunityPost.user_id,
            )
            # 현재 사용자가 관심 없음으로 처리하지 않은 게시글만 조회합니다.
            .where(
                ~current_user_hidden_query,
            )
            .order_by(
                CommunityPost.created_at.desc(),
                CommunityPost.post_id.desc(),
            )
            .offset(skip)
            .limit(limit)
        )

        # 완성된 피드 조회 쿼리를 실행.
        result = await db.execute(query)

        # SQLAlchemy Row 목록을 일반 튜플 목록으로 변환.
        return [
            # 각 행의 값을 명확한 Python 타입으로 묶습니다.
            (
                # 첫 번째 값인 게시글 객체를 넣습니다.
                row[0],
                # 두 번째 값인 작성자 객체를 넣습니다.
                row[1],
                # 세 번째 값인 좋아요 수를 int로 변환합니다.
                int(row[2]),
                # 네 번째 값인 댓글 수를 int로 변환합니다.
                int(row[3]),
                # 다섯 번째 값인 좋아요 여부를 bool로 변환합니다.
                bool(row[4]),
            )
            # 조회 결과의 모든 행을 순회합니다.
            for row in result.all()
        ]

    @staticmethod
    # 현재 사용자의 특정 게시글 좋아요 기록을 조회.
    async def get_post_like(
        db: AsyncSession,
        *,
        post_id: int,
        user_id: int,
    ) -> PostLike | None:
        """현재 사용자의 게시글 좋아요 기록을 조회합니다."""

        # 게시글 ID와 사용자 ID가 모두 같은 좋아요를 조회.
        query: Select[tuple[PostLike]] = select(PostLike).where(
            PostLike.post_id == post_id,
            PostLike.user_id == user_id,
        )

        result = await db.execute(query)

        return result.scalar_one_or_none()

    @staticmethod
    # 새로운 게시글 좋아요 기록을 생성.
    async def create_post_like(
        db: AsyncSession,
        *,
        post_id: int,
        user_id: int,
    ) -> PostLike:
        """게시글 좋아요를 생성합니다."""

        post_like = PostLike(
            post_id=post_id,
            user_id=user_id,
        )

        db.add(post_like)

        await db.flush()
        await db.refresh(post_like)

        return post_like

    @staticmethod
    # 기존 게시글 좋아요 기록을 삭제.
    async def delete_post_like(
        db: AsyncSession,
        *,
        post_like: PostLike,
    # 삭제 후 별도 객체를 반환하지 않습니다.
    ) -> None:
        await db.delete(post_like)
        await db.flush()

    @staticmethod
    # 특정 게시글을 좋아요 한 사용자 목록을 조회.
    async def list_post_like_users(
        db: AsyncSession,
        *,
        post_id: int,
        skip: int = 0,
        limit: int = 20,
    # 좋아요를 누른 User 객체 목록을 반환.
    ) -> list[User]:
        query: Select[tuple[User]] = (
            select(User)
            .join(
                PostLike,
                PostLike.user_id == User.user_id,
            )
            .where(
                PostLike.post_id == post_id,
            )
            .order_by(
                PostLike.created_at.desc(),
            )
            .offset(skip)
            .limit(limit)
        )

        result = await db.execute(query)

        return list(result.scalars().all())


    @staticmethod
    # 특정 게시글에 새 댓글을 생성.
    async def create_comment(
        db: AsyncSession,
        *,
        post_id: int,
        user_id: int,
        content: str,
    ) -> Comment:
        """게시글에 새 댓글을 생성합니다."""

        comment = Comment(
            post_id=post_id,
            user_id=user_id,
            content=content,
        )

        db.add(comment)

        await db.flush()
        await db.refresh(comment)

        return comment

    @staticmethod
    # 피드 카드에 미리 보여줄 최근 댓글 두 개를 조회.
    async def list_comment_previews(
        db: AsyncSession,
        *,
        post_id: int,
        limit: int = 2,
    # 댓글과 작성자가 묶인 튜플 목록을 반환.
    ) -> list[tuple[Comment, User]]:
        # 최근 댓글과 댓글 작성자를 함께 조회하는 쿼리.
        query = (
            select(Comment, User)
            .join(
                User,
                User.user_id == Comment.user_id,
            )
            .where(
                Comment.post_id == post_id,
            )
            .order_by(
                Comment.created_at.desc(),
                Comment.comment_id.desc(),
            )
            .limit(limit)
        )

        result = await db.execute(query)

        # 조회된 Row를 Comment와 User 튜플 목록으로 변환.
        return [
            (row[0], row[1])
            for row in result.all()
        ]

    @staticmethod
    # 댓글 바텀 시트에 표시할 전체 댓글 목록을 조회.
    async def list_post_comments(
        db: AsyncSession,
        *,
        post_id: int,
        skip: int = 0,
        limit: int = 50,
    # 댓글과 작성자가 묶인 튜플 목록을 반환.
    ) -> list[tuple[Comment, User]]:
        # 댓글과 댓글 작성자를 함께 조회하는 쿼리.
        query = (
            select(Comment, User)
            .join(
                User,
                User.user_id == Comment.user_id,
            )
            .where(
                Comment.post_id == post_id,
            )
            .order_by(
                Comment.created_at.asc(),
                Comment.comment_id.asc(),
            )
            .offset(skip)
            .limit(limit)
        )

        result = await db.execute(query)

        return [
            (row[0], row[1])
            for row in result.all()
        ]

    @staticmethod
    # 사용자가 특정 게시글을 관심 없음으로 처리한 기록을 생성.
    async def create_hidden_preference(
        db: AsyncSession,
        *,
        user_id: int,
        post_id: int,

    ) -> FeedHiddenPreference:

        hidden_preference = FeedHiddenPreference(
            user_id=user_id,
            post_id=post_id,
        )

        db.add(hidden_preference)

        await db.flush()
        await db.refresh(hidden_preference)

        return hidden_preference
    
    @staticmethod
    # 사용자가 특정 커뮤니티 게시글을 신고한 기록을 생성.
    async def create_report(
        db: AsyncSession,
        *,
        reporter_id: int,
        post_id: int,
        reason: str,
    ) -> Report:

        report = Report(
            reporter_id=reporter_id,
            post_id=post_id,
            reason=reason,
        )

        db.add(report)

        await db.flush()
        await db.refresh(report)

        return report

    """
    퀘스트 인증 내역 (추후 검토 예정)
    """

    @staticmethod
    async def list_recent_quest_submissions(
        db: AsyncSession,
        *,
        user_id: int,
        days: int = 30,
        skip: int = 0,
        limit: int = 20,
    ) -> list[QuestSubmission]:
        """최근 30일 내 승인된 퀘스트 인증 내역을 조회."""

        # 현재 시각에서 days일 전 시각을 계산.
        submitted_after = datetime.now().astimezone() - timedelta(days=days)

        # 사용자의 최근 승인된 퀘스트 인증 내역 조회 쿼리.
        query: Select[tuple[QuestSubmission]] = (
            select(QuestSubmission)
            .where(
                QuestSubmission.user_id == user_id,
                QuestSubmission.final_status == "ACCEPTED",
                QuestSubmission.submitted_at >= submitted_after,
            )
            .order_by(
                QuestSubmission.submitted_at.desc(),
                QuestSubmission.submission_id.desc(),
            )
            .offset(skip)
            .limit(limit)
        )

        result = await db.execute(query)

        return list(result.scalars().all())
