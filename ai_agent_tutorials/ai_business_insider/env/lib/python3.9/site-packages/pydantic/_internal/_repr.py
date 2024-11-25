"""Tools to provide pretty/human-readable display of objects."""

from __future__ import annotations as _annotations

import types
import typing
from typing import Any

import typing_extensions

from . import _typing_extra

if typing.TYPE_CHECKING:
    ReprArgs: typing_extensions.TypeAlias = 'typing.Iterable[tuple[str | None, Any]]'
    RichReprResult: typing_extensions.TypeAlias = (
        'typing.Iterable[Any | tuple[Any] | tuple[str, Any] | tuple[str, Any, Any]]'
    )


class PlainRepr(str):
    """String class where repr doesn't include quotes. Useful with Representation when you want to return a string
    representation of something that is valid (or pseudo-valid) python.
    """

    def __repr__(self) -> str:
        return str(self)


class Representation:
    # Mixin to provide `__str__`, `__repr__`, and `__pretty__` and `__rich_repr__` methods.
    # `__pretty__` is used by [devtools](https://python-devtools.helpmanual.io/).
    # `__rich_repr__` is used by [rich](https://rich.readthedocs.io/en/stable/pretty.html).
    # (this is not a docstring to avoid adding a docstring to classes which inherit from Representation)

    # we don't want to use a type annotation here as it can break get_type_hints
    __slots__ = ()  # type: typing.Collection[str]

    def __repr_args__(self) -> ReprArgs:
        """Returns the attributes to show in __str__, __repr__, and __pretty__ this is generally overridden.

        Can either return:
        * name - value pairs, e.g.: `[('foo_name', 'foo'), ('bar_name', ['b', 'a', 'r'])]`
        * or, just values, e.g.: `[(None, 'foo'), (None, ['b', 'a', 'r'])]`
        """
        attrs_names = self.__slots__
        if not attrs_names and hasattr(self, '__dict__'):
            attrs_names = self.__dict__.keys()
        attrs = ((s, getattr(self, s)) for s in attrs_names)
        return [(a, v if v is not self else self.__repr_recursion__(v)) for a, v in attrs if v is not None]

    def __repr_name__(self) -> str:
        """Name of the instance's class, used in __repr__."""
        return self.__class__.__name__

    def __repr_recursion__(self, object: Any) -> str:
        """Returns the string representation of a recursive object."""
        # This is copied over from the stdlib `pprint` module:
        return f'<Recursion on {type(object).__name__} with id={id(object)}>'

    def __repr_str__(self, join_str: str) -> str:
        return join_str.join(repr(v) if a is None else f'{a}={v!r}' for a, v in self.__repr_args__())

    def __pretty__(self, fmt: typing.Callable[[Any], Any], **kwargs: Any) -> typing.Generator[Any, None, None]:
        """Used by devtools (https://python-devtools.helpmanual.io/) to pretty print objects."""
        yield self.__repr_name__() + '('
        yield 1
        for name, value in self.__repr_args__():
            if name is not None:
                yield name + '='
            yield fmt(value)
            yield ','
            yield 0
        yield -1
        yield ')'

    def __rich_repr__(self) -> RichReprResult:
        """Used by Rich (https://rich.readthedocs.io/en/stable/pretty.html) to pretty print objects."""
        for name, field_repr in self.__repr_args__():
            if name is None:
                yield field_repr
            else:
                yield name, field_repr

    def __str__(self) -> str:
        return self.__repr_str__(' ')

    def __repr__(self) -> str:
        return f'{self.__repr_name__()}({self.__repr_str__(", ")})'


def display_as_type(obj: Any) -> str:
    """Pretty representation of a type, should be as close as possible to the original type definition string.

    Takes some logic from `typing._type_repr`.
    """
    if isinstance(obj, (types.FunctionType, types.BuiltinFunctionType)):
        return obj.__name__
    elif obj is ...:
        return '...'
    elif isinstance(obj, Representation):
        return repr(obj)
    elif isinstance(obj, typing.ForwardRef) or _typing_extra.is_type_alias_type(obj):
        return str(obj)

    if not isinstance(obj, (_typing_extra.typing_base, _typing_extra.WithArgsTypes, type)):
        obj = obj.__class__

    if _typing_extra.origin_is_union(typing_extensions.get_origin(obj)):
        args = ', '.join(map(display_as_type, typing_extensions.get_args(obj)))
        return f'Union[{args}]'
    elif isinstance(obj, _typing_extra.WithArgsTypes):
        if _typing_extra.is_literal(obj):
            args = ', '.join(map(repr, typing_extensions.get_args(obj)))
        else:
            args = ', '.join(map(display_as_type, typing_extensions.get_args(obj)))
        try:
            return f'{obj.__qualname__}[{args}]'
        except AttributeError:
            return str(obj).replace('typing.', '').replace('typing_extensions.', '')  # handles TypeAliasType in 3.12
    elif isinstance(obj, type):
        return obj.__qualname__
    else:
        return repr(obj).replace('typing.', '').replace('typing_extensions.', '')
