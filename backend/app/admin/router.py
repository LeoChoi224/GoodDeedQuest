from __future__ import annotations

# =========================================================
# [검토 및 확인할 내용]
#
# 1. DB 세션 Dependency
#    - backend.app.common.database.get_db를 사용합니다.
#    - 동기 Session은 각 요청이 끝나면 공통 DB Dependency에서 정리합니다.
#    - 요청 성공 시 commit, 오류 발생 시 rollback도 공통 DB Dependency에서 처리합니다.
#
# 2. 관리자 인증 Dependency
#    - JWT 생성 및 검증은 common.auth를 재사용합니다.
#    - get_current_user()에서 현재 로그인 사용자를 조회합니다.
#    - get_current_admin()에서 관리자 권한을 확인합니다.
#
# 3. 관리자 ID 사용
#    - 현재 로그인 관리자 객체의 current_admin.user_id를 사용합니다.
#    - 신고 처리 시 reviewed_by에 해당 관리자 ID를 저장합니다.
#
# 4. 신고 관리 API 주소
#    - GET   /admin/reports
#    - GET   /admin/reports/{report_id}
#    - PATCH /admin/reports/{report_id}/approve/post-delete
#    - PATCH /admin/reports/{report_id}/approve/user-deactivate
#
# 5. 사용자 관리 API 주소
#    - GET   /admin/users
#    - GET   /admin/users/{user_id}
#    - PATCH /admin/users/{user_id}/active-status
#
# 6. 관리자 대시보드 API 주소
#    - GET /admin/dashboard/summary
#    - GET /admin/dashboard/alerts
#    - GET /admin/dashboard/activity-trend
#
# 7. 대시보드 응답 Schema
#    - 오늘의 요약은 AdminDashboardSummaryResponse를 사용합니다.
#    - 주요 알림은 list[AdminDashboardAlertResponse] 형태를 사용합니다.
#    - 최근 7일 활동 추이는 list[AdminDashboardActivityTrendResponse] 형태를 사용합니다.
# =========================================================

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.auth.models import User
from backend.app.admin.dependencies import get_current_admin
from backend.app.common.database import get_db
from backend.app.admin.enums import AdminUserSort, UserReportStatus
from backend.app.admin.schema import (
    AdminDashboardActivityTrendResponse,
    AdminDashboardAlertResponse,
    AdminDashboardSummaryResponse,
    AdminUserDetailResponse,
    AdminUserListResponse,
    ReportResponse,
    ReportDetailResponse,
    UserActiveStatusUpdate,
)
from backend.app.admin import service

# 관리자 신고 API를 하나로 묶는 Router를 생성.
router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)

# 관리자 신고 목록을 조회하는 API.
@router.get(
    "/reports",
    response_model=list[ReportResponse],
    status_code=status.HTTP_200_OK,
    summary="관리자 신고 목록 조회",
)
def get_report_list(
    # 신고 상태 필터를 선택적으로 전달.
    report_status: UserReportStatus | None = Query(
        default=None,
        alias="status",
        description="조회할 신고 처리 상태",
    ),
    # 신고 목록에서 앞쪽 데이터 몇 개를 제외하고 조회할지 전달받습니다.
    # 무한 스크롤을 위해 skip을 사용
    skip: int = Query(
        default=0,
        ge=0,
        description="건너뛸 신고 개수",
    ),
    # 한 번에 조회할 신고 개수를 전달.
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="한 번에 조회할 신고 개수",
    ),
    # 최신순 또는 오래된 순 정렬 여부를 전달.
    newest_first: bool = Query(
        default=True,
        description="true이면 최신순, false이면 오래된 순",
    ),
    db: Session = Depends(get_db),
    # 관리자 권한이 확인된 로그인 사용자 정보를 주입받습니다.
    current_admin: User = Depends(get_current_admin),
) -> list[ReportResponse]:
    # 관리자가 신고 목록을 상태와 정렬 조건에 따라 조회.
    reports = service.get_report_list(
        db=db,
        report_status=report_status,
        skip=skip,
        limit=limit,
        newest_first=newest_first,
    )

    return reports

# 관리자 신고 상세 정보를 조회하는 API.
@router.get(
    "/reports/{report_id}",
    response_model=ReportDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="관리자 신고 상세 조회",
)
def get_report_detail(
    report_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
) -> ReportDetailResponse:
    return service.get_report_detail_with_post(
        db=db,
        report_id=report_id,
    )

# 처리 대기 중인 신고를 반려하는 API.
@router.patch(
    "/reports/{report_id}/reject",
    response_model=ReportResponse,
    status_code=status.HTTP_200_OK,
    summary="신고 반려",
)
def reject_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
) -> ReportResponse:
    return service.reject_report(
        db=db,
        report_id=report_id,
        admin_id=current_admin.user_id,
    )

# 신고된 커뮤니티 게시글을 삭제 승인하는 API.
@router.patch(
    "/reports/{report_id}/approve/post-delete",
    response_model=ReportResponse,
    status_code=status.HTTP_200_OK,
    summary="신고 게시글 삭제 승인",
)
def approve_report_post_deletion(
    report_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
) -> ReportResponse:
    # 신고 대상 게시글을 삭제하고 해당 신고를 승인 처리.
    report = service.approve_report_with_post_deletion(
        db=db,
        report_id=report_id,
        admin_id=current_admin.user_id,
    )

    return report


