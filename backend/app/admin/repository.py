from __future__ import annotations

# =========================================================
# [체크 사항]
#
# 1. 트랜잭션 처리 방식
#    - 이 Repository는 flush()까지만 처리합니다.
#    - 최종 commit()과 오류 발생 시 rollback()은 Service에서 처리합니다.
#
# 2. 신고 자동 만료 정책
#    - 접수 후 일정 기간 (30일) 처리되지 않은 PENDING 신고는 EXPIRED 상태로 자동 변경. (EXPIRED는 관리자 거부가 아니라 자동 종료 상태입니다.)
#    - 관리자 승인/거부는 update_report_review()에서 처리합니다. (추후 승인버튼, 거부버튼 팝업 신규 작업 필요 (스토리보드에 없는 신규 내용))
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
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.auth.models import User
from backend.app.admin.models import Report
from backend.app.admin.enums import UserReportStatus
from backend.app.community.models import CommunityPost, UserActivityLog


async def get_reports(
    db: AsyncSession,
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
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_report_by_id(
    db: AsyncSession,
    report_id: int,
) -> Report | None:
    """신고 ID로 신고 상세 정보를 조회합니다."""

    query = select(Report).where(
        Report.report_id == report_id,
    )


    result = await db.execute(query)
    return result.scalar_one_or_none()      # 신고가 존재하면 Report 객체를, 없으면 None을 반환합니다.


async def update_report_review(
    db: AsyncSession,
    report: Report,
    status: UserReportStatus,
    reviewed_by: int,
    reviewed_at: datetime,
) -> Report:
    """신고 상태와 관리자 처리 정보를 업데이트합니다."""

    report.status = status
    report.reviewed_by = reviewed_by
    report.reviewed_at = reviewed_at

    await db.flush()
    await db.refresh(report)
    return report


async def update_expired_reports(
    db: AsyncSession,
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

    result = await db.execute(query)

    await db.flush()
    return result.rowcount or 0





async def get_users(
    db: AsyncSession,
    nickname: str | None = None,
    is_active: bool | None = None,
    skip: int = 0,
    limit: int = 20,
    newest_first: bool = True,
) -> list[User]:
    """관리자용 사용자 목록을 조회합니다."""

    query: Select[tuple[User]] = select(User)

    if nickname:
        query = query.where(
            User.nickname.ilike(f"%{nickname}%"),
        )

    # 활성 상태가 전달되면 활성 또는 비활성 사용자만 조회합니다. (필터 조회)
    # None이면 활성·비활성 사용자 전체를 조회합니다.
    if is_active is not None:
        query = query.where(
            User.is_active == is_active,
        )

    if newest_first:
        query = query.order_by(User.created_at.desc())
    else:
        query = query.order_by(User.created_at.asc())

    query = query.offset(skip).limit(limit)
   
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_user_by_id(
    db: AsyncSession,
    user_id: int,
) -> User | None:
    """사용자 ID로 사용자 한 명을 조회합니다."""

    query = select(User).where(
        User.user_id == user_id,
    )

    result = await db.execute(query)
    return result.scalar_one_or_none()


async def update_user_active_status(
    db: AsyncSession,
    user: User,
    is_active: bool,
) -> User:
    """사용자의 활성 또는 비활성 상태를 변경합니다."""

    user.is_active = is_active

    await db.flush()
    await db.refresh(user)
    return user




async def get_post_by_id(
    db: AsyncSession,
    post_id: int,
) -> CommunityPost | None:
    """신고 대상 커뮤니티 게시물을 조회합니다."""

    query = select(CommunityPost).where(
        CommunityPost.post_id == post_id,
    )

    result = await db.execute(query)
    return result.scalar_one_or_none()


async def delete_community_post(
    db: AsyncSession,
    post: CommunityPost,
) -> None:
    """신고가 승인된 커뮤니티 게시물을 삭제합니다."""

    await db.delete(post)
    await db.flush()




async def count_users(
    db: AsyncSession,
) -> int:
    """전체 사용자 수를 조회합니다."""

    query = select(func.count(User.user_id))

    result = await db.execute(query)
    return result.scalar_one()


async def count_users_by_active_status(
    db: AsyncSession,
    is_active: bool,
) -> int:
    """활성 또는 비활성 사용자 수를 조회합니다."""

    query = select(func.count(User.user_id)).where(
        User.is_active == is_active,
    )

    result = await db.execute(query)
    return result.scalar_one()


async def count_reports_by_status(
    db: AsyncSession,
    status: UserReportStatus,
) -> int:
    """특정 처리 상태의 신고 수를 조회합니다."""

    query = select(func.count(Report.report_id)).where(
        Report.status == status,
    )

    result = await db.execute(query)
    return result.scalar_one()


async def get_daily_access_counts(
    db: AsyncSession,
    start_date: date,
    end_date: date,
) -> list[tuple[date, int]]:
    """지정한 기간의 날짜별 접속 사용자 수를 조회합니다."""

    query = (
        select(
            UserActivityLog.access_date,
            func.count(UserActivityLog.user_id).label("user_count"),
        )
        .where(
            UserActivityLog.access_date >= start_date,
            UserActivityLog.access_date <= end_date,
        )
        # 같은 날짜의 접속 기록을 하나의 그룹으로 묶습니다.
        .group_by(UserActivityLog.access_date)
        .order_by(UserActivityLog.access_date.asc())
    )

    result = await db.execute(query)

    # 날짜와 접속 사용자 수를 튜플 리스트로 반환합니다.
    return [
        (row.access_date, row.user_count)
        for row in result.all()
    ]