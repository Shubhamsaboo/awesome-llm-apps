from __future__ import annotations

import array
import math
import os
import socket
import sys
import types
import weakref
from collections.abc import (
    AsyncGenerator,
    AsyncIterator,
    Awaitable,
    Callable,
    Collection,
    Coroutine,
    Iterable,
    Sequence,
)
from concurrent.futures import Future
from contextlib import AbstractContextManager
from dataclasses import dataclass
from functools import partial
from io import IOBase
from os import PathLike
from signal import Signals
from socket import AddressFamily, SocketKind
from types import TracebackType
from typing import (
    IO,
    Any,
    Generic,
    NoReturn,
    TypeVar,
    cast,
    overload,
)

import trio.from_thread
import trio.lowlevel
from outcome import Error, Outcome, Value
from trio.lowlevel import (
    current_root_task,
    current_task,
    wait_readable,
    wait_writable,
)
from trio.socket import SocketType as TrioSocketType
from trio.to_thread import run_sync

from .. import (
    CapacityLimiterStatistics,
    EventStatistics,
    LockStatistics,
    TaskInfo,
    WouldBlock,
    abc,
)
from .._core._eventloop import claim_worker_thread
from .._core._exceptions import (
    BrokenResourceError,
    BusyResourceError,
    ClosedResourceError,
    EndOfStream,
)
from .._core._sockets import convert_ipv6_sockaddr
from .._core._streams import create_memory_object_stream
from .._core._synchronization import (
    CapacityLimiter as BaseCapacityLimiter,
)
from .._core._synchronization import Event as BaseEvent
from .._core._synchronization import Lock as BaseLock
from .._core._synchronization import (
    ResourceGuard,
    SemaphoreStatistics,
)
from .._core._synchronization import Semaphore as BaseSemaphore
from .._core._tasks import CancelScope as BaseCancelScope
from ..abc import IPSockAddrType, UDPPacketType, UNIXDatagramPacketType
from ..abc._eventloop import AsyncBackend, StrOrBytesPath
from ..streams.memory import MemoryObjectSendStream

if sys.version_info >= (3, 10):
    from typing import ParamSpec
else:
    from typing_extensions import ParamSpec

if sys.version_info >= (3, 11):
    from typing import TypeVarTuple, Unpack
else:
    from exceptiongroup import BaseExceptionGroup
    from typing_extensions import TypeVarTuple, Unpack

T = TypeVar("T")
T_Retval = TypeVar("T_Retval")
T_SockAddr = TypeVar("T_SockAddr", str, IPSockAddrType)
PosArgsT = TypeVarTuple("PosArgsT")
P = ParamSpec("P")


#
# Event loop
#

RunVar = trio.lowlevel.RunVar


#
# Timeouts and cancellation
#


class CancelScope(BaseCancelScope):
    def __new__(
        cls, original: trio.CancelScope | None = None, **kwargs: object
    ) -> CancelScope:
        return object.__new__(cls)

    def __init__(self, original: trio.CancelScope | None = None, **kwargs: Any) -> None:
        self.__original = original or trio.CancelScope(**kwargs)

    def __enter__(self) -> CancelScope:
        self.__original.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        # https://github.com/python-trio/trio-typing/pull/79
        return self.__original.__exit__(exc_type, exc_val, exc_tb)

    def cancel(self) -> None:
        self.__original.cancel()

    @property
    def deadline(self) -> float:
        return self.__original.deadline

    @deadline.setter
    def deadline(self, value: float) -> None:
        self.__original.deadline = value

    @property
    def cancel_called(self) -> bool:
        return self.__original.cancel_called

    @property
    def cancelled_caught(self) -> bool:
        return self.__original.cancelled_caught

    @property
    def shield(self) -> bool:
        return self.__original.shield

    @shield.setter
    def shield(self, value: bool) -> None:
        self.__original.shield = value


#
# Task groups
#


class TaskGroup(abc.TaskGroup):
    def __init__(self) -> None:
        self._active = False
        self._nursery_manager = trio.open_nursery(strict_exception_groups=True)
        self.cancel_scope = None  # type: ignore[assignment]

    async def __aenter__(self) -> TaskGroup:
        self._active = True
        self._nursery = await self._nursery_manager.__aenter__()
        self.cancel_scope = CancelScope(self._nursery.cancel_scope)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        try:
            return await self._nursery_manager.__aexit__(exc_type, exc_val, exc_tb)
        except BaseExceptionGroup as exc:
            if not exc.split(trio.Cancelled)[1]:
                raise trio.Cancelled._create() from exc

            raise
        finally:
            del exc_val, exc_tb
            self._active = False

    def start_soon(
        self,
        func: Callable[[Unpack[PosArgsT]], Awaitable[Any]],
        *args: Unpack[PosArgsT],
        name: object = None,
    ) -> None:
        if not self._active:
            raise RuntimeError(
                "This task group is not active; no new tasks can be started."
            )

        self._nursery.start_soon(func, *args, name=name)

    async def start(
        self, func: Callable[..., Awaitable[Any]], *args: object, name: object = None
    ) -> Any:
        if not self._active:
            raise RuntimeError(
                "This task group is not active; no new tasks can be started."
            )

        return await self._nursery.start(func, *args, name=name)


