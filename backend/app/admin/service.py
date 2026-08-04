from __future__ import annotations

# =========================================================
# [검토 및 확인할 내용]
#
# 1. 트랜잭션 처리
#    - Repository는 DB 조회·변경과 flush()까지만 수행합니다.
#    - 최종 commit()과 rollback()은 common.database.get_db에서 처리합니다.
#    - Service에서는 비즈니스 검증과 Repository 호출을 담당합니다.
#
# 2. HTTPException 사용
#    - 이번 프로젝트에서는 구현을 단순하게 유지하기 위해
#      Service에서 FastAPI의 HTTPException을 사용합니다.
#
# 3. 주요 알림 응답 방식
#    - 확인할 알림이 여러 개일 수 있으므로 알림 객체의 리스트로 반환합니다.
#    - 각 알림에는 type, level, title, message, count 정보가 포함됩니다.
#    - 알림을 화면에서 3초마다 순서대로 변경하는 처리는 React Native 프론트엔드에서 담당합니다.
# =========================================================

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app.admin import repository
from backend.app.admin.enums import AdminUserSort, UserReportStatus
from backend.app.admin.models import Report
from backend.app.auth.models import User
from backend.app.admin.schema import ReportDetailResponse, ReportResponse
from backend.app.common.s3_client import generate_download_presigned_url

KST = ZoneInfo("Asia/Seoul")
REPORT_STATUS_LABELS: dict[
    UserReportStatus,
    str,
] = {
    UserReportStatus.PENDING: "처리 대기 중",
    UserReportStatus.APPROVED: "승인 완료",
    UserReportStatus.REJECTED: "반려",
    UserReportStatus.EXPIRED: "처리 기한 만료",
}

# 신고 목록을 조회하는 Service 함수.
def get_report_list(
    db: Session,
    *,
    report_status: UserReportStatus | None = None,
    skip: int = 0,
    limit: int = 20,
    newest_first: bool = True,
) -> list[Report]:
    # Repository에 목록 조회 조건을 전달하여 신고 목록을 조회.
    reports = repository.get_reports(
        db=db,
        status=report_status,
        skip=skip,
        limit=limit,
        newest_first=newest_first,
    )

    return reports

def get_report_detail_with_post(
    db: Session,
    *,
    report_id: int,
) -> ReportDetailResponse:
    """신고 정보와 화면 표시용 닉네임, 게시물 사진을 조회합니다."""

    detail = (
        repository.get_report_detail_display_data(
            db=db,
            report_id=report_id,
        )
    )

    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="신고 정보를 찾을 수 없습니다.",
        )

    (
        report,
        reporter_nickname,
        reported_user_nickname,
        reviewer_nickname,
    ) = detail

    post = None

    if report.post_id is not None:
        post = repository.get_post_by_id(
            db=db,
            post_id=report.post_id,
        )

    post_media_url = None

    if post is not None and post.media_url:
        stored_media_url = post.media_url.strip()

        if stored_media_url.startswith(
            ("http://", "https://")
        ):
            post_media_url = stored_media_url
        else:
            post_media_url = (
                generate_download_presigned_url(
                    stored_media_url,
                )
            )

    report_data = (
        ReportResponse
        .model_validate(report)
        .model_dump()
    )

    return ReportDetailResponse(
        **report_data,
        reporter_nickname=reporter_nickname,
        reported_user_nickname=(
            reported_user_nickname
        ),
        reviewer_nickname=reviewer_nickname,
        status_label=REPORT_STATUS_LABELS[
            report.status
        ],
        post_media_url=post_media_url,
    )

# 신고 상세 정보를 조회하는 Service 함수.
def get_report_detail(
    db: Session,
    *,
    report_id: int,
) -> Report:
    # Repository를 통해 신고 ID와 일치하는 신고를 조회.
    report = repository.get_report_by_id(
        db=db,
        report_id=report_id,
    )
    # 신고가 존재하지 않으면 404 오류를 발생.
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="신고 정보를 찾을 수 없습니다.",
        )
    return report


