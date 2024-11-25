from __future__ import annotations

from collections.abc import Awaitable, Generator
from typing import Any, cast

from ._eventloop import get_async_backend


class TaskInfo:
    """
    Represents an asynchronous task.

    :ivar int id: the unique identifier of the task
    :ivar parent_id: the identifier of the parent task, if any
    :vartype parent_id: Optional[int]
    :ivar str name: the description of the task (if any)
    :ivar ~collections.abc.Coroutine coro: the coroutine object of the task
    """

    __slots__ = "_name", "id", "parent_id", "name", "coro"

    def __init__(
        self,
        id: int,
        parent_id: int | None,
        name: str | None,
        coro: Generator[Any, Any, Any] | Awaitable[Any],
    ):
        func = get_current_task
        self._name = f"{func.__module__}.{func.__qualname__}"
        self.id: int = id
        self.parent_id: int | None = parent_id
        self.name: str | None = name
        self.coro: Generator[Any, Any, Any] | Awaitable[Any] = coro

    def __eq__(self, other: object) -> bool:
        if isinstance(other, TaskInfo):
            return self.id == other.id

        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.id)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id!r}, name={self.name!r})"

    def has_pending_cancellation(self) -> bool:
        """
        Return ``True`` if the task has a cancellation pending, ``False`` otherwise.

        """
        return False


def get_current_task() -> TaskInfo:
    """
    Return the current task.

    :return: a representation of the current task

    """
    return get_async_backend().get_current_task()


def get_running_tasks() -> list[TaskInfo]:
    """
    Return a list of running tasks in the current event loop.

    :return: a list of task info objects

    """
    return cast("list[TaskInfo]", get_async_backend().get_running_tasks())


async def wait_all_tasks_blocked() -> None:
    """Wait until all other tasks are waiting for something."""
    await get_async_backend().wait_all_tasks_blocked()
