from contextvars import ContextVar
from typing import Optional
import sys
import threading

current_async_library_cvar = ContextVar(
    "current_async_library_cvar", default=None
)  # type: ContextVar[Optional[str]]


class _ThreadLocal(threading.local):
    # Since threading.local provides no explicit mechanism is for setting
    # a default for a value, a custom class with a class attribute is used
    # instead.
    name = None  # type: Optional[str]


thread_local = _ThreadLocal()


class AsyncLibraryNotFoundError(RuntimeError):
    pass


def current_async_library() -> str:
    """Detect which async library is currently running.

    The following libraries are currently supported:

    ================   ===========  ============================
    Library             Requires     Magic string
    ================   ===========  ============================
    **Trio**            Trio v0.6+   ``"trio"``
    **Curio**           -            ``"curio"``
    **asyncio**                      ``"asyncio"``
    **Trio-asyncio**    v0.8.2+     ``"trio"`` or ``"asyncio"``,
                                    depending on current mode
    ================   ===========  ============================

    Returns:
      A string like ``"trio"``.

    Raises:
      AsyncLibraryNotFoundError: if called from synchronous context,
        or if the current async library was not recognized.

    Examples:

        .. code-block:: python3

           from sniffio import current_async_library

           async def generic_sleep(seconds):
               library = current_async_library()
               if library == "trio":
                   import trio
                   await trio.sleep(seconds)
               elif library == "asyncio":
                   import asyncio
                   await asyncio.sleep(seconds)
               # ... and so on ...
               else:
                   raise RuntimeError(f"Unsupported library {library!r}")

    """
    value = thread_local.name
    if value is not None:
        return value

    value = current_async_library_cvar.get()
    if value is not None:
        return value

    # Need to sniff for asyncio
    if "asyncio" in sys.modules:
        import asyncio
        try:
            current_task = asyncio.current_task  # type: ignore[attr-defined]
        except AttributeError:
            current_task = asyncio.Task.current_task  # type: ignore[attr-defined]
        try:
            if current_task() is not None:
                return "asyncio"
        except RuntimeError:
            pass

    # Sniff for curio (for now)
    if 'curio' in sys.modules:
        from curio.meta import curio_running
        if curio_running():
            return 'curio'

    raise AsyncLibraryNotFoundError(
        "unknown async library, or not in async context"
    )