#
# Threads
#


class BlockingPortal(abc.BlockingPortal):
    def __new__(cls) -> BlockingPortal:
        return object.__new__(cls)

    def __init__(self) -> None:
        super().__init__()
        self._token = trio.lowlevel.current_trio_token()

    def _spawn_task_from_thread(
        self,
        func: Callable[[Unpack[PosArgsT]], Awaitable[T_Retval] | T_Retval],
        args: tuple[Unpack[PosArgsT]],
        kwargs: dict[str, Any],
        name: object,
        future: Future[T_Retval],
    ) -> None:
        trio.from_thread.run_sync(
            partial(self._task_group.start_soon, name=name),
            self._call_func,
            func,
            args,
            kwargs,
            future,
            trio_token=self._token,
        )


#
# Subprocesses
#


@dataclass(eq=False)
class ReceiveStreamWrapper(abc.ByteReceiveStream):
    _stream: trio.abc.ReceiveStream

    async def receive(self, max_bytes: int | None = None) -> bytes:
        try:
            data = await self._stream.receive_some(max_bytes)
        except trio.ClosedResourceError as exc:
            raise ClosedResourceError from exc.__cause__
        except trio.BrokenResourceError as exc:
            raise BrokenResourceError from exc.__cause__

        if data:
            return data
        else:
            raise EndOfStream

    async def aclose(self) -> None:
        await self._stream.aclose()


@dataclass(eq=False)
class SendStreamWrapper(abc.ByteSendStream):
    _stream: trio.abc.SendStream

    async def send(self, item: bytes) -> None:
        try:
            await self._stream.send_all(item)
        except trio.ClosedResourceError as exc:
            raise ClosedResourceError from exc.__cause__
        except trio.BrokenResourceError as exc:
            raise BrokenResourceError from exc.__cause__

    async def aclose(self) -> None:
        await self._stream.aclose()


@dataclass(eq=False)
class Process(abc.Process):
    _process: trio.Process
    _stdin: abc.ByteSendStream | None
    _stdout: abc.ByteReceiveStream | None
    _stderr: abc.ByteReceiveStream | None

    async def aclose(self) -> None:
        with CancelScope(shield=True):
            if self._stdin:
                await self._stdin.aclose()
            if self._stdout:
                await self._stdout.aclose()
            if self._stderr:
                await self._stderr.aclose()

        try:
            await self.wait()
        except BaseException:
            self.kill()
            with CancelScope(shield=True):
                await self.wait()
            raise

    async def wait(self) -> int:
        return await self._process.wait()

    def terminate(self) -> None:
        self._process.terminate()

    def kill(self) -> None:
        self._process.kill()

    def send_signal(self, signal: Signals) -> None:
        self._process.send_signal(signal)

    @property
    def pid(self) -> int:
        return self._process.pid

    @property
    def returncode(self) -> int | None:
        return self._process.returncode

    @property
    def stdin(self) -> abc.ByteSendStream | None:
        return self._stdin

    @property
    def stdout(self) -> abc.ByteReceiveStream | None:
        return self._stdout

    @property
    def stderr(self) -> abc.ByteReceiveStream | None:
        return self._stderr


class _ProcessPoolShutdownInstrument(trio.abc.Instrument):
    def after_run(self) -> None:
        super().after_run()


current_default_worker_process_limiter: trio.lowlevel.RunVar = RunVar(
    "current_default_worker_process_limiter"
)


async def _shutdown_process_pool(workers: set[abc.Process]) -> None:
    try:
        await trio.sleep(math.inf)
    except trio.Cancelled:
        for process in workers:
            if process.returncode is None:
                process.kill()

        with CancelScope(shield=True):
            for process in workers:
                await process.aclose()


#
# Sockets and networking
#


