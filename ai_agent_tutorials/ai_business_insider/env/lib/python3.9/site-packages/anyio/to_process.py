from __future__ import annotations

import os
import pickle
import subprocess
import sys
from collections import deque
from collections.abc import Callable
from importlib.util import module_from_spec, spec_from_file_location
from typing import TypeVar, cast

from ._core._eventloop import current_time, get_async_backend, get_cancelled_exc_class
from ._core._exceptions import BrokenWorkerProcess
from ._core._subprocesses import open_process
from ._core._synchronization import CapacityLimiter
from ._core._tasks import CancelScope, fail_after
from .abc import ByteReceiveStream, ByteSendStream, Process
from .lowlevel import RunVar, checkpoint_if_cancelled
from .streams.buffered import BufferedByteReceiveStream

if sys.version_info >= (3, 11):
    from typing import TypeVarTuple, Unpack
else:
    from typing_extensions import TypeVarTuple, Unpack

WORKER_MAX_IDLE_TIME = 300  # 5 minutes

T_Retval = TypeVar("T_Retval")
PosArgsT = TypeVarTuple("PosArgsT")

_process_pool_workers: RunVar[set[Process]] = RunVar("_process_pool_workers")
_process_pool_idle_workers: RunVar[deque[tuple[Process, float]]] = RunVar(
    "_process_pool_idle_workers"
)
_default_process_limiter: RunVar[CapacityLimiter] = RunVar("_default_process_limiter")


async def run_sync(
    func: Callable[[Unpack[PosArgsT]], T_Retval],
    *args: Unpack[PosArgsT],
    cancellable: bool = False,
    limiter: CapacityLimiter | None = None,
) -> T_Retval:
    """
    Call the given function with the given arguments in a worker process.

    If the ``cancellable`` option is enabled and the task waiting for its completion is
    cancelled, the worker process running it will be abruptly terminated using SIGKILL
    (or ``terminateProcess()`` on Windows).

    :param func: a callable
    :param args: positional arguments for the callable
    :param cancellable: ``True`` to allow cancellation of the operation while it's
        running
    :param limiter: capacity limiter to use to limit the total amount of processes
        running (if omitted, the default limiter is used)
    :return: an awaitable that yields the return value of the function.

    """

    async def send_raw_command(pickled_cmd: bytes) -> object:
        try:
            await stdin.send(pickled_cmd)
            response = await buffered.receive_until(b"\n", 50)
            status, length = response.split(b" ")
            if status not in (b"RETURN", b"EXCEPTION"):
                raise RuntimeError(
                    f"Worker process returned unexpected response: {response!r}"
                )

            pickled_response = await buffered.receive_exactly(int(length))
        except BaseException as exc:
            workers.discard(process)
            try:
                process.kill()
                with CancelScope(shield=True):
                    await process.aclose()
            except ProcessLookupError:
                pass

            if isinstance(exc, get_cancelled_exc_class()):
                raise
            else:
                raise BrokenWorkerProcess from exc

        retval = pickle.loads(pickled_response)
        if status == b"EXCEPTION":
            assert isinstance(retval, BaseException)
            raise retval
        else:
            return retval

    # First pickle the request before trying to reserve a worker process
    await checkpoint_if_cancelled()
    request = pickle.dumps(("run", func, args), protocol=pickle.HIGHEST_PROTOCOL)

    # If this is the first run in this event loop thread, set up the necessary variables
    try:
        workers = _process_pool_workers.get()
        idle_workers = _process_pool_idle_workers.get()
    except LookupError:
        workers = set()
        idle_workers = deque()
        _process_pool_workers.set(workers)
        _process_pool_idle_workers.set(idle_workers)
        get_async_backend().setup_process_pool_exit_at_shutdown(workers)

    async with limiter or current_default_process_limiter():
        # Pop processes from the pool (starting from the most recently used) until we
        # find one that hasn't exited yet
        process: Process
        while idle_workers:
            process, idle_since = idle_workers.pop()
            if process.returncode is None:
                stdin = cast(ByteSendStream, process.stdin)
                buffered = BufferedByteReceiveStream(
                    cast(ByteReceiveStream, process.stdout)
                )

                # Prune any other workers that have been idle for WORKER_MAX_IDLE_TIME
                # seconds or longer
                now = current_time()
                killed_processes: list[Process] = []
                while idle_workers:
                    if now - idle_workers[0][1] < WORKER_MAX_IDLE_TIME:
                        break

                    process_to_kill, idle_since = idle_workers.popleft()
                    process_to_kill.kill()
                    workers.remove(process_to_kill)
                    killed_processes.append(process_to_kill)

                with CancelScope(shield=True):
                    for killed_process in killed_processes:
                        await killed_process.aclose()

                break

            workers.remove(process)
        else:
            command = [sys.executable, "-u", "-m", __name__]
            process = await open_process(
                command, stdin=subprocess.PIPE, stdout=subprocess.PIPE
            )
            try:
                stdin = cast(ByteSendStream, process.stdin)
                buffered = BufferedByteReceiveStream(
                    cast(ByteReceiveStream, process.stdout)
                )
                with fail_after(20):
                    message = await buffered.receive(6)

                if message != b"READY\n":
                    raise BrokenWorkerProcess(
                        f"Worker process returned unexpected response: {message!r}"
                    )

                main_module_path = getattr(sys.modules["__main__"], "__file__", None)
                pickled = pickle.dumps(
                    ("init", sys.path, main_module_path),
                    protocol=pickle.HIGHEST_PROTOCOL,
                )
                await send_raw_command(pickled)
            except (BrokenWorkerProcess, get_cancelled_exc_class()):
                raise
            except BaseException as exc:
                process.kill()
                raise BrokenWorkerProcess(
                    "Error during worker process initialization"
                ) from exc

            workers.add(process)

        with CancelScope(shield=not cancellable):
            try:
                return cast(T_Retval, await send_raw_command(request))
            finally:
                if process in workers:
                    idle_workers.append((process, current_time()))


