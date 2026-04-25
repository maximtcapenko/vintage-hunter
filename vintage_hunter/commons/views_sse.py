import asyncio
import json
import logging

from django.conf import settings
from django.http import HttpResponseForbidden, StreamingHttpResponse
from redis import asyncio as async_redis

logger = logging.getLogger(__name__)

async def user_event_stream(user_id):
    redis = await async_redis.from_url(settings.REDIS_URL)
    pubsub = redis.pubsub()
    
    channels = [
        f'user:{user_id}'
    ]
    await pubsub.subscribe(*channels)
    
    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=20)
            
            if message:
                data = json.loads(message['data'])
                yield f"event: {data.get('type', 'message')}\ndata: {json.dumps(data.get('data'))}\n\n"
            else:
                yield ":ping\n\n"
            
            await asyncio.sleep(0.1)
    except asyncio.CancelledError:
        logger.info(f"User SSE connection cancelled for user {user_id}")
    finally:
        await pubsub.unsubscribe(*channels)
        await redis.aclose()

async def stream_user_events(request):
    user = await request.auser()

    if not user.is_authenticated:
        return HttpResponseForbidden("Authentication required.")

    response = StreamingHttpResponse(
        user_event_stream(user.id),
        content_type='text/event-stream'
    )
    response['Cache-Control'] = 'no-cache'
    response['Connection'] = 'keep-alive'
    return response
