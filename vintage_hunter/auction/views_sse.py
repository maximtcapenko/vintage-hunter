import asyncio
import json
import logging

from django.http import HttpResponseForbidden, StreamingHttpResponse
from commons.redis import get_async_redis_client

logger = logging.getLogger(__name__)


async def event_stream(auction_id, user_id):
    redis = get_async_redis_client()
    pubsub = redis.pubsub()
    
    channels = [
        'auction_global',
        f'auction:{auction_id}',
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
        logger.info("SSE connection cancelled.")
    finally:
        await pubsub.unsubscribe(*channels)
        await pubsub.aclose()

async def stream_events(request, auction_id):
    user = await request.auser()

    if not user.is_authenticated:
        return HttpResponseForbidden("Authentication required.")

    response = StreamingHttpResponse(
        event_stream(auction_id, user.id),
        content_type='text/event-stream'
    )
    response['Cache-Control'] = 'no-cache'
    response['Connection'] = 'keep-alive'
    return response
