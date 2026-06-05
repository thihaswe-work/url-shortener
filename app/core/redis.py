import logging
from typing import Optional

import redis as redis_lib

from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

_client: Optional[redis_lib.Redis] = None


def get_redis() -> redis_lib.Redis:
    global _client
    if _client is None:
        _client = redis_lib.Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
            retry_on_timeout=False,
            health_check_interval=30,
        )
    return _client


def cache_get(key: str) -> Optional[str]:
    try:
        r = get_redis()
        return r.get(key)
    except Exception as e:
        logger.warning("Redis cache_get failed: %s", e)
        return None


def cache_setex(key: str, seconds: int, value: str) -> None:
    try:
        r = get_redis()
        r.setex(key, seconds, value)
    except Exception as e:
        logger.warning("Redis cache_setex failed: %s", e)


def close_redis() -> None:
    global _client
    if _client is not None:
        try:
            _client.close()
        except Exception:
            pass
        _client = None
