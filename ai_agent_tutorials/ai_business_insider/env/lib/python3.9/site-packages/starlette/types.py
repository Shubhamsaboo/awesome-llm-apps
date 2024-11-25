import typing

if typing.TYPE_CHECKING:
    from starlette.requests import Request
    from starlette.responses import Response
    from starlette.websockets import WebSocket

AppType = typing.TypeVar("AppType")

Scope = typing.MutableMapping[str, typing.Any]
Message = typing.MutableMapping[str, typing.Any]

Receive = typing.Callable[[], typing.Awaitable[Message]]
Send = typing.Callable[[Message], typing.Awaitable[None]]

ASGIApp = typing.Callable[[Scope, Receive, Send], typing.Awaitable[None]]

StatelessLifespan = typing.Callable[[AppType], typing.AsyncContextManager[None]]
StatefulLifespan = typing.Callable[[AppType], typing.AsyncContextManager[typing.Mapping[str, typing.Any]]]
Lifespan = typing.Union[StatelessLifespan[AppType], StatefulLifespan[AppType]]

HTTPExceptionHandler = typing.Callable[["Request", Exception], "Response | typing.Awaitable[Response]"]
WebSocketExceptionHandler = typing.Callable[["WebSocket", Exception], typing.Awaitable[None]]
ExceptionHandler = typing.Union[HTTPExceptionHandler, WebSocketExceptionHandler]
