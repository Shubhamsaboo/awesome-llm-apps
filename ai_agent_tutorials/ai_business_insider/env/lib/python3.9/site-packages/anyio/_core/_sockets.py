from __future__ import annotations

import errno
import os
import socket
import ssl
import stat
import sys
from collections.abc import Awaitable
from ipaddress import IPv6Address, ip_address
from os import PathLike, chmod
from socket import AddressFamily, SocketKind
from typing import Any, Literal, cast, overload

from .. import to_thread
from ..abc import (
    ConnectedUDPSocket,
    ConnectedUNIXDatagramSocket,
    IPAddressType,
    IPSockAddrType,
    SocketListener,
    SocketStream,
    UDPSocket,
    UNIXDatagramSocket,
    UNIXSocketStream,
)
from ..streams.stapled import MultiListener
from ..streams.tls import TLSStream
from ._eventloop import get_async_backend
from ._resources import aclose_forcefully
from ._synchronization import Event
from ._tasks import create_task_group, move_on_after

if sys.version_info < (3, 11):
    from exceptiongroup import ExceptionGroup

IPPROTO_IPV6 = getattr(socket, "IPPROTO_IPV6", 41)  # https://bugs.python.org/issue29515

AnyIPAddressFamily = Literal[
    AddressFamily.AF_UNSPEC, AddressFamily.AF_INET, AddressFamily.AF_INET6
]
IPAddressFamily = Literal[AddressFamily.AF_INET, AddressFamily.AF_INET6]


# tls_hostname given
@overload
async def connect_tcp(
    remote_host: IPAddressType,
    remote_port: int,
    *,
    local_host: IPAddressType | None = ...,
    ssl_context: ssl.SSLContext | None = ...,
    tls_standard_compatible: bool = ...,
    tls_hostname: str,
    happy_eyeballs_delay: float = ...,
) -> TLSStream: ...


# ssl_context given
@overload
async def connect_tcp(
    remote_host: IPAddressType,
    remote_port: int,
    *,
    local_host: IPAddressType | None = ...,
    ssl_context: ssl.SSLContext,
    tls_standard_compatible: bool = ...,
    tls_hostname: str | None = ...,
    happy_eyeballs_delay: float = ...,
) -> TLSStream: ...


# tls=True
@overload
async def connect_tcp(
    remote_host: IPAddressType,
    remote_port: int,
    *,
    local_host: IPAddressType | None = ...,
    tls: Literal[True],
    ssl_context: ssl.SSLContext | None = ...,
    tls_standard_compatible: bool = ...,
    tls_hostname: str | None = ...,
    happy_eyeballs_delay: float = ...,
) -> TLSStream: ...


# tls=False
@overload
async def connect_tcp(
    remote_host: IPAddressType,
    remote_port: int,
    *,
    local_host: IPAddressType | None = ...,
    tls: Literal[False],
    ssl_context: ssl.SSLContext | None = ...,
    tls_standard_compatible: bool = ...,
    tls_hostname: str | None = ...,
    happy_eyeballs_delay: float = ...,
) -> SocketStream: ...


# No TLS arguments
@overload
async def connect_tcp(
    remote_host: IPAddressType,
    remote_port: int,
    *,
    local_host: IPAddressType | None = ...,
    happy_eyeballs_delay: float = ...,
) -> SocketStream: ...


