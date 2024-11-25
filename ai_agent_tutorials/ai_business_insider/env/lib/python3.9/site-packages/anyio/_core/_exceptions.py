from __future__ import annotations

import sys
from collections.abc import Generator

if sys.version_info < (3, 11):
    from exceptiongroup import BaseExceptionGroup


class BrokenResourceError(Exception):
    """
    Raised when trying to use a resource that has been rendered unusable due to external
    causes (e.g. a send stream whose peer has disconnected).
    """


class BrokenWorkerProcess(Exception):
    """
    Raised by :func:`run_sync_in_process` if the worker process terminates abruptly or
    otherwise misbehaves.
    """


class BusyResourceError(Exception):
    """
    Raised when two tasks are trying to read from or write to the same resource
    concurrently.
    """

    def __init__(self, action: str):
        super().__init__(f"Another task is already {action} this resource")


class ClosedResourceError(Exception):
    """Raised when trying to use a resource that has been closed."""


class DelimiterNotFound(Exception):
    """
    Raised during
    :meth:`~anyio.streams.buffered.BufferedByteReceiveStream.receive_until` if the
    maximum number of bytes has been read without the delimiter being found.
    """

    def __init__(self, max_bytes: int) -> None:
        super().__init__(
            f"The delimiter was not found among the first {max_bytes} bytes"
        )


class EndOfStream(Exception):
    """
    Raised when trying to read from a stream that has been closed from the other end.
    """


class IncompleteRead(Exception):
    """
    Raised during
    :meth:`~anyio.streams.buffered.BufferedByteReceiveStream.receive_exactly` or
    :meth:`~anyio.streams.buffered.BufferedByteReceiveStream.receive_until` if the
    connection is closed before the requested amount of bytes has been read.
    """

    def __init__(self) -> None:
        super().__init__(
            "The stream was closed before the read operation could be completed"
        )


class TypedAttributeLookupError(LookupError):
    """
    Raised by :meth:`~anyio.TypedAttributeProvider.extra` when the given typed attribute
    is not found and no default value has been given.
    """


class WouldBlock(Exception):
    """Raised by ``X_nowait`` functions if ``X()`` would block."""


def iterate_exceptions(
    exception: BaseException,
) -> Generator[BaseException, None, None]:
    if isinstance(exception, BaseExceptionGroup):
        for exc in exception.exceptions:
            yield from iterate_exceptions(exc)
    else:
        yield exception
