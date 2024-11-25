from __future__ import annotations

import sys
from collections.abc import Generator, Iterator
from contextlib import ExitStack, contextmanager
from inspect import isasyncgenfunction, iscoroutinefunction, ismethod
from typing import Any, cast

import pytest
import sniffio
from _pytest.fixtures import SubRequest
from _pytest.outcomes import Exit

from ._core._eventloop import get_all_backends, get_async_backend
from ._core._exceptions import iterate_exceptions
from .abc import TestRunner

if sys.version_info < (3, 11):
    from exceptiongroup import ExceptionGroup

_current_runner: TestRunner | None = None
_runner_stack: ExitStack | None = None
_runner_leases = 0


def extract_backend_and_options(backend: object) -> tuple[str, dict[str, Any]]:
    if isinstance(backend, str):
        return backend, {}
    elif isinstance(backend, tuple) and len(backend) == 2:
        if isinstance(backend[0], str) and isinstance(backend[1], dict):
            return cast(tuple[str, dict[str, Any]], backend)

    raise TypeError("anyio_backend must be either a string or tuple of (string, dict)")


@contextmanager
def get_runner(
    backend_name: str, backend_options: dict[str, Any]
) -> Iterator[TestRunner]:
    global _current_runner, _runner_leases, _runner_stack
    if _current_runner is None:
        asynclib = get_async_backend(backend_name)
        _runner_stack = ExitStack()
        if sniffio.current_async_library_cvar.get(None) is None:
            # Since we're in control of the event loop, we can cache the name of the
            # async library
            token = sniffio.current_async_library_cvar.set(backend_name)
            _runner_stack.callback(sniffio.current_async_library_cvar.reset, token)

        backend_options = backend_options or {}
        _current_runner = _runner_stack.enter_context(
            asynclib.create_test_runner(backend_options)
        )

    _runner_leases += 1
    try:
        yield _current_runner
    finally:
        _runner_leases -= 1
        if not _runner_leases:
            assert _runner_stack is not None
            _runner_stack.close()
            _runner_stack = _current_runner = None


def pytest_configure(config: Any) -> None:
    config.addinivalue_line(
        "markers",
        "anyio: mark the (coroutine function) test to be run "
        "asynchronously via anyio.",
    )


@pytest.hookimpl(hookwrapper=True)
def pytest_fixture_setup(fixturedef: Any, request: Any) -> Generator[Any]:
    def wrapper(
        *args: Any, anyio_backend: Any, request: SubRequest, **kwargs: Any
    ) -> Any:
        # Rebind any fixture methods to the request instance
        if (
            request.instance
            and ismethod(func)
            and type(func.__self__) is type(request.instance)
        ):
            local_func = func.__func__.__get__(request.instance)
        else:
            local_func = func

        backend_name, backend_options = extract_backend_and_options(anyio_backend)
        if has_backend_arg:
            kwargs["anyio_backend"] = anyio_backend

        if has_request_arg:
            kwargs["request"] = request

        with get_runner(backend_name, backend_options) as runner:
            if isasyncgenfunction(local_func):
                yield from runner.run_asyncgen_fixture(local_func, kwargs)
            else:
                yield runner.run_fixture(local_func, kwargs)

    # Only apply this to coroutine functions and async generator functions in requests
    # that involve the anyio_backend fixture
    func = fixturedef.func
    if isasyncgenfunction(func) or iscoroutinefunction(func):
        if "anyio_backend" in request.fixturenames:
            fixturedef.func = wrapper
            original_argname = fixturedef.argnames

            if not (has_backend_arg := "anyio_backend" in fixturedef.argnames):
                fixturedef.argnames += ("anyio_backend",)

            if not (has_request_arg := "request" in fixturedef.argnames):
                fixturedef.argnames += ("request",)

            try:
                return (yield)
            finally:
                fixturedef.func = func
                fixturedef.argnames = original_argname

    return (yield)


@pytest.hookimpl(tryfirst=True)
def pytest_pycollect_makeitem(collector: Any, name: Any, obj: Any) -> None:
    if collector.istestfunction(obj, name):
        inner_func = obj.hypothesis.inner_test if hasattr(obj, "hypothesis") else obj
        if iscoroutinefunction(inner_func):
            marker = collector.get_closest_marker("anyio")
            own_markers = getattr(obj, "pytestmark", ())
            if marker or any(marker.name == "anyio" for marker in own_markers):
                pytest.mark.usefixtures("anyio_backend")(obj)


@pytest.hookimpl(tryfirst=True)
def pytest_pyfunc_call(pyfuncitem: Any) -> bool | None:
    def run_with_hypothesis(**kwargs: Any) -> None:
        with get_runner(backend_name, backend_options) as runner:
            runner.run_test(original_func, kwargs)

    backend = pyfuncitem.funcargs.get("anyio_backend")
    if backend:
        backend_name, backend_options = extract_backend_and_options(backend)

        if hasattr(pyfuncitem.obj, "hypothesis"):
            # Wrap the inner test function unless it's already wrapped
            original_func = pyfuncitem.obj.hypothesis.inner_test
            if original_func.__qualname__ != run_with_hypothesis.__qualname__:
                if iscoroutinefunction(original_func):
                    pyfuncitem.obj.hypothesis.inner_test = run_with_hypothesis

            return None

        if iscoroutinefunction(pyfuncitem.obj):
            funcargs = pyfuncitem.funcargs
            testargs = {arg: funcargs[arg] for arg in pyfuncitem._fixtureinfo.argnames}
            with get_runner(backend_name, backend_options) as runner:
                try:
                    runner.run_test(pyfuncitem.obj, testargs)
                except ExceptionGroup as excgrp:
                    for exc in iterate_exceptions(excgrp):
                        if isinstance(exc, (Exit, KeyboardInterrupt, SystemExit)):
                            raise exc from excgrp

                    raise

            return True

    return None


@pytest.fixture(scope="module", params=get_all_backends())
def anyio_backend(request: Any) -> Any:
    return request.param


@pytest.fixture
def anyio_backend_name(anyio_backend: Any) -> str:
    if isinstance(anyio_backend, str):
        return anyio_backend
    else:
        return anyio_backend[0]


@pytest.fixture
def anyio_backend_options(anyio_backend: Any) -> dict[str, Any]:
    if isinstance(anyio_backend, str):
        return {}
    else:
        return anyio_backend[1]
