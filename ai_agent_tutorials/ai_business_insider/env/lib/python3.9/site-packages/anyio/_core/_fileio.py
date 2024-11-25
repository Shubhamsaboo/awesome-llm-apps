from __future__ import annotations

import os
import pathlib
import sys
from collections.abc import AsyncIterator, Callable, Iterable, Iterator, Sequence
from dataclasses import dataclass
from functools import partial
from os import PathLike
from typing import (
    IO,
    TYPE_CHECKING,
    Any,
    AnyStr,
    Final,
    Generic,
    overload,
)

from .. import to_thread
from ..abc import AsyncResource

if TYPE_CHECKING:
    from _typeshed import OpenBinaryMode, OpenTextMode, ReadableBuffer, WriteableBuffer
else:
    ReadableBuffer = OpenBinaryMode = OpenTextMode = WriteableBuffer = object


class AsyncFile(AsyncResource, Generic[AnyStr]):
    """
    An asynchronous file object.

    This class wraps a standard file object and provides async friendly versions of the
    following blocking methods (where available on the original file object):

    * read
    * read1
    * readline
    * readlines
    * readinto
    * readinto1
    * write
    * writelines
    * truncate
    * seek
    * tell
    * flush

    All other methods are directly passed through.

    This class supports the asynchronous context manager protocol which closes the
    underlying file at the end of the context block.

    This class also supports asynchronous iteration::

        async with await open_file(...) as f:
            async for line in f:
                print(line)
    """

    def __init__(self, fp: IO[AnyStr]) -> None:
        self._fp: Any = fp

    def __getattr__(self, name: str) -> object:
        return getattr(self._fp, name)

    @property
    def wrapped(self) -> IO[AnyStr]:
        """The wrapped file object."""
        return self._fp

    async def __aiter__(self) -> AsyncIterator[AnyStr]:
        while True:
            line = await self.readline()
            if line:
                yield line
            else:
                break

    async def aclose(self) -> None:
        return await to_thread.run_sync(self._fp.close)

    async def read(self, size: int = -1) -> AnyStr:
        return await to_thread.run_sync(self._fp.read, size)

    async def read1(self: AsyncFile[bytes], size: int = -1) -> bytes:
        return await to_thread.run_sync(self._fp.read1, size)

    async def readline(self) -> AnyStr:
        return await to_thread.run_sync(self._fp.readline)

    async def readlines(self) -> list[AnyStr]:
        return await to_thread.run_sync(self._fp.readlines)

    async def readinto(self: AsyncFile[bytes], b: WriteableBuffer) -> bytes:
        return await to_thread.run_sync(self._fp.readinto, b)

    async def readinto1(self: AsyncFile[bytes], b: WriteableBuffer) -> bytes:
        return await to_thread.run_sync(self._fp.readinto1, b)

    @overload
    async def write(self: AsyncFile[bytes], b: ReadableBuffer) -> int: ...

    @overload
    async def write(self: AsyncFile[str], b: str) -> int: ...

    async def write(self, b: ReadableBuffer | str) -> int:
        return await to_thread.run_sync(self._fp.write, b)

    @overload
    async def writelines(
        self: AsyncFile[bytes], lines: Iterable[ReadableBuffer]
    ) -> None: ...

    @overload
    async def writelines(self: AsyncFile[str], lines: Iterable[str]) -> None: ...

    async def writelines(self, lines: Iterable[ReadableBuffer] | Iterable[str]) -> None:
        return await to_thread.run_sync(self._fp.writelines, lines)

    async def truncate(self, size: int | None = None) -> int:
        return await to_thread.run_sync(self._fp.truncate, size)

    async def seek(self, offset: int, whence: int | None = os.SEEK_SET) -> int:
        return await to_thread.run_sync(self._fp.seek, offset, whence)

    async def tell(self) -> int:
        return await to_thread.run_sync(self._fp.tell)

    async def flush(self) -> None:
        return await to_thread.run_sync(self._fp.flush)


@overload
async def open_file(
    file: str | PathLike[str] | int,
    mode: OpenBinaryMode,
    buffering: int = ...,
    encoding: str | None = ...,
    errors: str | None = ...,
    newline: str | None = ...,
    closefd: bool = ...,
    opener: Callable[[str, int], int] | None = ...,
) -> AsyncFile[bytes]: ...


