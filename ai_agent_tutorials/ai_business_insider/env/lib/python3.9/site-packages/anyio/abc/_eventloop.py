from __future__ import annotations

import math
import sys
from abc import ABCMeta, abstractmethod
from collections.abc import AsyncIterator, Awaitable, Callable, Sequence
from contextlib import AbstractContextManager
from os import PathLike
from signal import Signals
from socket import AddressFamily, SocketKind, socket
from typing import (
    IO,
    TYPE_CHECKING,
    Any,
    TypeVar,
    Union,
    overload,
)

if sys.version_info >= (3, 11):
    from typing import TypeVarTuple, Unpack
else:
    from typing_extensions import TypeVarTuple, Unpack

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias

if TYPE_CHECKING:
    from .._core._synchronization import CapacityLimiter, Event, Lock, Semaphore
    from .._core._tasks import CancelScope
    from .._core._testing import TaskInfo
    from ..from_thread import BlockingPortal
    from ._sockets import (
        ConnectedUDPSocket,
        ConnectedUNIXDatagramSocket,
        IPSockAddrType,
        SocketListener,
        SocketStream,
        UDPSocket,
        UNIXDatagramSocket,
        UNIXSocketStream,
    )
    from ._subprocesses import Process
    from ._tasks import TaskGroup
    from ._testing import TestRunner

T_Retval = TypeVar("T_Retval")
PosArgsT = TypeVarTuple("PosArgsT")
StrOrBytesPath: TypeAlias = Union[str, bytes, "PathLike[str]", "PathLike[bytes]"]


