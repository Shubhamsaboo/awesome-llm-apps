from __future__ import annotations

import logging
import re
import ssl
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from functools import wraps
from typing import Any, TypeVar

from .. import (
    BrokenResourceError,
    EndOfStream,
    aclose_forcefully,
    get_cancelled_exc_class,
)
from .._core._typedattr import TypedAttributeSet, typed_attribute
from ..abc import AnyByteStream, ByteStream, Listener, TaskGroup

if sys.version_info >= (3, 11):
    from typing import TypeVarTuple, Unpack
else:
    from typing_extensions import TypeVarTuple, Unpack

T_Retval = TypeVar("T_Retval")
PosArgsT = TypeVarTuple("PosArgsT")
_PCTRTT = tuple[tuple[str, str], ...]
_PCTRTTT = tuple[_PCTRTT, ...]


class TLSAttribute(TypedAttributeSet):
    """Contains Transport Layer Security related attributes."""

    #: the selected ALPN protocol
    alpn_protocol: str | None = typed_attribute()
    #: the channel binding for type ``tls-unique``
    channel_binding_tls_unique: bytes = typed_attribute()
    #: the selected cipher
    cipher: tuple[str, str, int] = typed_attribute()
    #: the peer certificate in dictionary form (see :meth:`ssl.SSLSocket.getpeercert`
    # for more information)
    peer_certificate: None | (dict[str, str | _PCTRTTT | _PCTRTT]) = typed_attribute()
    #: the peer certificate in binary form
    peer_certificate_binary: bytes | None = typed_attribute()
    #: ``True`` if this is the server side of the connection
    server_side: bool = typed_attribute()
    #: ciphers shared by the client during the TLS handshake (``None`` if this is the
    #: client side)
    shared_ciphers: list[tuple[str, str, int]] | None = typed_attribute()
    #: the :class:`~ssl.SSLObject` used for encryption
    ssl_object: ssl.SSLObject = typed_attribute()
    #: ``True`` if this stream does (and expects) a closing TLS handshake when the
    #: stream is being closed
    standard_compatible: bool = typed_attribute()
    #: the TLS protocol version (e.g. ``TLSv1.2``)
    tls_version: str = typed_attribute()


