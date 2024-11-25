from __future__ import annotations

from collections.abc import Callable, Mapping
from io import SEEK_SET, UnsupportedOperation
from os import PathLike
from pathlib import Path
from typing import Any, BinaryIO, cast

from .. import (
    BrokenResourceError,
    ClosedResourceError,
    EndOfStream,
    TypedAttributeSet,
    to_thread,
    typed_attribute,
)
from ..abc import ByteReceiveStream, ByteSendStream


class FileStreamAttribute(TypedAttributeSet):
    #: the open file descriptor
    file: BinaryIO = typed_attribute()
    #: the path of the file on the file system, if available (file must be a real file)
    path: Path = typed_attribute()
    #: the file number, if available (file must be a real file or a TTY)
    fileno: int = typed_attribute()


class _BaseFileStream:
    def __init__(self, file: BinaryIO):
        self._file = file

    async def aclose(self) -> None:
        await to_thread.run_sync(self._file.close)

    @property
    def extra_attributes(self) -> Mapping[Any, Callable[[], Any]]:
        attributes: dict[Any, Callable[[], Any]] = {
            FileStreamAttribute.file: lambda: self._file,
        }

        if hasattr(self._file, "name"):
            attributes[FileStreamAttribute.path] = lambda: Path(self._file.name)

        try:
            self._file.fileno()
        except UnsupportedOperation:
            pass
        else:
            attributes[FileStreamAttribute.fileno] = lambda: self._file.fileno()

        return attributes


class FileReadStream(_BaseFileStream, ByteReceiveStream):
    """
    A byte stream that reads from a file in the file system.

    :param file: a file that has been opened for reading in binary mode

    .. versionadded:: 3.0
    """

    @classmethod
    async def from_path(cls, path: str | PathLike[str]) -> FileReadStream:
        """
        Create a file read stream by opening the given file.

        :param path: path of the file to read from

        """
        file = await to_thread.run_sync(Path(path).open, "rb")
        return cls(cast(BinaryIO, file))

    async def receive(self, max_bytes: int = 65536) -> bytes:
        try:
            data = await to_thread.run_sync(self._file.read, max_bytes)
        except ValueError:
            raise ClosedResourceError from None
        except OSError as exc:
            raise BrokenResourceError from exc

        if data:
            return data
        else:
            raise EndOfStream

    async def seek(self, position: int, whence: int = SEEK_SET) -> int:
        """
        Seek the file to the given position.

        .. seealso:: :meth:`io.IOBase.seek`

        .. note:: Not all file descriptors are seekable.

        :param position: position to seek the file to
        :param whence: controls how ``position`` is interpreted
        :return: the new absolute position
        :raises OSError: if the file is not seekable

        """
        return await to_thread.run_sync(self._file.seek, position, whence)

    async def tell(self) -> int:
        """
        Return the current stream position.

        .. note:: Not all file descriptors are seekable.

        :return: the current absolute position
        :raises OSError: if the file is not seekable

        """
        return await to_thread.run_sync(self._file.tell)


class FileWriteStream(_BaseFileStream, ByteSendStream):
    """
    A byte stream that writes to a file in the file system.

    :param file: a file that has been opened for writing in binary mode

    .. versionadded:: 3.0
    """

    @classmethod
    async def from_path(
        cls, path: str | PathLike[str], append: bool = False
    ) -> FileWriteStream:
        """
        Create a file write stream by opening the given file for writing.

        :param path: path of the file to write to
        :param append: if ``True``, open the file for appending; if ``False``, any
            existing file at the given path will be truncated

        """
        mode = "ab" if append else "wb"
        file = await to_thread.run_sync(Path(path).open, mode)
        return cls(cast(BinaryIO, file))

    async def send(self, item: bytes) -> None:
        try:
            await to_thread.run_sync(self._file.write, item)
        except ValueError:
            raise ClosedResourceError from None
        except OSError as exc:
            raise BrokenResourceError from exc
