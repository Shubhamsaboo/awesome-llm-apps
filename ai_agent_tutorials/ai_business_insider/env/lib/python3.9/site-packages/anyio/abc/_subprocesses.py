from __future__ import annotations

from abc import abstractmethod
from signal import Signals

from ._resources import AsyncResource
from ._streams import ByteReceiveStream, ByteSendStream


class Process(AsyncResource):
    """An asynchronous version of :class:`subprocess.Popen`."""

    @abstractmethod
    async def wait(self) -> int:
        """
        Wait until the process exits.

        :return: the exit code of the process
        """

    @abstractmethod
    def terminate(self) -> None:
        """
        Terminates the process, gracefully if possible.

        On Windows, this calls ``TerminateProcess()``.
        On POSIX systems, this sends ``SIGTERM`` to the process.

        .. seealso:: :meth:`subprocess.Popen.terminate`
        """

    @abstractmethod
    def kill(self) -> None:
        """
        Kills the process.

        On Windows, this calls ``TerminateProcess()``.
        On POSIX systems, this sends ``SIGKILL`` to the process.

        .. seealso:: :meth:`subprocess.Popen.kill`
        """

    @abstractmethod
    def send_signal(self, signal: Signals) -> None:
        """
        Send a signal to the subprocess.

        .. seealso:: :meth:`subprocess.Popen.send_signal`

        :param signal: the signal number (e.g. :data:`signal.SIGHUP`)
        """

    @property
    @abstractmethod
    def pid(self) -> int:
        """The process ID of the process."""

    @property
    @abstractmethod
    def returncode(self) -> int | None:
        """
        The return code of the process. If the process has not yet terminated, this will
        be ``None``.
        """

    @property
    @abstractmethod
    def stdin(self) -> ByteSendStream | None:
        """The stream for the standard input of the process."""

    @property
    @abstractmethod
    def stdout(self) -> ByteReceiveStream | None:
        """The stream for the standard output of the process."""

    @property
    @abstractmethod
    def stderr(self) -> ByteReceiveStream | None:
        """The stream for the standard error output of the process."""
