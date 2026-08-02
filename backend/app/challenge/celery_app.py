from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from backend.app.common.config import get_setting

# Celery Worker에서도 SQLAlchemy 전체 모델을 등록합니다.
import backend.app.models_registry  # noqa: F401


# 캐싱된 프로젝트 설정 객체를 가져옵니다.
settings = get_setting()

celery_app = Celery(
    "gooddeedquest_challenge",

    # 작업 요청을 Redis 메시지 큐에 저장합니다.
    broker=settings.REDIS_URL,

    # 작업 실행 결과도 Redis에 저장합니다.
    backend=settings.REDIS_URL,

    # Worker가 인식해야 하는 Task 파일을 등록합니다.
    include=[
        "backend.app.challenge.tasks",
        "backend.app.quest_verification.tasks",
    ],
)


# Celery의 공통 실행 설정을 지정합니다.
celery_app.conf.update(
    # Task 인자와 결과를 JSON 형식으로 처리합니다.
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # 한국 시간대를 사용합니다.
    timezone="Asia/Seoul",
    enable_utc=True,

    # 기본 작업 큐를 maintenance로 지정합니다.
    task_default_queue="maintenance",

    # Challenge 초대 만료 작업을 maintenance 큐로 전달합니다.
    task_routes={
        "challenge.expire_pending_invites": {
            "queue": "maintenance",
        },
    },

    # Celery Beat 정기 작업을 등록합니다.
        beat_schedule={
        # 매시간 정각에 만료된 팀 초대를 처리합니다.
        "expire-pending-team-invites-every-hour": {
            "task": "challenge.expire_pending_invites",
            "schedule": crontab(minute=0),
            "options": {
                "queue": "maintenance",
            },
        },
        # 10분마다 보류(ON_HOLD) 제출을 다시 판정합니다.
        "retry-held-submissions-every-10min": {
            "task": "quest_verification.retry_held_submissions",
            "schedule": crontab(minute="*/10"),
            "options": {
                "queue": "maintenance",
            },
        },
    },
)