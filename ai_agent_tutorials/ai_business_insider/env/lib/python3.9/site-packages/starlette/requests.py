from __future__ import annotations

import json
import typing
from http import cookies as http_cookies

import anyio

from starlette._utils import AwaitableOrContextManager, AwaitableOrContextManagerWrapper
from starlette.datastructures import URL, Address, FormData, Headers, QueryParams, State
from starlette.exceptions import HTTPException
from starlette.formparsers import FormParser, MultiPartException, MultiPartParser
from starlette.types import Message, Receive, Scope, Send

if typing.TYPE_CHECKING:
    from multipart.multipart import parse_options_header

    from starlette.applications import Starlette
    from starlette.routing import Router
else:
    try:
        try:
            from python_multipart.multipart import parse_options_header
        except ModuleNotFoundError:  # pragma: no cover
            from multipart.multipart import parse_options_header
    except ModuleNotFoundError:  # pragma: no cover
        parse_options_header = None


SERVER_PUSH_HEADERS_TO_COPY = {
    "accept",
    "accept-encoding",
    "accept-language",
    "cache-control",
    "user-agent",
}


def cookie_parser(cookie_string: str) -> dict[str, str]:
    """
    This function parses a ``Cookie`` HTTP header into a dict of key/value pairs.

    It attempts to mimic browser cookie parsing behavior: browsers and web servers
    frequently disregard the spec (RFC 6265) when setting and reading cookies,
    so we attempt to suit the common scenarios here.

    This function has been adapted from Django 3.1.0.
    Note: we are explicitly _NOT_ using `SimpleCookie.load` because it is based
    on an outdated spec and will fail on lots of input we want to support
    """
    cookie_dict: dict[str, str] = {}
    for chunk in cookie_string.split(";"):
        if "=" in chunk:
            key, val = chunk.split("=", 1)
        else:
            # Assume an empty name per
            # https://bugzilla.mozilla.org/show_bug.cgi?id=169091
            key, val = "", chunk
        key, val = key.strip(), val.strip()
        if key or val:
            # unquote using Python's algorithm.
            cookie_dict[key] = http_cookies._unquote(val)
    return cookie_dict


class ClientDisconnect(Exception):
    pass


class HTTPConnection(typing.Mapping[str, typing.Any]):
    """
    A base class for incoming HTTP connections, that is used to provide
    any functionality that is common to both `Request` and `WebSocket`.
    """

    def __init__(self, scope: Scope, receive: Receive | None = None) -> None:
        assert scope["type"] in ("http", "websocket")
        self.scope = scope

    def __getitem__(self, key: str) -> typing.Any:
        return self.scope[key]

    def __iter__(self) -> typing.Iterator[str]:
        return iter(self.scope)

    def __len__(self) -> int:
        return len(self.scope)

    # Don't use the `abc.Mapping.__eq__` implementation.
    # Connection instances should never be considered equal
    # unless `self is other`.
    __eq__ = object.__eq__
    __hash__ = object.__hash__

    @property
    def app(self) -> typing.Any:
        return self.scope["app"]

    @property
    def url(self) -> URL:
        if not hasattr(self, "_url"):  # pragma: no branch
            self._url = URL(scope=self.scope)
        return self._url

    @property
    def base_url(self) -> URL:
        if not hasattr(self, "_base_url"):
            base_url_scope = dict(self.scope)
            # This is used by request.url_for, it might be used inside a Mount which
            # would have its own child scope with its own root_path, but the base URL
            # for url_for should still be the top level app root path.
            app_root_path = base_url_scope.get("app_root_path", base_url_scope.get("root_path", ""))
            path = app_root_path
            if not path.endswith("/"):
                path += "/"
            base_url_scope["path"] = path
            base_url_scope["query_string"] = b""
            base_url_scope["root_path"] = app_root_path
            self._base_url = URL(scope=base_url_scope)
        return self._base_url

    @property
    def headers(self) -> Headers:
        if not hasattr(self, "_headers"):
            self._headers = Headers(scope=self.scope)
        return self._headers

    @property
    def query_params(self) -> QueryParams:
        if not hasattr(self, "_query_params"):  # pragma: no branch
            self._query_params = QueryParams(self.scope["query_string"])
        return self._query_params

    @property
    def path_params(self) -> dict[str, typing.Any]:
        return self.scope.get("path_params", {})

    @property
    def cookies(self) -> dict[str, str]:
        if not hasattr(self, "_cookies"):
            cookies: dict[str, str] = {}
            cookie_header = self.headers.get("cookie")

            if cookie_header:
                cookies = cookie_parser(cookie_header)
            self._cookies = cookies
        return self._cookies

    @property
    def client(self) -> Address | None:
        # client is a 2 item tuple of (host, port), None if missing
        host_port = self.scope.get("client")
        if host_port is not None:
            return Address(*host_port)
        return None

    @property
    def session(self) -> dict[str, typing.Any]:
        assert "session" in self.scope, "SessionMiddleware must be installed to access request.session"
        return self.scope["session"]  # type: ignore[no-any-return]

    @property
    def auth(self) -> typing.Any:
        assert "auth" in self.scope, "AuthenticationMiddleware must be installed to access request.auth"
        return self.scope["auth"]

    @property
    def user(self) -> typing.Any:
        assert "user" in self.scope, "AuthenticationMiddleware must be installed to access request.user"
        return self.scope["user"]

    @property
    def state(self) -> State:
        if not hasattr(self, "_state"):
            # Ensure 'state' has an empty dict if it's not already populated.
            self.scope.setdefault("state", {})
            # Create a state instance with a reference to the dict in which it should
            # store info
            self._state = State(self.scope["state"])
        return self._state

    def url_for(self, name: str, /, **path_params: typing.Any) -> URL:
        url_path_provider: Router | Starlette | None = self.scope.get("router") or self.scope.get("app")
        if url_path_provider is None:
            raise RuntimeError("The `url_for` method can only be used inside a Starlette application or with a router.")
        url_path = url_path_provider.url_path_for(name, **path_params)
        return url_path.make_absolute_url(base_url=self.base_url)