@dataclass(eq=False)
class TLSStream(ByteStream):
    """
    A stream wrapper that encrypts all sent data and decrypts received data.

    This class has no public initializer; use :meth:`wrap` instead.
    All extra attributes from :class:`~TLSAttribute` are supported.

    :var AnyByteStream transport_stream: the wrapped stream

    """

    transport_stream: AnyByteStream
    standard_compatible: bool
    _ssl_object: ssl.SSLObject
    _read_bio: ssl.MemoryBIO
    _write_bio: ssl.MemoryBIO

    @classmethod
    async def wrap(
        cls,
        transport_stream: AnyByteStream,
        *,
        server_side: bool | None = None,
        hostname: str | None = None,
        ssl_context: ssl.SSLContext | None = None,
        standard_compatible: bool = True,
    ) -> TLSStream:
        """
        Wrap an existing stream with Transport Layer Security.

        This performs a TLS handshake with the peer.

        :param transport_stream: a bytes-transporting stream to wrap
        :param server_side: ``True`` if this is the server side of the connection,
            ``False`` if this is the client side (if omitted, will be set to ``False``
            if ``hostname`` has been provided, ``False`` otherwise). Used only to create
            a default context when an explicit context has not been provided.
        :param hostname: host name of the peer (if host name checking is desired)
        :param ssl_context: the SSLContext object to use (if not provided, a secure
            default will be created)
        :param standard_compatible: if ``False``, skip the closing handshake when
            closing the connection, and don't raise an exception if the peer does the
            same
        :raises ~ssl.SSLError: if the TLS handshake fails

        """
        if server_side is None:
            server_side = not hostname

        if not ssl_context:
            purpose = (
                ssl.Purpose.CLIENT_AUTH if server_side else ssl.Purpose.SERVER_AUTH
            )
            ssl_context = ssl.create_default_context(purpose)

            # Re-enable detection of unexpected EOFs if it was disabled by Python
            if hasattr(ssl, "OP_IGNORE_UNEXPECTED_EOF"):
                ssl_context.options &= ~ssl.OP_IGNORE_UNEXPECTED_EOF

        bio_in = ssl.MemoryBIO()
        bio_out = ssl.MemoryBIO()
        ssl_object = ssl_context.wrap_bio(
            bio_in, bio_out, server_side=server_side, server_hostname=hostname
        )
        wrapper = cls(
            transport_stream=transport_stream,
            standard_compatible=standard_compatible,
            _ssl_object=ssl_object,
            _read_bio=bio_in,
            _write_bio=bio_out,
        )
        await wrapper._call_sslobject_method(ssl_object.do_handshake)
        return wrapper

    async def _call_sslobject_method(
        self, func: Callable[[Unpack[PosArgsT]], T_Retval], *args: Unpack[PosArgsT]
    ) -> T_Retval:
        while True:
            try:
                result = func(*args)
            except ssl.SSLWantReadError:
                try:
                    # Flush any pending writes first
                    if self._write_bio.pending:
                        await self.transport_stream.send(self._write_bio.read())

                    data = await self.transport_stream.receive()
                except EndOfStream:
                    self._read_bio.write_eof()
                except OSError as exc:
                    self._read_bio.write_eof()
                    self._write_bio.write_eof()
                    raise BrokenResourceError from exc
                else:
                    self._read_bio.write(data)
            except ssl.SSLWantWriteError:
                await self.transport_stream.send(self._write_bio.read())
            except ssl.SSLSyscallError as exc:
                self._read_bio.write_eof()
                self._write_bio.write_eof()
                raise BrokenResourceError from exc
            except ssl.SSLError as exc:
                self._read_bio.write_eof()
                self._write_bio.write_eof()
                if isinstance(exc, ssl.SSLEOFError) or (
                    exc.strerror and "UNEXPECTED_EOF_WHILE_READING" in exc.strerror
                ):
                    if self.standard_compatible:
                        raise BrokenResourceError from exc
                    else:
                        raise EndOfStream from None

                raise
            else:
                # Flush any pending writes first
                if self._write_bio.pending:
                    await self.transport_stream.send(self._write_bio.read())

                return result

    async def unwrap(self) -> tuple[AnyByteStream, bytes]:
        """
        Does the TLS closing handshake.

        :return: a tuple of (wrapped byte stream, bytes left in the read buffer)

        """
        await self._call_sslobject_method(self._ssl_object.unwrap)
        self._read_bio.write_eof()
        self._write_bio.write_eof()
        return self.transport_stream, self._read_bio.read()

    async def aclose(self) -> None:
        if self.standard_compatible:
            try:
                await self.unwrap()
            except BaseException:
                await aclose_forcefully(self.transport_stream)
                raise

        await self.transport_stream.aclose()

    async def receive(self, max_bytes: int = 65536) -> bytes:
        data = await self._call_sslobject_method(self._ssl_object.read, max_bytes)
        if not data:
            raise EndOfStream

        return data

    async def send(self, item: bytes) -> None:
        await self._call_sslobject_method(self._ssl_object.write, item)

    async def send_eof(self) -> None:
        tls_version = self.extra(TLSAttribute.tls_version)
        match = re.match(r"TLSv(\d+)(?:\.(\d+))?", tls_version)
        if match:
            major, minor = int(match.group(1)), int(match.group(2) or 0)
            if (major, minor) < (1, 3):
                raise NotImplementedError(
                    f"send_eof() requires at least TLSv1.3; current "
                    f"session uses {tls_version}"
                )

        raise NotImplementedError(
            "send_eof() has not yet been implemented for TLS streams"
        )

    @property
    def extra_attributes(self) -> Mapping[Any, Callable[[], Any]]:
        return {
            **self.transport_stream.extra_attributes,
            TLSAttribute.alpn_protocol: self._ssl_object.selected_alpn_protocol,
            TLSAttribute.channel_binding_tls_unique: (
                self._ssl_object.get_channel_binding
            ),
            TLSAttribute.cipher: self._ssl_object.cipher,
            TLSAttribute.peer_certificate: lambda: self._ssl_object.getpeercert(False),
            TLSAttribute.peer_certificate_binary: lambda: self._ssl_object.getpeercert(
                True
            ),
            TLSAttribute.server_side: lambda: self._ssl_object.server_side,
            TLSAttribute.shared_ciphers: lambda: self._ssl_object.shared_ciphers()
            if self._ssl_object.server_side
            else None,
            TLSAttribute.standard_compatible: lambda: self.standard_compatible,
            TLSAttribute.ssl_object: lambda: self._ssl_object,
            TLSAttribute.tls_version: self._ssl_object.version,
        }


