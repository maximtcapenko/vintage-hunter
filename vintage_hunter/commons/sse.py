import json
import logging
import redis
from django.conf import settings

logger = logging.getLogger(__name__)


def broadcast_event(channel_name: str, event_type: str, data: dict):
    try:
        r = redis.from_url(settings.REDIS_URL)
        message = {
            'type': event_type,
            'data': data
        }
        r.publish(channel_name, json.dumps(message))
    except Exception as e:
        logger.error(f"Failed to broadcast event {event_type} to {channel_name}: {e}")

async def async_broadcast_event(channel_name: str, event_type: str, data: dict):
    from redis import asyncio as async_redis
    
    try:
        redis = await async_redis.from_url(settings.REDIS_URL)
        message = {
            'type': event_type,
            'data': data
        }
        await redis.publish(channel_name, json.dumps(message))
        await redis.aclose()
    except Exception as e:
        logger.error(f"Failed to async broadcast event {event_type} to {channel_name}: {e}")
