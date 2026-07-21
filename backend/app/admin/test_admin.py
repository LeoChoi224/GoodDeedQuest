from __future__ import annotations

# =========================================================
# [반드시 확인 및 검토할 사항]
#
# 1. 테스트 파일 위치
#    - 권장 위치: backend/tests/admin/test_admin.py
#    - 프로젝트의 기존 tests 폴더 규칙이 다르면 위치만 맞춰 이동합니다.
#
# 2. 테스트 실행 명령어
#    - 프로젝트 루트에서 다음 명령어로 실행합니다.
#      python -m pytest backend/tests/admin/test_admin.py -v
#
# 3. 테스트 방식
#    - 실제 PostgreSQL을 사용하지 않는 단위 테스트입니다.
#    - Repository와 DB 세션을 Mock으로 대체하여 Service의 비즈니스 규칙,
#      commit/rollback 처리, 관리자 권한 검사를 확인합니다.
#
# 4. 필요한 패키지
#    - pytest가 필요합니다.
#    - 비동기 테스트는 unittest.IsolatedAsyncioTestCase를 사용하므로
#      pytest-asyncio 플러그인이 없어도 실행할 수 있습니다.
#
# 5. 프로젝트 경로
#    - import 경로는 현재 프로젝트 구조인 backend.app.admin 기준입니다.
# =========================================================

from datetime import date, timedelta
from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException, status

from backend.app.admin import service
from backend.app.admin.dependencies import get_current_admin
from backend.app.admin.enums import UserReportStatus
from backend.app.auth.enums import UserRole


# 테스트에서 공통으로 사용할 비동기 DB 세션 Mock을 생성합니다.
def make_db_mock() -> AsyncMock:
    db = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.refresh = AsyncMock()
    return db


