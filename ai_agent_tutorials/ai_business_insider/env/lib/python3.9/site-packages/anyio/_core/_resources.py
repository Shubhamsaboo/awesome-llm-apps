from __future__ import annotations

from ..abc import AsyncResource
from ._tasks import CancelScope


async def aclose_forcefully(resource: AsyncResource) -> None:
    """
    Close an asynchronous resource in a cancelled scope.

    Doing this closes the resource without waiting on anything.

    :param resource: the resource to close

    """
    with CancelScope() as scope:
        scope.cancel()
        await resource.aclose()
