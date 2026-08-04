from __future__ import annotations

# =========================================================
# [구현 기준]
#
# 1. 퀘스트 인증 연결
#    - QuestSubmission은 quest_verification 도메인의 모델을 사용.
#    - 현재 사용자의 SubmissionStatus.ACCEPTED 인증만 게시글에 연결.
#
# 2. 피드 응답
#    - list_feed_posts()는 게시글·작성자·집계값을 반환.
#    - 최종 화면 응답 변환과 댓글 미리보기 연결은 Service에서 처리.
#
# 3. 신고 기능
#    - 신고 생성은 Community Repository에서 처리.
#    - 신고 검토와 게시글 비활성화는 Admin 기능에서 처리.
#
# 4. 관심 없음 정책
#    - 현재는 FeedHiddenPreference 기록만 생성.
#    - 기본 피드에서 즉시 제외하지 않고 추후 추천 알고리즘에서 활용.
#
# 5. 트랜잭션 처리
#    - Repository는 flush()까지만 수행.
#    - commit()과 rollback()은 공통 get_db()에서 처리.
#
# 6. 개인화 추천 피드 (알고리즘)
#    - 관심 없음으로 처리한 게시글은 추천 후보에서 제외.
#    - Repository에서는 후보 데이터만 조회하고 추천 점수 계산과 정렬은 Service에서 처리.
# =========================================================

from datetime import datetime, timedelta, timezone
from sqlalchemy import Select, exists, func, select
from sqlalchemy.orm import Session

from backend.app.auth.models import User
from backend.app.admin.models import Report
from backend.app.community.models import (
    Comment,
    CommunityPost,
    FeedHiddenPreference,
    PostLike,
    UserActivityLog,
)
from backend.app.map.models import Region
from backend.app.quest.models import Category, Quest
from backend.app.quest_verification.enums import SubmissionStatus
from backend.app.quest_verification.models import QuestSubmission
from backend.app.badge.models import Badge, UserBadge
from backend.app.shop.enums import PurchaseStatus
from backend.app.shop.models import Item, Purchase

class DuplicateCommunityPostError(Exception):
    """이미 커뮤니티 게시글에 사용된 인증일 때 발생합니다."""