class AdminServiceReportTest(IsolatedAsyncioTestCase):
    """관리자 신고 처리 Service 테스트."""

    async def test_get_report_detail_returns_report(self) -> None:
        """신고가 존재하면 조회된 신고를 반환해야 합니다."""

        db = make_db_mock()
        report = SimpleNamespace(report_id=1)

        with patch(
            "backend.app.admin.service.repository.get_report_by_id",
            new=AsyncMock(return_value=report),
        ) as get_report_by_id:
            result = await service.get_report_detail(
                db=db,
                report_id=1,
            )

        self.assertIs(result, report)
        get_report_by_id.assert_awaited_once_with(
            db=db,
            report_id=1,
        )

    async def test_get_report_detail_raises_404_when_missing(self) -> None:
        """신고가 없으면 404 오류가 발생해야 합니다."""

        db = make_db_mock()

        with patch(
            "backend.app.admin.service.repository.get_report_by_id",
            new=AsyncMock(return_value=None),
        ):
            with self.assertRaises(HTTPException) as error:
                await service.get_report_detail(
                    db=db,
                    report_id=999,
                )

        self.assertEqual(error.exception.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(error.exception.detail, "신고 정보를 찾을 수 없습니다.")

    async def test_approve_report_with_post_deletion_commits(self) -> None:
        """게시글 삭제 승인이 성공하면 게시글 삭제와 신고 승인을 commit해야 합니다."""

        db = make_db_mock()
        report = SimpleNamespace(
            report_id=1,
            post_id=10,
            status=UserReportStatus.PENDING,
        )
        post = SimpleNamespace(post_id=10, user_id=20)
        updated_report = SimpleNamespace(
            report_id=1,
            status=UserReportStatus.APPROVED,
        )

        with (
            patch(
                "backend.app.admin.service.repository.get_report_by_id",
                new=AsyncMock(return_value=report),
            ),
            patch(
                "backend.app.admin.service.repository.get_post_by_id",
                new=AsyncMock(return_value=post),
            ),
            patch(
                "backend.app.admin.service.repository.delete_community_post",
                new=AsyncMock(),
            ) as delete_post,
            patch(
                "backend.app.admin.service.repository.update_report_review",
                new=AsyncMock(return_value=updated_report),
            ) as update_report,
        ):
            result = await service.approve_report_with_post_deletion(
                db=db,
                report_id=1,
                admin_id=100,
            )

        self.assertIs(result, updated_report)
        delete_post.assert_awaited_once_with(db=db, post=post)
        self.assertEqual(
            update_report.await_args.kwargs["status"],
            UserReportStatus.APPROVED,
        )
        self.assertEqual(update_report.await_args.kwargs["reviewed_by"], 100)
        db.commit.assert_awaited_once()
        db.refresh.assert_awaited_once_with(updated_report)
        db.rollback.assert_not_awaited()

    async def test_approve_report_rejects_non_pending_report(self) -> None:
        """이미 처리된 신고는 다시 승인할 수 없어야 합니다."""

        db = make_db_mock()
        report = SimpleNamespace(
            report_id=1,
            post_id=10,
            status=UserReportStatus.APPROVED,
        )

        with patch(
            "backend.app.admin.service.repository.get_report_by_id",
            new=AsyncMock(return_value=report),
        ):
            with self.assertRaises(HTTPException) as error:
                await service.approve_report_with_post_deletion(
                    db=db,
                    report_id=1,
                    admin_id=100,
                )

        self.assertEqual(error.exception.status_code, status.HTTP_409_CONFLICT)
        db.rollback.assert_awaited_once()
        db.commit.assert_not_awaited()

    async def test_approve_report_with_user_deactivation_commits(self) -> None:
        """신고 대상 사용자 비활성화와 신고 승인은 하나의 트랜잭션이어야 합니다."""

        db = make_db_mock()
        report = SimpleNamespace(
            report_id=1,
            post_id=10,
            status=UserReportStatus.PENDING,
        )
        post = SimpleNamespace(post_id=10, user_id=20)
        reported_user = SimpleNamespace(user_id=20, is_active=True)
        updated_report = SimpleNamespace(
            report_id=1,
            status=UserReportStatus.APPROVED,
        )

        with (
            patch(
                "backend.app.admin.service.repository.get_report_by_id",
                new=AsyncMock(return_value=report),
            ),
            patch(
                "backend.app.admin.service.repository.get_post_by_id",
                new=AsyncMock(return_value=post),
            ),
            patch(
                "backend.app.admin.service.repository.get_user_by_id",
                new=AsyncMock(return_value=reported_user),
            ),
            patch(
                "backend.app.admin.service.repository.update_user_active_status",
                new=AsyncMock(return_value=reported_user),
            ) as update_user,
            patch(
                "backend.app.admin.service.repository.update_report_review",
                new=AsyncMock(return_value=updated_report),
            ),
        ):
            result = await service.approve_report_with_user_deactivation(
                db=db,
                report_id=1,
                admin_id=100,
            )

        self.assertIs(result, updated_report)
        update_user.assert_awaited_once_with(
            db=db,
            user=reported_user,
            is_active=False,
        )
        db.commit.assert_awaited_once()
        db.rollback.assert_not_awaited()

    async def test_admin_cannot_deactivate_self_through_report(self) -> None:
        """관리자가 자신의 게시글 신고를 승인해 본인을 비활성화할 수 없어야 합니다."""

        db = make_db_mock()
        report = SimpleNamespace(
            report_id=1,
            post_id=10,
            status=UserReportStatus.PENDING,
        )
        post = SimpleNamespace(post_id=10, user_id=100)
        admin_user = SimpleNamespace(user_id=100, is_active=True)

        with (
            patch(
                "backend.app.admin.service.repository.get_report_by_id",
                new=AsyncMock(return_value=report),
            ),
            patch(
                "backend.app.admin.service.repository.get_post_by_id",
                new=AsyncMock(return_value=post),
            ),
            patch(
                "backend.app.admin.service.repository.get_user_by_id",
                new=AsyncMock(return_value=admin_user),
            ),
        ):
            with self.assertRaises(HTTPException) as error:
                await service.approve_report_with_user_deactivation(
                    db=db,
                    report_id=1,
                    admin_id=100,
                )

        self.assertEqual(error.exception.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(
            error.exception.detail,
            "관리자는 자신의 계정을 비활성화할 수 없습니다.",
        )
        db.rollback.assert_awaited_once()
        db.commit.assert_not_awaited()


class AdminServiceUserTest(IsolatedAsyncioTestCase):
    """관리자 사용자 관리 Service 테스트."""

    async def test_user_list_normalizes_blank_nickname(self) -> None:
        """공백뿐인 닉네임은 검색 조건 없이 Repository로 전달해야 합니다."""

        db = make_db_mock()

        with patch(
            "backend.app.admin.service.repository.get_users",
            new=AsyncMock(return_value=[]),
        ) as get_users:
            result = await service.get_admin_user_list(
                db=db,
                nickname="   ",
                is_active=None,
            )

        self.assertEqual(result, [])
        self.assertIsNone(get_users.await_args.kwargs["nickname"])

    async def test_update_user_active_status_commits(self) -> None:
        """사용자 상태가 실제로 변경되면 commit해야 합니다."""

        db = make_db_mock()
        user = SimpleNamespace(user_id=20, is_active=True)
        updated_user = SimpleNamespace(user_id=20, is_active=False)

        with (
            patch(
                "backend.app.admin.service.repository.get_user_by_id",
                new=AsyncMock(return_value=user),
            ),
            patch(
                "backend.app.admin.service.repository.update_user_active_status",
                new=AsyncMock(return_value=updated_user),
            ) as update_status,
        ):
            result = await service.update_admin_user_active_status(
                db=db,
                user_id=20,
                is_active=False,
                current_admin_id=100,
            )

        self.assertIs(result, updated_user)
        update_status.assert_awaited_once_with(
            db=db,
            user=user,
            is_active=False,
        )
        db.commit.assert_awaited_once()
        db.refresh.assert_awaited_once_with(updated_user)

    async def test_update_user_rejects_same_status(self) -> None:
        """현재 상태와 같은 값으로 중복 변경하면 409 오류가 발생해야 합니다."""

        db = make_db_mock()
        user = SimpleNamespace(user_id=20, is_active=True)

        with patch(
            "backend.app.admin.service.repository.get_user_by_id",
            new=AsyncMock(return_value=user),
        ):
            with self.assertRaises(HTTPException) as error:
                await service.update_admin_user_active_status(
                    db=db,
                    user_id=20,
                    is_active=True,
                    current_admin_id=100,
                )

        self.assertEqual(error.exception.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(error.exception.detail, "이미 활성 상태인 사용자입니다.")
        db.rollback.assert_awaited_once()
        db.commit.assert_not_awaited()


class AdminDashboardServiceTest(IsolatedAsyncioTestCase):
    """관리자 대시보드 Service 테스트."""

    async def test_dashboard_summary_returns_all_counts(self) -> None:
        """오늘의 요약에 필요한 다섯 가지 수치를 반환해야 합니다."""

        db = make_db_mock()

        with (
            patch(
                "backend.app.admin.service.repository.count_users",
                new=AsyncMock(return_value=10),
            ),
            patch(
                "backend.app.admin.service.repository.count_users_by_active_status",
                new=AsyncMock(side_effect=[8, 2]),
            ),
            patch(
                "backend.app.admin.service.repository.count_reports_by_status",
                new=AsyncMock(return_value=3),
            ),
            patch(
                "backend.app.admin.service.repository.get_daily_access_counts",
                new=AsyncMock(return_value=[(date.today(), 5)]),
            ),
        ):
            result = await service.get_admin_dashboard_summary(db=db)

        self.assertEqual(
            result,
            {
                "total_user_count": 10,
                "active_user_count": 8,
                "inactive_user_count": 2,
                "today_access_user_count": 5,
                "pending_report_count": 3,
            },
        )

    async def test_dashboard_alerts_returns_normal_when_no_alerts(self) -> None:
        """확인할 항목이 없으면 정상 상태 알림 한 건을 반환해야 합니다."""

        db = make_db_mock()

        with (
            patch(
                "backend.app.admin.service.repository.count_reports_by_status",
                new=AsyncMock(side_effect=[0, 0]),
            ),
            patch(
                "backend.app.admin.service.repository.count_users_by_active_status",
                new=AsyncMock(return_value=0),
            ),
        ):
            result = await service.get_admin_dashboard_alerts(db=db)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["type"], "normal")
        self.assertEqual(result[0]["level"], "success")
        self.assertEqual(result[0]["count"], 0)

    async def test_dashboard_alerts_returns_multiple_alerts(self) -> None:
        """처리할 항목이 여러 종류이면 알림을 모두 반환해야 합니다."""

        db = make_db_mock()

        with (
            patch(
                "backend.app.admin.service.repository.count_reports_by_status",
                new=AsyncMock(side_effect=[2, 1]),
            ),
            patch(
                "backend.app.admin.service.repository.count_users_by_active_status",
                new=AsyncMock(return_value=4),
            ),
        ):
            result = await service.get_admin_dashboard_alerts(db=db)

        self.assertEqual(
            [alert["type"] for alert in result],
            ["pending_report", "expired_report", "inactive_user"],
        )

    async def test_activity_trend_fills_missing_dates_with_zero(self) -> None:
        """접속 기록이 없는 날짜도 0명으로 채워 항상 7일을 반환해야 합니다."""

        db = make_db_mock()
        today = service.datetime.now(service.KST).date()
        start_date = today - timedelta(days=6)
        recorded_date = start_date + timedelta(days=2)

        with patch(
            "backend.app.admin.service.repository.get_daily_access_counts",
            new=AsyncMock(return_value=[(recorded_date, 7)]),
        ):
            result = await service.get_admin_dashboard_activity_trend(db=db)

        self.assertEqual(len(result), 7)
        self.assertEqual(result[0]["access_date"], start_date)
        self.assertEqual(result[-1]["access_date"], today)
        self.assertEqual(result[2]["user_count"], 7)
        self.assertEqual(
            sum(item["user_count"] for item in result),
            7,
        )

    async def test_expire_pending_reports_commits(self) -> None:
        """만료 처리 성공 시 변경 건수를 반환하고 commit해야 합니다."""

        db = make_db_mock()

        with patch(
            "backend.app.admin.service.repository.update_expired_reports",
            new=AsyncMock(return_value=3),
        ):
            result = await service.expire_pending_reports(db=db)

        self.assertEqual(result, 3)
        db.commit.assert_awaited_once()
        db.rollback.assert_not_awaited()

    async def test_expire_pending_reports_rolls_back_on_error(self) -> None:
        """만료 처리 중 예외가 발생하면 rollback하고 500 오류로 변환해야 합니다."""

        db = make_db_mock()

        with patch(
            "backend.app.admin.service.repository.update_expired_reports",
            new=AsyncMock(side_effect=RuntimeError("database error")),
        ):
            with self.assertRaises(HTTPException) as error:
                await service.expire_pending_reports(db=db)

        self.assertEqual(
            error.exception.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
        db.rollback.assert_awaited_once()
        db.commit.assert_not_awaited()


class AdminDependencyTest(IsolatedAsyncioTestCase):
    """관리자 권한 Dependency 테스트."""

    async def test_active_admin_is_allowed(self) -> None:
        """활성 ADMIN 사용자는 관리자 API에 접근할 수 있어야 합니다."""

        admin = SimpleNamespace(
            user_id=1,
            is_active=True,
            role=UserRole.ADMIN,
        )

        result = await get_current_admin(current_user=admin)

        self.assertIs(result, admin)

    async def test_inactive_admin_is_rejected(self) -> None:
        """비활성 관리자는 403 오류가 발생해야 합니다."""

        admin = SimpleNamespace(
            user_id=1,
            is_active=False,
            role=UserRole.ADMIN,
        )

        with self.assertRaises(HTTPException) as error:
            await get_current_admin(current_user=admin)

        self.assertEqual(error.exception.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(error.exception.detail, "비활성 계정입니다.")

    async def test_normal_user_is_rejected(self) -> None:
        """ADMIN 권한이 없는 사용자는 403 오류가 발생해야 합니다."""

        user = SimpleNamespace(
            user_id=2,
            is_active=True,
            role="USER",
        )

        with self.assertRaises(HTTPException) as error:
            await get_current_admin(current_user=user)

        self.assertEqual(error.exception.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(error.exception.detail, "관리자 권한이 필요합니다.")
