"""Top-level package for sniffio."""

__all__ = [
    "current_async_library",
    "AsyncLibraryNotFoundError",
    "current_async_library_cvar",
    "thread_local",
]

from ._version import __version__

from ._impl import (
    current_async_library,
    AsyncLibraryNotFoundError,
    current_async_library_cvar,
    thread_local,
)
