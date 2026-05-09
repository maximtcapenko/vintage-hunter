import redis
from redis import asyncio as async_redis
from django.conf import settings

_async_redis_client = None
_sync_redis_client = None

def get_async_redis_client():
    global _async_redis_client
    if _async_redis_client is None:
        _async_redis_client = async_redis.from_url(
            settings.REDIS_URL,
            decode_responses=True
        )
    return _async_redis_client

def get_sync_redis_client():
    global _sync_redis_client
    if _sync_redis_client is None:
        _sync_redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True
        )
    return _sync_redis_client
