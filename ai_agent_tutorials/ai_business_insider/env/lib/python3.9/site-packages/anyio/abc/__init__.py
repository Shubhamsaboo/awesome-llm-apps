from __future__ import annotations

from typing import Any

from ._eventloop import AsyncBackend as AsyncBackend
from ._resources import AsyncResource as AsyncResource
from ._sockets import ConnectedUDPSocket as ConnectedUDPSocket
from ._sockets import ConnectedUNIXDatagramSocket as ConnectedUNIXDatagramSocket
from ._sockets import IPAddressType as IPAddressType
from ._sockets import IPSockAddrType as IPSockAddrType
from ._sockets import SocketAttribute as SocketAttribute
from ._sockets import SocketListener as SocketListener
from ._sockets import SocketStream as SocketStream
from ._sockets import UDPPacketType as UDPPacketType
from ._sockets import UDPSocket as UDPSocket
from ._sockets import UNIXDatagramPacketType as UNIXDatagramPacketType
from ._sockets import UNIXDatagramSocket as UNIXDatagramSocket
from ._sockets import UNIXSocketStream as UNIXSocketStream
from ._streams import AnyByteReceiveStream as AnyByteReceiveStream
from ._streams import AnyByteSendStream as AnyByteSendStream
from ._streams import AnyByteStream as AnyByteStream
from ._streams import AnyUnreliableByteReceiveStream as AnyUnreliableByteReceiveStream
from ._streams import AnyUnreliableByteSendStream as AnyUnreliableByteSendStream
from ._streams import AnyUnreliableByteStream as AnyUnreliableByteStream
from ._streams import ByteReceiveStream as ByteReceiveStream
from ._streams import ByteSendStream as ByteSendStream
from ._streams import ByteStream as ByteStream
from ._streams import Listener as Listener
from ._streams import ObjectReceiveStream as ObjectReceiveStream
from ._streams import ObjectSendStream as ObjectSendStream
from ._streams import ObjectStream as ObjectStream
from ._streams import UnreliableObjectReceiveStream as UnreliableObjectReceiveStream
from ._streams import UnreliableObjectSendStream as UnreliableObjectSendStream
from ._streams import UnreliableObjectStream as UnreliableObjectStream
from ._subprocesses import Process as Process
from ._tasks import TaskGroup as TaskGroup
from ._tasks import TaskStatus as TaskStatus
from ._testing import TestRunner as TestRunner

# Re-exported here, for backwards compatibility
# isort: off
from .._core._synchronization import (
    CapacityLimiter as CapacityLimiter,
    Condition as Condition,
    Event as Event,
    Lock as Lock,
    Semaphore as Semaphore,
)
from .._core._tasks import CancelScope as CancelScope
from ..from_thread import BlockingPortal as BlockingPortal

# Re-export imports so they look like they live directly in this package
key: str
value: Any
for key, value in list(locals().items()):
    if getattr(value, "__module__", "").startswith("anyio.abc."):
        value.__module__ = __name__