async def connect_tcp(
    remote_host: IPAddressType,
    remote_port: int,
    *,
    local_host: IPAddressType | None = None,
    tls: bool = False,
    ssl_context: ssl.SSLContext | None = None,
    tls_standard_compatible: bool = True,
    tls_hostname: str | None = None,
    happy_eyeballs_delay: float = 0.25,
) -> SocketStream | TLSStream:
    """
    Connect to a host using the TCP protocol.

    This function implements the stateless version of the Happy Eyeballs algorithm (RFC
    6555). If ``remote_host`` is a host name that resolves to multiple IP addresses,
    each one is tried until one connection attempt succeeds. If the first attempt does
    not connected within 250 milliseconds, a second attempt is started using the next
    address in the list, and so on. On IPv6 enabled systems, an IPv6 address (if
    available) is tried first.

    When the connection has been established, a TLS handshake will be done if either
    ``ssl_context`` or ``tls_hostname`` is not ``None``, or if ``tls`` is ``True``.

    :param remote_host: the IP address or host name to connect to
    :param remote_port: port on the target host to connect to
    :param local_host: the interface address or name to bind the socket to before
        connecting
    :param tls: ``True`` to do a TLS handshake with the connected stream and return a
        :class:`~anyio.streams.tls.TLSStream` instead
    :param ssl_context: the SSL context object to use (if omitted, a default context is
        created)
    :param tls_standard_compatible: If ``True``, performs the TLS shutdown handshake
        before closing the stream and requires that the server does this as well.
        Otherwise, :exc:`~ssl.SSLEOFError` may be raised during reads from the stream.
        Some protocols, such as HTTP, require this option to be ``False``.
        See :meth:`~ssl.SSLContext.wrap_socket` for details.
    :param tls_hostname: host name to check the server certificate against (defaults to
        the value of ``remote_host``)
    :param happy_eyeballs_delay: delay (in seconds) before starting the next connection
        attempt
    :return: a socket stream object if no TLS handshake was done, otherwise a TLS stream
    :raises OSError: if the connection attempt fails

    """
    # Placed here due to https://github.com/python/mypy/issues/7057
    connected_stream: SocketStream | None = None

    async def try_connect(remote_host: str, event: Event) -> None:
        nonlocal connected_stream
        try:
            stream = await asynclib.connect_tcp(remote_host, remote_port, local_address)
        except OSError as exc:
            oserrors.append(exc)
            return
        else:
            if connected_stream is None:
                connected_stream = stream
                tg.cancel_scope.cancel()
            else:
                await stream.aclose()
        finally:
            event.set()

    asynclib = get_async_backend()
    local_address: IPSockAddrType | None = None
    family = socket.AF_UNSPEC
    if local_host:
        gai_res = await getaddrinfo(str(local_host), None)
        family, *_, local_address = gai_res[0]

    target_host = str(remote_host)
    try:
        addr_obj = ip_address(remote_host)
    except ValueError:
        # getaddrinfo() will raise an exception if name resolution fails
        gai_res = await getaddrinfo(
            target_host, remote_port, family=family, type=socket.SOCK_STREAM
        )

        # Organize the list so that the first address is an IPv6 address (if available)
        # and the second one is an IPv4 addresses. The rest can be in whatever order.
        v6_found = v4_found = False
        target_addrs: list[tuple[socket.AddressFamily, str]] = []
        for af, *rest, sa in gai_res:
            if af == socket.AF_INET6 and not v6_found:
                v6_found = True
                target_addrs.insert(0, (af, sa[0]))
            elif af == socket.AF_INET and not v4_found and v6_found:
                v4_found = True
                target_addrs.insert(1, (af, sa[0]))
            else:
                target_addrs.append((af, sa[0]))
    else:
        if isinstance(addr_obj, IPv6Address):
            target_addrs = [(socket.AF_INET6, addr_obj.compressed)]
        else:
            target_addrs = [(socket.AF_INET, addr_obj.compressed)]

    oserrors: list[OSError] = []
    async with create_task_group() as tg:
        for i, (af, addr) in enumerate(target_addrs):
            event = Event()
            tg.start_soon(try_connect, addr, event)
            with move_on_after(happy_eyeballs_delay):
                await event.wait()

    if connected_stream is None:
        cause = (
            oserrors[0]
            if len(oserrors) == 1
            else ExceptionGroup("multiple connection attempts failed", oserrors)
        )
        raise OSError("All connection attempts failed") from cause

    if tls or tls_hostname or ssl_context:
        try:
            return await TLSStream.wrap(
                connected_stream,
                server_side=False,
                hostname=tls_hostname or str(remote_host),
                ssl_context=ssl_context,
                standard_compatible=tls_standard_compatible,
            )
        except BaseException:
            await aclose_forcefully(connected_stream)
            raise

    return connected_stream


