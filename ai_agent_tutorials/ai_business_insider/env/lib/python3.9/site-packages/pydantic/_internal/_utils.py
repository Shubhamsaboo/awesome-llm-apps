"""Bucket of reusable internal utilities.

This should be reduced as much as possible with functions only used in one place, moved to that place.
"""

from __future__ import annotations as _annotations

import dataclasses
import keyword
import typing
import weakref
from collections import OrderedDict, defaultdict, deque
from copy import deepcopy
from functools import cached_property
from inspect import Parameter
from itertools import zip_longest
from types import BuiltinFunctionType, CodeType, FunctionType, GeneratorType, LambdaType, ModuleType
from typing import Any, Callable, Mapping, TypeVar

from typing_extensions import TypeAlias, TypeGuard

from . import _repr, _typing_extra
from ._import_utils import import_cached_base_model

if typing.TYPE_CHECKING:
    MappingIntStrAny: TypeAlias = 'typing.Mapping[int, Any] | typing.Mapping[str, Any]'
    AbstractSetIntStr: TypeAlias = 'typing.AbstractSet[int] | typing.AbstractSet[str]'
    from ..main import BaseModel


# these are types that are returned unchanged by deepcopy
IMMUTABLE_NON_COLLECTIONS_TYPES: set[type[Any]] = {
    int,
    float,
    complex,
    str,
    bool,
    bytes,
    type,
    _typing_extra.NoneType,
    FunctionType,
    BuiltinFunctionType,
    LambdaType,
    weakref.ref,
    CodeType,
    # note: including ModuleType will differ from behaviour of deepcopy by not producing error.
    # It might be not a good idea in general, but considering that this function used only internally
    # against default values of fields, this will allow to actually have a field with module as default value
    ModuleType,
    NotImplemented.__class__,
    Ellipsis.__class__,
}

# these are types that if empty, might be copied with simple copy() instead of deepcopy()
BUILTIN_COLLECTIONS: set[type[Any]] = {
    list,
    set,
    tuple,
    frozenset,
    dict,
    OrderedDict,
    defaultdict,
    deque,
}


def can_be_positional(param: Parameter) -> bool:
    """Return whether the parameter accepts a positional argument.

    ```python {test="skip" lint="skip"}
    def func(a, /, b, *, c):
        pass

    params = inspect.signature(func).parameters
    can_be_positional(params['a'])
    #> True
    can_be_positional(params['b'])
    #> True
    can_be_positional(params['c'])
    #> False
    ```
    """
    return param.kind in (Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD)


def sequence_like(v: Any) -> bool:
    return isinstance(v, (list, tuple, set, frozenset, GeneratorType, deque))


def lenient_isinstance(o: Any, class_or_tuple: type[Any] | tuple[type[Any], ...] | None) -> bool:  # pragma: no cover
    try:
        return isinstance(o, class_or_tuple)  # type: ignore[arg-type]
    except TypeError:
        return False


def lenient_issubclass(cls: Any, class_or_tuple: Any) -> bool:  # pragma: no cover
    try:
        return isinstance(cls, type) and issubclass(cls, class_or_tuple)
    except TypeError:
        if isinstance(cls, _typing_extra.WithArgsTypes):
            return False
        raise  # pragma: no cover


def is_model_class(cls: Any) -> TypeGuard[type[BaseModel]]:
    """Returns true if cls is a _proper_ subclass of BaseModel, and provides proper type-checking,
    unlike raw calls to lenient_issubclass.
    """
    BaseModel = import_cached_base_model()

    return lenient_issubclass(cls, BaseModel) and cls is not BaseModel


def is_valid_identifier(identifier: str) -> bool:
    """Checks that a string is a valid identifier and not a Python keyword.
    :param identifier: The identifier to test.
    :return: True if the identifier is valid.
    """
    return identifier.isidentifier() and not keyword.iskeyword(identifier)


KeyType = TypeVar('KeyType')


def deep_update(mapping: dict[KeyType, Any], *updating_mappings: dict[KeyType, Any]) -> dict[KeyType, Any]:
    updated_mapping = mapping.copy()
    for updating_mapping in updating_mappings:
        for k, v in updating_mapping.items():
            if k in updated_mapping and isinstance(updated_mapping[k], dict) and isinstance(v, dict):
                updated_mapping[k] = deep_update(updated_mapping[k], v)
            else:
                updated_mapping[k] = v
    return updated_mapping