# 신고가 처리 가능한 상태인지 확인하는 내부 함수.
def _validate_report_is_pending(
    report: Report,
) -> None:
    # PENDING 상태가 아니면 이미 처리됐거나 만료된 신고이므로 승인을 막습니다.
    if report.status != UserReportStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 처리되었거나 만료된 신고입니다.",
        )

# 신고를 반려하고 관리자 처리 정보를 기록하는 Service 함수.
def reject_report(
    db: Session,
    *,
    report_id: int,
    admin_id: int,
) -> Report:
    try:
        report = get_report_detail(
            db=db,
            report_id=report_id,
        )

        _validate_report_is_pending(report)

        return repository.update_report_review(
            db=db,
            report=report,
            status=UserReportStatus.REJECTED,
            reviewed_by=admin_id,
            reviewed_at=datetime.now(timezone.utc),
        )

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="신고 반려 처리 중 오류가 발생했습니다.",
        ) from exc

# 신고와 연결된 게시글을 조회하는 내부 함수.
def _get_reported_post(
    db: Session,
    *,
    report: Report,
):
    # 신고 대상 게시글 ID가 없으면 게시글을 처리할 수 없습니다.
    if report.post_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="신고 대상 게시글 정보가 존재하지 않습니다.",
        )

    # Repository를 통해 신고 대상 게시글을 조회.
    post = repository.get_post_by_id(
        db=db,
        post_id=report.post_id,
    )

    # 게시글이 이미 삭제되었거나 존재하지 않으면 404 오류를 발생.
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="신고 대상 게시글을 찾을 수 없습니다.",
        )
    
    return post


# 신고된 게시글을 삭제하고 신고를 승인 처리하는 Service 함수.
def approve_report_with_post_deletion(
    db: Session,
    *,
    report_id: int,
    admin_id: int,
) -> Report:
    try:
        report = get_report_detail(
            db=db,
            report_id=report_id,
        )
        _validate_report_is_pending(report)

        post = _get_reported_post(
            db=db,
            report=report,
        )

        repository.delete_community_post(
            db=db,
            post=post,
        )

        reviewed_at = datetime.now(timezone.utc)

        updated_report = repository.update_report_review(
            db=db,
            report=report,
            status=UserReportStatus.APPROVED,
            reviewed_by=admin_id,
            reviewed_at=reviewed_at,
        )

        return updated_report

    # HTTPException은 원래 상태 코드와 메시지를 유지해야 하므로 그대로 다시 발생.
    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="신고 게시글 삭제 처리 중 오류가 발생했습니다.",
        ) from exc


# 신고 대상 사용자를 차단(비활성화)하고 신고를 승인 처리하는 Service 함수.
def approve_report_with_user_deactivation(
    db: Session,
    *,
    report_id: int,
    admin_id: int,
) -> Report:

    try:
        report = get_report_detail(
            db=db,
            report_id=report_id,
        )

        _validate_report_is_pending(report)

        post = _get_reported_post(
            db=db,
            report=report,
        )

        reported_user_id = post.user_id

        # 게시글 작성자 정보가 이미 삭제되어 사용자 ID가 없으면 처리를 중단.
        if reported_user_id is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="신고 대상 사용자 정보가 존재하지 않습니다.",
            )
        
        # Repository를 통해 신고 대상 사용자를 조회.
        reported_user = repository.get_user_by_id(
            db=db,
            user_id=reported_user_id,
        )

        if reported_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="신고 대상 사용자를 찾을 수 없습니다.",
            )


        # 관리자가 자신의 게시글에 대한 신고를 승인하여
        # 본인 계정을 비활성화하는 상황을 차단합니다.
        if reported_user.user_id == admin_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="관리자는 자신의 계정을 비활성화할 수 없습니다.",
            )

        if reported_user.is_active is False:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 비활성화된 사용자입니다.",
            )

        # Repository를 통해 신고 대상 사용자를 비활성 상태로 변경.
        repository.update_user_active_status(
            db=db,
            user=reported_user,
            is_active=False,
        )

        reviewed_at = datetime.now(timezone.utc)

        updated_report = repository.update_report_review(
            db=db,
            report=report,
            status=UserReportStatus.APPROVED,
            reviewed_by=admin_id,
            reviewed_at=reviewed_at,
        )

        return updated_report

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="신고 대상 사용자 비활성 처리 중 오류가 발생했습니다.",
        ) from exc
    


