from __future__ import annotations

import sys as _sys
from typing import Any as _Any

from ._pydantic_core import (
    ArgsKwargs,
    MultiHostUrl,
    PydanticCustomError,
    PydanticKnownError,
    PydanticOmit,
    PydanticSerializationError,
    PydanticSerializationUnexpectedValue,
    PydanticUndefined,
    PydanticUndefinedType,
    PydanticUseDefault,
    SchemaError,
    SchemaSerializer,
    SchemaValidator,
    Some,
    TzInfo,
    Url,
    ValidationError,
    __version__,
    from_json,
    to_json,
    to_jsonable_python,
    validate_core_schema,
)
from .core_schema import CoreConfig, CoreSchema, CoreSchemaType, ErrorType

if _sys.version_info < (3, 11):
    from typing_extensions import NotRequired as _NotRequired
else:
    from typing import NotRequired as _NotRequired

if _sys.version_info < (3, 12):
    from typing_extensions import TypedDict as _TypedDict
else:
    from typing import TypedDict as _TypedDict

__all__ = [
    '__version__',
    'CoreConfig',
    'CoreSchema',
    'CoreSchemaType',
    'SchemaValidator',
    'SchemaSerializer',
    'Some',
    'Url',
    'MultiHostUrl',
    'ArgsKwargs',
    'PydanticUndefined',
    'PydanticUndefinedType',
    'SchemaError',
    'ErrorDetails',
    'InitErrorDetails',
    'ValidationError',
    'PydanticCustomError',
    'PydanticKnownError',
    'PydanticOmit',
    'PydanticUseDefault',
    'PydanticSerializationError',
    'PydanticSerializationUnexpectedValue',
    'TzInfo',
    'to_json',
    'from_json',
    'to_jsonable_python',
    'validate_core_schema',
]


class ErrorDetails(_TypedDict):
    type: str
    """
    The type of error that occurred, this is an identifier designed for
    programmatic use that will change rarely or never.

    `type` is unique for each error message, and can hence be used as an identifier to build custom error messages.
    """
    loc: tuple[int | str, ...]
    """Tuple of strings and ints identifying where in the schema the error occurred."""
    msg: str
    """A human readable error message."""
    input: _Any
    """The input data at this `loc` that caused the error."""
    ctx: _NotRequired[dict[str, _Any]]
    """
    Values which are required to render the error message, and could hence be useful in rendering custom error messages.
    Also useful for passing custom error data forward.
    """


class InitErrorDetails(_TypedDict):
    type: str | PydanticCustomError
    """The type of error that occurred, this should a "slug" identifier that changes rarely or never."""
    loc: _NotRequired[tuple[int | str, ...]]
    """Tuple of strings and ints identifying where in the schema the error occurred."""
    input: _Any
    """The input data at this `loc` that caused the error."""
    ctx: _NotRequired[dict[str, _Any]]
    """
    Values which are required to render the error message, and could hence be useful in rendering custom error messages.
    Also useful for passing custom error data forward.
    """


class ErrorTypeInfo(_TypedDict):
    """
    Gives information about errors.
    """

    type: ErrorType
    """The type of error that occurred, this should a "slug" identifier that changes rarely or never."""
    message_template_python: str
    """String template to render a human readable error message from using context, when the input is Python."""
    example_message_python: str
    """Example of a human readable error message, when the input is Python."""
    message_template_json: _NotRequired[str]
    """String template to render a human readable error message from using context, when the input is JSON data."""
    example_message_json: _NotRequired[str]
    """Example of a human readable error message, when the input is JSON data."""
    example_context: dict[str, _Any] | None
    """Example of context values."""


class MultiHostHost(_TypedDict):
    """
    A host part of a multi-host URL.
    """

    username: str | None
    """The username part of this host, or `None`."""
    password: str | None
    """The password part of this host, or `None`."""
    host: str | None
    """The host part of this host, or `None`."""
    port: int | None
    """The port part of this host, or `None`."""