@dataclass(eq=False)
class TLSListener(Listener[TLSStream]):
    """
    A convenience listener that wraps another listener and auto-negotiates a TLS session
    on every accepted connection.

    If the TLS handshake times out or raises an exception,
    :meth:`handle_handshake_error` is called to do whatever post-mortem processing is
    deemed necessary.

    Supports only the :attr:`~TLSAttribute.standard_compatible` extra attribute.

    :param Listener listener: the listener to wrap
    :param ssl_context: the SSL context object
    :param standard_compatible: a flag passed through to :meth:`TLSStream.wrap`
    :param handshake_timeout: time limit for the TLS handshake
        (passed to :func:`~anyio.fail_after`)
    """

    listener: Listener[Any]
    ssl_context: ssl.SSLContext
    standard_compatible: bool = True
    handshake_timeout: float = 30

    @staticmethod
    async def handle_handshake_error(exc: BaseException, stream: AnyByteStream) -> None:
        """
        Handle an exception raised during the TLS handshake.

        This method does 3 things:

        #. Forcefully closes the original stream
        #. Logs the exception (unless it was a cancellation exception) using the
           ``anyio.streams.tls`` logger
        #. Reraises the exception if it was a base exception or a cancellation exception

        :param exc: the exception
        :param stream: the original stream

        """
        await aclose_forcefully(stream)

        # Log all except cancellation exceptions
        if not isinstance(exc, get_cancelled_exc_class()):
            # CPython (as of 3.11.5) returns incorrect `sys.exc_info()` here when using
            # any asyncio implementation, so we explicitly pass the exception to log
            # (https://github.com/python/cpython/issues/108668). Trio does not have this
            # issue because it works around the CPython bug.
            logging.getLogger(__name__).exception(
                "Error during TLS handshake", exc_info=exc
            )

        # Only reraise base exceptions and cancellation exceptions
        if not isinstance(exc, Exception) or isinstance(exc, get_cancelled_exc_class()):
            raise

    async def serve(
        self,
        handler: Callable[[TLSStream], Any],
        task_group: TaskGroup | None = None,
    ) -> None:
        @wraps(handler)
        async def handler_wrapper(stream: AnyByteStream) -> None:
            from .. import fail_after

            try:
                with fail_after(self.handshake_timeout):
                    wrapped_stream = await TLSStream.wrap(
                        stream,
                        ssl_context=self.ssl_context,
                        standard_compatible=self.standard_compatible,
                    )
            except BaseException as exc:
                await self.handle_handshake_error(exc, stream)
            else:
                await handler(wrapped_stream)

        await self.listener.serve(handler_wrapper, task_group)

    async def aclose(self) -> None:
        await self.listener.aclose()

    @property
    def extra_attributes(self) -> Mapping[Any, Callable[[], Any]]:
        return {
            TLSAttribute.standard_compatible: lambda: self.standard_compatible,
        }