# 관리자 화면에서 사용자 목록을 조회하는 Service 함수.
def get_admin_user_list(
    db: Session,
    *,
    nickname: str | None = None,
    is_active: bool | None = None,
    skip: int = 0,
    limit: int = 20,
    sort_by: AdminUserSort = AdminUserSort.NEWEST,
) -> list[User]:
    """관리자 사용자 목록의 검색·필터·정렬 조건을 처리합니다."""

    normalized_nickname = (
        nickname.strip()
        if nickname is not None
        else None
    )

    if normalized_nickname == "":
        normalized_nickname = None

    return repository.get_users(
        db=db,
        nickname=normalized_nickname,
        is_active=is_active,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
    )


# 관리자 화면에서 사용자 상세 정보를 조회하는 Service 함수.
def get_admin_user_detail(
    db: Session,
    *,
    user_id: int,
) -> User:
    # Repository를 통해 사용자 한 명을 조회.
    user = repository.get_user_by_id(
        db=db,
        user_id=user_id,
    )

    # 사용자가 존재하지 않으면 404 오류 발생.
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자 정보를 찾을 수 없습니다.",
        )
    return user


# 관리자 화면에서 사용자 활성·비활성 상태를 변경하는 Service 함수.
def update_admin_user_active_status(
    db: Session,
    *,
    user_id: int,
    is_active: bool,
    current_admin_id: int,
) -> User:
    #사용자의 활성 상태를 변경합니다.
    try:
        # 상태를 변경할 사용자 정보를 조회.
        user = get_admin_user_detail(
            db=db,
            user_id=user_id,
        )

        # 관리자가 자신의 계정을 비활성화하려는 경우 처리를 막습니다.
        if user.user_id == current_admin_id and is_active is False:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="관리자는 자신의 계정을 비활성화할 수 없습니다.",
            )

        # 기존 상태와 요청 상태가 같으면 중복 변경을 막습니다.
        if user.is_active == is_active:
            current_status = "활성" if is_active else "비활성"

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"이미 {current_status} 상태인 사용자입니다.",
            )

        # Repository를 통해 사용자 활성 상태를 변경.
        updated_user = repository.update_user_active_status(
            db=db,
            user=user,
            is_active=is_active,
        )
        return updated_user

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 활성 상태 변경 중 오류가 발생했습니다.",
        ) from exc
    


# 관리자 대시보드의 오늘의 요약 정보를 조회하는 Service 함수.
def get_admin_dashboard_summary(
    db: Session,
) -> dict[str, int]:
    """관리자 대시보드에 표시할 오늘의 주요 수치를 조회합니다."""

    # 한국 시간을 기준으로 오늘 날짜를 계산.
    today = datetime.now(KST).date()

    # 전체 사용자 수를 조회.
    total_user_count = repository.count_users(
        db=db,
    )

    # 활성 상태인 사용자 수를 조회.
    active_user_count = repository.count_users_by_active_status(
        db=db,
        is_active=True,
    )

    # 비활성 상태인 사용자 수를 조회.
    inactive_user_count = repository.count_users_by_active_status(
        db=db,
        is_active=False,
    )

    # 처리 대기 상태인 신고 수를 조회.
    pending_report_count = repository.count_reports_by_status(
        db=db,
        status=UserReportStatus.PENDING,
    )

    # 오늘 날짜의 접속 사용자 수를 조회.
    today_access_counts = repository.get_daily_access_counts(
        db=db,
        start_date=today,
        end_date=today,
    )

    # 오늘 접속 기록이 없으면 0을 사용.
    today_access_user_count = (
        today_access_counts[0][1]
        if today_access_counts
        else 0
    )

    # 대시보드 오늘의 요약 정보를 딕셔너리로 반환.
    return {
        "total_user_count": total_user_count,
        "active_user_count": active_user_count,
        "inactive_user_count": inactive_user_count,
        "today_access_user_count": today_access_user_count,
        "pending_report_count": pending_report_count,
    }