async def connect_unix(path: str | bytes | PathLike[Any]) -> UNIXSocketStream:
    """
    Connect to the given UNIX socket.

    Not available on Windows.

    :param path: path to the socket
    :return: a socket stream object

    """
    path = os.fspath(path)
    return await get_async_backend().connect_unix(path)


async def create_tcp_listener(
    *,
    local_host: IPAddressType | None = None,
    local_port: int = 0,
    family: AnyIPAddressFamily = socket.AddressFamily.AF_UNSPEC,
    backlog: int = 65536,
    reuse_port: bool = False,
) -> MultiListener[SocketStream]:
    """
    Create a TCP socket listener.

    :param local_port: port number to listen on
    :param local_host: IP address of the interface to listen on. If omitted, listen on
        all IPv4 and IPv6 interfaces. To listen on all interfaces on a specific address
        family, use ``0.0.0.0`` for IPv4 or ``::`` for IPv6.
    :param family: address family (used if ``local_host`` was omitted)
    :param backlog: maximum number of queued incoming connections (up to a maximum of
        2**16, or 65536)
    :param reuse_port: ``True`` to allow multiple sockets to bind to the same
        address/port (not supported on Windows)
    :return: a list of listener objects

    """
    asynclib = get_async_backend()
    backlog = min(backlog, 65536)
    local_host = str(local_host) if local_host is not None else None
    gai_res = await getaddrinfo(
        local_host,
        local_port,
        family=family,
        type=socket.SocketKind.SOCK_STREAM if sys.platform == "win32" else 0,
        flags=socket.AI_PASSIVE | socket.AI_ADDRCONFIG,
    )
    listeners: list[SocketListener] = []
    try:
        # The set() is here to work around a glibc bug:
        # https://sourceware.org/bugzilla/show_bug.cgi?id=14969
        sockaddr: tuple[str, int] | tuple[str, int, int, int]
        for fam, kind, *_, sockaddr in sorted(set(gai_res)):
            # Workaround for an uvloop bug where we don't get the correct scope ID for
            # IPv6 link-local addresses when passing type=socket.SOCK_STREAM to
            # getaddrinfo(): https://github.com/MagicStack/uvloop/issues/539
            if sys.platform != "win32" and kind is not SocketKind.SOCK_STREAM:
                continue

            raw_socket = socket.socket(fam)
            raw_socket.setblocking(False)

            # For Windows, enable exclusive address use. For others, enable address
            # reuse.
            if sys.platform == "win32":
                raw_socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            else:
                raw_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            if reuse_port:
                raw_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

            # If only IPv6 was requested, disable dual stack operation
            if fam == socket.AF_INET6:
                raw_socket.setsockopt(IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)

                # Workaround for #554
                if "%" in sockaddr[0]:
                    addr, scope_id = sockaddr[0].split("%", 1)
                    sockaddr = (addr, sockaddr[1], 0, int(scope_id))

            raw_socket.bind(sockaddr)
            raw_socket.listen(backlog)
            listener = asynclib.create_tcp_listener(raw_socket)
            listeners.append(listener)
    except BaseException:
        for listener in listeners:
            await listener.aclose()

        raise

    return MultiListener(listeners)


