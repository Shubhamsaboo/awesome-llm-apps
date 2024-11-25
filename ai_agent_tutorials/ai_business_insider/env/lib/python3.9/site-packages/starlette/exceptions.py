from __future__ import annotations

import http
import typing
import warnings

__all__ = ("HTTPException", "WebSocketException")


class HTTPException(Exception):
    def __init__(
        self,
        status_code: int,
        detail: str | None = None,
        headers: typing.Mapping[str, str] | None = None,
    ) -> None:
        if detail is None:
            detail = http.HTTPStatus(status_code).phrase
        self.status_code = status_code
        self.detail = detail
        self.headers = headers

    def __str__(self) -> str:
        return f"{self.status_code}: {self.detail}"

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        return f"{class_name}(status_code={self.status_code!r}, detail={self.detail!r})"


class WebSocketException(Exception):
    def __init__(self, code: int, reason: str | None = None) -> None:
        self.code = code
        self.reason = reason or ""

    def __str__(self) -> str:
        return f"{self.code}: {self.reason}"

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        return f"{class_name}(code={self.code!r}, reason={self.reason!r})"


__deprecated__ = "ExceptionMiddleware"


def __getattr__(name: str) -> typing.Any:  # pragma: no cover
    if name == __deprecated__:
        from starlette.middleware.exceptions import ExceptionMiddleware

        warnings.warn(
            f"{__deprecated__} is deprecated on `starlette.exceptions`. "
            f"Import it from `starlette.middleware.exceptions` instead.",
            category=DeprecationWarning,
            stacklevel=3,
        )
        return ExceptionMiddleware
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def __dir__() -> list[str]:
    return sorted(list(__all__) + [__deprecated__])  # pragma: no cover