# 관리자 대시보드의 주요 알림을 조회하는 Service 함수.
def get_admin_dashboard_alerts(
    db: Session,
) -> list[dict[str, str | int]]:

    # 처리 대기 상태인 신고 수를 조회.
    pending_report_count = repository.count_reports_by_status(
        db=db,
        status=UserReportStatus.PENDING,
    )

    # 자동 만료된 신고 수를 조회.
    expired_report_count = repository.count_reports_by_status(
        db=db,
        status=UserReportStatus.EXPIRED,
    )

    # 비활성 상태인 사용자 수를 조회.
    inactive_user_count = repository.count_users_by_active_status(
        db=db,
        is_active=False,
    )

    # 관리자 화면에 반환할 알림 목록을 생성.
    alerts: list[dict[str, str | int]] = []

    # 처리 대기 신고가 존재하면 확인이 필요한 알림을 추가.
    if pending_report_count > 0:
        alerts.append(
            {
                "type": "pending_report",
                "level": "warning",
                "title": "처리 대기 신고",
                "message": f"처리가 필요한 신고가 {pending_report_count}건 있습니다.",
                "count": pending_report_count,
            }
        )

    # 자동 만료된 신고가 존재하면 확인용 알림을 추가.
    if expired_report_count > 0:
        alerts.append(
            {
                "type": "expired_report",
                "level": "info",
                "title": "자동 만료 신고",
                "message": f"처리 기한이 지나 자동 만료된 신고가 {expired_report_count}건 있습니다.",
                "count": expired_report_count,
            }
        )

    # 비활성 사용자가 존재하면 계정 상태 확인 알림을 추가.
    if inactive_user_count > 0:
        alerts.append(
            {
                "type": "inactive_user",
                "level": "info",
                "title": "비활성 사용자",
                "message": f"현재 비활성 상태인 사용자가 {inactive_user_count}명 있습니다.",
                "count": inactive_user_count,
            }
        )

    # 확인할 주요 항목이 없으면 정상 상태 알림을 추가.
    if not alerts:
        alerts.append(
            {
                "type": "normal",
                "level": "success",
                "title": "확인할 주요 알림 없음",
                "message": "현재 확인이 필요한 주요 알림이 없습니다.",
                "count": 0,
            }
        )

    return alerts

# 접수 후 30일이 지난 PENDING 신고를 자동 만료 처리하는 Service 함수.
def expire_pending_reports(
    db: Session,
) -> int:
    """30일 이상 처리되지 않은 신고를 EXPIRED 상태로 변경합니다."""

    try:
        # UTC 현재 시간을 기준으로 30일 전 시각을 계산.
        expiration_date = datetime.now(timezone.utc) - timedelta(days=30)

        # Repository를 통해 만료 대상 신고를 일괄 변경.
        expired_report_count = repository.update_expired_reports(
            db=db,
            expiration_date=expiration_date,
        )
        return expired_report_count

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="신고 자동 만료 처리 중 오류가 발생했습니다.",
        ) from exc
    

# 관리자 대시보드의 최근 7일 일별 접속 사용자 수를 조회하는 Service 함수.
def get_admin_dashboard_activity_trend(
    db: Session,
) -> list[dict[str, date | int]]:
    """오늘을 포함한 최근 7일의 일별 접속 사용자 수를 조회합니다."""

    today = datetime.now(KST).date()

    # 오늘을 포함한 최근 7일이므로 6일 전을 시작 날짜로 계산.
    start_date = today - timedelta(days=6)

    # Repository를 통해 최근 7일의 날짜별 접속 사용자 수를 조회.
    daily_access_counts = repository.get_daily_access_counts(
        db=db,
        start_date=start_date,
        end_date=today,
    )

    # 조회 결과를 날짜를 키로 사용하는 딕셔너리로 변환.
    access_count_by_date = {
        access_date: user_count
        for access_date, user_count in daily_access_counts
    }

    # 접속 기록이 없는 날짜도 0명으로 포함하여 항상 7일을 반환.
    activity_trend = [
        {
            "access_date": start_date + timedelta(days=day_offset),
            "user_count": access_count_by_date.get(
                start_date + timedelta(days=day_offset),
                0,
            ),
        }
        for day_offset in range(7)
    ]

    return activity_trend