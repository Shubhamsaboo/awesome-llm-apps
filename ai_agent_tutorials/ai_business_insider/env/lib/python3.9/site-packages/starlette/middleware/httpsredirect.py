from starlette.datastructures import URL
from starlette.responses import RedirectResponse
from starlette.types import ASGIApp, Receive, Scope, Send


class HTTPSRedirectMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] in ("http", "websocket") and scope["scheme"] in ("http", "ws"):
            url = URL(scope=scope)
            redirect_scheme = {"http": "https", "ws": "wss"}[url.scheme]
            netloc = url.hostname if url.port in (80, 443) else url.netloc
            url = url.replace(scheme=redirect_scheme, netloc=netloc)
            response = RedirectResponse(url, status_code=307)
            await response(scope, receive, send)
        else:
            await self.app(scope, receive, send)