def current_default_process_limiter() -> CapacityLimiter:
    """
    Return the capacity limiter that is used by default to limit the number of worker
    processes.

    :return: a capacity limiter object

    """
    try:
        return _default_process_limiter.get()
    except LookupError:
        limiter = CapacityLimiter(os.cpu_count() or 2)
        _default_process_limiter.set(limiter)
        return limiter


def process_worker() -> None:
    # Redirect standard streams to os.devnull so that user code won't interfere with the
    # parent-worker communication
    stdin = sys.stdin
    stdout = sys.stdout
    sys.stdin = open(os.devnull)
    sys.stdout = open(os.devnull, "w")

    stdout.buffer.write(b"READY\n")
    while True:
        retval = exception = None
        try:
            command, *args = pickle.load(stdin.buffer)
        except EOFError:
            return
        except BaseException as exc:
            exception = exc
        else:
            if command == "run":
                func, args = args
                try:
                    retval = func(*args)
                except BaseException as exc:
                    exception = exc
            elif command == "init":
                main_module_path: str | None
                sys.path, main_module_path = args
                del sys.modules["__main__"]
                if main_module_path and os.path.isfile(main_module_path):
                    # Load the parent's main module but as __mp_main__ instead of
                    # __main__ (like multiprocessing does) to avoid infinite recursion
                    try:
                        spec = spec_from_file_location("__mp_main__", main_module_path)
                        if spec and spec.loader:
                            main = module_from_spec(spec)
                            spec.loader.exec_module(main)
                            sys.modules["__main__"] = main
                    except BaseException as exc:
                        exception = exc
        try:
            if exception is not None:
                status = b"EXCEPTION"
                pickled = pickle.dumps(exception, pickle.HIGHEST_PROTOCOL)
            else:
                status = b"RETURN"
                pickled = pickle.dumps(retval, pickle.HIGHEST_PROTOCOL)
        except BaseException as exc:
            exception = exc
            status = b"EXCEPTION"
            pickled = pickle.dumps(exc, pickle.HIGHEST_PROTOCOL)

        stdout.buffer.write(b"%s %d\n" % (status, len(pickled)))
        stdout.buffer.write(pickled)

        # Respect SIGTERM
        if isinstance(exception, SystemExit):
            raise exception


if __name__ == "__main__":
    process_worker()
