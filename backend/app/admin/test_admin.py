from __future__ import annotations

# =========================================================
# [검토 및 확인할 내용]
#
# 1. 이 테스트 파일은 동기 SQLAlchemy Session 구조를 기준으로 작성했습니다.
# 2. Repository 함수는 실제 DB 대신 Mock으로 대체하여 Service 로직만 검증합니다.
# 3. commit()/rollback()은 Admin Service가 직접 호출하지 않는 정책을 검증합니다.
# 4. 실행 위치는 프로젝트 루트이며, 다음 명령어로 실행할 수 있습니다.
#    python -m pytest backend/app/admin/test_admin.py -v
# =========================================================

from datetime import date
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

from fastapi import HTTPException, status

from backend.app.admin import service
from backend.app.admin.dependencies import get_current_admin
from backend.app.admin.enums import UserReportStatus
from backend.app.auth.enums import UserRole


# 테스트에서 공통으로 사용할 동기 DB Session Mock을 생성합니다.
def make_db_mock() -> Mock:
    db = Mock()
    db.commit = Mock()
    db.rollback = Mock()
    db.refresh = Mock()
    return db


class AdminServiceReportTest(TestCase):
    """관리자 신고 처리 Service 테스트."""

    def test_get_report_detail_returns_report(self) -> None:
        """신고가 존재하면 조회된 신고를 반환해야 합니다."""

        db = make_db_mock()
        report = SimpleNamespace(report_id=1)

        with patch(
            "backend.app.admin.service.repository.get_report_by_id",
            return_value=report,
        ) as get_report_by_id:
            result = service.get_report_detail(
                db=db,
                report_id=1,
            )

        self.assertIs(result, report)
        get_report_by_id.assert_called_once_with(
            db=db,
            report_id=1,
        )

    def test_get_report_detail_raises_404_when_missing(self) -> None:
        """신고가 없으면 404 오류가 발생해야 합니다."""

        db = make_db_mock()

        with patch(
            "backend.app.admin.service.repository.get_report_by_id",
            return_value=None,
        ):
            with self.assertRaises(HTTPException) as error:
                service.get_report_detail(
                    db=db,
                    report_id=999,
                )

        self.assertEqual(error.exception.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(error.exception.detail, "신고 정보를 찾을 수 없습니다.")

    def test_approve_report_with_post_deletion(self) -> None:
        """게시글 삭제 승인 시 게시글 삭제와 신고 승인 처리를 수행해야 합니다."""

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
                return_value=report,
            ),
            patch(
                "backend.app.admin.service.repository.get_post_by_id",
                return_value=post,
            ),
            patch(
                "backend.app.admin.service.repository.delete_community_post",
            ) as delete_post,
            patch(
                "backend.app.admin.service.repository.update_report_review",
                return_value=updated_report,
            ) as update_report,
        ):
            result = service.approve_report_with_post_deletion(
                db=db,
                report_id=1,
                admin_id=100,
            )

        self.assertIs(result, updated_report)
        delete_post.assert_called_once_with(db=db, post=post)
        self.assertEqual(
            update_report.call_args.kwargs["status"],
            UserReportStatus.APPROVED,
        )
        self.assertEqual(update_report.call_args.kwargs["reviewed_by"], 100)
        db.commit.assert_not_called()
        db.rollback.assert_not_called()

    def test_approve_report_rejects_non_pending_report(self) -> None:
        """이미 처리된 신고는 다시 승인할 수 없어야 합니다."""

        db = make_db_mock()
        report = SimpleNamespace(
            report_id=1,
            post_id=10,
            status=UserReportStatus.APPROVED,
        )

        with patch(
            "backend.app.admin.service.repository.get_report_by_id",
            return_value=report,
        ):
            with self.assertRaises(HTTPException) as error:
                service.approve_report_with_post_deletion(
                    db=db,
                    report_id=1,
                    admin_id=100,
                )

        self.assertEqual(error.exception.status_code, status.HTTP_409_CONFLICT)
        db.commit.assert_not_called()
        db.rollback.assert_not_called()

    def test_approve_report_with_user_deactivation(self) -> None:
        """신고 대상 사용자를 비활성화하고 신고를 승인해야 합니다."""

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
                return_value=report,
            ),
            patch(
                "backend.app.admin.service.repository.get_post_by_id",
                return_value=post,
            ),
            patch(
                "backend.app.admin.service.repository.get_user_by_id",
                return_value=reported_user,
            ),
            patch(
                "backend.app.admin.service.repository.update_user_active_status",
                return_value=reported_user,
            ) as update_user,
            patch(
                "backend.app.admin.service.repository.update_report_review",
                return_value=updated_report,
            ),
        ):
            result = service.approve_report_with_user_deactivation(
                db=db,
                report_id=1,
                admin_id=100,
            )

        self.assertIs(result, updated_report)
        update_user.assert_called_once_with(
            db=db,
            user=reported_user,
            is_active=False,
        )
        db.commit.assert_not_called()
        db.rollback.assert_not_called()

    def test_admin_cannot_deactivate_self_through_report(self) -> None:
        """관리자는 신고 처리를 통해 자신의 계정을 비활성화할 수 없어야 합니다."""

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
                return_value=report,
            ),
            patch(
                "backend.app.admin.service.repository.get_post_by_id",
                return_value=post,
            ),
            patch(
                "backend.app.admin.service.repository.get_user_by_id",
                return_value=admin_user,
            ),
        ):
            with self.assertRaises(HTTPException) as error:
                service.approve_report_with_user_deactivation(
                    db=db,
                    report_id=1,
                    admin_id=100,
                )

        self.assertEqual(error.exception.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(
            error.exception.detail,
            "관리자는 자신의 계정을 비활성화할 수 없습니다.",
        )
        db.commit.assert_not_called()
        db.rollback.assert_not_called()


class AdminServiceUserTest(TestCase):
    """관리자 사용자 관리 Service 테스트."""

    def test_user_list_normalizes_blank_nickname(self) -> None:
        """공백뿐인 닉네임 검색어는 None으로 변환해야 합니다."""

        db = make_db_mock()

        with patch(
            "backend.app.admin.service.repository.get_users",
            return_value=[],
        ) as get_users:
            result = service.get_admin_user_list(
                db=db,
                nickname="   ",
            )

        self.assertEqual(result, [])
        self.assertIsNone(get_users.call_args.kwargs["nickname"])

    def test_update_user_active_status(self) -> None:
        """사용자의 활성 상태를 변경해야 합니다."""

        db = make_db_mock()
        user = SimpleNamespace(user_id=20, is_active=True)
        updated_user = SimpleNamespace(user_id=20, is_active=False)

        with (
            patch(
                "backend.app.admin.service.repository.get_user_by_id",
                return_value=user,
            ),
            patch(
                "backend.app.admin.service.repository.update_user_active_status",
                return_value=updated_user,
            ) as update_user,
        ):
            result = service.update_admin_user_active_status(
                db=db,
                user_id=20,
                is_active=False,
                current_admin_id=100,
            )

        self.assertIs(result, updated_user)
        update_user.assert_called_once_with(
            db=db,
            user=user,
            is_active=False,
        )
        db.commit.assert_not_called()
        db.rollback.assert_not_called()

    def test_update_user_rejects_same_status(self) -> None:
        """현재 상태와 동일한 상태로는 변경할 수 없어야 합니다."""

        db = make_db_mock()
        user = SimpleNamespace(user_id=20, is_active=True)

        with patch(
            "backend.app.admin.service.repository.get_user_by_id",
            return_value=user,
        ):
            with self.assertRaises(HTTPException) as error:
                service.update_admin_user_active_status(
                    db=db,
                    user_id=20,
                    is_active=True,
                    current_admin_id=100,
                )

        self.assertEqual(error.exception.status_code, status.HTTP_409_CONFLICT)


class AdminDashboardServiceTest(TestCase):
    """관리자 대시보드 Service 테스트."""

    def test_dashboard_summary_returns_all_counts(self) -> None:
        """오늘의 요약에 필요한 모든 수치를 반환해야 합니다."""

        db = make_db_mock()

        with (
            patch(
                "backend.app.admin.service.repository.count_users",
                return_value=10,
            ),
            patch(
                "backend.app.admin.service.repository.count_users_by_active_status",
                side_effect=[8, 2],
            ),
            patch(
                "backend.app.admin.service.repository.count_reports_by_status",
                return_value=3,
            ),
            patch(
                "backend.app.admin.service.repository.get_daily_access_counts",
                return_value=[(date.today(), 5)],
            ),
        ):
            result = service.get_admin_dashboard_summary(db=db)

        self.assertEqual(result["total_user_count"], 10)
        self.assertEqual(result["active_user_count"], 8)
        self.assertEqual(result["inactive_user_count"], 2)
        self.assertEqual(result["today_access_user_count"], 5)
        self.assertEqual(result["pending_report_count"], 3)

    def test_dashboard_alerts_returns_normal_when_no_alerts(self) -> None:
        """확인할 항목이 없으면 정상 상태 알림을 반환해야 합니다."""

        db = make_db_mock()

        with (
            patch(
                "backend.app.admin.service.repository.count_reports_by_status",
                side_effect=[0, 0],
            ),
            patch(
                "backend.app.admin.service.repository.count_users_by_active_status",
                return_value=0,
            ),
        ):
            result = service.get_admin_dashboard_alerts(db=db)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["type"], "normal")
        self.assertEqual(result[0]["count"], 0)

    def test_activity_trend_fills_missing_dates_with_zero(self) -> None:
        """접속 기록이 없는 날짜도 0명으로 포함하여 7일을 반환해야 합니다."""

        db = make_db_mock()
        recorded_date = date.today()

        with patch(
            "backend.app.admin.service.repository.get_daily_access_counts",
            return_value=[(recorded_date, 7)],
        ):
            result = service.get_admin_dashboard_activity_trend(db=db)

        self.assertEqual(len(result), 7)
        self.assertEqual(result[-1]["user_count"], 7)
        self.assertTrue(
            all(item["user_count"] == 0 for item in result[:-1])
        )

    def test_expire_pending_reports_does_not_commit_in_service(self) -> None:
        """자동 만료 Service도 commit/rollback을 직접 호출하지 않아야 합니다."""

        db = make_db_mock()

        with patch(
            "backend.app.admin.service.repository.update_expired_reports",
            return_value=3,
        ):
            result = service.expire_pending_reports(db=db)

        self.assertEqual(result, 3)
        db.commit.assert_not_called()
        db.rollback.assert_not_called()

    def test_expire_pending_reports_wraps_unexpected_error(self) -> None:
        """Repository 오류는 500 HTTPException으로 변환해야 합니다."""

        db = make_db_mock()

        with patch(
            "backend.app.admin.service.repository.update_expired_reports",
            side_effect=RuntimeError("database error"),
        ):
            with self.assertRaises(HTTPException) as error:
                service.expire_pending_reports(db=db)

        self.assertEqual(
            error.exception.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
        db.commit.assert_not_called()
        db.rollback.assert_not_called()


class AdminDependencyTest(TestCase):
    """관리자 권한 Dependency 테스트."""

    def test_active_admin_is_allowed(self) -> None:
        """활성 상태의 관리자는 Admin API에 접근할 수 있어야 합니다."""

        admin = SimpleNamespace(
            user_id=1,
            is_active=True,
            role=UserRole.ADMIN,
        )

        result = get_current_admin(current_user=admin)

        self.assertIs(result, admin)

    def test_inactive_admin_is_rejected(self) -> None:
        """비활성 관리자는 접근할 수 없어야 합니다."""

        admin = SimpleNamespace(
            user_id=1,
            is_active=False,
            role=UserRole.ADMIN,
        )

        with self.assertRaises(HTTPException) as error:
            get_current_admin(current_user=admin)

        self.assertEqual(error.exception.status_code, status.HTTP_403_FORBIDDEN)

    def test_normal_user_is_rejected(self) -> None:
        """일반 사용자는 Admin API에 접근할 수 없어야 합니다."""

        user = SimpleNamespace(
            user_id=2,
            is_active=True,
            role=UserRole.USER,
        )

        with self.assertRaises(HTTPException) as error:
            get_current_admin(current_user=user)

        self.assertEqual(error.exception.status_code, status.HTTP_403_FORBIDDEN)
