from datetime import datetime, timedelta, timezone
import redis
from backend.app.common.config import get_setting

KST = timezone(timedelta(hours=9))

_client = redis.Redis.from_url(
    get_setting().REDIS_URL, socket_connect_timeout=1, socket_timeout=1
)

def _next_kst_midnight() -> datetime:
    """다음 한국 자정. 카운터는 이때 저절로 사라진다."""
    now = datetime.now(KST)
    return (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

def count_daily_use(name: str, user_id: int, limit: int) -> bool:
    """오늘 사용 횟수를 1 늘리고, 상한을 넘지 않았으면 True."""
    today = datetime.now(KST).strftime("%Y-%m-%d")
    key = f"{name}:{user_id}:{today}"
    try:
        used = _client.incr(key)
        if used == 1:
            _client.expireat(key, _next_kst_midnight())
        return used <= limit
    except redis.RedisError as error:

        print(f"[rate_limit] Redis 접근 실패, 제한 없이 통과: {key} "
              f"{type(error).__name__}: {error}")
        return True