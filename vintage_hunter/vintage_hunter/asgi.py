import os

import anyio
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vintage_hunter.settings')

_django_app = get_asgi_application()  # calls django.setup() — must come before mcp_tools import

from mcp_tools import mcp  # noqa: E402

_mcp_app = mcp.http_app(path='/mcp')


class _Router:
    async def __call__(self, scope, receive, send):
        if scope['type'] == 'lifespan':
            await self._lifespan(receive, send)
        elif scope['type'] in ('http', 'websocket') and scope.get('path', '').startswith('/mcp'):
            await _mcp_app(scope, receive, send)
        else:
            await _django_app(scope, receive, send)

    async def _lifespan(self, receive, send):
        shutdown = anyio.Event()

        async def run_mcp_lifespan():
            async with _mcp_app.lifespan(_mcp_app):
                await shutdown.wait()

        async with anyio.create_task_group() as tg:
            tg.start_soon(run_mcp_lifespan)
            await receive()  # lifespan.startup
            await send({'type': 'lifespan.startup.complete'})
            await receive()  # lifespan.shutdown
            shutdown.set()
            await send({'type': 'lifespan.shutdown.complete'})


application = _Router()