async def empty_receive() -> typing.NoReturn:
    raise RuntimeError("Receive channel has not been made available")


async def empty_send(message: Message) -> typing.NoReturn:
    raise RuntimeError("Send channel has not been made available")


class Request(HTTPConnection):
    _form: FormData | None

    def __init__(self, scope: Scope, receive: Receive = empty_receive, send: Send = empty_send):
        super().__init__(scope)
        assert scope["type"] == "http"
        self._receive = receive
        self._send = send
        self._stream_consumed = False
        self._is_disconnected = False
        self._form = None

    @property
    def method(self) -> str:
        return typing.cast(str, self.scope["method"])

    @property
    def receive(self) -> Receive:
        return self._receive

    async def stream(self) -> typing.AsyncGenerator[bytes, None]:
        if hasattr(self, "_body"):
            yield self._body
            yield b""
            return
        if self._stream_consumed:
            raise RuntimeError("Stream consumed")
        while not self._stream_consumed:
            message = await self._receive()
            if message["type"] == "http.request":
                body = message.get("body", b"")
                if not message.get("more_body", False):
                    self._stream_consumed = True
                if body:
                    yield body
            elif message["type"] == "http.disconnect":
                self._is_disconnected = True
                raise ClientDisconnect()
        yield b""

    async def body(self) -> bytes:
        if not hasattr(self, "_body"):
            chunks: list[bytes] = []
            async for chunk in self.stream():
                chunks.append(chunk)
            self._body = b"".join(chunks)
        return self._body

    async def json(self) -> typing.Any:
        if not hasattr(self, "_json"):  # pragma: no branch
            body = await self.body()
            self._json = json.loads(body)
        return self._json

    async def _get_form(self, *, max_files: int | float = 1000, max_fields: int | float = 1000) -> FormData:
        if self._form is None:
            assert (
                parse_options_header is not None
            ), "The `python-multipart` library must be installed to use form parsing."
            content_type_header = self.headers.get("Content-Type")
            content_type: bytes
            content_type, _ = parse_options_header(content_type_header)
            if content_type == b"multipart/form-data":
                try:
                    multipart_parser = MultiPartParser(
                        self.headers,
                        self.stream(),
                        max_files=max_files,
                        max_fields=max_fields,
                    )
                    self._form = await multipart_parser.parse()
                except MultiPartException as exc:
                    if "app" in self.scope:
                        raise HTTPException(status_code=400, detail=exc.message)
                    raise exc
            elif content_type == b"application/x-www-form-urlencoded":
                form_parser = FormParser(self.headers, self.stream())
                self._form = await form_parser.parse()
            else:
                self._form = FormData()
        return self._form

    def form(
        self, *, max_files: int | float = 1000, max_fields: int | float = 1000
    ) -> AwaitableOrContextManager[FormData]:
        return AwaitableOrContextManagerWrapper(self._get_form(max_files=max_files, max_fields=max_fields))

    async def close(self) -> None:
        if self._form is not None:  # pragma: no branch
            await self._form.close()

    async def is_disconnected(self) -> bool:
        if not self._is_disconnected:
            message: Message = {}

            # If message isn't immediately available, move on
            with anyio.CancelScope() as cs:
                cs.cancel()
                message = await self._receive()

            if message.get("type") == "http.disconnect":
                self._is_disconnected = True

        return self._is_disconnected

    async def send_push_promise(self, path: str) -> None:
        if "http.response.push" in self.scope.get("extensions", {}):
            raw_headers: list[tuple[bytes, bytes]] = []
            for name in SERVER_PUSH_HEADERS_TO_COPY:
                for value in self.headers.getlist(name):
                    raw_headers.append((name.encode("latin-1"), value.encode("latin-1")))
            await self._send({"type": "http.response.push", "path": path, "headers": raw_headers})