class AsyncBackend(metaclass=ABCMeta):
    @classmethod
    @abstractmethod
    def run(
        cls,
        func: Callable[[Unpack[PosArgsT]], Awaitable[T_Retval]],
        args: tuple[Unpack[PosArgsT]],
        kwargs: dict[str, Any],
        options: dict[str, Any],
    ) -> T_Retval:
        """
        Run the given coroutine function in an asynchronous event loop.

        The current thread must not be already running an event loop.

        :param func: a coroutine function
        :param args: positional arguments to ``func``
        :param kwargs: positional arguments to ``func``
        :param options: keyword arguments to call the backend ``run()`` implementation
            with
        :return: the return value of the coroutine function
        """

    @classmethod
    @abstractmethod
    def current_token(cls) -> object:
        """

        :return:
        """

    @classmethod
    @abstractmethod
    def current_time(cls) -> float:
        """
        Return the current value of the event loop's internal clock.

        :return: the clock value (seconds)
        """

    @classmethod
    @abstractmethod
    def cancelled_exception_class(cls) -> type[BaseException]:
        """Return the exception class that is raised in a task if it's cancelled."""

    @classmethod
    @abstractmethod
    async def checkpoint(cls) -> None:
        """
        Check if the task has been cancelled, and allow rescheduling of other tasks.

        This is effectively the same as running :meth:`checkpoint_if_cancelled` and then
        :meth:`cancel_shielded_checkpoint`.
        """

    @classmethod
    async def checkpoint_if_cancelled(cls) -> None:
        """
        Check if the current task group has been cancelled.

        This will check if the task has been cancelled, but will not allow other tasks
        to be scheduled if not.

        """
        if cls.current_effective_deadline() == -math.inf:
            await cls.checkpoint()

    @classmethod
    async def cancel_shielded_checkpoint(cls) -> None:
        """
        Allow the rescheduling of other tasks.

        This will give other tasks the opportunity to run, but without checking if the
        current task group has been cancelled, unlike with :meth:`checkpoint`.

        """
        with cls.create_cancel_scope(shield=True):
            await cls.sleep(0)

    @classmethod
    @abstractmethod
    async def sleep(cls, delay: float) -> None:
        """
        Pause the current task for the specified duration.

        :param delay: the duration, in seconds
        """

    @classmethod
    @abstractmethod
    def create_cancel_scope(
        cls, *, deadline: float = math.inf, shield: bool = False
    ) -> CancelScope:
        pass

    @classmethod
    @abstractmethod
    def current_effective_deadline(cls) -> float:
        """
        Return the nearest deadline among all the cancel scopes effective for the
        current task.

        :return:
            - a clock value from the event loop's internal clock
            - ``inf`` if there is no deadline in effect
            - ``-inf`` if the current scope has been cancelled
        :rtype: float
        """

    @classmethod
    @abstractmethod
    def create_task_group(cls) -> TaskGroup:
        pass

    @classmethod
    @abstractmethod
    def create_event(cls) -> Event:
        pass

    @classmethod
    @abstractmethod
    def create_lock(cls, *, fast_acquire: bool) -> Lock:
        pass

    @classmethod
    @abstractmethod
    def create_semaphore(
        cls,
        initial_value: int,
        *,
        max_value: int | None = None,
        fast_acquire: bool = False,
    ) -> Semaphore:
        pass

    @classmethod
    @abstractmethod
    def create_capacity_limiter(cls, total_tokens: float) -> CapacityLimiter:
        pass

    @classmethod
    @abstractmethod
    async def run_sync_in_worker_thread(
        cls,
        func: Callable[[Unpack[PosArgsT]], T_Retval],
        args: tuple[Unpack[PosArgsT]],
        abandon_on_cancel: bool = False,
        limiter: CapacityLimiter | None = None,
    ) -> T_Retval:
        pass

    @classmethod
    @abstractmethod
    def check_cancelled(cls) -> None:
        pass

    @classmethod
    @abstractmethod
    def run_async_from_thread(
        cls,
        func: Callable[[Unpack[PosArgsT]], Awaitable[T_Retval]],
        args: tuple[Unpack[PosArgsT]],
        token: object,
    ) -> T_Retval:
        pass

    @classmethod
    @abstractmethod
    def run_sync_from_thread(
        cls,
        func: Callable[[Unpack[PosArgsT]], T_Retval],
        args: tuple[Unpack[PosArgsT]],
        token: object,
    ) -> T_Retval:
        pass

    @classmethod
    @abstractmethod
    def create_blocking_portal(cls) -> BlockingPortal:
        pass

    @classmethod
    @abstractmethod
    async def open_process(
        cls,
        command: StrOrBytesPath | Sequence[StrOrBytesPath],
        *,
        stdin: int | IO[Any] | None,
        stdout: int | IO[Any] | None,
        stderr: int | IO[Any] | None,
        **kwargs: Any,
    ) -> Process:
        pass

    @classmethod
    @abstractmethod
    def setup_process_pool_exit_at_shutdown(cls, workers: set[Process]) -> None:
        pass

    @classmethod
    @abstractmethod
    async def connect_tcp(
        cls, host: str, port: int, local_address: IPSockAddrType | None = None
    ) -> SocketStream:
        pass

    @classmethod
    @abstractmethod
    async def connect_unix(cls, path: str | bytes) -> UNIXSocketStream:
        pass

    @classmethod
    @abstractmethod
    def create_tcp_listener(cls, sock: socket) -> SocketListener:
        pass

    @classmethod
    @abstractmethod
    def create_unix_listener(cls, sock: socket) -> SocketListener:
        pass

    @classmethod
    @abstractmethod
    async def create_udp_socket(
        cls,
        family: AddressFamily,
        local_address: IPSockAddrType | None,
        remote_address: IPSockAddrType | None,
        reuse_port: bool,
    ) -> UDPSocket | ConnectedUDPSocket:
        pass

    @classmethod
    @overload
    async def create_unix_datagram_socket(
        cls, raw_socket: socket, remote_path: None
    ) -> UNIXDatagramSocket: ...

    @classmethod
    @overload
    async def create_unix_datagram_socket(
        cls, raw_socket: socket, remote_path: str | bytes
    ) -> ConnectedUNIXDatagramSocket: ...

    @classmethod
    @abstractmethod
    async def create_unix_datagram_socket(
        cls, raw_socket: socket, remote_path: str | bytes | None
    ) -> UNIXDatagramSocket | ConnectedUNIXDatagramSocket:
        pass

    @classmethod
    @abstractmethod
    async def getaddrinfo(
        cls,
        host: bytes | str | None,
        port: str | int | None,
        *,
        family: int | AddressFamily = 0,
        type: int | SocketKind = 0,
        proto: int = 0,
        flags: int = 0,
    ) -> list[
        tuple[
            AddressFamily,
            SocketKind,
            int,
            str,
            tuple[str, int] | tuple[str, int, int, int],
        ]
    ]:
        pass

    @classmethod
    @abstractmethod
    async def getnameinfo(
        cls, sockaddr: IPSockAddrType, flags: int = 0
    ) -> tuple[str, str]:
        pass

    @classmethod
    @abstractmethod
    async def wait_socket_readable(cls, sock: socket) -> None:
        pass

    @classmethod
    @abstractmethod
    async def wait_socket_writable(cls, sock: socket) -> None:
        pass

    @classmethod
    @abstractmethod
    def current_default_thread_limiter(cls) -> CapacityLimiter:
        pass

    @classmethod
    @abstractmethod
    def open_signal_receiver(
        cls, *signals: Signals
    ) -> AbstractContextManager[AsyncIterator[Signals]]:
        pass

    @classmethod
    @abstractmethod
    def get_current_task(cls) -> TaskInfo:
        pass

    @classmethod
    @abstractmethod
    def get_running_tasks(cls) -> Sequence[TaskInfo]:
        pass

    @classmethod
    @abstractmethod
    async def wait_all_tasks_blocked(cls) -> None:
        pass

    @classmethod
    @abstractmethod
    def create_test_runner(cls, options: dict[str, Any]) -> TestRunner:
        pass