class _TrioSocketMixin(Generic[T_SockAddr]):
    def __init__(self, trio_socket: TrioSocketType) -> None:
        self._trio_socket = trio_socket
        self._closed = False

    def _check_closed(self) -> None:
        if self._closed:
            raise ClosedResourceError
        if self._trio_socket.fileno() < 0:
            raise BrokenResourceError

    @property
    def _raw_socket(self) -> socket.socket:
        return self._trio_socket._sock  # type: ignore[attr-defined]

    async def aclose(self) -> None:
        if self._trio_socket.fileno() >= 0:
            self._closed = True
            self._trio_socket.close()

    def _convert_socket_error(self, exc: BaseException) -> NoReturn:
        if isinstance(exc, trio.ClosedResourceError):
            raise ClosedResourceError from exc
        elif self._trio_socket.fileno() < 0 and self._closed:
            raise ClosedResourceError from None
        elif isinstance(exc, OSError):
            raise BrokenResourceError from exc
        else:
            raise exc


class SocketStream(_TrioSocketMixin, abc.SocketStream):
    def __init__(self, trio_socket: TrioSocketType) -> None:
        super().__init__(trio_socket)
        self._receive_guard = ResourceGuard("reading from")
        self._send_guard = ResourceGuard("writing to")

    async def receive(self, max_bytes: int = 65536) -> bytes:
        with self._receive_guard:
            try:
                data = await self._trio_socket.recv(max_bytes)
            except BaseException as exc:
                self._convert_socket_error(exc)

            if data:
                return data
            else:
                raise EndOfStream

    async def send(self, item: bytes) -> None:
        with self._send_guard:
            view = memoryview(item)
            while view:
                try:
                    bytes_sent = await self._trio_socket.send(view)
                except BaseException as exc:
                    self._convert_socket_error(exc)

                view = view[bytes_sent:]

    async def send_eof(self) -> None:
        self._trio_socket.shutdown(socket.SHUT_WR)


class UNIXSocketStream(SocketStream, abc.UNIXSocketStream):
    async def receive_fds(self, msglen: int, maxfds: int) -> tuple[bytes, list[int]]:
        if not isinstance(msglen, int) or msglen < 0:
            raise ValueError("msglen must be a non-negative integer")
        if not isinstance(maxfds, int) or maxfds < 1:
            raise ValueError("maxfds must be a positive integer")

        fds = array.array("i")
        await trio.lowlevel.checkpoint()
        with self._receive_guard:
            while True:
                try:
                    message, ancdata, flags, addr = await self._trio_socket.recvmsg(
                        msglen, socket.CMSG_LEN(maxfds * fds.itemsize)
                    )
                except BaseException as exc:
                    self._convert_socket_error(exc)
                else:
                    if not message and not ancdata:
                        raise EndOfStream

                    break

        for cmsg_level, cmsg_type, cmsg_data in ancdata:
            if cmsg_level != socket.SOL_SOCKET or cmsg_type != socket.SCM_RIGHTS:
                raise RuntimeError(
                    f"Received unexpected ancillary data; message = {message!r}, "
                    f"cmsg_level = {cmsg_level}, cmsg_type = {cmsg_type}"
                )

            fds.frombytes(cmsg_data[: len(cmsg_data) - (len(cmsg_data) % fds.itemsize)])

        return message, list(fds)

    async def send_fds(self, message: bytes, fds: Collection[int | IOBase]) -> None:
        if not message:
            raise ValueError("message must not be empty")
        if not fds:
            raise ValueError("fds must not be empty")

        filenos: list[int] = []
        for fd in fds:
            if isinstance(fd, int):
                filenos.append(fd)
            elif isinstance(fd, IOBase):
                filenos.append(fd.fileno())

        fdarray = array.array("i", filenos)
        await trio.lowlevel.checkpoint()
        with self._send_guard:
            while True:
                try:
                    await self._trio_socket.sendmsg(
                        [message],
                        [
                            (
                                socket.SOL_SOCKET,
                                socket.SCM_RIGHTS,
                                fdarray,
                            )
                        ],
                    )
                    break
                except BaseException as exc:
                    self._convert_socket_error(exc)


class TCPSocketListener(_TrioSocketMixin, abc.SocketListener):
    def __init__(self, raw_socket: socket.socket):
        super().__init__(trio.socket.from_stdlib_socket(raw_socket))
        self._accept_guard = ResourceGuard("accepting connections from")

    async def accept(self) -> SocketStream:
        with self._accept_guard:
            try:
                trio_socket, _addr = await self._trio_socket.accept()
            except BaseException as exc:
                self._convert_socket_error(exc)

        trio_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        return SocketStream(trio_socket)