def update_not_none(mapping: dict[Any, Any], **update: Any) -> None:
    mapping.update({k: v for k, v in update.items() if v is not None})


T = TypeVar('T')


def unique_list(
    input_list: list[T] | tuple[T, ...],
    *,
    name_factory: typing.Callable[[T], str] = str,
) -> list[T]:
    """Make a list unique while maintaining order.
    We update the list if another one with the same name is set
    (e.g. model validator overridden in subclass).
    """
    result: list[T] = []
    result_names: list[str] = []
    for v in input_list:
        v_name = name_factory(v)
        if v_name not in result_names:
            result_names.append(v_name)
            result.append(v)
        else:
            result[result_names.index(v_name)] = v

    return result


class ValueItems(_repr.Representation):
    """Class for more convenient calculation of excluded or included fields on values."""

    __slots__ = ('_items', '_type')

    def __init__(self, value: Any, items: AbstractSetIntStr | MappingIntStrAny) -> None:
        items = self._coerce_items(items)

        if isinstance(value, (list, tuple)):
            items = self._normalize_indexes(items, len(value))  # type: ignore

        self._items: MappingIntStrAny = items  # type: ignore

    def is_excluded(self, item: Any) -> bool:
        """Check if item is fully excluded.

        :param item: key or index of a value
        """
        return self.is_true(self._items.get(item))

    def is_included(self, item: Any) -> bool:
        """Check if value is contained in self._items.

        :param item: key or index of value
        """
        return item in self._items

    def for_element(self, e: int | str) -> AbstractSetIntStr | MappingIntStrAny | None:
        """:param e: key or index of element on value
        :return: raw values for element if self._items is dict and contain needed element
        """
        item = self._items.get(e)  # type: ignore
        return item if not self.is_true(item) else None

    def _normalize_indexes(self, items: MappingIntStrAny, v_length: int) -> dict[int | str, Any]:
        """:param items: dict or set of indexes which will be normalized
        :param v_length: length of sequence indexes of which will be

        >>> self._normalize_indexes({0: True, -2: True, -1: True}, 4)
        {0: True, 2: True, 3: True}
        >>> self._normalize_indexes({'__all__': True}, 4)
        {0: True, 1: True, 2: True, 3: True}
        """
        normalized_items: dict[int | str, Any] = {}
        all_items = None
        for i, v in items.items():
            if not (isinstance(v, typing.Mapping) or isinstance(v, typing.AbstractSet) or self.is_true(v)):
                raise TypeError(f'Unexpected type of exclude value for index "{i}" {v.__class__}')
            if i == '__all__':
                all_items = self._coerce_value(v)
                continue
            if not isinstance(i, int):
                raise TypeError(
                    'Excluding fields from a sequence of sub-models or dicts must be performed index-wise: '
                    'expected integer keys or keyword "__all__"'
                )
            normalized_i = v_length + i if i < 0 else i
            normalized_items[normalized_i] = self.merge(v, normalized_items.get(normalized_i))

        if not all_items:
            return normalized_items
        if self.is_true(all_items):
            for i in range(v_length):
                normalized_items.setdefault(i, ...)
            return normalized_items
        for i in range(v_length):
            normalized_item = normalized_items.setdefault(i, {})
            if not self.is_true(normalized_item):
                normalized_items[i] = self.merge(all_items, normalized_item)
        return normalized_items

    @classmethod
    def merge(cls, base: Any, override: Any, intersect: bool = False) -> Any:
        """Merge a `base` item with an `override` item.

        Both `base` and `override` are converted to dictionaries if possible.
        Sets are converted to dictionaries with the sets entries as keys and
        Ellipsis as values.

        Each key-value pair existing in `base` is merged with `override`,
        while the rest of the key-value pairs are updated recursively with this function.

        Merging takes place based on the "union" of keys if `intersect` is
        set to `False` (default) and on the intersection of keys if
        `intersect` is set to `True`.
        """
        override = cls._coerce_value(override)
        base = cls._coerce_value(base)
        if override is None:
            return base
        if cls.is_true(base) or base is None:
            return override
        if cls.is_true(override):
            return base if intersect else override

        # intersection or union of keys while preserving ordering:
        if intersect:
            merge_keys = [k for k in base if k in override] + [k for k in override if k in base]
        else:
            merge_keys = list(base) + [k for k in override if k not in base]

        merged: dict[int | str, Any] = {}
        for k in merge_keys:
            merged_item = cls.merge(base.get(k), override.get(k), intersect=intersect)
            if merged_item is not None:
                merged[k] = merged_item

        return merged

    @staticmethod
    def _coerce_items(items: AbstractSetIntStr | MappingIntStrAny) -> MappingIntStrAny:
        if isinstance(items, typing.Mapping):
            pass
        elif isinstance(items, typing.AbstractSet):
            items = dict.fromkeys(items, ...)  # type: ignore
        else:
            class_name = getattr(items, '__class__', '???')
            raise TypeError(f'Unexpected type of exclude value {class_name}')
        return items  # type: ignore

    @classmethod
    def _coerce_value(cls, value: Any) -> Any:
        if value is None or cls.is_true(value):
            return value
        return cls._coerce_items(value)

    @staticmethod
    def is_true(v: Any) -> bool:
        return v is True or v is ...

    def __repr_args__(self) -> _repr.ReprArgs:
        return [(None, self._items)]


