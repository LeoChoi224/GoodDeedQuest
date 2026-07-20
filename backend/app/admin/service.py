from __future__ import annotations

# =========================================================
# [검토 및 확인할 내용]
#
# 1. 트랜잭션 처리
#    - Repository는 flush()까지만 수행합니다.
#    - Service에서 commit()과 rollback()을 처리합니다.
#
# 2. HTTPException 사용
#    - 이번 프로젝트에서는 구현을 단순하게 유지하기 위해
#      Service에서 FastAPI의 HTTPException을 사용합니다.
#
# 3. 관리자 본인 계정 비활성화
#    - 관리자가 본인 계정을 비활성화하지 못하도록 처리했습니다.
#    - Router에서 current_admin.user_id를 Service에 전달합니다.
#
# 4. 다른 관리자 계정 상태 변경
#    - 현재는 관리자 계정도 활성·비활성 상태 변경이 가능합니다.
#    - 일반 관리자끼리 상태를 변경하지 못하게 할지 팀 정책 확인이 필요합니다.
# =========================================================

from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin import repository
from backend.app.admin.enums import UserReportStatus
from backend.app.admin.models import Report
from backend.app.auth.models import User

# 신고 목록을 조회하는 Service 함수.
async def get_report_list(
    db: AsyncSession,
    *,
    report_status: UserReportStatus | None = None,
    skip: int = 0,
    limit: int = 20,
    newest_first: bool = True,
) -> list[Report]:
    # Repository에 목록 조회 조건을 전달하여 신고 목록을 조회.
    reports = await repository.get_reports(
        db=db,
        status=report_status,
        skip=skip,
        limit=limit,
        newest_first=newest_first,
    )

    return reports


# 신고 상세 정보를 조회하는 Service 함수.
async def get_report_detail(
    db: AsyncSession,
    *,
    report_id: int,
) -> Report:
    # Repository를 통해 신고 ID와 일치하는 신고를 조회.
    report = await repository.get_report_by_id(
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


# 신고와 연결된 게시글을 조회하는 내부 함수.
async def _get_reported_post(
    db: AsyncSession,
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
    post = await repository.get_post_by_id(
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
async def approve_report_with_post_deletion(
    db: AsyncSession,
    *,
    report_id: int,
    admin_id: int,
) -> Report:
    try:
        report = await get_report_detail(
            db=db,
            report_id=report_id,
        )
        _validate_report_is_pending(report)

        post = await _get_reported_post(
            db=db,
            report=report,
        )

        await repository.delete_community_post(
            db=db,
            post=post,
        )

        reviewed_at = datetime.now(timezone.utc)

        updated_report = await repository.update_report_review(
            db=db,
            report=report,
            status=UserReportStatus.APPROVED,
            reviewed_by=admin_id,
            reviewed_at=reviewed_at,
        )

        await db.commit()
        await db.refresh(updated_report)

        return updated_report

    # HTTPException은 원래 상태 코드와 메시지를 유지해야 하므로 그대로 다시 발생.
    except HTTPException:
        await db.rollback()
        raise

    except Exception as exc:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="신고 게시글 삭제 처리 중 오류가 발생했습니다.",
        ) from exc


# 신고 대상 사용자를 차단(비활성화)하고 신고를 승인 처리하는 Service 함수.
async def approve_report_with_user_deactivation(
    db: AsyncSession,
    *,
    report_id: int,
    admin_id: int,
) -> Report:

    try:
        report = await get_report_detail(
            db=db,
            report_id=report_id,
        )

        _validate_report_is_pending(report)

        post = await _get_reported_post(
            db=db,
            report=report,
        )

        reported_user_id = post.user_id

        # Repository를 통해 신고 대상 사용자를 조회.
        reported_user = await repository.get_user_by_id(
            db=db,
            user_id=reported_user_id,
        )

        if reported_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="신고 대상 사용자를 찾을 수 없습니다.",
            )

        if reported_user.is_active is False:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 비활성화된 사용자입니다.",
            )

        # Repository를 통해 신고 대상 사용자를 비활성 상태로 변경.
        await repository.update_user_active_status(
            db=db,
            user=reported_user,
            is_active=False,
        )

        reviewed_at = datetime.now(timezone.utc)

        updated_report = await repository.update_report_review(
            db=db,
            report=report,
            status=UserReportStatus.APPROVED,
            reviewed_by=admin_id,
            reviewed_at=reviewed_at,
        )

        await db.commit()
        await db.refresh(updated_report)

        return updated_report

    except HTTPException:
        await db.rollback()

        raise

    except Exception as exc:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="신고 대상 사용자 비활성 처리 중 오류가 발생했습니다.",
        ) from exc
    


# 관리자 화면에서 사용자 목록을 조회하는 Service 함수.
async def get_admin_user_list(
    db: AsyncSession,
    *,
    nickname: str | None = None,
    is_active: bool | None = None,
    skip: int = 0,
    limit: int = 20,
    newest_first: bool = True,
) -> list[User]:
    # 닉네임과 활성 상태 조건에 따라 사용자 목록을 조회.
    # 닉네임 검색어가 존재하면 앞뒤 공백을 제거합니다.
    normalized_nickname = nickname.strip() if nickname is not None else None

    # 닉네임 검색어가 공백뿐이라면 검색 조건을 제거.
    if normalized_nickname == "":
        normalized_nickname = None

    # Repository를 통해 조건에 맞는 사용자 목록을 조회.
    users = await repository.get_users(
        db=db,
        nickname=normalized_nickname,
        is_active=is_active,
        skip=skip,
        limit=limit,
        newest_first=newest_first,
    )

    return users


# 관리자 화면에서 사용자 상세 정보를 조회하는 Service 함수.
async def get_admin_user_detail(
    db: AsyncSession,
    *,
    user_id: int,
) -> User:
    # Repository를 통해 사용자 한 명을 조회.
    user = await repository.get_user_by_id(
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
async def update_admin_user_active_status(
    db: AsyncSession,
    *,
    user_id: int,
    is_active: bool,
    current_admin_id: int,
) -> User:
    #사용자의 활성 상태를 변경합니다.
    try:
        # 상태를 변경할 사용자 정보를 조회.
        user = await get_admin_user_detail(
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
        updated_user = await repository.update_user_active_status(
            db=db,
            user=user,
            is_active=is_active,
        )

        await db.commit()
        await db.refresh(updated_user)

        return updated_user

    except HTTPException:
        await db.rollback()
        raise

    except Exception as exc:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 활성 상태 변경 중 오류가 발생했습니다.",
        ) from exc