class CommunityRepository:
    @staticmethod
    def get_user_by_id(
        db: Session,
        *,
        user_id: int,
    ) -> User | None:
        """공개 프로필을 표시할 사용자 한 명을 조회합니다."""

        query: Select[tuple[User]] = select(User).where(
            User.user_id == user_id,
        )

        return db.execute(query).scalar_one_or_none()

    @staticmethod
    def list_user_activity_dates(
        db: Session,
        *,
        user_id: int,
    ) -> list:
        """연속 접속일 계산에 사용할 접속 날짜를 최신순으로 조회합니다."""

        query = (
            select(UserActivityLog.access_date)
            .where(UserActivityLog.user_id == user_id)
            .order_by(UserActivityLog.access_date.desc())
        )

        return list(db.execute(query).scalars().all())

    @staticmethod
    def get_equipped_badge_name(
        db: Session,
        *,
        user_id: int,
    ) -> str | None:
        """사용자가 현재 장착한 칭호 이름을 조회합니다."""

        query = (
            select(Badge.name)
            .join(
                UserBadge,
                UserBadge.badge_id == Badge.badge_id,
            )
            .where(
                UserBadge.user_id == user_id,
                UserBadge.is_equipped.is_(True),
            )
            .limit(1)
        )

        return db.execute(query).scalar_one_or_none()

    @staticmethod
    def get_equipped_border_image_url(
        db: Session,
        *,
        user_id: int,
    ) -> str | None:
        """사용자가 현재 장착한 프로필 테두리를 조회합니다."""

        query = (
            select(Item.image_url)
            .join(
                Purchase,
                Purchase.item_id == Item.item_id,
            )
            .where(
                Purchase.user_id == user_id,
                Purchase.status == PurchaseStatus.COMPLETED,
                Purchase.is_equipped.is_(True),
            )
            .limit(1)
        )

        return db.execute(query).scalar_one_or_none()

    @staticmethod
    def list_user_quest_achievements(
        db: Session,
        *,
        user_id: int,
    ) -> list[tuple[QuestSubmission, Quest, str]]:
        """사용자의 승인된 퀘스트 달성 내역을 조회합니다."""

        query = (
            select(
                QuestSubmission,
                Quest,
                Category.code,
            )
            .join(
                Quest,
                Quest.quest_id == QuestSubmission.quest_id,
            )
            .join(
                Category,
                Category.category_id == Quest.category_id,
            )
            .where(
                QuestSubmission.user_id == user_id,
                QuestSubmission.final_status
                == SubmissionStatus.ACCEPTED,
            )
            .order_by(
                QuestSubmission.submitted_at.desc(),
                QuestSubmission.submission_id.desc(),
            )
        )

        return [
            (row[0], row[1], row[2])
            for row in db.execute(query).all()
        ]

    """커뮤니티 게시글, 좋아요, 댓글, 관심 없음 기록을 관리."""
    @staticmethod
    # 현재 사용자의 승인된 퀘스트 인증 내역을 ID로 조회.
    def get_accepted_submission_by_id(
        db: Session,
        *,
        submission_id: int,
        user_id: int,
    ) -> QuestSubmission | None:
        """게시글 생성에 사용할 현재 사용자의 승인 인증을 조회합니다."""

        query: Select[tuple[QuestSubmission]] = (
            select(QuestSubmission)
            .where(
                QuestSubmission.submission_id == submission_id,
                QuestSubmission.user_id == user_id,
                QuestSubmission.final_status == SubmissionStatus.ACCEPTED,
            )
            # 동일 인증으로 동시에 게시글을 생성하지 못하도록
            # 해당 인증 행을 현재 트랜잭션이 끝날 때까지 잠급니다.
            .with_for_update()
        )

        submission = db.execute(query).scalar_one_or_none()

        if submission is None:
            return None

        duplicate_query = select(
            exists().where(
                CommunityPost.submission_id == submission_id,
            )
        )

        already_posted = db.execute(duplicate_query).scalar_one()

        if already_posted:
            raise DuplicateCommunityPostError

        return submission

    @staticmethod
    # 사용자가 작성한 새 커뮤니티 게시글을 DB에 생성.
    def create_post(
        db: Session,
        *,
        user_id: int,
        submission_id: int,
        media_url: str,
        caption: str | None,
    ) -> CommunityPost:
        post = CommunityPost(
            user_id=user_id,
            submission_id=submission_id,
            media_url=media_url,
            caption=caption,
        )

        db.add(post)

        db.flush()
        db.refresh(post)

        return post

    @staticmethod
    def update_post_caption(
        db: Session,
        *,
        post: CommunityPost,
        caption: str | None,
    ) -> CommunityPost:
        """게시글 본문을 수정합니다."""

        post.caption = caption

        db.flush()
        db.refresh(post)

        return post

    @staticmethod
    def delete_post(
        db: Session,
        *,
        post: CommunityPost,
    ) -> None:
        """작성자가 요청한 게시글을 삭제합니다."""

        db.delete(post)
        db.flush()

    @staticmethod
    # 게시글 ID로 커뮤니티 게시글 한 건을 조회.
    def get_post_by_id(
        db: Session,
        *,
        post_id: int,
    ) -> CommunityPost | None:

        # 게시글 존재 여부와 활성 상태 확인을 분리하기 위해
        # 게시글 ID만으로 조회하고 활성 여부는 Service에서 확인합니다.
        query: Select[tuple[CommunityPost]] = select(CommunityPost).where(
            CommunityPost.post_id == post_id,
        )

        result = db.execute(query)

        return result.scalar_one_or_none()

    @staticmethod
    # 메인 화면에 표시할 커뮤니티 피드 목록을 조회.
    def list_feed_posts(
        db: Session,
        *,
        user_id: int,
        author_id: int | None = None,
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

        # 피드 화면에 필요한 정보를 한 번에 가져오는 쿼리.
        query = (
            select(
                CommunityPost,
                User,
                like_count_query.label("like_count"),
                comment_count_query.label("comment_count"),
                current_user_liked_query.label("is_liked"),
            )
            .join(
                User,
                User.user_id == CommunityPost.user_id,
            )
            .where(
                CommunityPost.is_active.is_(True),
                CommunityPost.submission_id.is_not(None),
                User.is_active.is_(True),
            )
        )

        # 내 게시물 조회에서는 로그인 사용자가 작성한 게시글만 남깁니다.
        # 기본 피드 조회에서는 author_id가 None이므로 작성자 필터를 적용하지 않습니다.
        if author_id is not None:
            query = query.where(
                CommunityPost.user_id == author_id,
            )

        query = (
            query
            .order_by(
                CommunityPost.created_at.desc(),
                CommunityPost.post_id.desc(),
            )
            .offset(skip)
            .limit(limit)
        )

        result = db.execute(query)

        # SQLAlchemy Row 목록을 일반 튜플 목록으로 변환.
        return [
            (
                # 첫 번째 값인 게시글 객체를 넣습니다.
                row[0],
                row[1],
                # 세 번째 값인 좋아요 수를 int로 변환합니다.
                int(row[2]),
                int(row[3]),
                # 다섯 번째 값인 좋아요 여부를 bool로 변환합니다.
                bool(row[4]),
            )
            # 조회 결과의 모든 행을 순회합니다.
            for row in result.all()
        ]


    @staticmethod
    # 개인화 피드 점수 계산에 사용할 추천 후보 게시글을 조회.
    def list_personalized_feed_candidates(
        db: Session,
        *,
        user_id: int,
        candidate_limit: int = 200,
    ) -> list[
        tuple[
            CommunityPost,
            User,
            int | None,
            str | None,
            int,
            int,
            bool,
        ]
    ]:

        # 각 게시글의 좋아요 개수를 계산하는 연관 서브쿼리.
        like_count_query = (
            select(func.count(PostLike.user_id))
            .where(
                PostLike.post_id == CommunityPost.post_id,
            )
            .correlate(CommunityPost)
            .scalar_subquery()
        )

        # 각 게시글의 댓글 개수를 계산하는 연관 서브쿼리.
        comment_count_query = (
            select(func.count(Comment.comment_id))
            .where(
                Comment.post_id == CommunityPost.post_id,
            )
            .correlate(CommunityPost)
            .scalar_subquery()
        )

        # 현재 사용자가 해당 게시글에 좋아요를 눌렀는지 확인.
        current_user_liked_query = exists(
            select(1).where(
                PostLike.post_id == CommunityPost.post_id,
                PostLike.user_id == user_id,
            )
        )

        # 현재 사용자가 관심 없음으로 처리한 게시글인지 확인.
        hidden_post_query = exists(
            select(1).where(
                FeedHiddenPreference.post_id == CommunityPost.post_id,
                FeedHiddenPreference.user_id == user_id,
            )
        )

        # 추천 점수 계산에 필요한 후보 게시글 정보를 조회.
        query = (
            select(
                CommunityPost,
                User,
                Category.category_id.label("quest_category_id"),
                Quest.location.label("quest_location"),
                like_count_query.label("like_count"),
                comment_count_query.label("comment_count"),
                current_user_liked_query.label("is_liked"),
            )
            # 게시글 작성자 정보를 조회.
            .join(
                User,
                User.user_id == CommunityPost.user_id,
            )
            # 게시글과 연결된 승인 인증 정보를 조회합니다.
            .join(
                QuestSubmission,
                QuestSubmission.submission_id
                == CommunityPost.submission_id,
            )

            # 인증 내역과 연결된 퀘스트 정보를 조회합니다.
            .join(
                Quest,
                Quest.quest_id == QuestSubmission.quest_id,
            )

            # 퀘스트 카테고리 정보를 조회합니다.
            .join(
                Category,
                Category.category_id == Quest.category_id,
            )
            .where(
                CommunityPost.is_active.is_(True),
                CommunityPost.submission_id.is_not(None),
                QuestSubmission.final_status == SubmissionStatus.ACCEPTED,
                User.is_active.is_(True),
                ~hidden_post_query,
            )
            # 후보 제한 전 최신 게시글을 우선 조회.
            .order_by(
                CommunityPost.created_at.desc(),
                CommunityPost.post_id.desc(),
            )
            # 전체 게시글을 무제한 조회하지 않도록 후보 수를 제한.
            .limit(candidate_limit)
        )

        result = db.execute(query)

        # SQLAlchemy Row 결과를 Service에서 사용하기 쉬운 튜플로 변환.
        return [
            (
                # 커뮤니티 게시글 객체.
                row[0],
                # 게시글 작성자 객체.
                row[1],
                # 연결된 퀘스트의 카테고리 ID.
                row[2],
                # 연결된 퀘스트의 장소.
                row[3],
                # 게시글 좋아요 수.
                int(row[4] or 0),
                # 게시글 댓글 수.
                int(row[5] or 0),
                # 현재 사용자의 좋아요 여부.
                bool(row[6]),
            )
            for row in result.all()
        ]

    @staticmethod
    # 사용자의 region_id와 연결된 실제 지역명을 조회.
    def get_region_name_by_id(
        db: Session,
        *,
        region_id: int | None,
    ) -> str | None:
        """지역 ID로 Region의 지역명을 조회합니다."""

        # 사용자가 지역을 선택하지 않은 경우 DB를 조회하지 않음.
        if region_id is None:
            return None

        query = (
            select(Region.region_name)
            .where(
                Region.region_id == region_id,
            )
        )

        result = db.execute(query)

        return result.scalar_one_or_none()

    @staticmethod
    # 현재 사용자의 특정 게시글 좋아요 기록을 조회.
    def get_post_like(
        db: Session,
        *,
        post_id: int,
        user_id: int,
    ) -> PostLike | None:

        # 게시글 ID와 사용자 ID가 모두 같은 좋아요를 조회.
        query: Select[tuple[PostLike]] = select(PostLike).where(
            PostLike.post_id == post_id,
            PostLike.user_id == user_id,
        )

        result = db.execute(query)

        return result.scalar_one_or_none()

    @staticmethod
    # 특정 게시글의 전체 좋아요 수를 조회.
    def count_post_likes(
        db: Session,
        *,
        post_id: int,
    ) -> int:
        query = select(
            func.count(PostLike.user_id)
        ).where(
            PostLike.post_id == post_id,
        )

        result = db.execute(query)

        return int(result.scalar_one())

    @staticmethod
    # 새로운 게시글 좋아요 기록을 생성.
    def create_post_like(
        db: Session,
        *,
        post_id: int,
        user_id: int,
    ) -> PostLike:

        post_like = PostLike(
            post_id=post_id,
            user_id=user_id,
        )

        db.add(post_like)

        db.flush()
        db.refresh(post_like)

        return post_like

    @staticmethod
    # 기존 게시글 좋아요 기록을 삭제.
    def delete_post_like(
        db: Session,
        *,
        post_like: PostLike,
    ) -> None:
        db.delete(post_like)
        db.flush()

    @staticmethod
    # 특정 게시글을 좋아요 한 사용자 목록을 조회.
    def list_post_like_users(
        db: Session,
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

        result = db.execute(query)

        return list(result.scalars().all())


    @staticmethod
    # 특정 게시글에 새 댓글을 생성.
    def create_comment(
        db: Session,
        *,
        post_id: int,
        user_id: int,
        content: str,
    ) -> Comment:

        comment = Comment(
            post_id=post_id,
            user_id=user_id,
            content=content,
        )

        db.add(comment)

        db.flush()
        db.refresh(comment)

        return comment

    @staticmethod
    # 피드 카드에 미리 보여줄 최근 댓글 두 개를 조회.
    def list_comment_previews(
        db: Session,
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

        result = db.execute(query)

        # 조회된 Row를 Comment와 User 튜플 목록으로 변환.
        return [
            (row[0], row[1])
            for row in result.all()
        ]

    @staticmethod
    # 댓글 바텀 시트에 표시할 전체 댓글 목록을 조회.
    def list_post_comments(
        db: Session,
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

        result = db.execute(query)

        return [
            (row[0], row[1])
            for row in result.all()
        ]

    @staticmethod
    # 사용자가 특정 게시글을 이미 관심 없음으로 처리했는지 조회.
    def get_hidden_preference(
        db: Session,
        *,
        user_id: int,
        post_id: int,
    ) -> FeedHiddenPreference | None:

        query: Select[tuple[FeedHiddenPreference]] = (
            select(FeedHiddenPreference)
            .where(
                FeedHiddenPreference.user_id == user_id,
                FeedHiddenPreference.post_id == post_id,
            )
        )

        result = db.execute(query)

        return result.scalar_one_or_none()

    @staticmethod
    # 사용자가 특정 게시글을 관심 없음으로 처리한 기록을 생성.
    def create_hidden_preference(
        db: Session,
        *,
        user_id: int,
        post_id: int,

    ) -> FeedHiddenPreference:

        hidden_preference = FeedHiddenPreference(
            user_id=user_id,
            post_id=post_id,
        )

        db.add(hidden_preference)

        db.flush()
        db.refresh(hidden_preference)

        return hidden_preference
    

    @staticmethod
    def get_report_by_reporter_and_post(
        db: Session,
        *,
        reporter_id: int,
        post_id: int,
    ) -> Report | None:
        """사용자의 동일 게시글 신고 기록을 조회합니다."""

        query: Select[tuple[Report]] = select(Report).where(
            Report.reporter_id == reporter_id,
            Report.post_id == post_id,
        )

        result = db.execute(query)

        return result.scalar_one_or_none()

    @staticmethod
    # 사용자가 특정 커뮤니티 게시글을 신고한 기록을 생성.
    def create_report(
        db: Session,
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

        db.flush()
        db.refresh(report)

        return report

    @staticmethod
    def list_recent_quest_submissions(
        db: Session,
        *,
        user_id: int,
        days: int = 30,
        skip: int = 0,
        limit: int = 20,
    ) -> list[QuestSubmission]:
        """최근 30일 내 승인된 퀘스트 인증 내역을 조회."""

        submitted_after = (
            datetime.now(timezone.utc)
            - timedelta(days=days)
        )

        # 사용자의 최근 승인된 퀘스트 인증 내역 조회 쿼리.
        query: Select[tuple[QuestSubmission]] = (
            select(QuestSubmission)
            .where(
                QuestSubmission.user_id == user_id,
                QuestSubmission.final_status == SubmissionStatus.ACCEPTED,
                QuestSubmission.submitted_at >= submitted_after,
                ~exists().where(
                    CommunityPost.submission_id
                    == QuestSubmission.submission_id,
                ),
            )
            .order_by(
                QuestSubmission.submitted_at.desc(),
                QuestSubmission.submission_id.desc(),
            )
            .offset(skip)
            .limit(limit)
        )

        result = db.execute(query)

        return list(result.scalars().all())