class UNIXSocketListener(_TrioSocketMixin, abc.SocketListener):
    def __init__(self, raw_socket: socket.socket):
        super().__init__(trio.socket.from_stdlib_socket(raw_socket))
        self._accept_guard = ResourceGuard("accepting connections from")

    async def accept(self) -> UNIXSocketStream:
        with self._accept_guard:
            try:
                trio_socket, _addr = await self._trio_socket.accept()
            except BaseException as exc:
                self._convert_socket_error(exc)

        return UNIXSocketStream(trio_socket)


class UDPSocket(_TrioSocketMixin[IPSockAddrType], abc.UDPSocket):
    def __init__(self, trio_socket: TrioSocketType) -> None:
        super().__init__(trio_socket)
        self._receive_guard = ResourceGuard("reading from")
        self._send_guard = ResourceGuard("writing to")

    async def receive(self) -> tuple[bytes, IPSockAddrType]:
        with self._receive_guard:
            try:
                data, addr = await self._trio_socket.recvfrom(65536)
                return data, convert_ipv6_sockaddr(addr)
            except BaseException as exc:
                self._convert_socket_error(exc)

    async def send(self, item: UDPPacketType) -> None:
        with self._send_guard:
            try:
                await self._trio_socket.sendto(*item)
            except BaseException as exc:
                self._convert_socket_error(exc)


class ConnectedUDPSocket(_TrioSocketMixin[IPSockAddrType], abc.ConnectedUDPSocket):
    def __init__(self, trio_socket: TrioSocketType) -> None:
        super().__init__(trio_socket)
        self._receive_guard = ResourceGuard("reading from")
        self._send_guard = ResourceGuard("writing to")

    async def receive(self) -> bytes:
        with self._receive_guard:
            try:
                return await self._trio_socket.recv(65536)
            except BaseException as exc:
                self._convert_socket_error(exc)

    async def send(self, item: bytes) -> None:
        with self._send_guard:
            try:
                await self._trio_socket.send(item)
            except BaseException as exc:
                self._convert_socket_error(exc)


class UNIXDatagramSocket(_TrioSocketMixin[str], abc.UNIXDatagramSocket):
    def __init__(self, trio_socket: TrioSocketType) -> None:
        super().__init__(trio_socket)
        self._receive_guard = ResourceGuard("reading from")
        self._send_guard = ResourceGuard("writing to")

    async def receive(self) -> UNIXDatagramPacketType:
        with self._receive_guard:
            try:
                data, addr = await self._trio_socket.recvfrom(65536)
                return data, addr
            except BaseException as exc:
                self._convert_socket_error(exc)

    async def send(self, item: UNIXDatagramPacketType) -> None:
        with self._send_guard:
            try:
                await self._trio_socket.sendto(*item)
            except BaseException as exc:
                self._convert_socket_error(exc)


class ConnectedUNIXDatagramSocket(
    _TrioSocketMixin[str], abc.ConnectedUNIXDatagramSocket
):
    def __init__(self, trio_socket: TrioSocketType) -> None:
        super().__init__(trio_socket)
        self._receive_guard = ResourceGuard("reading from")
        self._send_guard = ResourceGuard("writing to")

    async def receive(self) -> bytes:
        with self._receive_guard:
            try:
                return await self._trio_socket.recv(65536)
            except BaseException as exc:
                self._convert_socket_error(exc)

    async def send(self, item: bytes) -> None:
        with self._send_guard:
            try:
                await self._trio_socket.send(item)
            except BaseException as exc:
                self._convert_socket_error(exc)


#
# Synchronization
#


class Event(BaseEvent):
    def __new__(cls) -> Event:
        return object.__new__(cls)

    def __init__(self) -> None:
        self.__original = trio.Event()

    def is_set(self) -> bool:
        return self.__original.is_set()

    async def wait(self) -> None:
        return await self.__original.wait()

    def statistics(self) -> EventStatistics:
        orig_statistics = self.__original.statistics()
        return EventStatistics(tasks_waiting=orig_statistics.tasks_waiting)

    def set(self) -> None:
        self.__original.set()


