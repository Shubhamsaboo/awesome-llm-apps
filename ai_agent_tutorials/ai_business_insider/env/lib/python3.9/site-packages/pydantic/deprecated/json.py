import datetime
import warnings
from collections import deque
from decimal import Decimal
from enum import Enum
from ipaddress import IPv4Address, IPv4Interface, IPv4Network, IPv6Address, IPv6Interface, IPv6Network
from pathlib import Path
from re import Pattern
from types import GeneratorType
from typing import TYPE_CHECKING, Any, Callable, Dict, Type, Union
from uuid import UUID

from typing_extensions import deprecated

from .._internal._import_utils import import_cached_base_model
from ..color import Color
from ..networks import NameEmail
from ..types import SecretBytes, SecretStr
from ..warnings import PydanticDeprecatedSince20

if not TYPE_CHECKING:
    # See PyCharm issues https://youtrack.jetbrains.com/issue/PY-21915
    # and https://youtrack.jetbrains.com/issue/PY-51428
    DeprecationWarning = PydanticDeprecatedSince20

__all__ = 'pydantic_encoder', 'custom_pydantic_encoder', 'timedelta_isoformat'


def isoformat(o: Union[datetime.date, datetime.time]) -> str:
    return o.isoformat()


def decimal_encoder(dec_value: Decimal) -> Union[int, float]:
    """Encodes a Decimal as int of there's no exponent, otherwise float.

    This is useful when we use ConstrainedDecimal to represent Numeric(x,0)
    where a integer (but not int typed) is used. Encoding this as a float
    results in failed round-tripping between encode and parse.
    Our Id type is a prime example of this.

    >>> decimal_encoder(Decimal("1.0"))
    1.0

    >>> decimal_encoder(Decimal("1"))
    1
    """
    exponent = dec_value.as_tuple().exponent
    if isinstance(exponent, int) and exponent >= 0:
        return int(dec_value)
    else:
        return float(dec_value)


ENCODERS_BY_TYPE: Dict[Type[Any], Callable[[Any], Any]] = {
    bytes: lambda o: o.decode(),
    Color: str,
    datetime.date: isoformat,
    datetime.datetime: isoformat,
    datetime.time: isoformat,
    datetime.timedelta: lambda td: td.total_seconds(),
    Decimal: decimal_encoder,
    Enum: lambda o: o.value,
    frozenset: list,
    deque: list,
    GeneratorType: list,
    IPv4Address: str,
    IPv4Interface: str,
    IPv4Network: str,
    IPv6Address: str,
    IPv6Interface: str,
    IPv6Network: str,
    NameEmail: str,
    Path: str,
    Pattern: lambda o: o.pattern,
    SecretBytes: str,
    SecretStr: str,
    set: list,
    UUID: str,
}


@deprecated(
    '`pydantic_encoder` is deprecated, use `pydantic_core.to_jsonable_python` instead.',
    category=None,
)
def pydantic_encoder(obj: Any) -> Any:
    warnings.warn(
        '`pydantic_encoder` is deprecated, use `pydantic_core.to_jsonable_python` instead.',
        category=PydanticDeprecatedSince20,
        stacklevel=2,
    )
    from dataclasses import asdict, is_dataclass

    BaseModel = import_cached_base_model()

    if isinstance(obj, BaseModel):
        return obj.model_dump()
    elif is_dataclass(obj):
        return asdict(obj)  # type: ignore

    # Check the class type and its superclasses for a matching encoder
    for base in obj.__class__.__mro__[:-1]:
        try:
            encoder = ENCODERS_BY_TYPE[base]
        except KeyError:
            continue
        return encoder(obj)
    else:  # We have exited the for loop without finding a suitable encoder
        raise TypeError(f"Object of type '{obj.__class__.__name__}' is not JSON serializable")


# TODO: Add a suggested migration path once there is a way to use custom encoders
@deprecated(
    '`custom_pydantic_encoder` is deprecated, use `BaseModel.model_dump` instead.',
    category=None,
)
def custom_pydantic_encoder(type_encoders: Dict[Any, Callable[[Type[Any]], Any]], obj: Any) -> Any:
    warnings.warn(
        '`custom_pydantic_encoder` is deprecated, use `BaseModel.model_dump` instead.',
        category=PydanticDeprecatedSince20,
        stacklevel=2,
    )
    # Check the class type and its superclasses for a matching encoder
    for base in obj.__class__.__mro__[:-1]:
        try:
            encoder = type_encoders[base]
        except KeyError:
            continue

        return encoder(obj)
    else:  # We have exited the for loop without finding a suitable encoder
        return pydantic_encoder(obj)


@deprecated('`timedelta_isoformat` is deprecated.', category=None)
def timedelta_isoformat(td: datetime.timedelta) -> str:
    """ISO 8601 encoding for Python timedelta object."""
    warnings.warn('`timedelta_isoformat` is deprecated.', category=PydanticDeprecatedSince20, stacklevel=2)
    minutes, seconds = divmod(td.seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f'{"-" if td.days < 0 else ""}P{abs(td.days)}DT{hours:d}H{minutes:d}M{seconds:d}.{td.microseconds:06d}S'
