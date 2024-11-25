from __future__ import annotations

import math
from typing import TypeVar
from warnings import warn

from ..streams.memory import (
    MemoryObjectReceiveStream,
    MemoryObjectSendStream,
    MemoryObjectStreamState,
)

T_Item = TypeVar("T_Item")


class create_memory_object_stream(
    tuple[MemoryObjectSendStream[T_Item], MemoryObjectReceiveStream[T_Item]],
):
    """
    Create a memory object stream.

    The stream's item type can be annotated like
    :func:`create_memory_object_stream[T_Item]`.

    :param max_buffer_size: number of items held in the buffer until ``send()`` starts
        blocking
    :param item_type: old way of marking the streams with the right generic type for
        static typing (does nothing on AnyIO 4)

        .. deprecated:: 4.0
          Use ``create_memory_object_stream[YourItemType](...)`` instead.
    :return: a tuple of (send stream, receive stream)

    """

    def __new__(  # type: ignore[misc]
        cls, max_buffer_size: float = 0, item_type: object = None
    ) -> tuple[MemoryObjectSendStream[T_Item], MemoryObjectReceiveStream[T_Item]]:
        if max_buffer_size != math.inf and not isinstance(max_buffer_size, int):
            raise ValueError("max_buffer_size must be either an integer or math.inf")
        if max_buffer_size < 0:
            raise ValueError("max_buffer_size cannot be negative")
        if item_type is not None:
            warn(
                "The item_type argument has been deprecated in AnyIO 4.0. "
                "Use create_memory_object_stream[YourItemType](...) instead.",
                DeprecationWarning,
                stacklevel=2,
            )

        state = MemoryObjectStreamState[T_Item](max_buffer_size)
        return (MemoryObjectSendStream(state), MemoryObjectReceiveStream(state))
