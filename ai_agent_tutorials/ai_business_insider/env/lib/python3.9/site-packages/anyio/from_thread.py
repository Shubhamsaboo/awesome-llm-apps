from __future__ import annotations

import sys
from collections.abc import Awaitable, Callable, Generator
from concurrent.futures import Future
from contextlib import (
    AbstractAsyncContextManager,
    AbstractContextManager,
    contextmanager,
)
from dataclasses import dataclass, field
from inspect import isawaitable
from threading import Lock, Thread, get_ident
from types import TracebackType
from typing import (
    Any,
    Generic,
    TypeVar,
    cast,
    overload,
)

from ._core import _eventloop
from ._core._eventloop import get_async_backend, get_cancelled_exc_class, threadlocals
from ._core._synchronization import Event
from ._core._tasks import CancelScope, create_task_group
from .abc import AsyncBackend
from .abc._tasks import TaskStatus

if sys.version_info >= (3, 11):
    from typing import TypeVarTuple, Unpack
else:
    from typing_extensions import TypeVarTuple, Unpack

T_Retval = TypeVar("T_Retval")
T_co = TypeVar("T_co", covariant=True)
PosArgsT = TypeVarTuple("PosArgsT")


def run(
    func: Callable[[Unpack[PosArgsT]], Awaitable[T_Retval]], *args: Unpack[PosArgsT]
) -> T_Retval:
    """
    Call a coroutine function from a worker thread.

    :param func: a coroutine function
    :param args: positional arguments for the callable
    :return: the return value of the coroutine function

    """
    try:
        async_backend = threadlocals.current_async_backend
        token = threadlocals.current_token
    except AttributeError:
        raise RuntimeError(
            "This function can only be run from an AnyIO worker thread"
        ) from None

    return async_backend.run_async_from_thread(func, args, token=token)


def run_sync(
    func: Callable[[Unpack[PosArgsT]], T_Retval], *args: Unpack[PosArgsT]
) -> T_Retval:
    """
    Call a function in the event loop thread from a worker thread.

    :param func: a callable
    :param args: positional arguments for the callable
    :return: the return value of the callable

    """
    try:
        async_backend = threadlocals.current_async_backend
        token = threadlocals.current_token
    except AttributeError:
        raise RuntimeError(
            "This function can only be run from an AnyIO worker thread"
        ) from None

    return async_backend.run_sync_from_thread(func, args, token=token)


class _BlockingAsyncContextManager(Generic[T_co], AbstractContextManager):
    _enter_future: Future[T_co]
    _exit_future: Future[bool | None]
    _exit_event: Event
    _exit_exc_info: tuple[
        type[BaseException] | None, BaseException | None, TracebackType | None
    ] = (None, None, None)

    def __init__(
        self, async_cm: AbstractAsyncContextManager[T_co], portal: BlockingPortal
    ):
        self._async_cm = async_cm
        self._portal = portal

    async def run_async_cm(self) -> bool | None:
        try:
            self._exit_event = Event()
            value = await self._async_cm.__aenter__()
        except BaseException as exc:
            self._enter_future.set_exception(exc)
            raise
        else:
            self._enter_future.set_result(value)

        try:
            # Wait for the sync context manager to exit.
            # This next statement can raise `get_cancelled_exc_class()` if
            # something went wrong in a task group in this async context
            # manager.
            await self._exit_event.wait()
        finally:
            # In case of cancellation, it could be that we end up here before
            # `_BlockingAsyncContextManager.__exit__` is called, and an
            # `_exit_exc_info` has been set.
            result = await self._async_cm.__aexit__(*self._exit_exc_info)
            return result

    def __enter__(self) -> T_co:
        self._enter_future = Future()
        self._exit_future = self._portal.start_task_soon(self.run_async_cm)
        return self._enter_future.result()

    def __exit__(
        self,
        __exc_type: type[BaseException] | None,
        __exc_value: BaseException | None,
        __traceback: TracebackType | None,
    ) -> bool | None:
        self._exit_exc_info = __exc_type, __exc_value, __traceback
        self._portal.call(self._exit_event.set)
        return self._exit_future.result()


class _BlockingPortalTaskStatus(TaskStatus):
    def __init__(self, future: Future):
        self._future = future

    def started(self, value: object = None) -> None:
        self._future.set_result(value)


