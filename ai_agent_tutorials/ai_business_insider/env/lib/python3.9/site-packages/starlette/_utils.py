from __future__ import annotations

import asyncio
import functools
import sys
import typing
from contextlib import contextmanager

from starlette.types import Scope

if sys.version_info >= (3, 10):  # pragma: no cover
    from typing import TypeGuard
else:  # pragma: no cover
    from typing_extensions import TypeGuard

has_exceptiongroups = True
if sys.version_info < (3, 11):  # pragma: no cover
    try:
        from exceptiongroup import BaseExceptionGroup
    except ImportError:
        has_exceptiongroups = False

T = typing.TypeVar("T")
AwaitableCallable = typing.Callable[..., typing.Awaitable[T]]


@typing.overload
def is_async_callable(obj: AwaitableCallable[T]) -> TypeGuard[AwaitableCallable[T]]: ...


@typing.overload
def is_async_callable(obj: typing.Any) -> TypeGuard[AwaitableCallable[typing.Any]]: ...


def is_async_callable(obj: typing.Any) -> typing.Any:
    while isinstance(obj, functools.partial):
        obj = obj.func

    return asyncio.iscoroutinefunction(obj) or (callable(obj) and asyncio.iscoroutinefunction(obj.__call__))


T_co = typing.TypeVar("T_co", covariant=True)


class AwaitableOrContextManager(typing.Awaitable[T_co], typing.AsyncContextManager[T_co], typing.Protocol[T_co]): ...


class SupportsAsyncClose(typing.Protocol):
    async def close(self) -> None: ...  # pragma: no cover


SupportsAsyncCloseType = typing.TypeVar("SupportsAsyncCloseType", bound=SupportsAsyncClose, covariant=False)


class AwaitableOrContextManagerWrapper(typing.Generic[SupportsAsyncCloseType]):
    __slots__ = ("aw", "entered")

    def __init__(self, aw: typing.Awaitable[SupportsAsyncCloseType]) -> None:
        self.aw = aw

    def __await__(self) -> typing.Generator[typing.Any, None, SupportsAsyncCloseType]:
        return self.aw.__await__()

    async def __aenter__(self) -> SupportsAsyncCloseType:
        self.entered = await self.aw
        return self.entered

    async def __aexit__(self, *args: typing.Any) -> None | bool:
        await self.entered.close()
        return None


@contextmanager
def collapse_excgroups() -> typing.Generator[None, None, None]:
    try:
        yield
    except BaseException as exc:
        if has_exceptiongroups:
            while isinstance(exc, BaseExceptionGroup) and len(exc.exceptions) == 1:
                exc = exc.exceptions[0]  # pragma: no cover

        raise exc


def get_route_path(scope: Scope) -> str:
    path: str = scope["path"]
    root_path = scope.get("root_path", "")
    if not root_path:
        return path

    if not path.startswith(root_path):
        return path

    if path == root_path:
        return ""

    if path[len(root_path)] == "/":
        return path[len(root_path) :]

    return path
