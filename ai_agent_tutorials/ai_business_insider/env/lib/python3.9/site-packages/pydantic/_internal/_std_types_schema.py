"""Logic for generating pydantic-core schemas for standard library types.

Import of this module is deferred since it contains imports of many standard library modules.
"""

# TODO: eventually, we'd like to move all of the types handled here to have pydantic-core validators
# so that we can avoid this annotation injection and just use the standard pydantic-core schema generation

from __future__ import annotations as _annotations

import collections
import collections.abc
import dataclasses
import os
import typing
from functools import partial
from typing import Any, Callable, Iterable, Tuple, TypeVar, cast

import typing_extensions
from pydantic_core import (
    CoreSchema,
    PydanticCustomError,
    core_schema,
)
from typing_extensions import get_args, get_origin

from pydantic._internal._serializers import serialize_sequence_via_list
from pydantic.errors import PydanticSchemaGenerationError
from pydantic.types import Strict

from ..json_schema import JsonSchemaValue
from . import _known_annotated_metadata, _typing_extra
from ._import_utils import import_cached_field_info
from ._internal_dataclass import slots_true
from ._schema_generation_shared import GetCoreSchemaHandler, GetJsonSchemaHandler

FieldInfo = import_cached_field_info()

if typing.TYPE_CHECKING:
    from ._generate_schema import GenerateSchema

    StdSchemaFunction = Callable[[GenerateSchema, type[Any]], core_schema.CoreSchema]


