from __future__ import annotations

import types
from abc import ABCMeta, abstractmethod
from collections.abc import AsyncGenerator, Callable, Coroutine, Iterable
from typing import Any, TypeVar

_T = TypeVar("_T")


class TestRunner(metaclass=ABCMeta):
    """
    Encapsulates a running event loop. Every call made through this object will use the
    same event loop.
    """

    def __enter__(self) -> TestRunner:
        return self

    @abstractmethod
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> bool | None: ...

    @abstractmethod
    def run_asyncgen_fixture(
        self,
        fixture_func: Callable[..., AsyncGenerator[_T, Any]],
        kwargs: dict[str, Any],
    ) -> Iterable[_T]:
        """
        Run an async generator fixture.

        :param fixture_func: the fixture function
        :param kwargs: keyword arguments to call the fixture function with
        :return: an iterator yielding the value yielded from the async generator
        """

    @abstractmethod
    def run_fixture(
        self,
        fixture_func: Callable[..., Coroutine[Any, Any, _T]],
        kwargs: dict[str, Any],
    ) -> _T:
        """
        Run an async fixture.

        :param fixture_func: the fixture function
        :param kwargs: keyword arguments to call the fixture function with
        :return: the return value of the fixture function
        """

    @abstractmethod
    def run_test(
        self, test_func: Callable[..., Coroutine[Any, Any, Any]], kwargs: dict[str, Any]
    ) -> None:
        """
        Run an async test function.

        :param test_func: the test function
        :param kwargs: keyword arguments to call the test function with
        """
