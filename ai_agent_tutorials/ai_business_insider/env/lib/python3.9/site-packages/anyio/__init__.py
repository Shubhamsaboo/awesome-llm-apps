from __future__ import annotations

from ._core._eventloop import current_time as current_time
from ._core._eventloop import get_all_backends as get_all_backends
from ._core._eventloop import get_cancelled_exc_class as get_cancelled_exc_class
from ._core._eventloop import run as run
from ._core._eventloop import sleep as sleep
from ._core._eventloop import sleep_forever as sleep_forever
from ._core._eventloop import sleep_until as sleep_until
from ._core._exceptions import BrokenResourceError as BrokenResourceError
from ._core._exceptions import BrokenWorkerProcess as BrokenWorkerProcess
from ._core._exceptions import BusyResourceError as BusyResourceError
from ._core._exceptions import ClosedResourceError as ClosedResourceError
from ._core._exceptions import DelimiterNotFound as DelimiterNotFound
from ._core._exceptions import EndOfStream as EndOfStream
from ._core._exceptions import IncompleteRead as IncompleteRead
from ._core._exceptions import TypedAttributeLookupError as TypedAttributeLookupError
from ._core._exceptions import WouldBlock as WouldBlock
from ._core._fileio import AsyncFile as AsyncFile
from ._core._fileio import Path as Path
from ._core._fileio import open_file as open_file
from ._core._fileio import wrap_file as wrap_file
from ._core._resources import aclose_forcefully as aclose_forcefully
from ._core._signals import open_signal_receiver as open_signal_receiver
from ._core._sockets import connect_tcp as connect_tcp
from ._core._sockets import connect_unix as connect_unix
from ._core._sockets import create_connected_udp_socket as create_connected_udp_socket
from ._core._sockets import (
    create_connected_unix_datagram_socket as create_connected_unix_datagram_socket,
)
from ._core._sockets import create_tcp_listener as create_tcp_listener
from ._core._sockets import create_udp_socket as create_udp_socket
from ._core._sockets import create_unix_datagram_socket as create_unix_datagram_socket
from ._core._sockets import create_unix_listener as create_unix_listener
from ._core._sockets import getaddrinfo as getaddrinfo
from ._core._sockets import getnameinfo as getnameinfo
from ._core._sockets import wait_socket_readable as wait_socket_readable
from ._core._sockets import wait_socket_writable as wait_socket_writable
from ._core._streams import create_memory_object_stream as create_memory_object_stream
from ._core._subprocesses import open_process as open_process
from ._core._subprocesses import run_process as run_process
from ._core._synchronization import CapacityLimiter as CapacityLimiter
from ._core._synchronization import (
    CapacityLimiterStatistics as CapacityLimiterStatistics,
)
from ._core._synchronization import Condition as Condition
from ._core._synchronization import ConditionStatistics as ConditionStatistics
from ._core._synchronization import Event as Event
from ._core._synchronization import EventStatistics as EventStatistics
from ._core._synchronization import Lock as Lock
from ._core._synchronization import LockStatistics as LockStatistics
from ._core._synchronization import ResourceGuard as ResourceGuard
from ._core._synchronization import Semaphore as Semaphore
from ._core._synchronization import SemaphoreStatistics as SemaphoreStatistics
from ._core._tasks import TASK_STATUS_IGNORED as TASK_STATUS_IGNORED
from ._core._tasks import CancelScope as CancelScope
from ._core._tasks import create_task_group as create_task_group
from ._core._tasks import current_effective_deadline as current_effective_deadline
from ._core._tasks import fail_after as fail_after
from ._core._tasks import move_on_after as move_on_after
from ._core._testing import TaskInfo as TaskInfo
from ._core._testing import get_current_task as get_current_task
from ._core._testing import get_running_tasks as get_running_tasks
from ._core._testing import wait_all_tasks_blocked as wait_all_tasks_blocked
from ._core._typedattr import TypedAttributeProvider as TypedAttributeProvider
from ._core._typedattr import TypedAttributeSet as TypedAttributeSet
from ._core._typedattr import typed_attribute as typed_attribute

# Re-export imports so they look like they live directly in this package
for __value in list(locals().values()):
    if getattr(__value, "__module__", "").startswith("anyio."):
        __value.__module__ = __name__

del __value
