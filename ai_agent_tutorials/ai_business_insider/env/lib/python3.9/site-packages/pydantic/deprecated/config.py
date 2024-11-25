from __future__ import annotations as _annotations

import warnings
from typing import TYPE_CHECKING, Any

from typing_extensions import Literal, deprecated

from .._internal import _config
from ..warnings import PydanticDeprecatedSince20

if not TYPE_CHECKING:
    # See PyCharm issues https://youtrack.jetbrains.com/issue/PY-21915
    # and https://youtrack.jetbrains.com/issue/PY-51428
    DeprecationWarning = PydanticDeprecatedSince20

__all__ = 'BaseConfig', 'Extra'


class _ConfigMetaclass(type):
    def __getattr__(self, item: str) -> Any:
        try:
            obj = _config.config_defaults[item]
            warnings.warn(_config.DEPRECATION_MESSAGE, DeprecationWarning)
            return obj
        except KeyError as exc:
            raise AttributeError(f"type object '{self.__name__}' has no attribute {exc}") from exc


@deprecated('BaseConfig is deprecated. Use the `pydantic.ConfigDict` instead.', category=PydanticDeprecatedSince20)
class BaseConfig(metaclass=_ConfigMetaclass):
    """This class is only retained for backwards compatibility.

    !!! Warning "Deprecated"
        BaseConfig is deprecated. Use the [`pydantic.ConfigDict`][pydantic.ConfigDict] instead.
    """

    def __getattr__(self, item: str) -> Any:
        try:
            obj = super().__getattribute__(item)
            warnings.warn(_config.DEPRECATION_MESSAGE, DeprecationWarning)
            return obj
        except AttributeError as exc:
            try:
                return getattr(type(self), item)
            except AttributeError:
                # re-raising changes the displayed text to reflect that `self` is not a type
                raise AttributeError(str(exc)) from exc

    def __init_subclass__(cls, **kwargs: Any) -> None:
        warnings.warn(_config.DEPRECATION_MESSAGE, DeprecationWarning)
        return super().__init_subclass__(**kwargs)


class _ExtraMeta(type):
    def __getattribute__(self, __name: str) -> Any:
        # The @deprecated decorator accesses other attributes, so we only emit a warning for the expected ones
        if __name in {'allow', 'ignore', 'forbid'}:
            warnings.warn(
                "`pydantic.config.Extra` is deprecated, use literal values instead (e.g. `extra='allow'`)",
                DeprecationWarning,
                stacklevel=2,
            )
        return super().__getattribute__(__name)


@deprecated(
    "Extra is deprecated. Use literal values instead (e.g. `extra='allow'`)", category=PydanticDeprecatedSince20
)
class Extra(metaclass=_ExtraMeta):
    allow: Literal['allow'] = 'allow'
    ignore: Literal['ignore'] = 'ignore'
    forbid: Literal['forbid'] = 'forbid'
