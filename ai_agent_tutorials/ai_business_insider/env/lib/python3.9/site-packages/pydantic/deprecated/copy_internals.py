from __future__ import annotations as _annotations

import typing
from copy import deepcopy
from enum import Enum
from typing import Any, Tuple

import typing_extensions

from .._internal import (
    _model_construction,
    _typing_extra,
    _utils,
)

if typing.TYPE_CHECKING:
    from .. import BaseModel
    from .._internal._utils import AbstractSetIntStr, MappingIntStrAny

    AnyClassMethod = classmethod[Any, Any, Any]
    TupleGenerator = typing.Generator[Tuple[str, Any], None, None]
    Model = typing.TypeVar('Model', bound='BaseModel')
    # should be `set[int] | set[str] | dict[int, IncEx] | dict[str, IncEx] | None`, but mypy can't cope
    IncEx: typing_extensions.TypeAlias = 'set[int] | set[str] | dict[int, Any] | dict[str, Any] | None'

_object_setattr = _model_construction.object_setattr


def _iter(
    self: BaseModel,
    to_dict: bool = False,
    by_alias: bool = False,
    include: AbstractSetIntStr | MappingIntStrAny | None = None,
    exclude: AbstractSetIntStr | MappingIntStrAny | None = None,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
) -> TupleGenerator:
    # Merge field set excludes with explicit exclude parameter with explicit overriding field set options.
    # The extra "is not None" guards are not logically necessary but optimizes performance for the simple case.
    if exclude is not None:
        exclude = _utils.ValueItems.merge(
            {k: v.exclude for k, v in self.__pydantic_fields__.items() if v.exclude is not None}, exclude
        )

    if include is not None:
        include = _utils.ValueItems.merge({k: True for k in self.__pydantic_fields__}, include, intersect=True)

    allowed_keys = _calculate_keys(self, include=include, exclude=exclude, exclude_unset=exclude_unset)  # type: ignore
    if allowed_keys is None and not (to_dict or by_alias or exclude_unset or exclude_defaults or exclude_none):
        # huge boost for plain _iter()
        yield from self.__dict__.items()
        if self.__pydantic_extra__:
            yield from self.__pydantic_extra__.items()
        return

    value_exclude = _utils.ValueItems(self, exclude) if exclude is not None else None
    value_include = _utils.ValueItems(self, include) if include is not None else None

    if self.__pydantic_extra__ is None:
        items = self.__dict__.items()
    else:
        items = list(self.__dict__.items()) + list(self.__pydantic_extra__.items())

    for field_key, v in items:
        if (allowed_keys is not None and field_key not in allowed_keys) or (exclude_none and v is None):
            continue

        if exclude_defaults:
            try:
                field = self.__pydantic_fields__[field_key]
            except KeyError:
                pass
            else:
                if not field.is_required() and field.default == v:
                    continue

        if by_alias and field_key in self.__pydantic_fields__:
            dict_key = self.__pydantic_fields__[field_key].alias or field_key
        else:
            dict_key = field_key

        if to_dict or value_include or value_exclude:
            v = _get_value(
                type(self),
                v,
                to_dict=to_dict,
                by_alias=by_alias,
                include=value_include and value_include.for_element(field_key),
                exclude=value_exclude and value_exclude.for_element(field_key),
                exclude_unset=exclude_unset,
                exclude_defaults=exclude_defaults,
                exclude_none=exclude_none,
            )
        yield dict_key, v


def _copy_and_set_values(
    self: Model,
    values: dict[str, Any],
    fields_set: set[str],
    extra: dict[str, Any] | None = None,
    private: dict[str, Any] | None = None,
    *,
    deep: bool,  # UP006
) -> Model:
    if deep:
        # chances of having empty dict here are quite low for using smart_deepcopy
        values = deepcopy(values)
        extra = deepcopy(extra)
        private = deepcopy(private)

    cls = self.__class__
    m = cls.__new__(cls)
    _object_setattr(m, '__dict__', values)
    _object_setattr(m, '__pydantic_extra__', extra)
    _object_setattr(m, '__pydantic_fields_set__', fields_set)
    _object_setattr(m, '__pydantic_private__', private)

    return m


@typing.no_type_check
def _get_value(
    cls: type[BaseModel],
    v: Any,
    to_dict: bool,
    by_alias: bool,
    include: AbstractSetIntStr | MappingIntStrAny | None,
    exclude: AbstractSetIntStr | MappingIntStrAny | None,
    exclude_unset: bool,
    exclude_defaults: bool,
    exclude_none: bool,
) -> Any:
    from .. import BaseModel

    if isinstance(v, BaseModel):
        if to_dict:
            return v.model_dump(
                by_alias=by_alias,
                exclude_unset=exclude_unset,
                exclude_defaults=exclude_defaults,
                include=include,  # type: ignore
                exclude=exclude,  # type: ignore
                exclude_none=exclude_none,
            )
        else:
            return v.copy(include=include, exclude=exclude)

    value_exclude = _utils.ValueItems(v, exclude) if exclude else None
    value_include = _utils.ValueItems(v, include) if include else None

    if isinstance(v, dict):
        return {
            k_: _get_value(
                cls,
                v_,
                to_dict=to_dict,
                by_alias=by_alias,
                exclude_unset=exclude_unset,
                exclude_defaults=exclude_defaults,
                include=value_include and value_include.for_element(k_),
                exclude=value_exclude and value_exclude.for_element(k_),
                exclude_none=exclude_none,
            )
            for k_, v_ in v.items()
            if (not value_exclude or not value_exclude.is_excluded(k_))
            and (not value_include or value_include.is_included(k_))
        }

    elif _utils.sequence_like(v):
        seq_args = (
            _get_value(
                cls,
                v_,
                to_dict=to_dict,
                by_alias=by_alias,
                exclude_unset=exclude_unset,
                exclude_defaults=exclude_defaults,
                include=value_include and value_include.for_element(i),
                exclude=value_exclude and value_exclude.for_element(i),
                exclude_none=exclude_none,
            )
            for i, v_ in enumerate(v)
            if (not value_exclude or not value_exclude.is_excluded(i))
            and (not value_include or value_include.is_included(i))
        )

        return v.__class__(*seq_args) if _typing_extra.is_namedtuple(v.__class__) else v.__class__(seq_args)

    elif isinstance(v, Enum) and getattr(cls.model_config, 'use_enum_values', False):
        return v.value

    else:
        return v


def _calculate_keys(
    self: BaseModel,
    include: MappingIntStrAny | None,
    exclude: MappingIntStrAny | None,
    exclude_unset: bool,
    update: typing.Dict[str, Any] | None = None,  # noqa UP006
) -> typing.AbstractSet[str] | None:
    if include is None and exclude is None and exclude_unset is False:
        return None

    keys: typing.AbstractSet[str]
    if exclude_unset:
        keys = self.__pydantic_fields_set__.copy()
    else:
        keys = set(self.__dict__.keys())
        keys = keys | (self.__pydantic_extra__ or {}).keys()

    if include is not None:
        keys &= include.keys()

    if update:
        keys -= update.keys()

    if exclude:
        keys -= {k for k, v in exclude.items() if _utils.ValueItems.is_true(v)}

    return keys