# 신고 대상 사용자를 비활성 승인하는 API.
@router.patch(
    "/reports/{report_id}/approve/user-deactivate",
    response_model=ReportResponse,
    status_code=status.HTTP_200_OK,
    summary="신고 대상 사용자 비활성 승인",
)
def approve_report_user_deactivation(
    report_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
) -> ReportResponse:
    # Service를 호출하여 사용자 비활성과 신고 승인을 하나의 트랜잭션으로 처리.
    report = service.approve_report_with_user_deactivation(
        db=db,
        report_id=report_id,
        admin_id=current_admin.user_id,
    )

    return report



# 관리자 사용자 목록을 조회하는 API.
@router.get(
    "/users",
    response_model=list[AdminUserListResponse],
    status_code=status.HTTP_200_OK,
    summary="관리자 사용자 목록 조회",
)
def get_admin_user_list(
    # 닉네임 검색어를 선택적으로 전달.
    nickname: str | None = Query(
        default=None,
        min_length=1,
        max_length=50,
        description="검색할 사용자 닉네임",
    ),
    # 사용자 활성·비활성 상태를 선택적으로 전달.
    is_active: bool | None = Query(
        default=None,
        description="true이면 활성 사용자, false이면 비활성 사용자",
    ),
    # 사용자 목록에서 앞쪽 데이터 몇 개를 제외할지 전달.
    skip: int = Query(
        default=0,
        ge=0,
        description="건너뛸 사용자 개수",
    ),
    # 한 번에 조회할 사용자 개수를 전달.
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="한 번에 조회할 사용자 개수",
    ),
    # 사용자 정렬 여부를 전달.
    sort_by: AdminUserSort = Query(
        default=AdminUserSort.NEWEST,
        description=(
            "사용자 정렬 기준: "
            "newest, oldest, level, nickname, trust"
        ),
    ),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
) -> list[AdminUserListResponse]:
    # Service를 호출하여 조건에 맞는 사용자 목록을 조회합니다.
    users = service.get_admin_user_list(
        db=db,
        nickname=nickname,
        is_active=is_active,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
    )

    return users


# 관리자 사용자 상세 정보를 조회하는 API.
@router.get(
    "/users/{user_id}",
    response_model=AdminUserDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="관리자 사용자 상세 조회",
)
def get_admin_user_detail(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
) -> AdminUserDetailResponse:
    # Service를 호출하여 사용자 상세 정보를 조회.
    user = service.get_admin_user_detail(
        db=db,
        user_id=user_id,
    )

    return user

# 관리자 사용자 활성·비활성 상태를 변경하는 API.
@router.patch(
    "/users/{user_id}/active-status",
    response_model=AdminUserDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="관리자 사용자 활성 상태 변경",
)
def update_admin_user_active_status(
    user_id: int,
    request: UserActiveStatusUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
) -> AdminUserDetailResponse:

    # Service를 호출하여 사용자 활성 상태를 변경.
    updated_user = service.update_admin_user_active_status(
        db=db,
        user_id=user_id,
        is_active=request.is_active,
        current_admin_id=current_admin.user_id,
    )

    return updated_user



# 관리자 대시보드의 오늘의 요약 정보를 조회하는 API.
@router.get(
    "/dashboard/summary",
    response_model=AdminDashboardSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="관리자 대시보드 오늘의 요약 조회",
)
def get_admin_dashboard_summary(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
) -> AdminDashboardSummaryResponse:

    # Service를 호출하여 대시보드 오늘의 요약 정보를 조회.
    summary = service.get_admin_dashboard_summary(
        db=db,
    )

    return summary


# 관리자 대시보드의 주요 알림을 조회하는 API.
@router.get(
    "/dashboard/alerts",
    response_model=list[AdminDashboardAlertResponse],
    status_code=status.HTTP_200_OK,
    summary="관리자 대시보드 주요 알림 조회",
)
def get_admin_dashboard_alerts(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
) -> list[AdminDashboardAlertResponse]:
    """관리자가 확인해야 할 주요 알림 목록을 조회합니다."""

    # Service를 호출하여 관리자 주요 알림 목록을 조회.
    alerts = service.get_admin_dashboard_alerts(
        db=db,
    )

    return alerts

# 관리자 대시보드의 최근 7일 일별 접속 사용자 수를 조회하는 API.
@router.get(
    "/dashboard/activity-trend",
    response_model=list[AdminDashboardActivityTrendResponse],
    status_code=status.HTTP_200_OK,
    summary="관리자 대시보드 최근 7일 활동 추이 조회",
)
def get_admin_dashboard_activity_trend(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
) -> list[AdminDashboardActivityTrendResponse]:
    """오늘을 포함한 최근 7일의 일별 접속 사용자 수를 조회합니다."""

    # Service를 호출하여 최근 7일 활동 추이를 조회.
    activity_trend = service.get_admin_dashboard_activity_trend(
        db=db,
    )

    return activity_trend