class Lock(BaseLock):
    def __new__(cls, *, fast_acquire: bool = False) -> Lock:
        return object.__new__(cls)

    def __init__(self, *, fast_acquire: bool = False) -> None:
        self._fast_acquire = fast_acquire
        self.__original = trio.Lock()

    @staticmethod
    def _convert_runtime_error_msg(exc: RuntimeError) -> None:
        if exc.args == ("attempt to re-acquire an already held Lock",):
            exc.args = ("Attempted to acquire an already held Lock",)

    async def acquire(self) -> None:
        if not self._fast_acquire:
            try:
                await self.__original.acquire()
            except RuntimeError as exc:
                self._convert_runtime_error_msg(exc)
                raise

            return

        # This is the "fast path" where we don't let other tasks run
        await trio.lowlevel.checkpoint_if_cancelled()
        try:
            self.__original.acquire_nowait()
        except trio.WouldBlock:
            await self.__original._lot.park()
        except RuntimeError as exc:
            self._convert_runtime_error_msg(exc)
            raise

    def acquire_nowait(self) -> None:
        try:
            self.__original.acquire_nowait()
        except trio.WouldBlock:
            raise WouldBlock from None
        except RuntimeError as exc:
            self._convert_runtime_error_msg(exc)
            raise

    def locked(self) -> bool:
        return self.__original.locked()

    def release(self) -> None:
        self.__original.release()

    def statistics(self) -> LockStatistics:
        orig_statistics = self.__original.statistics()
        owner = TrioTaskInfo(orig_statistics.owner) if orig_statistics.owner else None
        return LockStatistics(
            orig_statistics.locked, owner, orig_statistics.tasks_waiting
        )


class Semaphore(BaseSemaphore):
    def __new__(
        cls,
        initial_value: int,
        *,
        max_value: int | None = None,
        fast_acquire: bool = False,
    ) -> Semaphore:
        return object.__new__(cls)

    def __init__(
        self,
        initial_value: int,
        *,
        max_value: int | None = None,
        fast_acquire: bool = False,
    ) -> None:
        super().__init__(initial_value, max_value=max_value, fast_acquire=fast_acquire)
        self.__original = trio.Semaphore(initial_value, max_value=max_value)

    async def acquire(self) -> None:
        if not self._fast_acquire:
            await self.__original.acquire()
            return

        # This is the "fast path" where we don't let other tasks run
        await trio.lowlevel.checkpoint_if_cancelled()
        try:
            self.__original.acquire_nowait()
        except trio.WouldBlock:
            await self.__original._lot.park()

    def acquire_nowait(self) -> None:
        try:
            self.__original.acquire_nowait()
        except trio.WouldBlock:
            raise WouldBlock from None

    @property
    def max_value(self) -> int | None:
        return self.__original.max_value

    @property
    def value(self) -> int:
        return self.__original.value

    def release(self) -> None:
        self.__original.release()

    def statistics(self) -> SemaphoreStatistics:
        orig_statistics = self.__original.statistics()
        return SemaphoreStatistics(orig_statistics.tasks_waiting)


class CapacityLimiter(BaseCapacityLimiter):
    def __new__(
        cls,
        total_tokens: float | None = None,
        *,
        original: trio.CapacityLimiter | None = None,
    ) -> CapacityLimiter:
        return object.__new__(cls)

    def __init__(
        self,
        total_tokens: float | None = None,
        *,
        original: trio.CapacityLimiter | None = None,
    ) -> None:
        if original is not None:
            self.__original = original
        else:
            assert total_tokens is not None
            self.__original = trio.CapacityLimiter(total_tokens)

    async def __aenter__(self) -> None:
        return await self.__original.__aenter__()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.__original.__aexit__(exc_type, exc_val, exc_tb)

    @property
    def total_tokens(self) -> float:
        return self.__original.total_tokens

    @total_tokens.setter
    def total_tokens(self, value: float) -> None:
        self.__original.total_tokens = value

    @property
    def borrowed_tokens(self) -> int:
        return self.__original.borrowed_tokens

    @property
    def available_tokens(self) -> float:
        return self.__original.available_tokens

    def acquire_nowait(self) -> None:
        self.__original.acquire_nowait()

    def acquire_on_behalf_of_nowait(self, borrower: object) -> None:
        self.__original.acquire_on_behalf_of_nowait(borrower)

    async def acquire(self) -> None:
        await self.__original.acquire()

    async def acquire_on_behalf_of(self, borrower: object) -> None:
        await self.__original.acquire_on_behalf_of(borrower)

    def release(self) -> None:
        return self.__original.release()

    def release_on_behalf_of(self, borrower: object) -> None:
        return self.__original.release_on_behalf_of(borrower)

    def statistics(self) -> CapacityLimiterStatistics:
        orig = self.__original.statistics()
        return CapacityLimiterStatistics(
            borrowed_tokens=orig.borrowed_tokens,
            total_tokens=orig.total_tokens,
            borrowers=tuple(orig.borrowers),
            tasks_waiting=orig.tasks_waiting,
        )


_capacity_limiter_wrapper: trio.lowlevel.RunVar = RunVar("_capacity_limiter_wrapper")


#
# Signal handling
#