async def create_unix_listener(
    path: str | bytes | PathLike[Any],
    *,
    mode: int | None = None,
    backlog: int = 65536,
) -> SocketListener:
    """
    Create a UNIX socket listener.

    Not available on Windows.

    :param path: path of the socket
    :param mode: permissions to set on the socket
    :param backlog: maximum number of queued incoming connections (up to a maximum of
        2**16, or 65536)
    :return: a listener object

    .. versionchanged:: 3.0
        If a socket already exists on the file system in the given path, it will be
        removed first.

    """
    backlog = min(backlog, 65536)
    raw_socket = await setup_unix_local_socket(path, mode, socket.SOCK_STREAM)
    try:
        raw_socket.listen(backlog)
        return get_async_backend().create_unix_listener(raw_socket)
    except BaseException:
        raw_socket.close()
        raise


async def create_udp_socket(
    family: AnyIPAddressFamily = AddressFamily.AF_UNSPEC,
    *,
    local_host: IPAddressType | None = None,
    local_port: int = 0,
    reuse_port: bool = False,
) -> UDPSocket:
    """
    Create a UDP socket.

    If ``port`` has been given, the socket will be bound to this port on the local
    machine, making this socket suitable for providing UDP based services.

    :param family: address family (``AF_INET`` or ``AF_INET6``) – automatically
        determined from ``local_host`` if omitted
    :param local_host: IP address or host name of the local interface to bind to
    :param local_port: local port to bind to
    :param reuse_port: ``True`` to allow multiple sockets to bind to the same
        address/port (not supported on Windows)
    :return: a UDP socket

    """
    if family is AddressFamily.AF_UNSPEC and not local_host:
        raise ValueError('Either "family" or "local_host" must be given')

    if local_host:
        gai_res = await getaddrinfo(
            str(local_host),
            local_port,
            family=family,
            type=socket.SOCK_DGRAM,
            flags=socket.AI_PASSIVE | socket.AI_ADDRCONFIG,
        )
        family = cast(AnyIPAddressFamily, gai_res[0][0])
        local_address = gai_res[0][-1]
    elif family is AddressFamily.AF_INET6:
        local_address = ("::", 0)
    else:
        local_address = ("0.0.0.0", 0)

    sock = await get_async_backend().create_udp_socket(
        family, local_address, None, reuse_port
    )
    return cast(UDPSocket, sock)


async def create_connected_udp_socket(
    remote_host: IPAddressType,
    remote_port: int,
    *,
    family: AnyIPAddressFamily = AddressFamily.AF_UNSPEC,
    local_host: IPAddressType | None = None,
    local_port: int = 0,
    reuse_port: bool = False,
) -> ConnectedUDPSocket:
    """
    Create a connected UDP socket.

    Connected UDP sockets can only communicate with the specified remote host/port, an
    any packets sent from other sources are dropped.

    :param remote_host: remote host to set as the default target
    :param remote_port: port on the remote host to set as the default target
    :param family: address family (``AF_INET`` or ``AF_INET6``) – automatically
        determined from ``local_host`` or ``remote_host`` if omitted
    :param local_host: IP address or host name of the local interface to bind to
    :param local_port: local port to bind to
    :param reuse_port: ``True`` to allow multiple sockets to bind to the same
        address/port (not supported on Windows)
    :return: a connected UDP socket

    """
    local_address = None
    if local_host:
        gai_res = await getaddrinfo(
            str(local_host),
            local_port,
            family=family,
            type=socket.SOCK_DGRAM,
            flags=socket.AI_PASSIVE | socket.AI_ADDRCONFIG,
        )
        family = cast(AnyIPAddressFamily, gai_res[0][0])
        local_address = gai_res[0][-1]

    gai_res = await getaddrinfo(
        str(remote_host), remote_port, family=family, type=socket.SOCK_DGRAM
    )
    family = cast(AnyIPAddressFamily, gai_res[0][0])
    remote_address = gai_res[0][-1]

    sock = await get_async_backend().create_udp_socket(
        family, local_address, remote_address, reuse_port
    )
    return cast(ConnectedUDPSocket, sock)