class BlockingPortal:
    """An object that lets external threads run code in an asynchronous event loop."""

    def __new__(cls) -> BlockingPortal:
        return get_async_backend().create_blocking_portal()

    def __init__(self) -> None:
        self._event_loop_thread_id: int | None = get_ident()
        self._stop_event = Event()
        self._task_group = create_task_group()
        self._cancelled_exc_class = get_cancelled_exc_class()

    async def __aenter__(self) -> BlockingPortal:
        await self._task_group.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        await self.stop()
        return await self._task_group.__aexit__(exc_type, exc_val, exc_tb)

    def _check_running(self) -> None:
        if self._event_loop_thread_id is None:
            raise RuntimeError("This portal is not running")
        if self._event_loop_thread_id == get_ident():
            raise RuntimeError(
                "This method cannot be called from the event loop thread"
            )

    async def sleep_until_stopped(self) -> None:
        """Sleep until :meth:`stop` is called."""
        await self._stop_event.wait()

    async def stop(self, cancel_remaining: bool = False) -> None:
        """
        Signal the portal to shut down.

        This marks the portal as no longer accepting new calls and exits from
        :meth:`sleep_until_stopped`.

        :param cancel_remaining: ``True`` to cancel all the remaining tasks, ``False``
            to let them finish before returning

        """
        self._event_loop_thread_id = None
        self._stop_event.set()
        if cancel_remaining:
            self._task_group.cancel_scope.cancel()

    async def _call_func(
        self,
        func: Callable[[Unpack[PosArgsT]], Awaitable[T_Retval] | T_Retval],
        args: tuple[Unpack[PosArgsT]],
        kwargs: dict[str, Any],
        future: Future[T_Retval],
    ) -> None:
        def callback(f: Future[T_Retval]) -> None:
            if f.cancelled() and self._event_loop_thread_id not in (
                None,
                get_ident(),
            ):
                self.call(scope.cancel)

        try:
            retval_or_awaitable = func(*args, **kwargs)
            if isawaitable(retval_or_awaitable):
                with CancelScope() as scope:
                    if future.cancelled():
                        scope.cancel()
                    else:
                        future.add_done_callback(callback)

                    retval = await retval_or_awaitable
            else:
                retval = retval_or_awaitable
        except self._cancelled_exc_class:
            future.cancel()
            future.set_running_or_notify_cancel()
        except BaseException as exc:
            if not future.cancelled():
                future.set_exception(exc)

            # Let base exceptions fall through
            if not isinstance(exc, Exception):
                raise
        else:
            if not future.cancelled():
                future.set_result(retval)
        finally:
            scope = None  # type: ignore[assignment]

    def _spawn_task_from_thread(
        self,
        func: Callable[[Unpack[PosArgsT]], Awaitable[T_Retval] | T_Retval],
        args: tuple[Unpack[PosArgsT]],
        kwargs: dict[str, Any],
        name: object,
        future: Future[T_Retval],
    ) -> None:
        """
        Spawn a new task using the given callable.

        Implementors must ensure that the future is resolved when the task finishes.

        :param func: a callable
        :param args: positional arguments to be passed to the callable
        :param kwargs: keyword arguments to be passed to the callable
        :param name: name of the task (will be coerced to a string if not ``None``)
        :param future: a future that will resolve to the return value of the callable,
            or the exception raised during its execution

        """
        raise NotImplementedError

    @overload
    def call(
        self,
        func: Callable[[Unpack[PosArgsT]], Awaitable[T_Retval]],
        *args: Unpack[PosArgsT],
    ) -> T_Retval: ...

    @overload
    def call(
        self, func: Callable[[Unpack[PosArgsT]], T_Retval], *args: Unpack[PosArgsT]
    ) -> T_Retval: ...

    def call(
        self,
        func: Callable[[Unpack[PosArgsT]], Awaitable[T_Retval] | T_Retval],
        *args: Unpack[PosArgsT],
    ) -> T_Retval:
        """
        Call the given function in the event loop thread.

        If the callable returns a coroutine object, it is awaited on.

        :param func: any callable
        :raises RuntimeError: if the portal is not running or if this method is called
            from within the event loop thread

        """
        return cast(T_Retval, self.start_task_soon(func, *args).result())

    @overload
    def start_task_soon(
        self,
        func: Callable[[Unpack[PosArgsT]], Awaitable[T_Retval]],
        *args: Unpack[PosArgsT],
        name: object = None,
    ) -> Future[T_Retval]: ...

    @overload
    def start_task_soon(
        self,
        func: Callable[[Unpack[PosArgsT]], T_Retval],
        *args: Unpack[PosArgsT],
        name: object = None,
    ) -> Future[T_Retval]: ...

    def start_task_soon(
        self,
        func: Callable[[Unpack[PosArgsT]], Awaitable[T_Retval] | T_Retval],
        *args: Unpack[PosArgsT],
        name: object = None,
    ) -> Future[T_Retval]:
        """
        Start a task in the portal's task group.

        The task will be run inside a cancel scope which can be cancelled by cancelling
        the returned future.

        :param func: the target function
        :param args: positional arguments passed to ``func``
        :param name: name of the task (will be coerced to a string if not ``None``)
        :return: a future that resolves with the return value of the callable if the
            task completes successfully, or with the exception raised in the task
        :raises RuntimeError: if the portal is not running or if this method is called
            from within the event loop thread
        :rtype: concurrent.futures.Future[T_Retval]

        .. versionadded:: 3.0

        """
        self._check_running()
        f: Future[T_Retval] = Future()
        self._spawn_task_from_thread(func, args, {}, name, f)
        return f

    def start_task(
        self,
        func: Callable[..., Awaitable[T_Retval]],
        *args: object,
        name: object = None,
    ) -> tuple[Future[T_Retval], Any]:
        """
        Start a task in the portal's task group and wait until it signals for readiness.

        This method works the same way as :meth:`.abc.TaskGroup.start`.

        :param func: the target function
        :param args: positional arguments passed to ``func``
        :param name: name of the task (will be coerced to a string if not ``None``)
        :return: a tuple of (future, task_status_value) where the ``task_status_value``
            is the value passed to ``task_status.started()`` from within the target
            function
        :rtype: tuple[concurrent.futures.Future[T_Retval], Any]

        .. versionadded:: 3.0

        """

        def task_done(future: Future[T_Retval]) -> None:
            if not task_status_future.done():
                if future.cancelled():
                    task_status_future.cancel()
                elif future.exception():
                    task_status_future.set_exception(future.exception())
                else:
                    exc = RuntimeError(
                        "Task exited without calling task_status.started()"
                    )
                    task_status_future.set_exception(exc)

        self._check_running()
        task_status_future: Future = Future()
        task_status = _BlockingPortalTaskStatus(task_status_future)
        f: Future = Future()
        f.add_done_callback(task_done)
        self._spawn_task_from_thread(func, args, {"task_status": task_status}, name, f)
        return f, task_status_future.result()

    def wrap_async_context_manager(
        self, cm: AbstractAsyncContextManager[T_co]
    ) -> AbstractContextManager[T_co]:
        """
        Wrap an async context manager as a synchronous context manager via this portal.

        Spawns a task that will call both ``__aenter__()`` and ``__aexit__()``, stopping
        in the middle until the synchronous context manager exits.

        :param cm: an asynchronous context manager
        :return: a synchronous context manager

        .. versionadded:: 2.1

        """
        return _BlockingAsyncContextManager(cm, self)