@overload
async def open_file(
    file: str | PathLike[str] | int,
    mode: OpenTextMode = ...,
    buffering: int = ...,
    encoding: str | None = ...,
    errors: str | None = ...,
    newline: str | None = ...,
    closefd: bool = ...,
    opener: Callable[[str, int], int] | None = ...,
) -> AsyncFile[str]: ...


async def open_file(
    file: str | PathLike[str] | int,
    mode: str = "r",
    buffering: int = -1,
    encoding: str | None = None,
    errors: str | None = None,
    newline: str | None = None,
    closefd: bool = True,
    opener: Callable[[str, int], int] | None = None,
) -> AsyncFile[Any]:
    """
    Open a file asynchronously.

    The arguments are exactly the same as for the builtin :func:`open`.

    :return: an asynchronous file object

    """
    fp = await to_thread.run_sync(
        open, file, mode, buffering, encoding, errors, newline, closefd, opener
    )
    return AsyncFile(fp)


def wrap_file(file: IO[AnyStr]) -> AsyncFile[AnyStr]:
    """
    Wrap an existing file as an asynchronous file.

    :param file: an existing file-like object
    :return: an asynchronous file object

    """
    return AsyncFile(file)


@dataclass(eq=False)
class _PathIterator(AsyncIterator["Path"]):
    iterator: Iterator[PathLike[str]]

    async def __anext__(self) -> Path:
        nextval = await to_thread.run_sync(
            next, self.iterator, None, abandon_on_cancel=True
        )
        if nextval is None:
            raise StopAsyncIteration from None

        return Path(nextval)


