"""
backend/app/common/datetime_utils.py

DB의 TIMESTAMP(timezone 없음) 컬럼은 서버(Postgres) 세션 타임존인 UTC 기준 값이
naive datetime으로 저장/조회된다. 이 값을 tzinfo 없이 그대로 API 응답으로 내려보내면
프론트(new Date(iso))가 로컬(KST) 시각으로 오해해서 9시간 오차가 생긴다.
API 응답에 노출하는 모든 DB datetime 필드는 이 함수로 UTC-aware로 변환해야 한다.
"""
from datetime import datetime, timezone


def to_utc_aware(dt: datetime) -> datetime:
    """naive datetime(DB에서 온 UTC 값)에 UTC tzinfo를 붙인다. 이미 timezone-aware면 그대로 반환."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt
