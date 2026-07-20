from __future__ import annotations

# =========================================================
# [검토 및 확인할 내용]
#
# 1. DB 세션 Dependency 경로
#    - 현재는 backend.app.common.database.get_db를 사용한다고 가정.
#    - 실제 프로젝트의 AsyncSession Dependency 함수 이름과 경로를 확인 필요.
#
# 2. 관리자 인증 Dependency 경로
#    - 현재는 backend.app.auth.dependencies.get_current_admin을 사용한다고 가정.
#    - 실제 인증 담당 팀원이 만든 관리자 인증 함수 이름과 경로를 확인 필요.
#
# 3. 관리자 ID 컬럼명
#    - 현재 로그인 관리자 객체에서 current_admin.user_id를 사용.
#    - 실제 User 모델의 PK 컬럼명이 user_id인지 확인 필요.
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
# =========================================================

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.auth.models import User
from backend.app.auth.dependencies import get_current_admin
from backend.app.common.database import get_db
from backend.app.admin.enums import UserReportStatus
from backend.app.admin.schema import (
    AdminUserDetailResponse,
    AdminUserListResponse,
    ReportResponse,
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
async def get_report_list(
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
    db: AsyncSession = Depends(get_db),
    # 관리자 권한이 확인된 로그인 사용자 정보를 주입받습니다.
    current_admin: User = Depends(get_current_admin),
) -> list[ReportResponse]:
    # 관리자가 신고 목록을 상태와 정렬 조건에 따라 조회.
    reports = await service.get_report_list(
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
    response_model=ReportResponse,
    status_code=status.HTTP_200_OK,
    summary="관리자 신고 상세 조회",
)
async def get_report_detail(
    # URL 경로를 통해 조회할 신고 ID를 전달.
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
) -> ReportResponse:
    # 관리자가 특정 신고의 상세 정보를 조회.
    report = await service.get_report_detail(
        db=db,
        report_id=report_id,
    )

    return report

# 신고된 커뮤니티 게시글을 삭제 승인하는 API.
@router.patch(
    "/reports/{report_id}/approve/post-delete",
    response_model=ReportResponse,
    status_code=status.HTTP_200_OK,
    summary="신고 게시글 삭제 승인",
)
async def approve_report_post_deletion(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
) -> ReportResponse:
    # 신고 대상 게시글을 삭제하고 해당 신고를 승인 처리.
    report = await service.approve_report_with_post_deletion(
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
async def approve_report_user_deactivation(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
) -> ReportResponse:
    # Service를 호출하여 사용자 비활성과 신고 승인을 하나의 트랜잭션으로 처리.
    report = await service.approve_report_with_user_deactivation(
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
async def get_admin_user_list(
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
    # 최신순 또는 오래된 순 정렬 여부를 전달.
    newest_first: bool = Query(
        default=True,
        description="true이면 최신 가입순, false이면 오래된 가입순",
    ),
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
) -> list[AdminUserListResponse]:
    # Service를 호출하여 조건에 맞는 사용자 목록을 조회합니다.
    users = await service.get_admin_user_list(
        db=db,
        nickname=nickname,
        is_active=is_active,
        skip=skip,
        limit=limit,
        newest_first=newest_first,
    )

    return users


# 관리자 사용자 상세 정보를 조회하는 API.
@router.get(
    "/users/{user_id}",
    response_model=AdminUserDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="관리자 사용자 상세 조회",
)
async def get_admin_user_detail(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
) -> AdminUserDetailResponse:
    # Service를 호출하여 사용자 상세 정보를 조회.
    user = await service.get_admin_user_detail(
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
async def update_admin_user_active_status(
    user_id: int,
    request: UserActiveStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
) -> AdminUserDetailResponse:

    # Service를 호출하여 사용자 활성 상태를 변경.
    updated_user = await service.update_admin_user_active_status(
        db=db,
        user_id=user_id,
        is_active=request.is_active,
        current_admin_id=current_admin.user_id,
    )

    return updated_user