class _SignalReceiver:
    _iterator: AsyncIterator[int]

    def __init__(self, signals: tuple[Signals, ...]):
        self._signals = signals

    def __enter__(self) -> _SignalReceiver:
        self._cm = trio.open_signal_receiver(*self._signals)
        self._iterator = self._cm.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        return self._cm.__exit__(exc_type, exc_val, exc_tb)

    def __aiter__(self) -> _SignalReceiver:
        return self

    async def __anext__(self) -> Signals:
        signum = await self._iterator.__anext__()
        return Signals(signum)


#
# Testing and debugging
#


class TestRunner(abc.TestRunner):
    def __init__(self, **options: Any) -> None:
        from queue import Queue

        self._call_queue: Queue[Callable[[], object]] = Queue()
        self._send_stream: MemoryObjectSendStream | None = None
        self._options = options

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        if self._send_stream:
            self._send_stream.close()
            while self._send_stream is not None:
                self._call_queue.get()()

    async def _run_tests_and_fixtures(self) -> None:
        self._send_stream, receive_stream = create_memory_object_stream(1)
        with receive_stream:
            async for coro, outcome_holder in receive_stream:
                try:
                    retval = await coro
                except BaseException as exc:
                    outcome_holder.append(Error(exc))
                else:
                    outcome_holder.append(Value(retval))

    def _main_task_finished(self, outcome: object) -> None:
        self._send_stream = None

    def _call_in_runner_task(
        self,
        func: Callable[P, Awaitable[T_Retval]],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> T_Retval:
        if self._send_stream is None:
            trio.lowlevel.start_guest_run(
                self._run_tests_and_fixtures,
                run_sync_soon_threadsafe=self._call_queue.put,
                done_callback=self._main_task_finished,
                **self._options,
            )
            while self._send_stream is None:
                self._call_queue.get()()

        outcome_holder: list[Outcome] = []
        self._send_stream.send_nowait((func(*args, **kwargs), outcome_holder))
        while not outcome_holder:
            self._call_queue.get()()

        return outcome_holder[0].unwrap()

    def run_asyncgen_fixture(
        self,
        fixture_func: Callable[..., AsyncGenerator[T_Retval, Any]],
        kwargs: dict[str, Any],
    ) -> Iterable[T_Retval]:
        asyncgen = fixture_func(**kwargs)
        fixturevalue: T_Retval = self._call_in_runner_task(asyncgen.asend, None)

        yield fixturevalue

        try:
            self._call_in_runner_task(asyncgen.asend, None)
        except StopAsyncIteration:
            pass
        else:
            self._call_in_runner_task(asyncgen.aclose)
            raise RuntimeError("Async generator fixture did not stop")

    def run_fixture(
        self,
        fixture_func: Callable[..., Coroutine[Any, Any, T_Retval]],
        kwargs: dict[str, Any],
    ) -> T_Retval:
        return self._call_in_runner_task(fixture_func, **kwargs)

    def run_test(
        self, test_func: Callable[..., Coroutine[Any, Any, Any]], kwargs: dict[str, Any]
    ) -> None:
        self._call_in_runner_task(test_func, **kwargs)


class TrioTaskInfo(TaskInfo):
    def __init__(self, task: trio.lowlevel.Task):
        parent_id = None
        if task.parent_nursery and task.parent_nursery.parent_task:
            parent_id = id(task.parent_nursery.parent_task)

        super().__init__(id(task), parent_id, task.name, task.coro)
        self._task = weakref.proxy(task)

    def has_pending_cancellation(self) -> bool:
        try:
            return self._task._cancel_status.effectively_cancelled
        except ReferenceError:
            # If the task is no longer around, it surely doesn't have a cancellation
            # pending
            return False


class TrioBackend(AsyncBackend):
    @classmethod
    def run(
        cls,
        func: Callable[[Unpack[PosArgsT]], Awaitable[T_Retval]],
        args: tuple[Unpack[PosArgsT]],
        kwargs: dict[str, Any],
        options: dict[str, Any],
    ) -> T_Retval:
        return trio.run(func, *args)

    @classmethod
    def current_token(cls) -> object:
        return trio.lowlevel.current_trio_token()

    @classmethod
    def current_time(cls) -> float:
        return trio.current_time()

    @classmethod
    def cancelled_exception_class(cls) -> type[BaseException]:
        return trio.Cancelled

    @classmethod
    async def checkpoint(cls) -> None:
        await trio.lowlevel.checkpoint()

    @classmethod
    async def checkpoint_if_cancelled(cls) -> None:
        await trio.lowlevel.checkpoint_if_cancelled()

    @classmethod
    async def cancel_shielded_checkpoint(cls) -> None:
        await trio.lowlevel.cancel_shielded_checkpoint()

    @classmethod
    async def sleep(cls, delay: float) -> None:
        await trio.sleep(delay)

    @classmethod
    def create_cancel_scope(
        cls, *, deadline: float = math.inf, shield: bool = False
    ) -> abc.CancelScope:
        return CancelScope(deadline=deadline, shield=shield)

    @classmethod
    def current_effective_deadline(cls) -> float:
        return trio.current_effective_deadline()

    @classmethod
    def create_task_group(cls) -> abc.TaskGroup:
        return TaskGroup()

    @classmethod
    def create_event(cls) -> abc.Event:
        return Event()

    @classmethod
    def create_lock(cls, *, fast_acquire: bool) -> Lock:
        return Lock(fast_acquire=fast_acquire)

    @classmethod
    def create_semaphore(
        cls,
        initial_value: int,
        *,
        max_value: int | None = None,
        fast_acquire: bool = False,
    ) -> abc.Semaphore:
        return Semaphore(initial_value, max_value=max_value, fast_acquire=fast_acquire)

    @classmethod
    def create_capacity_limiter(cls, total_tokens: float) -> CapacityLimiter:
        return CapacityLimiter(total_tokens)

    @classmethod
    async def run_sync_in_worker_thread(
        cls,
        func: Callable[[Unpack[PosArgsT]], T_Retval],
        args: tuple[Unpack[PosArgsT]],
        abandon_on_cancel: bool = False,
        limiter: abc.CapacityLimiter | None = None,
    ) -> T_Retval:
        def wrapper() -> T_Retval:
            with claim_worker_thread(TrioBackend, token):
                return func(*args)

        token = TrioBackend.current_token()
        return await run_sync(
            wrapper,
            abandon_on_cancel=abandon_on_cancel,
            limiter=cast(trio.CapacityLimiter, limiter),
        )

    @classmethod
    def check_cancelled(cls) -> None:
        trio.from_thread.check_cancelled()

    @classmethod
    def run_async_from_thread(
        cls,
        func: Callable[[Unpack[PosArgsT]], Awaitable[T_Retval]],
        args: tuple[Unpack[PosArgsT]],
        token: object,
    ) -> T_Retval:
        return trio.from_thread.run(func, *args)

    @classmethod
    def run_sync_from_thread(
        cls,
        func: Callable[[Unpack[PosArgsT]], T_Retval],
        args: tuple[Unpack[PosArgsT]],
        token: object,
    ) -> T_Retval:
        return trio.from_thread.run_sync(func, *args)

    @classmethod
    def create_blocking_portal(cls) -> abc.BlockingPortal:
        return BlockingPortal()

    @classmethod
    async def open_process(
        cls,
        command: StrOrBytesPath | Sequence[StrOrBytesPath],
        *,
        stdin: int | IO[Any] | None,
        stdout: int | IO[Any] | None,
        stderr: int | IO[Any] | None,
        **kwargs: Any,
    ) -> Process:
        def convert_item(item: StrOrBytesPath) -> str:
            str_or_bytes = os.fspath(item)
            if isinstance(str_or_bytes, str):
                return str_or_bytes
            else:
                return os.fsdecode(str_or_bytes)

        if isinstance(command, (str, bytes, PathLike)):
            process = await trio.lowlevel.open_process(
                convert_item(command),
                stdin=stdin,
                stdout=stdout,
                stderr=stderr,
                shell=True,
                **kwargs,
            )
        else:
            process = await trio.lowlevel.open_process(
                [convert_item(item) for item in command],
                stdin=stdin,
                stdout=stdout,
                stderr=stderr,
                shell=False,
                **kwargs,
            )

        stdin_stream = SendStreamWrapper(process.stdin) if process.stdin else None
        stdout_stream = ReceiveStreamWrapper(process.stdout) if process.stdout else None
        stderr_stream = ReceiveStreamWrapper(process.stderr) if process.stderr else None
        return Process(process, stdin_stream, stdout_stream, stderr_stream)

    @classmethod
    def setup_process_pool_exit_at_shutdown(cls, workers: set[abc.Process]) -> None:
        trio.lowlevel.spawn_system_task(_shutdown_process_pool, workers)

    @classmethod
    async def connect_tcp(
        cls, host: str, port: int, local_address: IPSockAddrType | None = None
    ) -> SocketStream:
        family = socket.AF_INET6 if ":" in host else socket.AF_INET
        trio_socket = trio.socket.socket(family)
        trio_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        if local_address:
            await trio_socket.bind(local_address)

        try:
            await trio_socket.connect((host, port))
        except BaseException:
            trio_socket.close()
            raise

        return SocketStream(trio_socket)

    @classmethod
    async def connect_unix(cls, path: str | bytes) -> abc.UNIXSocketStream:
        trio_socket = trio.socket.socket(socket.AF_UNIX)
        try:
            await trio_socket.connect(path)
        except BaseException:
            trio_socket.close()
            raise

        return UNIXSocketStream(trio_socket)

    @classmethod
    def create_tcp_listener(cls, sock: socket.socket) -> abc.SocketListener:
        return TCPSocketListener(sock)

    @classmethod
    def create_unix_listener(cls, sock: socket.socket) -> abc.SocketListener:
        return UNIXSocketListener(sock)

    @classmethod
    async def create_udp_socket(
        cls,
        family: socket.AddressFamily,
        local_address: IPSockAddrType | None,
        remote_address: IPSockAddrType | None,
        reuse_port: bool,
    ) -> UDPSocket | ConnectedUDPSocket:
        trio_socket = trio.socket.socket(family=family, type=socket.SOCK_DGRAM)

        if reuse_port:
            trio_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

        if local_address:
            await trio_socket.bind(local_address)

        if remote_address:
            await trio_socket.connect(remote_address)
            return ConnectedUDPSocket(trio_socket)
        else:
            return UDPSocket(trio_socket)

    @classmethod
    @overload
    async def create_unix_datagram_socket(
        cls, raw_socket: socket.socket, remote_path: None
    ) -> abc.UNIXDatagramSocket: ...

    @classmethod
    @overload
    async def create_unix_datagram_socket(
        cls, raw_socket: socket.socket, remote_path: str | bytes
    ) -> abc.ConnectedUNIXDatagramSocket: ...

    @classmethod
    async def create_unix_datagram_socket(
        cls, raw_socket: socket.socket, remote_path: str | bytes | None
    ) -> abc.UNIXDatagramSocket | abc.ConnectedUNIXDatagramSocket:
        trio_socket = trio.socket.from_stdlib_socket(raw_socket)

        if remote_path:
            await trio_socket.connect(remote_path)
            return ConnectedUNIXDatagramSocket(trio_socket)
        else:
            return UNIXDatagramSocket(trio_socket)

    @classmethod
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
        return await trio.socket.getaddrinfo(host, port, family, type, proto, flags)

    @classmethod
    async def getnameinfo(
        cls, sockaddr: IPSockAddrType, flags: int = 0
    ) -> tuple[str, str]:
        return await trio.socket.getnameinfo(sockaddr, flags)

    @classmethod
    async def wait_socket_readable(cls, sock: socket.socket) -> None:
        try:
            await wait_readable(sock)
        except trio.ClosedResourceError as exc:
            raise ClosedResourceError().with_traceback(exc.__traceback__) from None
        except trio.BusyResourceError:
            raise BusyResourceError("reading from") from None

    @classmethod
    async def wait_socket_writable(cls, sock: socket.socket) -> None:
        try:
            await wait_writable(sock)
        except trio.ClosedResourceError as exc:
            raise ClosedResourceError().with_traceback(exc.__traceback__) from None
        except trio.BusyResourceError:
            raise BusyResourceError("writing to") from None

    @classmethod
    def current_default_thread_limiter(cls) -> CapacityLimiter:
        try:
            return _capacity_limiter_wrapper.get()
        except LookupError:
            limiter = CapacityLimiter(
                original=trio.to_thread.current_default_thread_limiter()
            )
            _capacity_limiter_wrapper.set(limiter)
            return limiter

    @classmethod
    def open_signal_receiver(
        cls, *signals: Signals
    ) -> AbstractContextManager[AsyncIterator[Signals]]:
        return _SignalReceiver(signals)

    @classmethod
    def get_current_task(cls) -> TaskInfo:
        task = current_task()
        return TrioTaskInfo(task)

    @classmethod
    def get_running_tasks(cls) -> Sequence[TaskInfo]:
        root_task = current_root_task()
        assert root_task
        task_infos = [TrioTaskInfo(root_task)]
        nurseries = root_task.child_nurseries
        while nurseries:
            new_nurseries: list[trio.Nursery] = []
            for nursery in nurseries:
                for task in nursery.child_tasks:
                    task_infos.append(TrioTaskInfo(task))
                    new_nurseries.extend(task.child_nurseries)

            nurseries = new_nurseries

        return task_infos

    @classmethod
    async def wait_all_tasks_blocked(cls) -> None:
        from trio.testing import wait_all_tasks_blocked

        await wait_all_tasks_blocked()

    @classmethod
    def create_test_runner(cls, options: dict[str, Any]) -> TestRunner:
        return TestRunner(**options)


backend_class = TrioBackend
