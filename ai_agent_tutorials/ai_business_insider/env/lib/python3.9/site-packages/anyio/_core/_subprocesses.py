from __future__ import annotations

import sys
from collections.abc import AsyncIterable, Iterable, Mapping, Sequence
from io import BytesIO
from os import PathLike
from subprocess import DEVNULL, PIPE, CalledProcessError, CompletedProcess
from typing import IO, Any, Union, cast

from ..abc import Process
from ._eventloop import get_async_backend
from ._tasks import create_task_group

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias

StrOrBytesPath: TypeAlias = Union[str, bytes, "PathLike[str]", "PathLike[bytes]"]


async def run_process(
    command: StrOrBytesPath | Sequence[StrOrBytesPath],
    *,
    input: bytes | None = None,
    stdout: int | IO[Any] | None = PIPE,
    stderr: int | IO[Any] | None = PIPE,
    check: bool = True,
    cwd: StrOrBytesPath | None = None,
    env: Mapping[str, str] | None = None,
    startupinfo: Any = None,
    creationflags: int = 0,
    start_new_session: bool = False,
    pass_fds: Sequence[int] = (),
    user: str | int | None = None,
    group: str | int | None = None,
    extra_groups: Iterable[str | int] | None = None,
    umask: int = -1,
) -> CompletedProcess[bytes]:
    """
    Run an external command in a subprocess and wait until it completes.

    .. seealso:: :func:`subprocess.run`

    :param command: either a string to pass to the shell, or an iterable of strings
        containing the executable name or path and its arguments
    :param input: bytes passed to the standard input of the subprocess
    :param stdout: one of :data:`subprocess.PIPE`, :data:`subprocess.DEVNULL`,
        a file-like object, or `None`
    :param stderr: one of :data:`subprocess.PIPE`, :data:`subprocess.DEVNULL`,
        :data:`subprocess.STDOUT`, a file-like object, or `None`
    :param check: if ``True``, raise :exc:`~subprocess.CalledProcessError` if the
        process terminates with a return code other than 0
    :param cwd: If not ``None``, change the working directory to this before running the
        command
    :param env: if not ``None``, this mapping replaces the inherited environment
        variables from the parent process
    :param startupinfo: an instance of :class:`subprocess.STARTUPINFO` that can be used
        to specify process startup parameters (Windows only)
    :param creationflags: flags that can be used to control the creation of the
        subprocess (see :class:`subprocess.Popen` for the specifics)
    :param start_new_session: if ``true`` the setsid() system call will be made in the
        child process prior to the execution of the subprocess. (POSIX only)
    :param pass_fds: sequence of file descriptors to keep open between the parent and
        child processes. (POSIX only)
    :param user: effective user to run the process as (Python >= 3.9, POSIX only)
    :param group: effective group to run the process as (Python >= 3.9, POSIX only)
    :param extra_groups: supplementary groups to set in the subprocess (Python >= 3.9,
        POSIX only)
    :param umask: if not negative, this umask is applied in the child process before
        running the given command (Python >= 3.9, POSIX only)
    :return: an object representing the completed process
    :raises ~subprocess.CalledProcessError: if ``check`` is ``True`` and the process
        exits with a nonzero return code

    """

    async def drain_stream(stream: AsyncIterable[bytes], index: int) -> None:
        buffer = BytesIO()
        async for chunk in stream:
            buffer.write(chunk)

        stream_contents[index] = buffer.getvalue()

    async with await open_process(
        command,
        stdin=PIPE if input else DEVNULL,
        stdout=stdout,
        stderr=stderr,
        cwd=cwd,
        env=env,
        startupinfo=startupinfo,
        creationflags=creationflags,
        start_new_session=start_new_session,
        pass_fds=pass_fds,
        user=user,
        group=group,
        extra_groups=extra_groups,
        umask=umask,
    ) as process:
        stream_contents: list[bytes | None] = [None, None]
        async with create_task_group() as tg:
            if process.stdout:
                tg.start_soon(drain_stream, process.stdout, 0)

            if process.stderr:
                tg.start_soon(drain_stream, process.stderr, 1)

            if process.stdin and input:
                await process.stdin.send(input)
                await process.stdin.aclose()

            await process.wait()

    output, errors = stream_contents
    if check and process.returncode != 0:
        raise CalledProcessError(cast(int, process.returncode), command, output, errors)

    return CompletedProcess(command, cast(int, process.returncode), output, errors)


async def open_process(
    command: StrOrBytesPath | Sequence[StrOrBytesPath],
    *,
    stdin: int | IO[Any] | None = PIPE,
    stdout: int | IO[Any] | None = PIPE,
    stderr: int | IO[Any] | None = PIPE,
    cwd: StrOrBytesPath | None = None,
    env: Mapping[str, str] | None = None,
    startupinfo: Any = None,
    creationflags: int = 0,
    start_new_session: bool = False,
    pass_fds: Sequence[int] = (),
    user: str | int | None = None,
    group: str | int | None = None,
    extra_groups: Iterable[str | int] | None = None,
    umask: int = -1,
) -> Process:
    """
    Start an external command in a subprocess.

    .. seealso:: :class:`subprocess.Popen`

    :param command: either a string to pass to the shell, or an iterable of strings
        containing the executable name or path and its arguments
    :param stdin: one of :data:`subprocess.PIPE`, :data:`subprocess.DEVNULL`, a
        file-like object, or ``None``
    :param stdout: one of :data:`subprocess.PIPE`, :data:`subprocess.DEVNULL`,
        a file-like object, or ``None``
    :param stderr: one of :data:`subprocess.PIPE`, :data:`subprocess.DEVNULL`,
        :data:`subprocess.STDOUT`, a file-like object, or ``None``
    :param cwd: If not ``None``, the working directory is changed before executing
    :param env: If env is not ``None``, it must be a mapping that defines the
        environment variables for the new process
    :param creationflags: flags that can be used to control the creation of the
        subprocess (see :class:`subprocess.Popen` for the specifics)
    :param startupinfo: an instance of :class:`subprocess.STARTUPINFO` that can be used
        to specify process startup parameters (Windows only)
    :param start_new_session: if ``true`` the setsid() system call will be made in the
        child process prior to the execution of the subprocess. (POSIX only)
    :param pass_fds: sequence of file descriptors to keep open between the parent and
        child processes. (POSIX only)
    :param user: effective user to run the process as (POSIX only)
    :param group: effective group to run the process as (POSIX only)
    :param extra_groups: supplementary groups to set in the subprocess (POSIX only)
    :param umask: if not negative, this umask is applied in the child process before
        running the given command (POSIX only)
    :return: an asynchronous process object

    """
    kwargs: dict[str, Any] = {}
    if user is not None:
        kwargs["user"] = user

    if group is not None:
        kwargs["group"] = group

    if extra_groups is not None:
        kwargs["extra_groups"] = group

    if umask >= 0:
        kwargs["umask"] = umask

    return await get_async_backend().open_process(
        command,
        stdin=stdin,
        stdout=stdout,
        stderr=stderr,
        cwd=cwd,
        env=env,
        startupinfo=startupinfo,
        creationflags=creationflags,
        start_new_session=start_new_session,
        pass_fds=pass_fds,
        **kwargs,
    )