async def create_unix_datagram_socket(
    *,
    local_path: None | str | bytes | PathLike[Any] = None,
    local_mode: int | None = None,
) -> UNIXDatagramSocket:
    """
    Create a UNIX datagram socket.

    Not available on Windows.

    If ``local_path`` has been given, the socket will be bound to this path, making this
    socket suitable for receiving datagrams from other processes. Other processes can
    send datagrams to this socket only if ``local_path`` is set.

    If a socket already exists on the file system in the ``local_path``, it will be
    removed first.

    :param local_path: the path on which to bind to
    :param local_mode: permissions to set on the local socket
    :return: a UNIX datagram socket

    """
    raw_socket = await setup_unix_local_socket(
        local_path, local_mode, socket.SOCK_DGRAM
    )
    return await get_async_backend().create_unix_datagram_socket(raw_socket, None)


async def create_connected_unix_datagram_socket(
    remote_path: str | bytes | PathLike[Any],
    *,
    local_path: None | str | bytes | PathLike[Any] = None,
    local_mode: int | None = None,
) -> ConnectedUNIXDatagramSocket:
    """
    Create a connected UNIX datagram socket.

    Connected datagram sockets can only communicate with the specified remote path.

    If ``local_path`` has been given, the socket will be bound to this path, making
    this socket suitable for receiving datagrams from other processes. Other processes
    can send datagrams to this socket only if ``local_path`` is set.

    If a socket already exists on the file system in the ``local_path``, it will be
    removed first.

    :param remote_path: the path to set as the default target
    :param local_path: the path on which to bind to
    :param local_mode: permissions to set on the local socket
    :return: a connected UNIX datagram socket

    """
    remote_path = os.fspath(remote_path)
    raw_socket = await setup_unix_local_socket(
        local_path, local_mode, socket.SOCK_DGRAM
    )
    return await get_async_backend().create_unix_datagram_socket(
        raw_socket, remote_path
    )


async def getaddrinfo(
    host: bytes | str | None,
    port: str | int | None,
    *,
    family: int | AddressFamily = 0,
    type: int | SocketKind = 0,
    proto: int = 0,
    flags: int = 0,
) -> list[tuple[AddressFamily, SocketKind, int, str, tuple[str, int]]]:
    """
    Look up a numeric IP address given a host name.

    Internationalized domain names are translated according to the (non-transitional)
    IDNA 2008 standard.

    .. note:: 4-tuple IPv6 socket addresses are automatically converted to 2-tuples of
        (host, port), unlike what :func:`socket.getaddrinfo` does.

    :param host: host name
    :param port: port number
    :param family: socket family (`'AF_INET``, ...)
    :param type: socket type (``SOCK_STREAM``, ...)
    :param proto: protocol number
    :param flags: flags to pass to upstream ``getaddrinfo()``
    :return: list of tuples containing (family, type, proto, canonname, sockaddr)

    .. seealso:: :func:`socket.getaddrinfo`

    """
    # Handle unicode hostnames
    if isinstance(host, str):
        try:
            encoded_host: bytes | None = host.encode("ascii")
        except UnicodeEncodeError:
            import idna

            encoded_host = idna.encode(host, uts46=True)
    else:
        encoded_host = host

    gai_res = await get_async_backend().getaddrinfo(
        encoded_host, port, family=family, type=type, proto=proto, flags=flags
    )
    return [
        (family, type, proto, canonname, convert_ipv6_sockaddr(sockaddr))
        for family, type, proto, canonname, sockaddr in gai_res
    ]


def getnameinfo(sockaddr: IPSockAddrType, flags: int = 0) -> Awaitable[tuple[str, str]]:
    """
    Look up the host name of an IP address.

    :param sockaddr: socket address (e.g. (ipaddress, port) for IPv4)
    :param flags: flags to pass to upstream ``getnameinfo()``
    :return: a tuple of (host name, service name)

    .. seealso:: :func:`socket.getnameinfo`

    """
    return get_async_backend().getnameinfo(sockaddr, flags)


