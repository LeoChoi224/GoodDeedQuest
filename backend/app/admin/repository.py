from __future__ import annotations

# =========================================================
# [체크 사항]
#
# 1. 트랜잭션 처리 방식
#    - 이 Repository는 DB 조회·변경과 flush()까지만 처리합니다.
#    - 최종 commit()과 rollback()은 common.database.get_db에서 처리합니다.
#
# 2. 신고 자동 만료 및 승인 정책
#    - 접수 후 30일 동안 처리되지 않은 PENDING 신고는 EXPIRED 상태로 자동 변경합니다.
#    - EXPIRED는 관리자가 신고를 거부한 상태가 아니라 처리 기한이 지나 자동 종료된 상태입니다.
#    - 관리자는 신고를 승인하여 게시글을 삭제하거나 신고 대상 사용자를 비활성화할 수 있습니다.
#    - 별도의 신고 반려 기능은 이번 프로젝트에서 구현하지 않습니다.
#
# 3. 퀘스트 인증 악용사례 이미지
#    - 현재 코드는 커뮤니티 게시물 신고만 직접 조회합니다.
#    - 퀘스트 인증 모델이 완성된 후 인증 이미지 조회 함수를 추가해야 합니다.
#
# 4. 전날 대비 변동 수치
#     - 현재 DB 구조만으로 과거 시점의 활성/비활성 사용자 수를
#       정확히 계산하기 어려워 이번 프로젝트에서는 우선순위를 두고 현재 작업은 하지 않았습니다.
# =========================================================

from datetime import date, datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.orm import Session, aliased

from backend.app.auth.models import User
from backend.app.admin.models import Report
from backend.app.admin.enums import AdminUserSort, UserReportStatus
from backend.app.community.models import CommunityPost, UserActivityLog


def get_reports(
    db: Session,
    status: UserReportStatus | None = None,
    skip: int = 0,
    limit: int = 20,
    newest_first: bool = True,
) -> list[Report]:
    """관리자용 신고 목록을 조회합니다."""

    """
    Select[tuple[Report]] → "이 쿼리의 결과가 Report를 가져온다" 라고 IDE와 개발자에게 알려주는 타입 힌트.
    SQL은 한 줄(Row) 씩 데이터를 가져오는데, SQLAlchemy는 그 한 줄을 튜플(tuple) 형태로 표현
    """
    query: Select[tuple[Report]] = select(Report)

    if status is not None:
        query = query.where(Report.status == status)

    if newest_first:
        query = query.order_by(Report.created_at.desc())
    else:
        query = query.order_by(Report.created_at.asc())

    # 무한 스크롤 또는 페이지 조회에 사용할 범위를 적용.
    query = query.offset(skip).limit(limit)

    # 완성된 신고 목록 조회 쿼리를 실행 후 조회된 신고 객체를 리스트 형태로 반환.
    result = db.execute(query)
    return list(result.scalars().all())


def get_report_by_id(
    db: Session,
    report_id: int,
) -> Report | None:
    """신고 ID로 신고 상세 정보를 조회합니다."""

    query = select(Report).where(
        Report.report_id == report_id,
    )


    result = db.execute(query)
    return result.scalar_one_or_none()      # 신고가 존재하면 Report 객체를, 없으면 None을 반환합니다.

def get_report_detail_display_data(
    db: Session,
    report_id: int,
) -> tuple[
    Report,
    str,
    str | None,
    str | None,
] | None:
    """신고 상세에 표시할 사용자 닉네임을 함께 조회합니다."""

    reporter = aliased(User)
    reported_user = aliased(User)
    reviewer = aliased(User)

    query = (
        select(
            Report,
            reporter.nickname.label(
                "reporter_nickname"
            ),
            reported_user.nickname.label(
                "reported_user_nickname"
            ),
            reviewer.nickname.label(
                "reviewer_nickname"
            ),
        )
        .join(
            reporter,
            reporter.user_id == Report.reporter_id,
        )
        .outerjoin(
            CommunityPost,
            CommunityPost.post_id == Report.post_id,
        )
        .outerjoin(
            reported_user,
            reported_user.user_id
            == CommunityPost.user_id,
        )
        .outerjoin(
            reviewer,
            reviewer.user_id == Report.reviewed_by,
        )
        .where(
            Report.report_id == report_id,
        )
    )

    row = db.execute(query).one_or_none()

    if row is None:
        return None

    (
        report,
        reporter_nickname,
        reported_user_nickname,
        reviewer_nickname,
    ) = row

    return (
        report,
        reporter_nickname,
        reported_user_nickname,
        reviewer_nickname,
    )

def update_report_review(
    db: Session,
    report: Report,
    status: UserReportStatus,
    reviewed_by: int,
    reviewed_at: datetime,
) -> Report:
    """신고 상태와 관리자 처리 정보를 업데이트합니다."""

    report.status = status
    report.reviewed_by = reviewed_by
    report.reviewed_at = reviewed_at

    db.flush()
    db.refresh(report)
    return report


