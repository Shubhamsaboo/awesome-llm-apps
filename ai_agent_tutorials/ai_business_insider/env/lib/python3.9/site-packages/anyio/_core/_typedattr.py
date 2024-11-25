from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, TypeVar, final, overload

from ._exceptions import TypedAttributeLookupError

T_Attr = TypeVar("T_Attr")
T_Default = TypeVar("T_Default")
undefined = object()


def typed_attribute() -> Any:
    """Return a unique object, used to mark typed attributes."""
    return object()


class TypedAttributeSet:
    """
    Superclass for typed attribute collections.

    Checks that every public attribute of every subclass has a type annotation.
    """

    def __init_subclass__(cls) -> None:
        annotations: dict[str, Any] = getattr(cls, "__annotations__", {})
        for attrname in dir(cls):
            if not attrname.startswith("_") and attrname not in annotations:
                raise TypeError(
                    f"Attribute {attrname!r} is missing its type annotation"
                )

        super().__init_subclass__()


class TypedAttributeProvider:
    """Base class for classes that wish to provide typed extra attributes."""

    @property
    def extra_attributes(self) -> Mapping[T_Attr, Callable[[], T_Attr]]:
        """
        A mapping of the extra attributes to callables that return the corresponding
        values.

        If the provider wraps another provider, the attributes from that wrapper should
        also be included in the returned mapping (but the wrapper may override the
        callables from the wrapped instance).

        """
        return {}

    @overload
    def extra(self, attribute: T_Attr) -> T_Attr: ...

    @overload
    def extra(self, attribute: T_Attr, default: T_Default) -> T_Attr | T_Default: ...

    @final
    def extra(self, attribute: Any, default: object = undefined) -> object:
        """
        extra(attribute, default=undefined)

        Return the value of the given typed extra attribute.

        :param attribute: the attribute (member of a :class:`~TypedAttributeSet`) to
            look for
        :param default: the value that should be returned if no value is found for the
            attribute
        :raises ~anyio.TypedAttributeLookupError: if the search failed and no default
            value was given

        """
        try:
            getter = self.extra_attributes[attribute]
        except KeyError:
            if default is undefined:
                raise TypedAttributeLookupError("Attribute not found") from None
            else:
                return default

        return getter()