if typing.TYPE_CHECKING:

    def LazyClassAttribute(name: str, get_value: Callable[[], T]) -> T: ...

else:

    class LazyClassAttribute:
        """A descriptor exposing an attribute only accessible on a class (hidden from instances).

        The attribute is lazily computed and cached during the first access.
        """

        def __init__(self, name: str, get_value: Callable[[], Any]) -> None:
            self.name = name
            self.get_value = get_value

        @cached_property
        def value(self) -> Any:
            return self.get_value()

        def __get__(self, instance: Any, owner: type[Any]) -> None:
            if instance is None:
                return self.value
            raise AttributeError(f'{self.name!r} attribute of {owner.__name__!r} is class-only')


Obj = TypeVar('Obj')


def smart_deepcopy(obj: Obj) -> Obj:
    """Return type as is for immutable built-in types
    Use obj.copy() for built-in empty collections
    Use copy.deepcopy() for non-empty collections and unknown objects.
    """
    obj_type = obj.__class__
    if obj_type in IMMUTABLE_NON_COLLECTIONS_TYPES:
        return obj  # fastest case: obj is immutable and not collection therefore will not be copied anyway
    try:
        if not obj and obj_type in BUILTIN_COLLECTIONS:
            # faster way for empty collections, no need to copy its members
            return obj if obj_type is tuple else obj.copy()  # tuple doesn't have copy method  # type: ignore
    except (TypeError, ValueError, RuntimeError):
        # do we really dare to catch ALL errors? Seems a bit risky
        pass

    return deepcopy(obj)  # slowest way when we actually might need a deepcopy


_SENTINEL = object()


def all_identical(left: typing.Iterable[Any], right: typing.Iterable[Any]) -> bool:
    """Check that the items of `left` are the same objects as those in `right`.

    >>> a, b = object(), object()
    >>> all_identical([a, b, a], [a, b, a])
    True
    >>> all_identical([a, b, [a]], [a, b, [a]])  # new list object, while "equal" is not "identical"
    False
    """
    for left_item, right_item in zip_longest(left, right, fillvalue=_SENTINEL):
        if left_item is not right_item:
            return False
    return True


@dataclasses.dataclass(frozen=True)
class SafeGetItemProxy:
    """Wrapper redirecting `__getitem__` to `get` with a sentinel value as default

    This makes is safe to use in `operator.itemgetter` when some keys may be missing
    """

    # Define __slots__manually for performances
    # @dataclasses.dataclass() only support slots=True in python>=3.10
    __slots__ = ('wrapped',)

    wrapped: Mapping[str, Any]

    def __getitem__(self, key: str, /) -> Any:
        return self.wrapped.get(key, _SENTINEL)

    # required to pass the object to operator.itemgetter() instances due to a quirk of typeshed
    # https://github.com/python/mypy/issues/13713
    # https://github.com/python/typeshed/pull/8785
    # Since this is typing-only, hide it in a typing.TYPE_CHECKING block
    if typing.TYPE_CHECKING:

        def __contains__(self, key: str, /) -> bool:
            return self.wrapped.__contains__(key)