def update_expired_reports(
    db: Session,
    expiration_date: datetime,
) -> int:
    """처리 기한이 지난 PENDING 신고를 EXPIRED로 변경합니다."""

    """
    admin/repository.py
    → 실제 DB의 신고 상태 변경

    admin/service.py
    → 오늘로부터 30일 전 날짜를 계산하고 Repository 호출

    스케줄러 설정 파일
    → 매일 정해진 시간에 Service 실행
    """
    # PENDING 상태이면서 기준 날짜 이전에 접수된 신고를 일괄 변경합니다.
    query = (
        update(Report)
        .where(
            Report.status == UserReportStatus.PENDING,
            Report.created_at < expiration_date,
        )
        .values(
            status=UserReportStatus.EXPIRED,
        )
    )

    result = db.execute(query)

    db.flush()
    return result.rowcount or 0





def get_users(
    db: Session,
    nickname: str | None = None,
    is_active: bool | None = None,
    skip: int = 0,
    limit: int = 20,
    sort_by: AdminUserSort = AdminUserSort.NEWEST,
) -> list[User]:
    """검색·활성 상태·정렬 조건에 맞는 관리자용 사용자 목록을 조회합니다."""

    query: Select[tuple[User]] = select(User)

    if nickname:
        query = query.where(
            User.nickname.ilike(f"%{nickname}%"),
        )

    # false이면 비활성화된 사용자만 조회합니다.
    if is_active is not None:
        query = query.where(
            User.is_active == is_active,
        )

    if sort_by == AdminUserSort.OLDEST:
        query = query.order_by(
            User.created_at.asc(),
            User.user_id.asc(),
        )

    elif sort_by == AdminUserSort.LEVEL:
        query = query.order_by(
            User.current_level.desc(),
            User.created_at.desc(),
            User.user_id.desc(),
        )

    elif sort_by == AdminUserSort.NICKNAME:
        query = query.order_by(
            func.lower(User.nickname).asc(),
            User.user_id.asc(),
        )

    elif sort_by == AdminUserSort.TRUST:
        query = query.order_by(
            User.trust_score.desc(),
            User.created_at.desc(),
            User.user_id.desc(),
        )

    else:
        query = query.order_by(
            User.created_at.desc(),
            User.user_id.desc(),
        )

    query = query.offset(skip).limit(limit)

    result = db.execute(query)

    return list(result.scalars().all())


def get_user_by_id(
    db: Session,
    user_id: int,
) -> User | None:
    """사용자 ID로 사용자 한 명을 조회합니다."""

    query = select(User).where(
        User.user_id == user_id,
    )

    result = db.execute(query)
    return result.scalar_one_or_none()


def update_user_active_status(
    db: Session,
    user: User,
    is_active: bool,
) -> User:
    """사용자의 활성 또는 비활성 상태를 변경합니다."""

    user.is_active = is_active

    db.flush()
    db.refresh(user)
    return user




def get_post_by_id(
    db: Session,
    post_id: int,
) -> CommunityPost | None:
    """신고 대상 커뮤니티 게시물을 조회합니다."""

    query = select(CommunityPost).where(
        CommunityPost.post_id == post_id,
    )

    result = db.execute(query)
    return result.scalar_one_or_none()


def delete_community_post(
    db: Session,
    post: CommunityPost,
) -> None:
    """신고가 승인된 커뮤니티 게시물을 삭제합니다."""

    db.delete(post)
    db.flush()




def count_users(
    db: Session,
) -> int:
    """전체 사용자 수를 조회합니다."""

    query = select(func.count(User.user_id))

    result = db.execute(query)
    return result.scalar_one()


def count_users_by_active_status(
    db: Session,
    is_active: bool,
) -> int:
    """활성 또는 비활성 사용자 수를 조회합니다."""

    query = select(func.count(User.user_id)).where(
        User.is_active == is_active,
    )

    result = db.execute(query)
    return result.scalar_one()


def count_reports_by_status(
    db: Session,
    status: UserReportStatus,
) -> int:
    """특정 처리 상태의 신고 수를 조회합니다."""

    query = select(func.count(Report.report_id)).where(
        Report.status == status,
    )

    result = db.execute(query)
    return result.scalar_one()


def get_daily_access_counts(
    db: Session,
    start_date: date,
    end_date: date,
) -> list[tuple[date, int]]:
    """지정한 기간의 날짜별 접속 사용자 수를 조회합니다."""

    query = (
        select(
            UserActivityLog.access_date,
            func.count(
                func.distinct(UserActivityLog.user_id)
            ).label("user_count"),
        )
        .where(
            UserActivityLog.access_date >= start_date,
            UserActivityLog.access_date <= end_date,
        )
        # 같은 날짜의 접속 기록을 하나의 그룹으로 묶습니다.
        .group_by(UserActivityLog.access_date)
        .order_by(UserActivityLog.access_date.asc())
    )

    result = db.execute(query)

    # 날짜와 접속 사용자 수를 튜플 리스트로 반환합니다.
    return [
        (row.access_date, row.user_count)
        for row in result.all()
    ]