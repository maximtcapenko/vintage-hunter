import json
import logging

from .redis import get_sync_redis_client

logger = logging.getLogger(__name__)

def broadcast_event(channel_name: str, event_type: str, data: dict):
    try:
        redis = get_sync_redis_client()
        message = {
            'type': event_type,
            'data': data
        }
        redis.publish(channel_name, json.dumps(message))
    except Exception as e:
        logger.error(f"Failed to broadcast event {event_type} to {channel_name}: {e}")
