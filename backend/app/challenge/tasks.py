from __future__ import annotations

# =========================================================
# [반드시 확인 및 검토할 사항]
#
# 1. Celery Task는 FastAPI 요청 밖에서 실행됩니다.
#    - Depends(get_db)를 사용할 수 없습니다.
#    - SessionLocal로 DB 세션을 직접 생성해야 합니다.
#
# 2. Task 내부에서는 commit(), rollback(), close()를 직접 처리합니다.
#    - common/database.py의 get_db()는 Router 요청에서만 동작합니다.
#
# 3. 만료 처리 비즈니스 로직은 새로 작성하지 않습니다.
#    - ChallengeTeamService.expire_pending_invites()를 재사용합니다.
#
# 4. 이 Task는 maintenance 큐에서 실행합니다.
#    - Worker 실행 시 반드시 `-Q maintenance`를 지정해야 합니다.
# =========================================================

import logging

from sqlalchemy.orm import Session

from backend.app.challenge.service import ChallengeTeamService
from backend.app.challenge.celery_app import celery_app
from backend.app.common.database import SessionLocal


# Task 실행 결과와 오류를 기록할 Logger를 생성.
logger = logging.getLogger(__name__)


# 만료 시간이 지난 PENDING 초대를 자동으로 EXPIRED 처리.
@celery_app.task(
    name="challenge.expire_pending_invites",

    # 이 Task가 maintenance 큐를 사용하도록 지정.
    queue="maintenance",
)
def expire_pending_invites_task() -> int:
    """
    만료 시간이 지난 Challenge 팀 초대를 일괄 만료 처리합니다.

    Returns:
        이번 실행에서 EXPIRED 상태로 변경된 초대 개수
    """

    # Celery Task는 FastAPI Dependency를 사용할 수 없으므로 DB 세션을 직접 생성합니다.
    session: Session = SessionLocal()

    try:
        # 기존 Service의 초대 만료 기능을 재사용.
        expired_count = (
            ChallengeTeamService.expire_pending_invites(
                session,
            )
        )

        session.commit()

        logger.info(
            "Challenge 팀 초대 자동 만료 처리 완료: %s건",
            expired_count,
        )

        return expired_count

    except Exception:
        session.rollback()

        logger.exception(
            "Challenge 팀 초대 자동 만료 처리 중 오류가 발생했습니다."
        )

        raise

    finally:
        session.close()