@dataclasses.dataclass(**slots_true)
class InnerSchemaValidator:
    """Use a fixed CoreSchema, avoiding interference from outward annotations."""

    core_schema: CoreSchema
    js_schema: JsonSchemaValue | None = None
    js_core_schema: CoreSchema | None = None
    js_schema_update: JsonSchemaValue | None = None

    def __get_pydantic_json_schema__(self, _schema: CoreSchema, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
        if self.js_schema is not None:
            return self.js_schema
        js_schema = handler(self.js_core_schema or self.core_schema)
        if self.js_schema_update is not None:
            js_schema.update(self.js_schema_update)
        return js_schema

    def __get_pydantic_core_schema__(self, _source_type: Any, _handler: GetCoreSchemaHandler) -> CoreSchema:
        return self.core_schema


def path_schema_prepare_pydantic_annotations(
    source_type: Any, annotations: Iterable[Any]
) -> tuple[Any, list[Any]] | None:
    import pathlib

    orig_source_type: Any = get_origin(source_type) or source_type
    if (
        (source_type_args := get_args(source_type))
        and orig_source_type is os.PathLike
        and source_type_args[0] not in {str, bytes, Any}
    ):
        return None

    if orig_source_type not in {
        os.PathLike,
        pathlib.Path,
        pathlib.PurePath,
        pathlib.PosixPath,
        pathlib.PurePosixPath,
        pathlib.PureWindowsPath,
    }:
        return None

    metadata, remaining_annotations = _known_annotated_metadata.collect_known_metadata(annotations)
    _known_annotated_metadata.check_metadata(metadata, _known_annotated_metadata.STR_CONSTRAINTS, orig_source_type)

    is_first_arg_byte = source_type_args and source_type_args[0] is bytes
    construct_path = pathlib.PurePath if orig_source_type is os.PathLike else orig_source_type
    constrained_schema = (
        core_schema.bytes_schema(**metadata) if is_first_arg_byte else core_schema.str_schema(**metadata)
    )

    def path_validator(input_value: str | bytes) -> os.PathLike[Any]:  # type: ignore
        try:
            if is_first_arg_byte:
                if isinstance(input_value, bytes):
                    try:
                        input_value = input_value.decode()
                    except UnicodeDecodeError as e:
                        raise PydanticCustomError('bytes_type', 'Input must be valid bytes') from e
                else:
                    raise PydanticCustomError('bytes_type', 'Input must be bytes')
            elif not isinstance(input_value, str):
                raise PydanticCustomError('path_type', 'Input is not a valid path')

            return construct_path(input_value)
        except TypeError as e:
            raise PydanticCustomError('path_type', 'Input is not a valid path') from e

    instance_schema = core_schema.json_or_python_schema(
        json_schema=core_schema.no_info_after_validator_function(path_validator, constrained_schema),
        python_schema=core_schema.is_instance_schema(orig_source_type),
    )

    strict: bool | None = None
    for annotation in annotations:
        if isinstance(annotation, Strict):
            strict = annotation.strict

    schema = core_schema.lax_or_strict_schema(
        lax_schema=core_schema.union_schema(
            [
                instance_schema,
                core_schema.no_info_after_validator_function(path_validator, constrained_schema),
            ],
            custom_error_type='path_type',
            custom_error_message=f'Input is not a valid path for {orig_source_type}',
            strict=True,
        ),
        strict_schema=instance_schema,
        serialization=core_schema.to_string_ser_schema(),
        strict=strict,
    )

    return (
        orig_source_type,
        [
            InnerSchemaValidator(schema, js_core_schema=constrained_schema, js_schema_update={'format': 'path'}),
            *remaining_annotations,
        ],
    )


def deque_validator(
    input_value: Any, handler: core_schema.ValidatorFunctionWrapHandler, maxlen: None | int
) -> collections.deque[Any]:
    if isinstance(input_value, collections.deque):
        maxlens = [v for v in (input_value.maxlen, maxlen) if v is not None]
        if maxlens:
            maxlen = min(maxlens)
        return collections.deque(handler(input_value), maxlen=maxlen)
    else:
        return collections.deque(handler(input_value), maxlen=maxlen)


@dataclasses.dataclass(**slots_true)
class DequeValidator:
    item_source_type: type[Any]
    metadata: dict[str, Any]

    def __get_pydantic_core_schema__(self, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        if _typing_extra.is_any(self.item_source_type):
            items_schema = None
        else:
            items_schema = handler.generate_schema(self.item_source_type)

        # if we have a MaxLen annotation might as well set that as the default maxlen on the deque
        # this lets us reuse existing metadata annotations to let users set the maxlen on a dequeue
        # that e.g. comes from JSON
        coerce_instance_wrap = partial(
            core_schema.no_info_wrap_validator_function,
            partial(deque_validator, maxlen=self.metadata.get('max_length', None)),
        )

        # we have to use a lax list schema here, because we need to validate the deque's
        # items via a list schema, but it's ok if the deque itself is not a list
        metadata_with_strict_override = {**self.metadata, 'strict': False}
        constrained_schema = core_schema.list_schema(items_schema, **metadata_with_strict_override)

        check_instance = core_schema.json_or_python_schema(
            json_schema=core_schema.list_schema(),
            python_schema=core_schema.is_instance_schema(collections.deque),
        )

        serialization = core_schema.wrap_serializer_function_ser_schema(
            serialize_sequence_via_list, schema=items_schema or core_schema.any_schema(), info_arg=True
        )

        strict = core_schema.chain_schema([check_instance, coerce_instance_wrap(constrained_schema)])

        if self.metadata.get('strict', False):
            schema = strict
        else:
            lax = coerce_instance_wrap(constrained_schema)
            schema = core_schema.lax_or_strict_schema(lax_schema=lax, strict_schema=strict)
        schema['serialization'] = serialization

        return schema


def deque_schema_prepare_pydantic_annotations(
    source_type: Any, annotations: Iterable[Any]
) -> tuple[Any, list[Any]] | None:
    args = get_args(source_type)

    if not args:
        args = typing.cast(Tuple[Any], (Any,))
    elif len(args) != 1:
        raise ValueError('Expected deque to have exactly 1 generic parameter')

    item_source_type = args[0]

    metadata, remaining_annotations = _known_annotated_metadata.collect_known_metadata(annotations)
    _known_annotated_metadata.check_metadata(metadata, _known_annotated_metadata.SEQUENCE_CONSTRAINTS, source_type)

    return (source_type, [DequeValidator(item_source_type, metadata), *remaining_annotations])


MAPPING_ORIGIN_MAP: dict[Any, Any] = {
    typing.DefaultDict: collections.defaultdict,
    collections.defaultdict: collections.defaultdict,
    collections.OrderedDict: collections.OrderedDict,
    typing_extensions.OrderedDict: collections.OrderedDict,
    dict: dict,
    typing.Dict: dict,
    collections.Counter: collections.Counter,
    typing.Counter: collections.Counter,
    # this doesn't handle subclasses of these
    typing.Mapping: dict,
    typing.MutableMapping: dict,
    # parametrized typing.{Mutable}Mapping creates one of these
    collections.abc.MutableMapping: dict,
    collections.abc.Mapping: dict,
}


def defaultdict_validator(
    input_value: Any, handler: core_schema.ValidatorFunctionWrapHandler, default_default_factory: Callable[[], Any]
) -> collections.defaultdict[Any, Any]:
    if isinstance(input_value, collections.defaultdict):
        default_factory = input_value.default_factory
        return collections.defaultdict(default_factory, handler(input_value))
    else:
        return collections.defaultdict(default_default_factory, handler(input_value))


def get_defaultdict_default_default_factory(values_source_type: Any) -> Callable[[], Any]:
    def infer_default() -> Callable[[], Any]:
        allowed_default_types: dict[Any, Any] = {
            typing.Tuple: tuple,
            tuple: tuple,
            collections.abc.Sequence: tuple,
            collections.abc.MutableSequence: list,
            typing.List: list,
            list: list,
            typing.Sequence: list,
            typing.Set: set,
            set: set,
            typing.MutableSet: set,
            collections.abc.MutableSet: set,
            collections.abc.Set: frozenset,
            typing.MutableMapping: dict,
            typing.Mapping: dict,
            collections.abc.Mapping: dict,
            collections.abc.MutableMapping: dict,
            float: float,
            int: int,
            str: str,
            bool: bool,
        }
        values_type_origin = get_origin(values_source_type) or values_source_type
        instructions = 'set using `DefaultDict[..., Annotated[..., Field(default_factory=...)]]`'
        if isinstance(values_type_origin, TypeVar):

            def type_var_default_factory() -> None:
                raise RuntimeError(
                    'Generic defaultdict cannot be used without a concrete value type or an'
                    ' explicit default factory, ' + instructions
                )

            return type_var_default_factory
        elif values_type_origin not in allowed_default_types:
            # a somewhat subjective set of types that have reasonable default values
            allowed_msg = ', '.join([t.__name__ for t in set(allowed_default_types.values())])
            raise PydanticSchemaGenerationError(
                f'Unable to infer a default factory for keys of type {values_source_type}.'
                f' Only {allowed_msg} are supported, other types require an explicit default factory'
                ' ' + instructions
            )
        return allowed_default_types[values_type_origin]

    # Assume Annotated[..., Field(...)]
    if _typing_extra.is_annotated(values_source_type):
        field_info = next((v for v in get_args(values_source_type) if isinstance(v, FieldInfo)), None)
    else:
        field_info = None
    if field_info and field_info.default_factory:
        # Assume the default factory does not take any argument:
        default_default_factory = cast(Callable[[], Any], field_info.default_factory)
    else:
        default_default_factory = infer_default()
    return default_default_factory


@dataclasses.dataclass(**slots_true)
class MappingValidator:
    mapped_origin: type[Any]
    keys_source_type: type[Any]
    values_source_type: type[Any]
    min_length: int | None = None
    max_length: int | None = None
    strict: bool = False

    def serialize_mapping_via_dict(self, v: Any, handler: core_schema.SerializerFunctionWrapHandler) -> Any:
        return handler(v)

    def __get_pydantic_core_schema__(self, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        if _typing_extra.is_any(self.keys_source_type):
            keys_schema = None
        else:
            keys_schema = handler.generate_schema(self.keys_source_type)
        if _typing_extra.is_any(self.values_source_type):
            values_schema = None
        else:
            values_schema = handler.generate_schema(self.values_source_type)

        metadata = {'min_length': self.min_length, 'max_length': self.max_length, 'strict': self.strict}

        if self.mapped_origin is dict:
            schema = core_schema.dict_schema(keys_schema, values_schema, **metadata)
        else:
            constrained_schema = core_schema.dict_schema(keys_schema, values_schema, **metadata)
            check_instance = core_schema.json_or_python_schema(
                json_schema=core_schema.dict_schema(),
                python_schema=core_schema.is_instance_schema(self.mapped_origin),
            )

            if self.mapped_origin is collections.defaultdict:
                default_default_factory = get_defaultdict_default_default_factory(self.values_source_type)
                coerce_instance_wrap = partial(
                    core_schema.no_info_wrap_validator_function,
                    partial(defaultdict_validator, default_default_factory=default_default_factory),
                )
            else:
                coerce_instance_wrap = partial(core_schema.no_info_after_validator_function, self.mapped_origin)

            serialization = core_schema.wrap_serializer_function_ser_schema(
                self.serialize_mapping_via_dict,
                schema=core_schema.dict_schema(
                    keys_schema or core_schema.any_schema(), values_schema or core_schema.any_schema()
                ),
                info_arg=False,
            )

            strict = core_schema.chain_schema([check_instance, coerce_instance_wrap(constrained_schema)])

            if metadata.get('strict', False):
                schema = strict
            else:
                lax = coerce_instance_wrap(constrained_schema)
                schema = core_schema.lax_or_strict_schema(lax_schema=lax, strict_schema=strict)
                schema['serialization'] = serialization

        return schema


def mapping_like_prepare_pydantic_annotations(
    source_type: Any, annotations: Iterable[Any]
) -> tuple[Any, list[Any]] | None:
    origin: Any = get_origin(source_type)

    mapped_origin = MAPPING_ORIGIN_MAP.get(origin, None) if origin else MAPPING_ORIGIN_MAP.get(source_type, None)
    if mapped_origin is None:
        return None

    args = get_args(source_type)

    if not args:
        args = typing.cast(Tuple[Any, Any], (Any, Any))
    elif mapped_origin is collections.Counter:
        # a single generic
        if len(args) != 1:
            raise ValueError('Expected Counter to have exactly 1 generic parameter')
        args = (args[0], int)  # keys are always an int
    elif len(args) != 2:
        raise ValueError('Expected mapping to have exactly 2 generic parameters')

    keys_source_type, values_source_type = args

    metadata, remaining_annotations = _known_annotated_metadata.collect_known_metadata(annotations)
    _known_annotated_metadata.check_metadata(metadata, _known_annotated_metadata.SEQUENCE_CONSTRAINTS, source_type)

    return (
        source_type,
        [
            MappingValidator(mapped_origin, keys_source_type, values_source_type, **metadata),
            *remaining_annotations,
        ],
    )
