from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Any, Generic, Literal, TypeVar, overload
from weakref import WeakKeyDictionary

from ._core._eventloop import get_async_backend

T = TypeVar("T")
D = TypeVar("D")


async def checkpoint() -> None:
    """
    Check for cancellation and allow the scheduler to switch to another task.

    Equivalent to (but more efficient than)::

        await checkpoint_if_cancelled()
        await cancel_shielded_checkpoint()


    .. versionadded:: 3.0

    """
    await get_async_backend().checkpoint()


async def checkpoint_if_cancelled() -> None:
    """
    Enter a checkpoint if the enclosing cancel scope has been cancelled.

    This does not allow the scheduler to switch to a different task.

    .. versionadded:: 3.0

    """
    await get_async_backend().checkpoint_if_cancelled()


async def cancel_shielded_checkpoint() -> None:
    """
    Allow the scheduler to switch to another task but without checking for cancellation.

    Equivalent to (but potentially more efficient than)::

        with CancelScope(shield=True):
            await checkpoint()


    .. versionadded:: 3.0

    """
    await get_async_backend().cancel_shielded_checkpoint()


def current_token() -> object:
    """
    Return a backend specific token object that can be used to get back to the event
    loop.

    """
    return get_async_backend().current_token()


_run_vars: WeakKeyDictionary[Any, dict[str, Any]] = WeakKeyDictionary()
_token_wrappers: dict[Any, _TokenWrapper] = {}


@dataclass(frozen=True)
class _TokenWrapper:
    __slots__ = "_token", "__weakref__"
    _token: object


class _NoValueSet(enum.Enum):
    NO_VALUE_SET = enum.auto()


class RunvarToken(Generic[T]):
    __slots__ = "_var", "_value", "_redeemed"

    def __init__(self, var: RunVar[T], value: T | Literal[_NoValueSet.NO_VALUE_SET]):
        self._var = var
        self._value: T | Literal[_NoValueSet.NO_VALUE_SET] = value
        self._redeemed = False


class RunVar(Generic[T]):
    """
    Like a :class:`~contextvars.ContextVar`, except scoped to the running event loop.
    """

    __slots__ = "_name", "_default"

    NO_VALUE_SET: Literal[_NoValueSet.NO_VALUE_SET] = _NoValueSet.NO_VALUE_SET

    _token_wrappers: set[_TokenWrapper] = set()

    def __init__(
        self, name: str, default: T | Literal[_NoValueSet.NO_VALUE_SET] = NO_VALUE_SET
    ):
        self._name = name
        self._default = default

    @property
    def _current_vars(self) -> dict[str, T]:
        token = current_token()
        try:
            return _run_vars[token]
        except KeyError:
            run_vars = _run_vars[token] = {}
            return run_vars

    @overload
    def get(self, default: D) -> T | D: ...

    @overload
    def get(self) -> T: ...

    def get(
        self, default: D | Literal[_NoValueSet.NO_VALUE_SET] = NO_VALUE_SET
    ) -> T | D:
        try:
            return self._current_vars[self._name]
        except KeyError:
            if default is not RunVar.NO_VALUE_SET:
                return default
            elif self._default is not RunVar.NO_VALUE_SET:
                return self._default

        raise LookupError(
            f'Run variable "{self._name}" has no value and no default set'
        )

    def set(self, value: T) -> RunvarToken[T]:
        current_vars = self._current_vars
        token = RunvarToken(self, current_vars.get(self._name, RunVar.NO_VALUE_SET))
        current_vars[self._name] = value
        return token

    def reset(self, token: RunvarToken[T]) -> None:
        if token._var is not self:
            raise ValueError("This token does not belong to this RunVar")

        if token._redeemed:
            raise ValueError("This token has already been used")

        if token._value is _NoValueSet.NO_VALUE_SET:
            try:
                del self._current_vars[self._name]
            except KeyError:
                pass
        else:
            self._current_vars[self._name] = token._value

        token._redeemed = True

    def __repr__(self) -> str:
        return f"<RunVar name={self._name!r}>"
