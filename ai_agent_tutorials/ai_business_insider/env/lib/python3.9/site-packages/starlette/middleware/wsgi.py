from __future__ import annotations

import io
import math
import sys
import typing
import warnings

import anyio
from anyio.abc import ObjectReceiveStream, ObjectSendStream

from starlette.types import Receive, Scope, Send

warnings.warn(
    "starlette.middleware.wsgi is deprecated and will be removed in a future release. "
    "Please refer to https://github.com/abersheeran/a2wsgi as a replacement.",
    DeprecationWarning,
)


def build_environ(scope: Scope, body: bytes) -> dict[str, typing.Any]:
    """
    Builds a scope and request body into a WSGI environ object.
    """

    script_name = scope.get("root_path", "").encode("utf8").decode("latin1")
    path_info = scope["path"].encode("utf8").decode("latin1")
    if path_info.startswith(script_name):
        path_info = path_info[len(script_name) :]

    environ = {
        "REQUEST_METHOD": scope["method"],
        "SCRIPT_NAME": script_name,
        "PATH_INFO": path_info,
        "QUERY_STRING": scope["query_string"].decode("ascii"),
        "SERVER_PROTOCOL": f"HTTP/{scope['http_version']}",
        "wsgi.version": (1, 0),
        "wsgi.url_scheme": scope.get("scheme", "http"),
        "wsgi.input": io.BytesIO(body),
        "wsgi.errors": sys.stdout,
        "wsgi.multithread": True,
        "wsgi.multiprocess": True,
        "wsgi.run_once": False,
    }

    # Get server name and port - required in WSGI, not in ASGI
    server = scope.get("server") or ("localhost", 80)
    environ["SERVER_NAME"] = server[0]
    environ["SERVER_PORT"] = server[1]

    # Get client IP address
    if scope.get("client"):
        environ["REMOTE_ADDR"] = scope["client"][0]

    # Go through headers and make them into environ entries
    for name, value in scope.get("headers", []):
        name = name.decode("latin1")
        if name == "content-length":
            corrected_name = "CONTENT_LENGTH"
        elif name == "content-type":
            corrected_name = "CONTENT_TYPE"
        else:
            corrected_name = f"HTTP_{name}".upper().replace("-", "_")
        # HTTPbis say only ASCII chars are allowed in headers, but we latin1 just in
        # case
        value = value.decode("latin1")
        if corrected_name in environ:
            value = environ[corrected_name] + "," + value
        environ[corrected_name] = value
    return environ


class WSGIMiddleware:
    def __init__(self, app: typing.Callable[..., typing.Any]) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        assert scope["type"] == "http"
        responder = WSGIResponder(self.app, scope)
        await responder(receive, send)


class WSGIResponder:
    stream_send: ObjectSendStream[typing.MutableMapping[str, typing.Any]]
    stream_receive: ObjectReceiveStream[typing.MutableMapping[str, typing.Any]]

    def __init__(self, app: typing.Callable[..., typing.Any], scope: Scope) -> None:
        self.app = app
        self.scope = scope
        self.status = None
        self.response_headers = None
        self.stream_send, self.stream_receive = anyio.create_memory_object_stream(math.inf)
        self.response_started = False
        self.exc_info: typing.Any = None

    async def __call__(self, receive: Receive, send: Send) -> None:
        body = b""
        more_body = True
        while more_body:
            message = await receive()
            body += message.get("body", b"")
            more_body = message.get("more_body", False)
        environ = build_environ(self.scope, body)

        async with anyio.create_task_group() as task_group:
            task_group.start_soon(self.sender, send)
            async with self.stream_send:
                await anyio.to_thread.run_sync(self.wsgi, environ, self.start_response)
        if self.exc_info is not None:
            raise self.exc_info[0].with_traceback(self.exc_info[1], self.exc_info[2])

    async def sender(self, send: Send) -> None:
        async with self.stream_receive:
            async for message in self.stream_receive:
                await send(message)

    def start_response(
        self,
        status: str,
        response_headers: list[tuple[str, str]],
        exc_info: typing.Any = None,
    ) -> None:
        self.exc_info = exc_info
        if not self.response_started:
            self.response_started = True
            status_code_string, _ = status.split(" ", 1)
            status_code = int(status_code_string)
            headers = [
                (name.strip().encode("ascii").lower(), value.strip().encode("ascii"))
                for name, value in response_headers
            ]
            anyio.from_thread.run(
                self.stream_send.send,
                {
                    "type": "http.response.start",
                    "status": status_code,
                    "headers": headers,
                },
            )

    def wsgi(
        self,
        environ: dict[str, typing.Any],
        start_response: typing.Callable[..., typing.Any],
    ) -> None:
        for chunk in self.app(environ, start_response):
            anyio.from_thread.run(
                self.stream_send.send,
                {"type": "http.response.body", "body": chunk, "more_body": True},
            )

        anyio.from_thread.run(self.stream_send.send, {"type": "http.response.body", "body": b""})
