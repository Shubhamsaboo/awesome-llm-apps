from __future__ import annotations

import functools
import inspect
import sys
import typing
from urllib.parse import urlencode

if sys.version_info >= (3, 10):  # pragma: no cover
    from typing import ParamSpec
else:  # pragma: no cover
    from typing_extensions import ParamSpec

from starlette._utils import is_async_callable
from starlette.exceptions import HTTPException
from starlette.requests import HTTPConnection, Request
from starlette.responses import RedirectResponse
from starlette.websockets import WebSocket

_P = ParamSpec("_P")


def has_required_scope(conn: HTTPConnection, scopes: typing.Sequence[str]) -> bool:
    for scope in scopes:
        if scope not in conn.auth.scopes:
            return False
    return True


def requires(
    scopes: str | typing.Sequence[str],
    status_code: int = 403,
    redirect: str | None = None,
) -> typing.Callable[[typing.Callable[_P, typing.Any]], typing.Callable[_P, typing.Any]]:
    scopes_list = [scopes] if isinstance(scopes, str) else list(scopes)

    def decorator(
        func: typing.Callable[_P, typing.Any],
    ) -> typing.Callable[_P, typing.Any]:
        sig = inspect.signature(func)
        for idx, parameter in enumerate(sig.parameters.values()):
            if parameter.name == "request" or parameter.name == "websocket":
                type_ = parameter.name
                break
        else:
            raise Exception(f'No "request" or "websocket" argument on function "{func}"')

        if type_ == "websocket":
            # Handle websocket functions. (Always async)
            @functools.wraps(func)
            async def websocket_wrapper(*args: _P.args, **kwargs: _P.kwargs) -> None:
                websocket = kwargs.get("websocket", args[idx] if idx < len(args) else None)
                assert isinstance(websocket, WebSocket)

                if not has_required_scope(websocket, scopes_list):
                    await websocket.close()
                else:
                    await func(*args, **kwargs)

            return websocket_wrapper

        elif is_async_callable(func):
            # Handle async request/response functions.
            @functools.wraps(func)
            async def async_wrapper(*args: _P.args, **kwargs: _P.kwargs) -> typing.Any:
                request = kwargs.get("request", args[idx] if idx < len(args) else None)
                assert isinstance(request, Request)

                if not has_required_scope(request, scopes_list):
                    if redirect is not None:
                        orig_request_qparam = urlencode({"next": str(request.url)})
                        next_url = f"{request.url_for(redirect)}?{orig_request_qparam}"
                        return RedirectResponse(url=next_url, status_code=303)
                    raise HTTPException(status_code=status_code)
                return await func(*args, **kwargs)

            return async_wrapper

        else:
            # Handle sync request/response functions.
            @functools.wraps(func)
            def sync_wrapper(*args: _P.args, **kwargs: _P.kwargs) -> typing.Any:
                request = kwargs.get("request", args[idx] if idx < len(args) else None)
                assert isinstance(request, Request)

                if not has_required_scope(request, scopes_list):
                    if redirect is not None:
                        orig_request_qparam = urlencode({"next": str(request.url)})
                        next_url = f"{request.url_for(redirect)}?{orig_request_qparam}"
                        return RedirectResponse(url=next_url, status_code=303)
                    raise HTTPException(status_code=status_code)
                return func(*args, **kwargs)

            return sync_wrapper

    return decorator


class AuthenticationError(Exception):
    pass


class AuthenticationBackend:
    async def authenticate(self, conn: HTTPConnection) -> tuple[AuthCredentials, BaseUser] | None:
        raise NotImplementedError()  # pragma: no cover


class AuthCredentials:
    def __init__(self, scopes: typing.Sequence[str] | None = None):
        self.scopes = [] if scopes is None else list(scopes)


class BaseUser:
    @property
    def is_authenticated(self) -> bool:
        raise NotImplementedError()  # pragma: no cover

    @property
    def display_name(self) -> str:
        raise NotImplementedError()  # pragma: no cover

    @property
    def identity(self) -> str:
        raise NotImplementedError()  # pragma: no cover


class SimpleUser(BaseUser):
    def __init__(self, username: str) -> None:
        self.username = username

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def display_name(self) -> str:
        return self.username


class UnauthenticatedUser(BaseUser):
    @property
    def is_authenticated(self) -> bool:
        return False

    @property
    def display_name(self) -> str:
        return ""