@dataclass
class BlockingPortalProvider:
    """
    A manager for a blocking portal. Used as a context manager. The first thread to
    enter this context manager causes a blocking portal to be started with the specific
    parameters, and the last thread to exit causes the portal to be shut down. Thus,
    there will be exactly one blocking portal running in this context as long as at
    least one thread has entered this context manager.

    The parameters are the same as for :func:`~anyio.run`.

    :param backend: name of the backend
    :param backend_options: backend options

    .. versionadded:: 4.4
    """

    backend: str = "asyncio"
    backend_options: dict[str, Any] | None = None
    _lock: Lock = field(init=False, default_factory=Lock)
    _leases: int = field(init=False, default=0)
    _portal: BlockingPortal = field(init=False)
    _portal_cm: AbstractContextManager[BlockingPortal] | None = field(
        init=False, default=None
    )

    def __enter__(self) -> BlockingPortal:
        with self._lock:
            if self._portal_cm is None:
                self._portal_cm = start_blocking_portal(
                    self.backend, self.backend_options
                )
                self._portal = self._portal_cm.__enter__()

            self._leases += 1
            return self._portal

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        portal_cm: AbstractContextManager[BlockingPortal] | None = None
        with self._lock:
            assert self._portal_cm
            assert self._leases > 0
            self._leases -= 1
            if not self._leases:
                portal_cm = self._portal_cm
                self._portal_cm = None
                del self._portal

        if portal_cm:
            portal_cm.__exit__(None, None, None)


@contextmanager
def start_blocking_portal(
    backend: str = "asyncio", backend_options: dict[str, Any] | None = None
) -> Generator[BlockingPortal, Any, None]:
    """
    Start a new event loop in a new thread and run a blocking portal in its main task.

    The parameters are the same as for :func:`~anyio.run`.

    :param backend: name of the backend
    :param backend_options: backend options
    :return: a context manager that yields a blocking portal

    .. versionchanged:: 3.0
        Usage as a context manager is now required.

    """

    async def run_portal() -> None:
        async with BlockingPortal() as portal_:
            future.set_result(portal_)
            await portal_.sleep_until_stopped()

    def run_blocking_portal() -> None:
        if future.set_running_or_notify_cancel():
            try:
                _eventloop.run(
                    run_portal, backend=backend, backend_options=backend_options
                )
            except BaseException as exc:
                if not future.done():
                    future.set_exception(exc)

    future: Future[BlockingPortal] = Future()
    thread = Thread(target=run_blocking_portal, daemon=True)
    thread.start()
    try:
        cancel_remaining_tasks = False
        portal = future.result()
        try:
            yield portal
        except BaseException:
            cancel_remaining_tasks = True
            raise
        finally:
            try:
                portal.call(portal.stop, cancel_remaining_tasks)
            except RuntimeError:
                pass
    finally:
        thread.join()


def check_cancelled() -> None:
    """
    Check if the cancel scope of the host task's running the current worker thread has
    been cancelled.

    If the host task's current cancel scope has indeed been cancelled, the
    backend-specific cancellation exception will be raised.

    :raises RuntimeError: if the current thread was not spawned by
        :func:`.to_thread.run_sync`

    """
    try:
        async_backend: AsyncBackend = threadlocals.current_async_backend
    except AttributeError:
        raise RuntimeError(
            "This function can only be run from an AnyIO worker thread"
        ) from None

    async_backend.check_cancelled()