def wait_socket_readable(sock: socket.socket) -> Awaitable[None]:
    """
    Wait until the given socket has data to be read.

    This does **NOT** work on Windows when using the asyncio backend with a proactor
    event loop (default on py3.8+).

    .. warning:: Only use this on raw sockets that have not been wrapped by any higher
        level constructs like socket streams!

    :param sock: a socket object
    :raises ~anyio.ClosedResourceError: if the socket was closed while waiting for the
        socket to become readable
    :raises ~anyio.BusyResourceError: if another task is already waiting for the socket
        to become readable

    """
    return get_async_backend().wait_socket_readable(sock)


def wait_socket_writable(sock: socket.socket) -> Awaitable[None]:
    """
    Wait until the given socket can be written to.

    This does **NOT** work on Windows when using the asyncio backend with a proactor
    event loop (default on py3.8+).

    .. warning:: Only use this on raw sockets that have not been wrapped by any higher
        level constructs like socket streams!

    :param sock: a socket object
    :raises ~anyio.ClosedResourceError: if the socket was closed while waiting for the
        socket to become writable
    :raises ~anyio.BusyResourceError: if another task is already waiting for the socket
        to become writable

    """
    return get_async_backend().wait_socket_writable(sock)


#
# Private API
#


def convert_ipv6_sockaddr(
    sockaddr: tuple[str, int, int, int] | tuple[str, int],
) -> tuple[str, int]:
    """
    Convert a 4-tuple IPv6 socket address to a 2-tuple (address, port) format.

    If the scope ID is nonzero, it is added to the address, separated with ``%``.
    Otherwise the flow id and scope id are simply cut off from the tuple.
    Any other kinds of socket addresses are returned as-is.

    :param sockaddr: the result of :meth:`~socket.socket.getsockname`
    :return: the converted socket address

    """
    # This is more complicated than it should be because of MyPy
    if isinstance(sockaddr, tuple) and len(sockaddr) == 4:
        host, port, flowinfo, scope_id = sockaddr
        if scope_id:
            # PyPy (as of v7.3.11) leaves the interface name in the result, so
            # we discard it and only get the scope ID from the end
            # (https://foss.heptapod.net/pypy/pypy/-/issues/3938)
            host = host.split("%")[0]

            # Add scope_id to the address
            return f"{host}%{scope_id}", port
        else:
            return host, port
    else:
        return sockaddr


async def setup_unix_local_socket(
    path: None | str | bytes | PathLike[Any],
    mode: int | None,
    socktype: int,
) -> socket.socket:
    """
    Create a UNIX local socket object, deleting the socket at the given path if it
    exists.

    Not available on Windows.

    :param path: path of the socket
    :param mode: permissions to set on the socket
    :param socktype: socket.SOCK_STREAM or socket.SOCK_DGRAM

    """
    path_str: str | None
    if path is not None:
        path_str = os.fsdecode(path)

        # Linux abstract namespace sockets aren't backed by a concrete file so skip stat call
        if not path_str.startswith("\0"):
            # Copied from pathlib...
            try:
                stat_result = os.stat(path)
            except OSError as e:
                if e.errno not in (
                    errno.ENOENT,
                    errno.ENOTDIR,
                    errno.EBADF,
                    errno.ELOOP,
                ):
                    raise
            else:
                if stat.S_ISSOCK(stat_result.st_mode):
                    os.unlink(path)
    else:
        path_str = None

    raw_socket = socket.socket(socket.AF_UNIX, socktype)
    raw_socket.setblocking(False)

    if path_str is not None:
        try:
            await to_thread.run_sync(raw_socket.bind, path_str, abandon_on_cancel=True)
            if mode is not None:
                await to_thread.run_sync(chmod, path_str, mode, abandon_on_cancel=True)
        except BaseException:
            raw_socket.close()
            raise

    return raw_socket