class Path:
    """
    An asynchronous version of :class:`pathlib.Path`.

    This class cannot be substituted for :class:`pathlib.Path` or
    :class:`pathlib.PurePath`, but it is compatible with the :class:`os.PathLike`
    interface.

    It implements the Python 3.10 version of :class:`pathlib.Path` interface, except for
    the deprecated :meth:`~pathlib.Path.link_to` method.

    Some methods may be unavailable or have limited functionality, based on the Python
    version:

    * :meth:`~pathlib.Path.from_uri` (available on Python 3.13 or later)
    * :meth:`~pathlib.Path.full_match` (available on Python 3.13 or later)
    * :meth:`~pathlib.Path.is_junction` (available on Python 3.12 or later)
    * :meth:`~pathlib.Path.match` (the ``case_sensitive`` paramater is only available on
      Python 3.13 or later)
    * :meth:`~pathlib.Path.relative_to` (the ``walk_up`` parameter is only available on
      Python 3.12 or later)
    * :meth:`~pathlib.Path.walk` (available on Python 3.12 or later)

    Any methods that do disk I/O need to be awaited on. These methods are:

    * :meth:`~pathlib.Path.absolute`
    * :meth:`~pathlib.Path.chmod`
    * :meth:`~pathlib.Path.cwd`
    * :meth:`~pathlib.Path.exists`
    * :meth:`~pathlib.Path.expanduser`
    * :meth:`~pathlib.Path.group`
    * :meth:`~pathlib.Path.hardlink_to`
    * :meth:`~pathlib.Path.home`
    * :meth:`~pathlib.Path.is_block_device`
    * :meth:`~pathlib.Path.is_char_device`
    * :meth:`~pathlib.Path.is_dir`
    * :meth:`~pathlib.Path.is_fifo`
    * :meth:`~pathlib.Path.is_file`
    * :meth:`~pathlib.Path.is_junction`
    * :meth:`~pathlib.Path.is_mount`
    * :meth:`~pathlib.Path.is_socket`
    * :meth:`~pathlib.Path.is_symlink`
    * :meth:`~pathlib.Path.lchmod`
    * :meth:`~pathlib.Path.lstat`
    * :meth:`~pathlib.Path.mkdir`
    * :meth:`~pathlib.Path.open`
    * :meth:`~pathlib.Path.owner`
    * :meth:`~pathlib.Path.read_bytes`
    * :meth:`~pathlib.Path.read_text`
    * :meth:`~pathlib.Path.readlink`
    * :meth:`~pathlib.Path.rename`
    * :meth:`~pathlib.Path.replace`
    * :meth:`~pathlib.Path.resolve`
    * :meth:`~pathlib.Path.rmdir`
    * :meth:`~pathlib.Path.samefile`
    * :meth:`~pathlib.Path.stat`
    * :meth:`~pathlib.Path.symlink_to`
    * :meth:`~pathlib.Path.touch`
    * :meth:`~pathlib.Path.unlink`
    * :meth:`~pathlib.Path.walk`
    * :meth:`~pathlib.Path.write_bytes`
    * :meth:`~pathlib.Path.write_text`

    Additionally, the following methods return an async iterator yielding
    :class:`~.Path` objects:

    * :meth:`~pathlib.Path.glob`
    * :meth:`~pathlib.Path.iterdir`
    * :meth:`~pathlib.Path.rglob`
    """

    __slots__ = "_path", "__weakref__"

    __weakref__: Any

    def __init__(self, *args: str | PathLike[str]) -> None:
        self._path: Final[pathlib.Path] = pathlib.Path(*args)

    def __fspath__(self) -> str:
        return self._path.__fspath__()

    def __str__(self) -> str:
        return self._path.__str__()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.as_posix()!r})"

    def __bytes__(self) -> bytes:
        return self._path.__bytes__()

    def __hash__(self) -> int:
        return self._path.__hash__()

    def __eq__(self, other: object) -> bool:
        target = other._path if isinstance(other, Path) else other
        return self._path.__eq__(target)

    def __lt__(self, other: pathlib.PurePath | Path) -> bool:
        target = other._path if isinstance(other, Path) else other
        return self._path.__lt__(target)

    def __le__(self, other: pathlib.PurePath | Path) -> bool:
        target = other._path if isinstance(other, Path) else other
        return self._path.__le__(target)

    def __gt__(self, other: pathlib.PurePath | Path) -> bool:
        target = other._path if isinstance(other, Path) else other
        return self._path.__gt__(target)

    def __ge__(self, other: pathlib.PurePath | Path) -> bool:
        target = other._path if isinstance(other, Path) else other
        return self._path.__ge__(target)

    def __truediv__(self, other: str | PathLike[str]) -> Path:
        return Path(self._path / other)

    def __rtruediv__(self, other: str | PathLike[str]) -> Path:
        return Path(other) / self

    @property
    def parts(self) -> tuple[str, ...]:
        return self._path.parts

    @property
    def drive(self) -> str:
        return self._path.drive

    @property
    def root(self) -> str:
        return self._path.root

    @property
    def anchor(self) -> str:
        return self._path.anchor

    @property
    def parents(self) -> Sequence[Path]:
        return tuple(Path(p) for p in self._path.parents)

    @property
    def parent(self) -> Path:
        return Path(self._path.parent)

    @property
    def name(self) -> str:
        return self._path.name

    @property
    def suffix(self) -> str:
        return self._path.suffix

    @property
    def suffixes(self) -> list[str]:
        return self._path.suffixes

    @property
    def stem(self) -> str:
        return self._path.stem

    async def absolute(self) -> Path:
        path = await to_thread.run_sync(self._path.absolute)
        return Path(path)

    def as_posix(self) -> str:
        return self._path.as_posix()

    def as_uri(self) -> str:
        return self._path.as_uri()

    if sys.version_info >= (3, 13):
        parser = pathlib.Path.parser

        @classmethod
        def from_uri(cls, uri: str) -> Path:
            return Path(pathlib.Path.from_uri(uri))

        def full_match(
            self, path_pattern: str, *, case_sensitive: bool | None = None
        ) -> bool:
            return self._path.full_match(path_pattern, case_sensitive=case_sensitive)

        def match(
            self, path_pattern: str, *, case_sensitive: bool | None = None
        ) -> bool:
            return self._path.match(path_pattern, case_sensitive=case_sensitive)
    else:

        def match(self, path_pattern: str) -> bool:
            return self._path.match(path_pattern)

    def is_relative_to(self, other: str | PathLike[str]) -> bool:
        try:
            self.relative_to(other)
            return True
        except ValueError:
            return False

    async def chmod(self, mode: int, *, follow_symlinks: bool = True) -> None:
        func = partial(os.chmod, follow_symlinks=follow_symlinks)
        return await to_thread.run_sync(func, self._path, mode)

    @classmethod
    async def cwd(cls) -> Path:
        path = await to_thread.run_sync(pathlib.Path.cwd)
        return cls(path)

    async def exists(self) -> bool:
        return await to_thread.run_sync(self._path.exists, abandon_on_cancel=True)

    async def expanduser(self) -> Path:
        return Path(
            await to_thread.run_sync(self._path.expanduser, abandon_on_cancel=True)
        )

    def glob(self, pattern: str) -> AsyncIterator[Path]:
        gen = self._path.glob(pattern)
        return _PathIterator(gen)

    async def group(self) -> str:
        return await to_thread.run_sync(self._path.group, abandon_on_cancel=True)

    async def hardlink_to(
        self, target: str | bytes | PathLike[str] | PathLike[bytes]
    ) -> None:
        if isinstance(target, Path):
            target = target._path

        await to_thread.run_sync(os.link, target, self)

    @classmethod
    async def home(cls) -> Path:
        home_path = await to_thread.run_sync(pathlib.Path.home)
        return cls(home_path)

    def is_absolute(self) -> bool:
        return self._path.is_absolute()

    async def is_block_device(self) -> bool:
        return await to_thread.run_sync(
            self._path.is_block_device, abandon_on_cancel=True
        )

    async def is_char_device(self) -> bool:
        return await to_thread.run_sync(
            self._path.is_char_device, abandon_on_cancel=True
        )

    async def is_dir(self) -> bool:
        return await to_thread.run_sync(self._path.is_dir, abandon_on_cancel=True)

    async def is_fifo(self) -> bool:
        return await to_thread.run_sync(self._path.is_fifo, abandon_on_cancel=True)

    async def is_file(self) -> bool:
        return await to_thread.run_sync(self._path.is_file, abandon_on_cancel=True)

    if sys.version_info >= (3, 12):

        async def is_junction(self) -> bool:
            return await to_thread.run_sync(self._path.is_junction)

    async def is_mount(self) -> bool:
        return await to_thread.run_sync(
            os.path.ismount, self._path, abandon_on_cancel=True
        )

    def is_reserved(self) -> bool:
        return self._path.is_reserved()

    async def is_socket(self) -> bool:
        return await to_thread.run_sync(self._path.is_socket, abandon_on_cancel=True)

    async def is_symlink(self) -> bool:
        return await to_thread.run_sync(self._path.is_symlink, abandon_on_cancel=True)

    def iterdir(self) -> AsyncIterator[Path]:
        gen = self._path.iterdir()
        return _PathIterator(gen)

    def joinpath(self, *args: str | PathLike[str]) -> Path:
        return Path(self._path.joinpath(*args))

    async def lchmod(self, mode: int) -> None:
        await to_thread.run_sync(self._path.lchmod, mode)

    async def lstat(self) -> os.stat_result:
        return await to_thread.run_sync(self._path.lstat, abandon_on_cancel=True)

    async def mkdir(
        self, mode: int = 0o777, parents: bool = False, exist_ok: bool = False
    ) -> None:
        await to_thread.run_sync(self._path.mkdir, mode, parents, exist_ok)

    @overload
    async def open(
        self,
        mode: OpenBinaryMode,
        buffering: int = ...,
        encoding: str | None = ...,
        errors: str | None = ...,
        newline: str | None = ...,
    ) -> AsyncFile[bytes]: ...

    @overload
    async def open(
        self,
        mode: OpenTextMode = ...,
        buffering: int = ...,
        encoding: str | None = ...,
        errors: str | None = ...,
        newline: str | None = ...,
    ) -> AsyncFile[str]: ...

    async def open(
        self,
        mode: str = "r",
        buffering: int = -1,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> AsyncFile[Any]:
        fp = await to_thread.run_sync(
            self._path.open, mode, buffering, encoding, errors, newline
        )
        return AsyncFile(fp)

    async def owner(self) -> str:
        return await to_thread.run_sync(self._path.owner, abandon_on_cancel=True)

    async def read_bytes(self) -> bytes:
        return await to_thread.run_sync(self._path.read_bytes)

    async def read_text(
        self, encoding: str | None = None, errors: str | None = None
    ) -> str:
        return await to_thread.run_sync(self._path.read_text, encoding, errors)

    if sys.version_info >= (3, 12):

        def relative_to(
            self, *other: str | PathLike[str], walk_up: bool = False
        ) -> Path:
            return Path(self._path.relative_to(*other, walk_up=walk_up))

    else:

        def relative_to(self, *other: str | PathLike[str]) -> Path:
            return Path(self._path.relative_to(*other))

    async def readlink(self) -> Path:
        target = await to_thread.run_sync(os.readlink, self._path)
        return Path(target)

    async def rename(self, target: str | pathlib.PurePath | Path) -> Path:
        if isinstance(target, Path):
            target = target._path

        await to_thread.run_sync(self._path.rename, target)
        return Path(target)

    async def replace(self, target: str | pathlib.PurePath | Path) -> Path:
        if isinstance(target, Path):
            target = target._path

        await to_thread.run_sync(self._path.replace, target)
        return Path(target)

    async def resolve(self, strict: bool = False) -> Path:
        func = partial(self._path.resolve, strict=strict)
        return Path(await to_thread.run_sync(func, abandon_on_cancel=True))

    def rglob(self, pattern: str) -> AsyncIterator[Path]:
        gen = self._path.rglob(pattern)
        return _PathIterator(gen)

    async def rmdir(self) -> None:
        await to_thread.run_sync(self._path.rmdir)

    async def samefile(self, other_path: str | PathLike[str]) -> bool:
        if isinstance(other_path, Path):
            other_path = other_path._path

        return await to_thread.run_sync(
            self._path.samefile, other_path, abandon_on_cancel=True
        )

    async def stat(self, *, follow_symlinks: bool = True) -> os.stat_result:
        func = partial(os.stat, follow_symlinks=follow_symlinks)
        return await to_thread.run_sync(func, self._path, abandon_on_cancel=True)

    async def symlink_to(
        self,
        target: str | bytes | PathLike[str] | PathLike[bytes],
        target_is_directory: bool = False,
    ) -> None:
        if isinstance(target, Path):
            target = target._path

        await to_thread.run_sync(self._path.symlink_to, target, target_is_directory)

    async def touch(self, mode: int = 0o666, exist_ok: bool = True) -> None:
        await to_thread.run_sync(self._path.touch, mode, exist_ok)

    async def unlink(self, missing_ok: bool = False) -> None:
        try:
            await to_thread.run_sync(self._path.unlink)
        except FileNotFoundError:
            if not missing_ok:
                raise

    if sys.version_info >= (3, 12):

        async def walk(
            self,
            top_down: bool = True,
            on_error: Callable[[OSError], object] | None = None,
            follow_symlinks: bool = False,
        ) -> AsyncIterator[tuple[Path, list[str], list[str]]]:
            def get_next_value() -> tuple[pathlib.Path, list[str], list[str]] | None:
                try:
                    return next(gen)
                except StopIteration:
                    return None

            gen = self._path.walk(top_down, on_error, follow_symlinks)
            while True:
                value = await to_thread.run_sync(get_next_value)
                if value is None:
                    return

                root, dirs, paths = value
                yield Path(root), dirs, paths

    def with_name(self, name: str) -> Path:
        return Path(self._path.with_name(name))

    def with_stem(self, stem: str) -> Path:
        return Path(self._path.with_name(stem + self._path.suffix))

    def with_suffix(self, suffix: str) -> Path:
        return Path(self._path.with_suffix(suffix))

    def with_segments(self, *pathsegments: str | PathLike[str]) -> Path:
        return Path(*pathsegments)

    async def write_bytes(self, data: bytes) -> int:
        return await to_thread.run_sync(self._path.write_bytes, data)

    async def write_text(
        self,
        data: str,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> int:
        # Path.write_text() does not support the "newline" parameter before Python 3.10
        def sync_write_text() -> int:
            with self._path.open(
                "w", encoding=encoding, errors=errors, newline=newline
            ) as fp:
                return fp.write(data)

        return await to_thread.run_sync(sync_write_text)


PathLike.register(Path)
