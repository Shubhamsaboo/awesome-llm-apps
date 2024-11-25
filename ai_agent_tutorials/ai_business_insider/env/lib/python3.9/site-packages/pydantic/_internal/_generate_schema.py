"""Convert python types to pydantic-core schema."""

from __future__ import annotations as _annotations

import collections.abc
import dataclasses
import datetime
import inspect
import os
import pathlib
import re
import sys
import typing
import warnings
from contextlib import contextmanager
from copy import copy, deepcopy
from decimal import Decimal
from enum import Enum
from fractions import Fraction
from functools import partial
from inspect import Parameter, _ParameterKind, signature
from ipaddress import IPv4Address, IPv4Interface, IPv4Network, IPv6Address, IPv6Interface, IPv6Network
from itertools import chain
from operator import attrgetter
from types import BuiltinFunctionType, BuiltinMethodType, FunctionType, LambdaType, MethodType
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Final,
    ForwardRef,
    Iterable,
    Iterator,
    Mapping,
    Type,
    TypeVar,
    Union,
    cast,
    overload,
)
from uuid import UUID
from warnings import warn

import typing_extensions
from pydantic_core import (
    CoreSchema,
    MultiHostUrl,
    PydanticCustomError,
    PydanticSerializationUnexpectedValue,
    PydanticUndefined,
    Url,
    core_schema,
    to_jsonable_python,
)
from typing_extensions import Literal, TypeAliasType, TypedDict, get_args, get_origin, is_typeddict

from ..aliases import AliasChoices, AliasGenerator, AliasPath
from ..annotated_handlers import GetCoreSchemaHandler, GetJsonSchemaHandler
from ..config import ConfigDict, JsonDict, JsonEncoder, JsonSchemaExtraCallable
from ..errors import PydanticSchemaGenerationError, PydanticUndefinedAnnotation, PydanticUserError
from ..functional_validators import AfterValidator, BeforeValidator, FieldValidatorModes, PlainValidator, WrapValidator
from ..json_schema import JsonSchemaValue
from ..version import version_short
from ..warnings import PydanticDeprecatedSince20
from . import _core_utils, _decorators, _discriminated_union, _known_annotated_metadata, _typing_extra
from ._config import ConfigWrapper, ConfigWrapperStack
from ._core_metadata import update_core_metadata
from ._core_utils import (
    collect_invalid_schemas,
    define_expected_missing_refs,
    get_ref,
    get_type_ref,
    is_function_with_inner_schema,
    is_list_like_schema_with_items_schema,
    simplify_schema_references,
    validate_core_schema,
)
from ._decorators import (
    Decorator,
    DecoratorInfos,
    FieldSerializerDecoratorInfo,
    FieldValidatorDecoratorInfo,
    ModelSerializerDecoratorInfo,
    ModelValidatorDecoratorInfo,
    RootValidatorDecoratorInfo,
    ValidatorDecoratorInfo,
    get_attribute_from_bases,
    inspect_field_serializer,
    inspect_model_serializer,
    inspect_validator,
)
from ._docs_extraction import extract_docstrings_from_cls
from ._fields import collect_dataclass_fields, takes_validated_data_argument
from ._forward_ref import PydanticRecursiveRef
from ._generics import get_standard_typevars_map, has_instance_in_type, recursively_defined_type_refs, replace_types
from ._import_utils import import_cached_base_model, import_cached_field_info
from ._mock_val_ser import MockCoreSchema
from ._namespace_utils import NamespacesTuple, NsResolver
from ._schema_generation_shared import CallbackGetCoreSchemaHandler
from ._utils import lenient_issubclass, smart_deepcopy

if TYPE_CHECKING:
    from ..fields import ComputedFieldInfo, FieldInfo
    from ..main import BaseModel
    from ..types import Discriminator
    from ._dataclasses import StandardDataclass
    from ._schema_generation_shared import GetJsonSchemaFunction

_SUPPORTS_TYPEDDICT = sys.version_info >= (3, 12)

FieldDecoratorInfo = Union[ValidatorDecoratorInfo, FieldValidatorDecoratorInfo, FieldSerializerDecoratorInfo]
FieldDecoratorInfoType = TypeVar('FieldDecoratorInfoType', bound=FieldDecoratorInfo)
AnyFieldDecorator = Union[
    Decorator[ValidatorDecoratorInfo],
    Decorator[FieldValidatorDecoratorInfo],
    Decorator[FieldSerializerDecoratorInfo],
]

ModifyCoreSchemaWrapHandler = GetCoreSchemaHandler
GetCoreSchemaFunction = Callable[[Any, ModifyCoreSchemaWrapHandler], core_schema.CoreSchema]

TUPLE_TYPES: list[type] = [tuple, typing.Tuple]
LIST_TYPES: list[type] = [list, typing.List, collections.abc.MutableSequence]
SET_TYPES: list[type] = [set, typing.Set, collections.abc.MutableSet]
FROZEN_SET_TYPES: list[type] = [frozenset, typing.FrozenSet, collections.abc.Set]
DICT_TYPES: list[type] = [dict, typing.Dict]
IP_TYPES: list[type] = [IPv4Address, IPv4Interface, IPv4Network, IPv6Address, IPv6Interface, IPv6Network]
SEQUENCE_TYPES: list[type] = [typing.Sequence, collections.abc.Sequence]
PATH_TYPES: list[type] = [
    os.PathLike,
    pathlib.Path,
    pathlib.PurePath,
    pathlib.PosixPath,
    pathlib.PurePosixPath,
    pathlib.PureWindowsPath,
]
MAPPING_TYPES = [
    typing.Mapping,
    typing.MutableMapping,
    collections.abc.Mapping,
    collections.abc.MutableMapping,
    collections.OrderedDict,
    typing_extensions.OrderedDict,
    typing.DefaultDict,
    collections.defaultdict,
    collections.Counter,
    typing.Counter,
]
DEQUE_TYPES: list[type] = [collections.deque, typing.Deque]

# Note: This does not play very well with type checkers. For example,
# `a: LambdaType = lambda x: x` will raise a type error by Pyright.
ValidateCallSupportedTypes = Union[
    LambdaType,
    FunctionType,
    MethodType,
    BuiltinFunctionType,
    BuiltinMethodType,
    partial,
]

VALIDATE_CALL_SUPPORTED_TYPES = get_args(ValidateCallSupportedTypes)

_mode_to_validator: dict[
    FieldValidatorModes, type[BeforeValidator | AfterValidator | PlainValidator | WrapValidator]
] = {'before': BeforeValidator, 'after': AfterValidator, 'plain': PlainValidator, 'wrap': WrapValidator}


def check_validator_fields_against_field_name(
    info: FieldDecoratorInfo,
    field: str,
) -> bool:
    """Check if field name is in validator fields.

    Args:
        info: The field info.
        field: The field name to check.

    Returns:
        `True` if field name is in validator fields, `False` otherwise.
    """
    if '*' in info.fields:
        return True
    for v_field_name in info.fields:
        if v_field_name == field:
            return True
    return False


def check_decorator_fields_exist(decorators: Iterable[AnyFieldDecorator], fields: Iterable[str]) -> None:
    """Check if the defined fields in decorators exist in `fields` param.

    It ignores the check for a decorator if the decorator has `*` as field or `check_fields=False`.

    Args:
        decorators: An iterable of decorators.
        fields: An iterable of fields name.

    Raises:
        PydanticUserError: If one of the field names does not exist in `fields` param.
    """
    fields = set(fields)
    for dec in decorators:
        if '*' in dec.info.fields:
            continue
        if dec.info.check_fields is False:
            continue
        for field in dec.info.fields:
            if field not in fields:
                raise PydanticUserError(
                    f'Decorators defined with incorrect fields: {dec.cls_ref}.{dec.cls_var_name}'
                    " (use check_fields=False if you're inheriting from the model and intended this)",
                    code='decorator-missing-field',
                )


def filter_field_decorator_info_by_field(
    validator_functions: Iterable[Decorator[FieldDecoratorInfoType]], field: str
) -> list[Decorator[FieldDecoratorInfoType]]:
    return [dec for dec in validator_functions if check_validator_fields_against_field_name(dec.info, field)]


def apply_each_item_validators(
    schema: core_schema.CoreSchema,
    each_item_validators: list[Decorator[ValidatorDecoratorInfo]],
    field_name: str | None,
) -> core_schema.CoreSchema:
    # This V1 compatibility shim should eventually be removed

    # fail early if each_item_validators is empty
    if not each_item_validators:
        return schema

    # push down any `each_item=True` validators
    # note that this won't work for any Annotated types that get wrapped by a function validator
    # but that's okay because that didn't exist in V1
    if schema['type'] == 'nullable':
        schema['schema'] = apply_each_item_validators(schema['schema'], each_item_validators, field_name)
        return schema
    elif schema['type'] == 'tuple':
        if (variadic_item_index := schema.get('variadic_item_index')) is not None:
            schema['items_schema'][variadic_item_index] = apply_validators(
                schema['items_schema'][variadic_item_index],
                each_item_validators,
                field_name,
            )
    elif is_list_like_schema_with_items_schema(schema):
        inner_schema = schema.get('items_schema', core_schema.any_schema())
        schema['items_schema'] = apply_validators(inner_schema, each_item_validators, field_name)
    elif schema['type'] == 'dict':
        inner_schema = schema.get('values_schema', core_schema.any_schema())
        schema['values_schema'] = apply_validators(inner_schema, each_item_validators, field_name)
    else:
        raise TypeError(
            f"`@validator(..., each_item=True)` cannot be applied to fields with a schema of {schema['type']}"
        )
    return schema


def _extract_json_schema_info_from_field_info(
    info: FieldInfo | ComputedFieldInfo,
) -> tuple[JsonDict | None, JsonDict | JsonSchemaExtraCallable | None]:
    json_schema_updates = {
        'title': info.title,
        'description': info.description,
        'deprecated': bool(info.deprecated) or info.deprecated == '' or None,
        'examples': to_jsonable_python(info.examples),
    }
    json_schema_updates = {k: v for k, v in json_schema_updates.items() if v is not None}
    return (json_schema_updates or None, info.json_schema_extra)


JsonEncoders = Dict[Type[Any], JsonEncoder]


def _add_custom_serialization_from_json_encoders(
    json_encoders: JsonEncoders | None, tp: Any, schema: CoreSchema
) -> CoreSchema:
    """Iterate over the json_encoders and add the first matching encoder to the schema.

    Args:
        json_encoders: A dictionary of types and their encoder functions.
        tp: The type to check for a matching encoder.
        schema: The schema to add the encoder to.
    """
    if not json_encoders:
        return schema
    if 'serialization' in schema:
        return schema
    # Check the class type and its superclasses for a matching encoder
    # Decimal.__class__.__mro__ (and probably other cases) doesn't include Decimal itself
    # if the type is a GenericAlias (e.g. from list[int]) we need to use __class__ instead of .__mro__
    for base in (tp, *getattr(tp, '__mro__', tp.__class__.__mro__)[:-1]):
        encoder = json_encoders.get(base)
        if encoder is None:
            continue

        warnings.warn(
            f'`json_encoders` is deprecated. See https://docs.pydantic.dev/{version_short()}/concepts/serialization/#custom-serializers for alternatives',
            PydanticDeprecatedSince20,
        )

        # TODO: in theory we should check that the schema accepts a serialization key
        schema['serialization'] = core_schema.plain_serializer_function_ser_schema(encoder, when_used='json')
        return schema

    return schema


def _get_first_non_null(a: Any, b: Any) -> Any:
    """Return the first argument if it is not None, otherwise return the second argument.

    Use case: serialization_alias (argument a) and alias (argument b) are both defined, and serialization_alias is ''.
    This function will return serialization_alias, which is the first argument, even though it is an empty string.
    """
    return a if a is not None else b


class GenerateSchema:
    """Generate core schema for a Pydantic model, dataclass and types like `str`, `datetime`, ... ."""

    __slots__ = (
        '_config_wrapper_stack',
        '_ns_resolver',
        '_typevars_map',
        'field_name_stack',
        'model_type_stack',
        'defs',
    )

    def __init__(
        self,
        config_wrapper: ConfigWrapper,
        ns_resolver: NsResolver | None = None,
        typevars_map: dict[Any, Any] | None = None,
    ) -> None:
        # we need a stack for recursing into nested models
        self._config_wrapper_stack = ConfigWrapperStack(config_wrapper)
        self._ns_resolver = ns_resolver or NsResolver()
        self._typevars_map = typevars_map
        self.field_name_stack = _FieldNameStack()
        self.model_type_stack = _ModelTypeStack()
        self.defs = _Definitions()

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        warnings.warn(
            'Subclassing `GenerateSchema` is not supported. The API is highly subject to change in minor versions.',
            UserWarning,
            stacklevel=2,
        )

    @property
    def _config_wrapper(self) -> ConfigWrapper:
        return self._config_wrapper_stack.tail

    @property
    def _types_namespace(self) -> NamespacesTuple:
        return self._ns_resolver.types_namespace

    @property
    def _arbitrary_types(self) -> bool:
        return self._config_wrapper.arbitrary_types_allowed

    # the following methods can be overridden but should be considered
    # unstable / private APIs
    def _list_schema(self, items_type: Any) -> CoreSchema:
        return core_schema.list_schema(self.generate_schema(items_type))

    def _dict_schema(self, keys_type: Any, values_type: Any) -> CoreSchema:
        return core_schema.dict_schema(self.generate_schema(keys_type), self.generate_schema(values_type))

    def _set_schema(self, items_type: Any) -> CoreSchema:
        return core_schema.set_schema(self.generate_schema(items_type))

    def _frozenset_schema(self, items_type: Any) -> CoreSchema:
        return core_schema.frozenset_schema(self.generate_schema(items_type))

    def _enum_schema(self, enum_type: type[Enum]) -> CoreSchema:
        cases: list[Any] = list(enum_type.__members__.values())

        enum_ref = get_type_ref(enum_type)
        description = None if not enum_type.__doc__ else inspect.cleandoc(enum_type.__doc__)
        if (
            description == 'An enumeration.'
        ):  # This is the default value provided by enum.EnumMeta.__new__; don't use it
            description = None
        js_updates = {'title': enum_type.__name__, 'description': description}
        js_updates = {k: v for k, v in js_updates.items() if v is not None}

        sub_type: Literal['str', 'int', 'float'] | None = None
        if issubclass(enum_type, int):
            sub_type = 'int'
            value_ser_type: core_schema.SerSchema = core_schema.simple_ser_schema('int')
        elif issubclass(enum_type, str):
            # this handles `StrEnum` (3.11 only), and also `Foobar(str, Enum)`
            sub_type = 'str'
            value_ser_type = core_schema.simple_ser_schema('str')
        elif issubclass(enum_type, float):
            sub_type = 'float'
            value_ser_type = core_schema.simple_ser_schema('float')
        else:
            # TODO this is an ugly hack, how do we trigger an Any schema for serialization?
            value_ser_type = core_schema.plain_serializer_function_ser_schema(lambda x: x)

        if cases:

            def get_json_schema(schema: CoreSchema, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
                json_schema = handler(schema)
                original_schema = handler.resolve_ref_schema(json_schema)
                original_schema.update(js_updates)
                return json_schema

            # we don't want to add the missing to the schema if it's the default one
            default_missing = getattr(enum_type._missing_, '__func__', None) is Enum._missing_.__func__  # pyright: ignore[reportFunctionMemberAccess]
            enum_schema = core_schema.enum_schema(
                enum_type,
                cases,
                sub_type=sub_type,
                missing=None if default_missing else enum_type._missing_,
                ref=enum_ref,
                metadata={'pydantic_js_functions': [get_json_schema]},
            )

            if self._config_wrapper.use_enum_values:
                enum_schema = core_schema.no_info_after_validator_function(
                    attrgetter('value'), enum_schema, serialization=value_ser_type
                )

            return enum_schema

        else:

            def get_json_schema_no_cases(_, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
                json_schema = handler(core_schema.enum_schema(enum_type, cases, sub_type=sub_type, ref=enum_ref))
                original_schema = handler.resolve_ref_schema(json_schema)
                original_schema.update(js_updates)
                return json_schema

            # Use an isinstance check for enums with no cases.
            # The most important use case for this is creating TypeVar bounds for generics that should
            # be restricted to enums. This is more consistent than it might seem at first, since you can only
            # subclass enum.Enum (or subclasses of enum.Enum) if all parent classes have no cases.
            # We use the get_json_schema function when an Enum subclass has been declared with no cases
            # so that we can still generate a valid json schema.
            return core_schema.is_instance_schema(
                enum_type,
                metadata={'pydantic_js_functions': [get_json_schema_no_cases]},
            )

    def _ip_schema(self, tp: Any) -> CoreSchema:
        from ._validators import IP_VALIDATOR_LOOKUP, IpType

        ip_type_json_schema_format: dict[type[IpType], str] = {
            IPv4Address: 'ipv4',
            IPv4Network: 'ipv4network',
            IPv4Interface: 'ipv4interface',
            IPv6Address: 'ipv6',
            IPv6Network: 'ipv6network',
            IPv6Interface: 'ipv6interface',
        }

        def ser_ip(ip: Any, info: core_schema.SerializationInfo) -> str | IpType:
            if not isinstance(ip, (tp, str)):
                raise PydanticSerializationUnexpectedValue(
                    f"Expected `{tp}` but got `{type(ip)}` with value `'{ip}'` - serialized value may not be as expected."
                )
            if info.mode == 'python':
                return ip
            return str(ip)

        return core_schema.lax_or_strict_schema(
            lax_schema=core_schema.no_info_plain_validator_function(IP_VALIDATOR_LOOKUP[tp]),
            strict_schema=core_schema.json_or_python_schema(
                json_schema=core_schema.no_info_after_validator_function(tp, core_schema.str_schema()),
                python_schema=core_schema.is_instance_schema(tp),
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(ser_ip, info_arg=True, when_used='always'),
            metadata={
                'pydantic_js_functions': [lambda _1, _2: {'type': 'string', 'format': ip_type_json_schema_format[tp]}]
            },
        )

    def _fraction_schema(self) -> CoreSchema:
        """Support for [`fractions.Fraction`][fractions.Fraction]."""
        from ._validators import fraction_validator

        # TODO: note, this is a fairly common pattern, re lax / strict for attempted type coercion,
        # can we use a helper function to reduce boilerplate?
        return core_schema.lax_or_strict_schema(
            lax_schema=core_schema.no_info_plain_validator_function(fraction_validator),
            strict_schema=core_schema.json_or_python_schema(
                json_schema=core_schema.no_info_plain_validator_function(fraction_validator),
                python_schema=core_schema.is_instance_schema(Fraction),
            ),
            # use str serialization to guarantee round trip behavior
            serialization=core_schema.to_string_ser_schema(when_used='always'),
            metadata={'pydantic_js_functions': [lambda _1, _2: {'type': 'string', 'format': 'fraction'}]},
        )

    def _arbitrary_type_schema(self, tp: Any) -> CoreSchema:
        if not isinstance(tp, type):
            warn(
                f'{tp!r} is not a Python type (it may be an instance of an object),'
                ' Pydantic will allow any object with no validation since we cannot even'
                ' enforce that the input is an instance of the given type.'
                ' To get rid of this error wrap the type with `pydantic.SkipValidation`.',
                UserWarning,
            )
            return core_schema.any_schema()
        return core_schema.is_instance_schema(tp)

    def _unknown_type_schema(self, obj: Any) -> CoreSchema:
        raise PydanticSchemaGenerationError(
            f'Unable to generate pydantic-core schema for {obj!r}. '
            'Set `arbitrary_types_allowed=True` in the model_config to ignore this error'
            ' or implement `__get_pydantic_core_schema__` on your type to fully support it.'
            '\n\nIf you got this error by calling handler(<some type>) within'
            ' `__get_pydantic_core_schema__` then you likely need to call'
            ' `handler.generate_schema(<some type>)` since we do not call'
            ' `__get_pydantic_core_schema__` on `<some type>` otherwise to avoid infinite recursion.'
        )

    def _apply_discriminator_to_union(
        self, schema: CoreSchema, discriminator: str | Discriminator | None
    ) -> CoreSchema:
        if discriminator is None:
            return schema
        try:
            return _discriminated_union.apply_discriminator(
                schema,
                discriminator,
            )
        except _discriminated_union.MissingDefinitionForUnionRef:
            # defer until defs are resolved
            _discriminated_union.set_discriminator_in_metadata(
                schema,
                discriminator,
            )
            return schema

    class CollectedInvalid(Exception):
        pass

    def clean_schema(self, schema: CoreSchema) -> CoreSchema:
        schema = self.collect_definitions(schema)
        schema = simplify_schema_references(schema)
        if collect_invalid_schemas(schema):
            raise self.CollectedInvalid()
        schema = _discriminated_union.apply_discriminators(schema)
        schema = validate_core_schema(schema)
        return schema

    def collect_definitions(self, schema: CoreSchema) -> CoreSchema:
        ref = cast('str | None', schema.get('ref', None))
        if ref:
            self.defs.definitions[ref] = schema
        if 'ref' in schema:
            schema = core_schema.definition_reference_schema(schema['ref'])
        return core_schema.definitions_schema(
            schema,
            list(self.defs.definitions.values()),
        )

    def _add_js_function(self, metadata_schema: CoreSchema, js_function: Callable[..., Any]) -> None:
        metadata = metadata_schema.get('metadata', {})
        pydantic_js_functions = metadata.setdefault('pydantic_js_functions', [])
        # because of how we generate core schemas for nested generic models
        # we can end up adding `BaseModel.__get_pydantic_json_schema__` multiple times
        # this check may fail to catch duplicates if the function is a `functools.partial`
        # or something like that, but if it does it'll fail by inserting the duplicate
        if js_function not in pydantic_js_functions:
            pydantic_js_functions.append(js_function)
        metadata_schema['metadata'] = metadata

    def generate_schema(
        self,
        obj: Any,
        from_dunder_get_core_schema: bool = True,
    ) -> core_schema.CoreSchema:
        """Generate core schema.

        Args:
            obj: The object to generate core schema for.
            from_dunder_get_core_schema: Whether to generate schema from either the
                `__get_pydantic_core_schema__` function or `__pydantic_core_schema__` property.

        Returns:
            The generated core schema.

        Raises:
            PydanticUndefinedAnnotation:
                If it is not possible to evaluate forward reference.
            PydanticSchemaGenerationError:
                If it is not possible to generate pydantic-core schema.
            TypeError:
                - If `alias_generator` returns a disallowed type (must be str, AliasPath or AliasChoices).
                - If V1 style validator with `each_item=True` applied on a wrong field.
            PydanticUserError:
                - If `typing.TypedDict` is used instead of `typing_extensions.TypedDict` on Python < 3.12.
                - If `__modify_schema__` method is used instead of `__get_pydantic_json_schema__`.
        """
        schema: CoreSchema | None = None

        if from_dunder_get_core_schema:
            from_property = self._generate_schema_from_property(obj, obj)
            if from_property is not None:
                schema = from_property

        if schema is None:
            schema = self._generate_schema_inner(obj)

        metadata_js_function = _extract_get_pydantic_json_schema(obj, schema)
        if metadata_js_function is not None:
            metadata_schema = resolve_original_schema(schema, self.defs.definitions)
            if metadata_schema:
                self._add_js_function(metadata_schema, metadata_js_function)

        schema = _add_custom_serialization_from_json_encoders(self._config_wrapper.json_encoders, obj, schema)

        return schema

    def _model_schema(self, cls: type[BaseModel]) -> core_schema.CoreSchema:
        """Generate schema for a Pydantic model."""
        with self.defs.get_schema_or_ref(cls) as (model_ref, maybe_schema):
            if maybe_schema is not None:
                return maybe_schema

            fields = getattr(cls, '__pydantic_fields__', {})
            decorators = cls.__pydantic_decorators__
            computed_fields = decorators.computed_fields
            check_decorator_fields_exist(
                chain(
                    decorators.field_validators.values(),
                    decorators.field_serializers.values(),
                    decorators.validators.values(),
                ),
                {*fields.keys(), *computed_fields.keys()},
            )
            config_wrapper = ConfigWrapper(cls.model_config, check=False)
            core_config = config_wrapper.core_config(title=cls.__name__)
            model_validators = decorators.model_validators.values()

            with self._config_wrapper_stack.push(config_wrapper), self._ns_resolver.push(cls):
                extras_schema = None
                if core_config.get('extra_fields_behavior') == 'allow':
                    assert cls.__mro__[0] is cls
                    assert cls.__mro__[-1] is object
                    for candidate_cls in cls.__mro__[:-1]:
                        extras_annotation = getattr(candidate_cls, '__annotations__', {}).get(
                            '__pydantic_extra__', None
                        )
                        if extras_annotation is not None:
                            if isinstance(extras_annotation, str):
                                extras_annotation = _typing_extra.eval_type_backport(
                                    _typing_extra._make_forward_ref(
                                        extras_annotation, is_argument=False, is_class=True
                                    ),
                                    *self._types_namespace,
                                )
                            tp = get_origin(extras_annotation)
                            if tp not in (Dict, dict):
                                raise PydanticSchemaGenerationError(
                                    'The type annotation for `__pydantic_extra__` must be `Dict[str, ...]`'
                                )
                            extra_items_type = self._get_args_resolving_forward_refs(
                                extras_annotation,
                                required=True,
                            )[1]
                            if not _typing_extra.is_any(extra_items_type):
                                extras_schema = self.generate_schema(extra_items_type)
                                break

                generic_origin: type[BaseModel] | None = getattr(cls, '__pydantic_generic_metadata__', {}).get('origin')

                if cls.__pydantic_root_model__:
                    root_field = self._common_field_schema('root', fields['root'], decorators)
                    inner_schema = root_field['schema']
                    inner_schema = apply_model_validators(inner_schema, model_validators, 'inner')
                    model_schema = core_schema.model_schema(
                        cls,
                        inner_schema,
                        generic_origin=generic_origin,
                        custom_init=getattr(cls, '__pydantic_custom_init__', None),
                        root_model=True,
                        post_init=getattr(cls, '__pydantic_post_init__', None),
                        config=core_config,
                        ref=model_ref,
                    )
                else:
                    fields_schema: core_schema.CoreSchema = core_schema.model_fields_schema(
                        {k: self._generate_md_field_schema(k, v, decorators) for k, v in fields.items()},
                        computed_fields=[
                            self._computed_field_schema(d, decorators.field_serializers)
                            for d in computed_fields.values()
                        ],
                        extras_schema=extras_schema,
                        model_name=cls.__name__,
                    )
                    inner_schema = apply_validators(fields_schema, decorators.root_validators.values(), None)
                    new_inner_schema = define_expected_missing_refs(inner_schema, recursively_defined_type_refs())
                    if new_inner_schema is not None:
                        inner_schema = new_inner_schema
                    inner_schema = apply_model_validators(inner_schema, model_validators, 'inner')

                    model_schema = core_schema.model_schema(
                        cls,
                        inner_schema,
                        generic_origin=generic_origin,
                        custom_init=getattr(cls, '__pydantic_custom_init__', None),
                        root_model=False,
                        post_init=getattr(cls, '__pydantic_post_init__', None),
                        config=core_config,
                        ref=model_ref,
                    )

                schema = self._apply_model_serializers(model_schema, decorators.model_serializers.values())
                schema = apply_model_validators(schema, model_validators, 'outer')
                self.defs.definitions[model_ref] = schema
                return core_schema.definition_reference_schema(model_ref)

    def _unpack_refs_defs(self, schema: CoreSchema) -> CoreSchema:
        """Unpack all 'definitions' schemas into `GenerateSchema.defs.definitions`
        and return the inner schema.
        """
        if schema['type'] == 'definitions':
            definitions = self.defs.definitions
            for s in schema['definitions']:
                definitions[s['ref']] = s  # type: ignore
            return schema['schema']
        return schema

    def _resolve_self_type(self, obj: Any) -> Any:
        obj = self.model_type_stack.get()
        if obj is None:
            raise PydanticUserError('`typing.Self` is invalid in this context', code='invalid-self-type')
        return obj

    def _generate_schema_from_property(self, obj: Any, source: Any) -> core_schema.CoreSchema | None:
        """Try to generate schema from either the `__get_pydantic_core_schema__` function or
        `__pydantic_core_schema__` property.

        Note: `__get_pydantic_core_schema__` takes priority so it can
        decide whether to use a `__pydantic_core_schema__` attribute, or generate a fresh schema.
        """
        # avoid calling `__get_pydantic_core_schema__` if we've already visited this object
        if _typing_extra.is_self(obj):
            obj = self._resolve_self_type(obj)
        with self.defs.get_schema_or_ref(obj) as (_, maybe_schema):
            if maybe_schema is not None:
                return maybe_schema
        if obj is source:
            ref_mode = 'unpack'
        else:
            ref_mode = 'to-def'

        schema: CoreSchema

        if (get_schema := getattr(obj, '__get_pydantic_core_schema__', None)) is not None:
            schema = get_schema(
                source, CallbackGetCoreSchemaHandler(self._generate_schema_inner, self, ref_mode=ref_mode)
            )
        elif (
            hasattr(obj, '__dict__')
            # In some cases (e.g. a stdlib dataclass subclassing a Pydantic dataclass),
            # doing an attribute access to get the schema will result in the parent schema
            # being fetched. Thus, only look for the current obj's dict:
            and (existing_schema := obj.__dict__.get('__pydantic_core_schema__')) is not None
            and not isinstance(existing_schema, MockCoreSchema)
        ):
            schema = existing_schema
        elif (validators := getattr(obj, '__get_validators__', None)) is not None:
            from pydantic.v1 import BaseModel as BaseModelV1

            if issubclass(obj, BaseModelV1):
                warn(
                    f'Mixing V1 models and V2 models (or constructs, like `TypeAdapter`) is not supported. Please upgrade `{obj.__name__}` to V2.',
                    UserWarning,
                )
            else:
                warn(
                    '`__get_validators__` is deprecated and will be removed, use `__get_pydantic_core_schema__` instead.',
                    PydanticDeprecatedSince20,
                )
            schema = core_schema.chain_schema([core_schema.with_info_plain_validator_function(v) for v in validators()])
        else:
            # we have no existing schema information on the property, exit early so that we can go generate a schema
            return None

        schema = self._unpack_refs_defs(schema)

        if is_function_with_inner_schema(schema):
            ref = schema['schema'].pop('ref', None)  # pyright: ignore[reportCallIssue, reportArgumentType]
            if ref:
                schema['ref'] = ref
        else:
            ref = get_ref(schema)

        if ref:
            self.defs.definitions[ref] = schema
            return core_schema.definition_reference_schema(ref)

        return schema

    def _resolve_forward_ref(self, obj: Any) -> Any:
        # we assume that types_namespace has the target of forward references in its scope,
        # but this could fail, for example, if calling Validator on an imported type which contains
        # forward references to other types only defined in the module from which it was imported
        # `Validator(SomeImportedTypeAliasWithAForwardReference)`
        # or the equivalent for BaseModel
        # class Model(BaseModel):
        #   x: SomeImportedTypeAliasWithAForwardReference
        try:
            obj = _typing_extra.eval_type_backport(obj, *self._types_namespace)
        except NameError as e:
            raise PydanticUndefinedAnnotation.from_name_error(e) from e

        # if obj is still a ForwardRef, it means we can't evaluate it, raise PydanticUndefinedAnnotation
        if isinstance(obj, ForwardRef):
            raise PydanticUndefinedAnnotation(obj.__forward_arg__, f'Unable to evaluate forward reference {obj}')

        if self._typevars_map:
            obj = replace_types(obj, self._typevars_map)

        return obj

    @overload
    def _get_args_resolving_forward_refs(self, obj: Any, required: Literal[True]) -> tuple[Any, ...]: ...

    @overload
    def _get_args_resolving_forward_refs(self, obj: Any) -> tuple[Any, ...] | None: ...

    def _get_args_resolving_forward_refs(self, obj: Any, required: bool = False) -> tuple[Any, ...] | None:
        args = get_args(obj)
        if args:
            if sys.version_info >= (3, 9):
                from types import GenericAlias

                if isinstance(obj, GenericAlias):
                    # PEP 585 generic aliases don't convert args to ForwardRefs, unlike `typing.List/Dict` etc.
                    args = (_typing_extra._make_forward_ref(a) if isinstance(a, str) else a for a in args)
            args = tuple(self._resolve_forward_ref(a) if isinstance(a, ForwardRef) else a for a in args)
        elif required:  # pragma: no cover
            raise TypeError(f'Expected {obj} to have generic parameters but it had none')
        return args

    def _get_first_arg_or_any(self, obj: Any) -> Any:
        args = self._get_args_resolving_forward_refs(obj)
        if not args:
            return Any
        return args[0]

    def _get_first_two_args_or_any(self, obj: Any) -> tuple[Any, Any]:
        args = self._get_args_resolving_forward_refs(obj)
        if not args:
            return (Any, Any)
        if len(args) < 2:
            origin = get_origin(obj)
            raise TypeError(f'Expected two type arguments for {origin}, got 1')
        return args[0], args[1]

    def _generate_schema_inner(self, obj: Any) -> core_schema.CoreSchema:
        if _typing_extra.is_annotated(obj):
            return self._annotated_schema(obj)

        if isinstance(obj, dict):
            # we assume this is already a valid schema
            return obj  # type: ignore[return-value]

        if isinstance(obj, str):
            obj = ForwardRef(obj)

        if isinstance(obj, ForwardRef):
            return self.generate_schema(self._resolve_forward_ref(obj))

        BaseModel = import_cached_base_model()

        if lenient_issubclass(obj, BaseModel):
            with self.model_type_stack.push(obj):
                return self._model_schema(obj)

        if isinstance(obj, PydanticRecursiveRef):
            return core_schema.definition_reference_schema(schema_ref=obj.type_ref)

        return self.match_type(obj)

    def match_type(self, obj: Any) -> core_schema.CoreSchema:  # noqa: C901
        """Main mapping of types to schemas.

        The general structure is a series of if statements starting with the simple cases
        (non-generic primitive types) and then handling generics and other more complex cases.

        Each case either generates a schema directly, calls into a public user-overridable method
        (like `GenerateSchema.tuple_variable_schema`) or calls into a private method that handles some
        boilerplate before calling into the user-facing method (e.g. `GenerateSchema._tuple_schema`).

        The idea is that we'll evolve this into adding more and more user facing methods over time
        as they get requested and we figure out what the right API for them is.
        """
        if obj is str:
            return core_schema.str_schema()
        elif obj is bytes:
            return core_schema.bytes_schema()
        elif obj is int:
            return core_schema.int_schema()
        elif obj is float:
            return core_schema.float_schema()
        elif obj is bool:
            return core_schema.bool_schema()
        elif obj is complex:
            return core_schema.complex_schema()
        elif _typing_extra.is_any(obj) or obj is object:
            return core_schema.any_schema()
        elif obj is datetime.date:
            return core_schema.date_schema()
        elif obj is datetime.datetime:
            return core_schema.datetime_schema()
        elif obj is datetime.time:
            return core_schema.time_schema()
        elif obj is datetime.timedelta:
            return core_schema.timedelta_schema()
        elif obj is Decimal:
            return core_schema.decimal_schema()
        elif obj is UUID:
            return core_schema.uuid_schema()
        elif obj is Url:
            return core_schema.url_schema()
        elif obj is Fraction:
            return self._fraction_schema()
        elif obj is MultiHostUrl:
            return core_schema.multi_host_url_schema()
        elif obj is None or obj is _typing_extra.NoneType:
            return core_schema.none_schema()
        elif obj in IP_TYPES:
            return self._ip_schema(obj)
        elif obj in TUPLE_TYPES:
            return self._tuple_schema(obj)
        elif obj in LIST_TYPES:
            return self._list_schema(Any)
        elif obj in SET_TYPES:
            return self._set_schema(Any)
        elif obj in FROZEN_SET_TYPES:
            return self._frozenset_schema(Any)
        elif obj in SEQUENCE_TYPES:
            return self._sequence_schema(Any)
        elif obj in DICT_TYPES:
            return self._dict_schema(Any, Any)
        elif _typing_extra.is_type_alias_type(obj):
            return self._type_alias_type_schema(obj)
        elif obj is type:
            return self._type_schema()
        elif _typing_extra.is_callable(obj):
            return core_schema.callable_schema()
        elif _typing_extra.is_literal(obj):
            return self._literal_schema(obj)
        elif is_typeddict(obj):
            return self._typed_dict_schema(obj, None)
        elif _typing_extra.is_namedtuple(obj):
            return self._namedtuple_schema(obj, None)
        elif _typing_extra.is_new_type(obj):
            # NewType, can't use isinstance because it fails <3.10
            return self.generate_schema(obj.__supertype__)
        elif obj is re.Pattern:
            return self._pattern_schema(obj)
        elif _typing_extra.is_hashable(obj):
            return self._hashable_schema()
        elif isinstance(obj, typing.TypeVar):
            return self._unsubstituted_typevar_schema(obj)
        elif _typing_extra.is_finalvar(obj):
            if obj is Final:
                return core_schema.any_schema()
            return self.generate_schema(
                self._get_first_arg_or_any(obj),
            )
        elif isinstance(obj, VALIDATE_CALL_SUPPORTED_TYPES):
            return self._call_schema(obj)
        elif inspect.isclass(obj) and issubclass(obj, Enum):
            return self._enum_schema(obj)
        elif _typing_extra.is_zoneinfo_type(obj):
            return self._zoneinfo_schema()

        if dataclasses.is_dataclass(obj):
            return self._dataclass_schema(obj, None)

        origin = get_origin(obj)
        if origin is not None:
            return self._match_generic_type(obj, origin)

        res = self._get_prepare_pydantic_annotations_for_known_type(obj, ())
        if res is not None:
            source_type, annotations = res
            return self._apply_annotations(source_type, annotations)

        if self._arbitrary_types:
            return self._arbitrary_type_schema(obj)
        return self._unknown_type_schema(obj)

    def _match_generic_type(self, obj: Any, origin: Any) -> CoreSchema:  # noqa: C901
        # Need to handle generic dataclasses before looking for the schema properties because attribute accesses
        # on _GenericAlias delegate to the origin type, so lose the information about the concrete parametrization
        # As a result, currently, there is no way to cache the schema for generic dataclasses. This may be possible
        # to resolve by modifying the value returned by `Generic.__class_getitem__`, but that is a dangerous game.
        if dataclasses.is_dataclass(origin):
            return self._dataclass_schema(obj, origin)  # pyright: ignore[reportArgumentType]
        if _typing_extra.is_namedtuple(origin):
            return self._namedtuple_schema(obj, origin)

        from_property = self._generate_schema_from_property(origin, obj)
        if from_property is not None:
            return from_property

        if _typing_extra.is_type_alias_type(origin):
            return self._type_alias_type_schema(obj)
        elif _typing_extra.origin_is_union(origin):
            return self._union_schema(obj)
        elif origin in TUPLE_TYPES:
            return self._tuple_schema(obj)
        elif origin in LIST_TYPES:
            return self._list_schema(self._get_first_arg_or_any(obj))
        elif origin in SET_TYPES:
            return self._set_schema(self._get_first_arg_or_any(obj))
        elif origin in FROZEN_SET_TYPES:
            return self._frozenset_schema(self._get_first_arg_or_any(obj))
        elif origin in DICT_TYPES:
            return self._dict_schema(*self._get_first_two_args_or_any(obj))
        elif is_typeddict(origin):
            return self._typed_dict_schema(obj, origin)
        elif origin in (typing.Type, type):
            return self._subclass_schema(obj)
        elif origin in SEQUENCE_TYPES:
            return self._sequence_schema(self._get_first_arg_or_any(obj))
        elif origin in {typing.Iterable, collections.abc.Iterable, typing.Generator, collections.abc.Generator}:
            return self._iterable_schema(obj)
        elif origin in (re.Pattern, typing.Pattern):
            return self._pattern_schema(obj)

        res = self._get_prepare_pydantic_annotations_for_known_type(obj, ())
        if res is not None:
            source_type, annotations = res
            return self._apply_annotations(source_type, annotations)

        if self._arbitrary_types:
            return self._arbitrary_type_schema(origin)
        return self._unknown_type_schema(obj)

    def _generate_td_field_schema(
        self,
        name: str,
        field_info: FieldInfo,
        decorators: DecoratorInfos,
        *,
        required: bool = True,
    ) -> core_schema.TypedDictField:
        """Prepare a TypedDictField to represent a model or typeddict field."""
        common_field = self._common_field_schema(name, field_info, decorators)
        return core_schema.typed_dict_field(
            common_field['schema'],
            required=False if not field_info.is_required() else required,
            serialization_exclude=common_field['serialization_exclude'],
            validation_alias=common_field['validation_alias'],
            serialization_alias=common_field['serialization_alias'],
            metadata=common_field['metadata'],
        )

    def _generate_md_field_schema(
        self,
        name: str,
        field_info: FieldInfo,
        decorators: DecoratorInfos,
    ) -> core_schema.ModelField:
        """Prepare a ModelField to represent a model field."""
        common_field = self._common_field_schema(name, field_info, decorators)
        return core_schema.model_field(
            common_field['schema'],
            serialization_exclude=common_field['serialization_exclude'],
            validation_alias=common_field['validation_alias'],
            serialization_alias=common_field['serialization_alias'],
            frozen=common_field['frozen'],
            metadata=common_field['metadata'],
        )

    def _generate_dc_field_schema(
        self,
        name: str,
        field_info: FieldInfo,
        decorators: DecoratorInfos,
    ) -> core_schema.DataclassField:
        """Prepare a DataclassField to represent the parameter/field, of a dataclass."""
        common_field = self._common_field_schema(name, field_info, decorators)
        return core_schema.dataclass_field(
            name,
            common_field['schema'],
            init=field_info.init,
            init_only=field_info.init_var or None,
            kw_only=None if field_info.kw_only else False,
            serialization_exclude=common_field['serialization_exclude'],
            validation_alias=common_field['validation_alias'],
            serialization_alias=common_field['serialization_alias'],
            frozen=common_field['frozen'],
            metadata=common_field['metadata'],
        )

    @staticmethod
    def _apply_alias_generator_to_field_info(
        alias_generator: Callable[[str], str] | AliasGenerator, field_info: FieldInfo, field_name: str
    ) -> None:
        """Apply an alias_generator to aliases on a FieldInfo instance if appropriate.

        Args:
            alias_generator: A callable that takes a string and returns a string, or an AliasGenerator instance.
            field_info: The FieldInfo instance to which the alias_generator is (maybe) applied.
            field_name: The name of the field from which to generate the alias.
        """
        # Apply an alias_generator if
        # 1. An alias is not specified
        # 2. An alias is specified, but the priority is <= 1
        if (
            field_info.alias_priority is None
            or field_info.alias_priority <= 1
            or field_info.alias is None
            or field_info.validation_alias is None
            or field_info.serialization_alias is None
        ):
            alias, validation_alias, serialization_alias = None, None, None

            if isinstance(alias_generator, AliasGenerator):
                alias, validation_alias, serialization_alias = alias_generator.generate_aliases(field_name)
            elif isinstance(alias_generator, Callable):
                alias = alias_generator(field_name)
                if not isinstance(alias, str):
                    raise TypeError(f'alias_generator {alias_generator} must return str, not {alias.__class__}')

            # if priority is not set, we set to 1
            # which supports the case where the alias_generator from a child class is used
            # to generate an alias for a field in a parent class
            if field_info.alias_priority is None or field_info.alias_priority <= 1:
                field_info.alias_priority = 1

            # if the priority is 1, then we set the aliases to the generated alias
            if field_info.alias_priority == 1:
                field_info.serialization_alias = _get_first_non_null(serialization_alias, alias)
                field_info.validation_alias = _get_first_non_null(validation_alias, alias)
                field_info.alias = alias

            # if any of the aliases are not set, then we set them to the corresponding generated alias
            if field_info.alias is None:
                field_info.alias = alias
            if field_info.serialization_alias is None:
                field_info.serialization_alias = _get_first_non_null(serialization_alias, alias)
            if field_info.validation_alias is None:
                field_info.validation_alias = _get_first_non_null(validation_alias, alias)

    @staticmethod
    def _apply_alias_generator_to_computed_field_info(
        alias_generator: Callable[[str], str] | AliasGenerator,
        computed_field_info: ComputedFieldInfo,
        computed_field_name: str,
    ):
        """Apply an alias_generator to alias on a ComputedFieldInfo instance if appropriate.

        Args:
            alias_generator: A callable that takes a string and returns a string, or an AliasGenerator instance.
            computed_field_info: The ComputedFieldInfo instance to which the alias_generator is (maybe) applied.
            computed_field_name: The name of the computed field from which to generate the alias.
        """
        # Apply an alias_generator if
        # 1. An alias is not specified
        # 2. An alias is specified, but the priority is <= 1

        if (
            computed_field_info.alias_priority is None
            or computed_field_info.alias_priority <= 1
            or computed_field_info.alias is None
        ):
            alias, validation_alias, serialization_alias = None, None, None

            if isinstance(alias_generator, AliasGenerator):
                alias, validation_alias, serialization_alias = alias_generator.generate_aliases(computed_field_name)
            elif isinstance(alias_generator, Callable):
                alias = alias_generator(computed_field_name)
                if not isinstance(alias, str):
                    raise TypeError(f'alias_generator {alias_generator} must return str, not {alias.__class__}')

            # if priority is not set, we set to 1
            # which supports the case where the alias_generator from a child class is used
            # to generate an alias for a field in a parent class
            if computed_field_info.alias_priority is None or computed_field_info.alias_priority <= 1:
                computed_field_info.alias_priority = 1

            # if the priority is 1, then we set the aliases to the generated alias
            # note that we use the serialization_alias with priority over alias, as computed_field
            # aliases are used for serialization only (not validation)
            if computed_field_info.alias_priority == 1:
                computed_field_info.alias = _get_first_non_null(serialization_alias, alias)

    @staticmethod
    def _apply_field_title_generator_to_field_info(
        config_wrapper: ConfigWrapper, field_info: FieldInfo | ComputedFieldInfo, field_name: str
    ) -> None:
        """Apply a field_title_generator on a FieldInfo or ComputedFieldInfo instance if appropriate
        Args:
            config_wrapper: The config of the model
            field_info: The FieldInfo or ComputedField instance to which the title_generator is (maybe) applied.
            field_name: The name of the field from which to generate the title.
        """
        field_title_generator = field_info.field_title_generator or config_wrapper.field_title_generator

        if field_title_generator is None:
            return

        if field_info.title is None:
            title = field_title_generator(field_name, field_info)  # type: ignore
            if not isinstance(title, str):
                raise TypeError(f'field_title_generator {field_title_generator} must return str, not {title.__class__}')

            field_info.title = title

    def _common_field_schema(  # C901
        self, name: str, field_info: FieldInfo, decorators: DecoratorInfos
    ) -> _CommonField:
        # Update FieldInfo annotation if appropriate:
        FieldInfo = import_cached_field_info()
        if has_instance_in_type(field_info.annotation, (ForwardRef, str)):
            # TODO Can we use field_info.apply_typevars_map here? Shouldn't we use lenient=False?
            evaluated = _typing_extra.eval_type(field_info.annotation, *self._types_namespace, lenient=True)
            evaluated = replace_types(evaluated, self._typevars_map)
            if evaluated is not field_info.annotation and not has_instance_in_type(evaluated, PydanticRecursiveRef):
                new_field_info = FieldInfo.from_annotation(evaluated)
                field_info.annotation = new_field_info.annotation

                # Handle any field info attributes that may have been obtained from now-resolved annotations
                for k, v in new_field_info._attributes_set.items():
                    # If an attribute is already set, it means it was set by assigning to a call to Field (or just a
                    # default value), and that should take the highest priority. So don't overwrite existing attributes.
                    # We skip over "attributes" that are present in the metadata_lookup dict because these won't
                    # actually end up as attributes of the `FieldInfo` instance.
                    if k not in field_info._attributes_set and k not in field_info.metadata_lookup:
                        setattr(field_info, k, v)

                # Finally, ensure the field info also reflects all the `_attributes_set` that are actually metadata.
                field_info.metadata = [*new_field_info.metadata, *field_info.metadata]

        source_type, annotations = field_info.annotation, field_info.metadata

        def set_discriminator(schema: CoreSchema) -> CoreSchema:
            schema = self._apply_discriminator_to_union(schema, field_info.discriminator)
            return schema

        # Convert `@field_validator` decorators to `Before/After/Plain/WrapValidator` instances:
        validators_from_decorators = []
        for decorator in filter_field_decorator_info_by_field(decorators.field_validators.values(), name):
            validators_from_decorators.append(_mode_to_validator[decorator.info.mode]._from_decorator(decorator))

        with self.field_name_stack.push(name):
            if field_info.discriminator is not None:
                schema = self._apply_annotations(
                    source_type, annotations + validators_from_decorators, transform_inner_schema=set_discriminator
                )
            else:
                schema = self._apply_annotations(
                    source_type,
                    annotations + validators_from_decorators,
                )

        # This V1 compatibility shim should eventually be removed
        # push down any `each_item=True` validators
        # note that this won't work for any Annotated types that get wrapped by a function validator
        # but that's okay because that didn't exist in V1
        this_field_validators = filter_field_decorator_info_by_field(decorators.validators.values(), name)
        if _validators_require_validate_default(this_field_validators):
            field_info.validate_default = True
        each_item_validators = [v for v in this_field_validators if v.info.each_item is True]
        this_field_validators = [v for v in this_field_validators if v not in each_item_validators]
        schema = apply_each_item_validators(schema, each_item_validators, name)

        schema = apply_validators(schema, this_field_validators, name)

        # the default validator needs to go outside of any other validators
        # so that it is the topmost validator for the field validator
        # which uses it to check if the field has a default value or not
        if not field_info.is_required():
            schema = wrap_default(field_info, schema)

        schema = self._apply_field_serializers(
            schema, filter_field_decorator_info_by_field(decorators.field_serializers.values(), name)
        )
        self._apply_field_title_generator_to_field_info(self._config_wrapper, field_info, name)

        pydantic_js_updates, pydantic_js_extra = _extract_json_schema_info_from_field_info(field_info)
        core_metadata: dict[str, Any] = {}
        update_core_metadata(
            core_metadata, pydantic_js_updates=pydantic_js_updates, pydantic_js_extra=pydantic_js_extra
        )

        alias_generator = self._config_wrapper.alias_generator
        if alias_generator is not None:
            self._apply_alias_generator_to_field_info(alias_generator, field_info, name)

        if isinstance(field_info.validation_alias, (AliasChoices, AliasPath)):
            validation_alias = field_info.validation_alias.convert_to_aliases()
        else:
            validation_alias = field_info.validation_alias

        return _common_field(
            schema,
            serialization_exclude=True if field_info.exclude else None,
            validation_alias=validation_alias,
            serialization_alias=field_info.serialization_alias,
            frozen=field_info.frozen,
            metadata=core_metadata,
        )

    def _union_schema(self, union_type: Any) -> core_schema.CoreSchema:
        """Generate schema for a Union."""
        args = self._get_args_resolving_forward_refs(union_type, required=True)
        choices: list[CoreSchema] = []
        nullable = False
        for arg in args:
            if arg is None or arg is _typing_extra.NoneType:
                nullable = True
            else:
                choices.append(self.generate_schema(arg))

        if len(choices) == 1:
            s = choices[0]
        else:
            choices_with_tags: list[CoreSchema | tuple[CoreSchema, str]] = []
            for choice in choices:
                tag = choice.get('metadata', {}).get(_core_utils.TAGGED_UNION_TAG_KEY)
                if tag is not None:
                    choices_with_tags.append((choice, tag))
                else:
                    choices_with_tags.append(choice)
            s = core_schema.union_schema(choices_with_tags)

        if nullable:
            s = core_schema.nullable_schema(s)
        return s

    def _type_alias_type_schema(self, obj: TypeAliasType) -> CoreSchema:
        with self.defs.get_schema_or_ref(obj) as (ref, maybe_schema):
            if maybe_schema is not None:
                return maybe_schema

            origin: TypeAliasType = get_origin(obj) or obj

            annotation = origin.__value__
            typevars_map = get_standard_typevars_map(obj)

            with self._ns_resolver.push(origin):
                annotation = _typing_extra.eval_type(annotation, *self._types_namespace, lenient=True)
                annotation = replace_types(annotation, typevars_map)
                schema = self.generate_schema(annotation)
                assert schema['type'] != 'definitions'
                schema['ref'] = ref  # type: ignore
            self.defs.definitions[ref] = schema
            return core_schema.definition_reference_schema(ref)

    def _literal_schema(self, literal_type: Any) -> CoreSchema:
        """Generate schema for a Literal."""
        expected = _typing_extra.literal_values(literal_type)
        assert expected, f'literal "expected" cannot be empty, obj={literal_type}'
        schema = core_schema.literal_schema(expected)

        if self._config_wrapper.use_enum_values and any(isinstance(v, Enum) for v in expected):
            schema = core_schema.no_info_after_validator_function(
                lambda v: v.value if isinstance(v, Enum) else v, schema
            )

        return schema

    def _typed_dict_schema(self, typed_dict_cls: Any, origin: Any) -> core_schema.CoreSchema:
        """Generate schema for a TypedDict.

        It is not possible to track required/optional keys in TypedDict without __required_keys__
        since TypedDict.__new__ erases the base classes (it replaces them with just `dict`)
        and thus we can track usage of total=True/False
        __required_keys__ was added in Python 3.9
        (https://github.com/miss-islington/cpython/blob/1e9939657dd1f8eb9f596f77c1084d2d351172fc/Doc/library/typing.rst?plain=1#L1546-L1548)
        however it is buggy
        (https://github.com/python/typing_extensions/blob/ac52ac5f2cb0e00e7988bae1e2a1b8257ac88d6d/src/typing_extensions.py#L657-L666).

        On 3.11 but < 3.12 TypedDict does not preserve inheritance information.

        Hence to avoid creating validators that do not do what users expect we only
        support typing.TypedDict on Python >= 3.12 or typing_extension.TypedDict on all versions
        """
        FieldInfo = import_cached_field_info()

        with self.model_type_stack.push(typed_dict_cls), self.defs.get_schema_or_ref(typed_dict_cls) as (
            typed_dict_ref,
            maybe_schema,
        ):
            if maybe_schema is not None:
                return maybe_schema

            typevars_map = get_standard_typevars_map(typed_dict_cls)
            if origin is not None:
                typed_dict_cls = origin

            if not _SUPPORTS_TYPEDDICT and type(typed_dict_cls).__module__ == 'typing':
                raise PydanticUserError(
                    'Please use `typing_extensions.TypedDict` instead of `typing.TypedDict` on Python < 3.12.',
                    code='typed-dict-version',
                )

            try:
                # if a typed dictionary class doesn't have config, we use the parent's config, hence a default of `None`
                # see https://github.com/pydantic/pydantic/issues/10917
                config: ConfigDict | None = get_attribute_from_bases(typed_dict_cls, '__pydantic_config__')
            except AttributeError:
                config = None

            with self._config_wrapper_stack.push(config):
                core_config = self._config_wrapper.core_config(title=typed_dict_cls.__name__)

                required_keys: frozenset[str] = typed_dict_cls.__required_keys__

                fields: dict[str, core_schema.TypedDictField] = {}

                decorators = DecoratorInfos.build(typed_dict_cls)

                if self._config_wrapper.use_attribute_docstrings:
                    field_docstrings = extract_docstrings_from_cls(typed_dict_cls, use_inspect=True)
                else:
                    field_docstrings = None

                try:
                    annotations = _typing_extra.get_cls_type_hints(
                        typed_dict_cls, ns_resolver=self._ns_resolver, lenient=False
                    )
                except NameError as e:
                    raise PydanticUndefinedAnnotation.from_name_error(e) from e

                for field_name, annotation in annotations.items():
                    annotation = replace_types(annotation, typevars_map)
                    required = field_name in required_keys

                    if _typing_extra.is_required(annotation):
                        required = True
                        annotation = self._get_args_resolving_forward_refs(
                            annotation,
                            required=True,
                        )[0]
                    elif _typing_extra.is_not_required(annotation):
                        required = False
                        annotation = self._get_args_resolving_forward_refs(
                            annotation,
                            required=True,
                        )[0]

                    field_info = FieldInfo.from_annotation(annotation)
                    if (
                        field_docstrings is not None
                        and field_info.description is None
                        and field_name in field_docstrings
                    ):
                        field_info.description = field_docstrings[field_name]
                    self._apply_field_title_generator_to_field_info(self._config_wrapper, field_info, field_name)
                    fields[field_name] = self._generate_td_field_schema(
                        field_name, field_info, decorators, required=required
                    )

                td_schema = core_schema.typed_dict_schema(
                    fields,
                    cls=typed_dict_cls,
                    computed_fields=[
                        self._computed_field_schema(d, decorators.field_serializers)
                        for d in decorators.computed_fields.values()
                    ],
                    ref=typed_dict_ref,
                    config=core_config,
                )

                schema = self._apply_model_serializers(td_schema, decorators.model_serializers.values())
                schema = apply_model_validators(schema, decorators.model_validators.values(), 'all')
                self.defs.definitions[typed_dict_ref] = schema
                return core_schema.definition_reference_schema(typed_dict_ref)

    def _namedtuple_schema(self, namedtuple_cls: Any, origin: Any) -> core_schema.CoreSchema:
        """Generate schema for a NamedTuple."""
        with self.model_type_stack.push(namedtuple_cls), self.defs.get_schema_or_ref(namedtuple_cls) as (
            namedtuple_ref,
            maybe_schema,
        ):
            if maybe_schema is not None:
                return maybe_schema
            typevars_map = get_standard_typevars_map(namedtuple_cls)
            if origin is not None:
                namedtuple_cls = origin

            try:
                annotations = _typing_extra.get_cls_type_hints(
                    namedtuple_cls, ns_resolver=self._ns_resolver, lenient=False
                )
            except NameError as e:
                raise PydanticUndefinedAnnotation.from_name_error(e) from e
            if not annotations:
                # annotations is empty, happens if namedtuple_cls defined via collections.namedtuple(...)
                annotations: dict[str, Any] = {k: Any for k in namedtuple_cls._fields}

            if typevars_map:
                annotations = {
                    field_name: replace_types(annotation, typevars_map)
                    for field_name, annotation in annotations.items()
                }

            arguments_schema = core_schema.arguments_schema(
                [
                    self._generate_parameter_schema(
                        field_name,
                        annotation,
                        default=namedtuple_cls._field_defaults.get(field_name, Parameter.empty),
                    )
                    for field_name, annotation in annotations.items()
                ],
                metadata={'pydantic_js_prefer_positional_arguments': True},
            )
            return core_schema.call_schema(arguments_schema, namedtuple_cls, ref=namedtuple_ref)

    def _generate_parameter_schema(
        self,
        name: str,
        annotation: type[Any],
        default: Any = Parameter.empty,
        mode: Literal['positional_only', 'positional_or_keyword', 'keyword_only'] | None = None,
    ) -> core_schema.ArgumentsParameter:
        """Prepare a ArgumentsParameter to represent a field in a namedtuple or function signature."""
        FieldInfo = import_cached_field_info()

        if default is Parameter.empty:
            field = FieldInfo.from_annotation(annotation)
        else:
            field = FieldInfo.from_annotated_attribute(annotation, default)
        assert field.annotation is not None, 'field.annotation should not be None when generating a schema'
        with self.field_name_stack.push(name):
            schema = self._apply_annotations(field.annotation, [field])

        if not field.is_required():
            schema = wrap_default(field, schema)

        parameter_schema = core_schema.arguments_parameter(name, schema)
        if mode is not None:
            parameter_schema['mode'] = mode
        if field.alias is not None:
            parameter_schema['alias'] = field.alias
        else:
            alias_generator = self._config_wrapper.alias_generator
            if isinstance(alias_generator, AliasGenerator) and alias_generator.alias is not None:
                parameter_schema['alias'] = alias_generator.alias(name)
            elif isinstance(alias_generator, Callable):
                parameter_schema['alias'] = alias_generator(name)
        return parameter_schema

    def _tuple_schema(self, tuple_type: Any) -> core_schema.CoreSchema:
        """Generate schema for a Tuple, e.g. `tuple[int, str]` or `tuple[int, ...]`."""
        # TODO: do we really need to resolve type vars here?
        typevars_map = get_standard_typevars_map(tuple_type)
        params = self._get_args_resolving_forward_refs(tuple_type)

        if typevars_map and params:
            params = tuple(replace_types(param, typevars_map) for param in params)

        # NOTE: subtle difference: `tuple[()]` gives `params=()`, whereas `typing.Tuple[()]` gives `params=((),)`
        # This is only true for <3.11, on Python 3.11+ `typing.Tuple[()]` gives `params=()`
        if not params:
            if tuple_type in TUPLE_TYPES:
                return core_schema.tuple_schema([core_schema.any_schema()], variadic_item_index=0)
            else:
                # special case for `tuple[()]` which means `tuple[]` - an empty tuple
                return core_schema.tuple_schema([])
        elif params[-1] is Ellipsis:
            if len(params) == 2:
                return core_schema.tuple_schema([self.generate_schema(params[0])], variadic_item_index=0)
            else:
                # TODO: something like https://github.com/pydantic/pydantic/issues/5952
                raise ValueError('Variable tuples can only have one type')
        elif len(params) == 1 and params[0] == ():
            # special case for `Tuple[()]` which means `Tuple[]` - an empty tuple
            # NOTE: This conditional can be removed when we drop support for Python 3.10.
            return core_schema.tuple_schema([])
        else:
            return core_schema.tuple_schema([self.generate_schema(param) for param in params])

    def _type_schema(self) -> core_schema.CoreSchema:
        return core_schema.custom_error_schema(
            core_schema.is_instance_schema(type),
            custom_error_type='is_type',
            custom_error_message='Input should be a type',
        )

    def _zoneinfo_schema(self) -> core_schema.CoreSchema:
        """Generate schema for a zone_info.ZoneInfo object"""
        # we're def >=py3.9 if ZoneInfo was included in input
        if sys.version_info < (3, 9):
            assert False, 'Unreachable'

        # import in this path is safe
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

        def validate_str_is_valid_iana_tz(value: Any, /) -> ZoneInfo:
            if isinstance(value, ZoneInfo):
                return value
            try:
                return ZoneInfo(value)
            except (ZoneInfoNotFoundError, ValueError, TypeError):
                raise PydanticCustomError('zoneinfo_str', 'invalid timezone: {value}', {'value': value})

        metadata = {'pydantic_js_functions': [lambda _1, _2: {'type': 'string', 'format': 'zoneinfo'}]}
        return core_schema.no_info_plain_validator_function(
            validate_str_is_valid_iana_tz,
            serialization=core_schema.to_string_ser_schema(),
            metadata=metadata,
        )

    def _union_is_subclass_schema(self, union_type: Any) -> core_schema.CoreSchema:
        """Generate schema for `Type[Union[X, ...]]`."""
        args = self._get_args_resolving_forward_refs(union_type, required=True)
        return core_schema.union_schema([self.generate_schema(typing.Type[args]) for args in args])

    def _subclass_schema(self, type_: Any) -> core_schema.CoreSchema:
        """Generate schema for a Type, e.g. `Type[int]`."""
        type_param = self._get_first_arg_or_any(type_)

        # Assume `type[Annotated[<typ>, ...]]` is equivalent to `type[<typ>]`:
        type_param = _typing_extra.annotated_type(type_param) or type_param

        if _typing_extra.is_any(type_param):
            return self._type_schema()
        elif _typing_extra.is_type_alias_type(type_param):
            return self.generate_schema(typing.Type[type_param.__value__])
        elif isinstance(type_param, typing.TypeVar):
            if type_param.__bound__:
                if _typing_extra.origin_is_union(get_origin(type_param.__bound__)):
                    return self._union_is_subclass_schema(type_param.__bound__)
                return core_schema.is_subclass_schema(type_param.__bound__)
            elif type_param.__constraints__:
                return core_schema.union_schema(
                    [self.generate_schema(typing.Type[c]) for c in type_param.__constraints__]
                )
            else:
                return self._type_schema()
        elif _typing_extra.origin_is_union(get_origin(type_param)):
            return self._union_is_subclass_schema(type_param)
        else:
            if _typing_extra.is_self(type_param):
                type_param = self._resolve_self_type(type_param)

            if not inspect.isclass(type_param):
                raise TypeError(f'Expected a class, got {type_param!r}')
            return core_schema.is_subclass_schema(type_param)

    def _sequence_schema(self, items_type: Any) -> core_schema.CoreSchema:
        """Generate schema for a Sequence, e.g. `Sequence[int]`."""
        from ._serializers import serialize_sequence_via_list

        item_type_schema = self.generate_schema(items_type)
        list_schema = core_schema.list_schema(item_type_schema)

        json_schema = smart_deepcopy(list_schema)
        python_schema = core_schema.is_instance_schema(typing.Sequence, cls_repr='Sequence')
        if not _typing_extra.is_any(items_type):
            from ._validators import sequence_validator

            python_schema = core_schema.chain_schema(
                [python_schema, core_schema.no_info_wrap_validator_function(sequence_validator, list_schema)],
            )

        serialization = core_schema.wrap_serializer_function_ser_schema(
            serialize_sequence_via_list, schema=item_type_schema, info_arg=True
        )
        return core_schema.json_or_python_schema(
            json_schema=json_schema, python_schema=python_schema, serialization=serialization
        )

    def _iterable_schema(self, type_: Any) -> core_schema.GeneratorSchema:
        """Generate a schema for an `Iterable`."""
        item_type = self._get_first_arg_or_any(type_)

        return core_schema.generator_schema(self.generate_schema(item_type))

    def _pattern_schema(self, pattern_type: Any) -> core_schema.CoreSchema:
        from . import _validators

        metadata = {'pydantic_js_functions': [lambda _1, _2: {'type': 'string', 'format': 'regex'}]}
        ser = core_schema.plain_serializer_function_ser_schema(
            attrgetter('pattern'), when_used='json', return_schema=core_schema.str_schema()
        )
        if pattern_type is typing.Pattern or pattern_type is re.Pattern:
            # bare type
            return core_schema.no_info_plain_validator_function(
                _validators.pattern_either_validator, serialization=ser, metadata=metadata
            )

        param = self._get_args_resolving_forward_refs(
            pattern_type,
            required=True,
        )[0]
        if param is str:
            return core_schema.no_info_plain_validator_function(
                _validators.pattern_str_validator, serialization=ser, metadata=metadata
            )
        elif param is bytes:
            return core_schema.no_info_plain_validator_function(
                _validators.pattern_bytes_validator, serialization=ser, metadata=metadata
            )
        else:
            raise PydanticSchemaGenerationError(f'Unable to generate pydantic-core schema for {pattern_type!r}.')

    def _hashable_schema(self) -> core_schema.CoreSchema:
        return core_schema.custom_error_schema(
            schema=core_schema.json_or_python_schema(
                json_schema=core_schema.chain_schema(
                    [core_schema.any_schema(), core_schema.is_instance_schema(collections.abc.Hashable)]
                ),
                python_schema=core_schema.is_instance_schema(collections.abc.Hashable),
            ),
            custom_error_type='is_hashable',
            custom_error_message='Input should be hashable',
        )

    def _dataclass_schema(
        self, dataclass: type[StandardDataclass], origin: type[StandardDataclass] | None
    ) -> core_schema.CoreSchema:
        """Generate schema for a dataclass."""
        with self.model_type_stack.push(dataclass), self.defs.get_schema_or_ref(dataclass) as (
            dataclass_ref,
            maybe_schema,
        ):
            if maybe_schema is not None:
                return maybe_schema

            typevars_map = get_standard_typevars_map(dataclass)
            if origin is not None:
                dataclass = origin

            # if (plain) dataclass doesn't have config, we use the parent's config, hence a default of `None`
            # (Pydantic dataclasses have an empty dict config by default).
            # see https://github.com/pydantic/pydantic/issues/10917
            config = getattr(dataclass, '__pydantic_config__', None)

            from ..dataclasses import is_pydantic_dataclass

            with self._ns_resolver.push(dataclass), self._config_wrapper_stack.push(config):
                if is_pydantic_dataclass(dataclass):
                    fields = deepcopy(dataclass.__pydantic_fields__)
                    if typevars_map:
                        for field in fields.values():
                            field.apply_typevars_map(typevars_map, *self._types_namespace)
                else:
                    fields = collect_dataclass_fields(
                        dataclass,
                        typevars_map=typevars_map,
                    )

                if self._config_wrapper.extra == 'allow':
                    # disallow combination of init=False on a dataclass field and extra='allow' on a dataclass
                    for field_name, field in fields.items():
                        if field.init is False:
                            raise PydanticUserError(
                                f'Field {field_name} has `init=False` and dataclass has config setting `extra="allow"`. '
                                f'This combination is not allowed.',
                                code='dataclass-init-false-extra-allow',
                            )

                decorators = dataclass.__dict__.get('__pydantic_decorators__') or DecoratorInfos.build(dataclass)
                # Move kw_only=False args to the start of the list, as this is how vanilla dataclasses work.
                # Note that when kw_only is missing or None, it is treated as equivalent to kw_only=True
                args = sorted(
                    (self._generate_dc_field_schema(k, v, decorators) for k, v in fields.items()),
                    key=lambda a: a.get('kw_only') is not False,
                )
                has_post_init = hasattr(dataclass, '__post_init__')
                has_slots = hasattr(dataclass, '__slots__')

                args_schema = core_schema.dataclass_args_schema(
                    dataclass.__name__,
                    args,
                    computed_fields=[
                        self._computed_field_schema(d, decorators.field_serializers)
                        for d in decorators.computed_fields.values()
                    ],
                    collect_init_only=has_post_init,
                )

                inner_schema = apply_validators(args_schema, decorators.root_validators.values(), None)

                model_validators = decorators.model_validators.values()
                inner_schema = apply_model_validators(inner_schema, model_validators, 'inner')

                core_config = self._config_wrapper.core_config(title=dataclass.__name__)

                dc_schema = core_schema.dataclass_schema(
                    dataclass,
                    inner_schema,
                    generic_origin=origin,
                    post_init=has_post_init,
                    ref=dataclass_ref,
                    fields=[field.name for field in dataclasses.fields(dataclass)],
                    slots=has_slots,
                    config=core_config,
                    # we don't use a custom __setattr__ for dataclasses, so we must
                    # pass along the frozen config setting to the pydantic-core schema
                    frozen=self._config_wrapper_stack.tail.frozen,
                )
                schema = self._apply_model_serializers(dc_schema, decorators.model_serializers.values())
                schema = apply_model_validators(schema, model_validators, 'outer')
                self.defs.definitions[dataclass_ref] = schema
                return core_schema.definition_reference_schema(dataclass_ref)

    def _call_schema(self, function: ValidateCallSupportedTypes) -> core_schema.CallSchema:
        """Generate schema for a Callable.

        TODO support functional validators once we support them in Config
        """
        sig = signature(function)

        mode_lookup: dict[_ParameterKind, Literal['positional_only', 'positional_or_keyword', 'keyword_only']] = {
            Parameter.POSITIONAL_ONLY: 'positional_only',
            Parameter.POSITIONAL_OR_KEYWORD: 'positional_or_keyword',
            Parameter.KEYWORD_ONLY: 'keyword_only',
        }

        arguments_list: list[core_schema.ArgumentsParameter] = []
        var_args_schema: core_schema.CoreSchema | None = None
        var_kwargs_schema: core_schema.CoreSchema | None = None
        var_kwargs_mode: core_schema.VarKwargsMode | None = None

        for name, p in sig.parameters.items():
            if p.annotation is sig.empty:
                annotation = typing.cast(Any, Any)
            else:
                # Note: This was originally get by `_typing_extra.get_function_type_hints`,
                #       but we switch to simply `p.annotation` to support bultins (e.g. `sorted`).
                #       May need to revisit if anything breaks.
                annotation = (
                    _typing_extra._make_forward_ref(p.annotation) if isinstance(p.annotation, str) else p.annotation
                )
                annotation = self._resolve_forward_ref(annotation)

            parameter_mode = mode_lookup.get(p.kind)
            if parameter_mode is not None:
                arg_schema = self._generate_parameter_schema(name, annotation, p.default, parameter_mode)
                arguments_list.append(arg_schema)
            elif p.kind == Parameter.VAR_POSITIONAL:
                var_args_schema = self.generate_schema(annotation)
            else:
                assert p.kind == Parameter.VAR_KEYWORD, p.kind

                unpack_type = _typing_extra.unpack_type(annotation)
                if unpack_type is not None:
                    if not is_typeddict(unpack_type):
                        raise PydanticUserError(
                            f'Expected a `TypedDict` class, got {unpack_type.__name__!r}', code='unpack-typed-dict'
                        )
                    non_pos_only_param_names = {
                        name for name, p in sig.parameters.items() if p.kind != Parameter.POSITIONAL_ONLY
                    }
                    overlapping_params = non_pos_only_param_names.intersection(unpack_type.__annotations__)
                    if overlapping_params:
                        raise PydanticUserError(
                            f'Typed dictionary {unpack_type.__name__!r} overlaps with parameter'
                            f"{'s' if len(overlapping_params) >= 2 else ''} "
                            f"{', '.join(repr(p) for p in sorted(overlapping_params))}",
                            code='overlapping-unpack-typed-dict',
                        )

                    var_kwargs_mode = 'unpacked-typed-dict'
                    var_kwargs_schema = self._typed_dict_schema(unpack_type, None)
                else:
                    var_kwargs_mode = 'uniform'
                    var_kwargs_schema = self.generate_schema(annotation)

        return_schema: core_schema.CoreSchema | None = None
        config_wrapper = self._config_wrapper
        if config_wrapper.validate_return:
            return_hint = sig.return_annotation
            if return_hint is not sig.empty:
                return_schema = self.generate_schema(return_hint)

        return core_schema.call_schema(
            core_schema.arguments_schema(
                arguments_list,
                var_args_schema=var_args_schema,
                var_kwargs_mode=var_kwargs_mode,
                var_kwargs_schema=var_kwargs_schema,
                populate_by_name=config_wrapper.populate_by_name,
            ),
            function,
            return_schema=return_schema,
        )

    def _unsubstituted_typevar_schema(self, typevar: typing.TypeVar) -> core_schema.CoreSchema:
        assert isinstance(typevar, typing.TypeVar)

        bound = typevar.__bound__
        constraints = typevar.__constraints__

        try:
            typevar_has_default = typevar.has_default()  # type: ignore
        except AttributeError:
            # could still have a default if it's an old version of typing_extensions.TypeVar
            typevar_has_default = getattr(typevar, '__default__', None) is not None

        if (bound is not None) + (len(constraints) != 0) + typevar_has_default > 1:
            raise NotImplementedError(
                'Pydantic does not support mixing more than one of TypeVar bounds, constraints and defaults'
            )

        if typevar_has_default:
            return self.generate_schema(typevar.__default__)  # type: ignore
        elif constraints:
            return self._union_schema(typing.Union[constraints])  # type: ignore
        elif bound:
            schema = self.generate_schema(bound)
            schema['serialization'] = core_schema.wrap_serializer_function_ser_schema(
                lambda x, h: h(x), schema=core_schema.any_schema()
            )
            return schema
        else:
            return core_schema.any_schema()

    def _computed_field_schema(
        self,
        d: Decorator[ComputedFieldInfo],
        field_serializers: dict[str, Decorator[FieldSerializerDecoratorInfo]],
    ) -> core_schema.ComputedField:
        try:
            # Do not pass in globals as the function could be defined in a different module.
            # Instead, let `get_function_return_type` infer the globals to use, but still pass
            # in locals that may contain a parent/rebuild namespace:
            return_type = _decorators.get_function_return_type(
                d.func, d.info.return_type, localns=self._types_namespace.locals
            )
        except NameError as e:
            raise PydanticUndefinedAnnotation.from_name_error(e) from e
        if return_type is PydanticUndefined:
            raise PydanticUserError(
                'Computed field is missing return type annotation or specifying `return_type`'
                ' to the `@computed_field` decorator (e.g. `@computed_field(return_type=int|str)`)',
                code='model-field-missing-annotation',
            )

        return_type = replace_types(return_type, self._typevars_map)
        # Create a new ComputedFieldInfo so that different type parametrizations of the same
        # generic model's computed field can have different return types.
        d.info = dataclasses.replace(d.info, return_type=return_type)
        return_type_schema = self.generate_schema(return_type)
        # Apply serializers to computed field if there exist
        return_type_schema = self._apply_field_serializers(
            return_type_schema,
            filter_field_decorator_info_by_field(field_serializers.values(), d.cls_var_name),
        )

        alias_generator = self._config_wrapper.alias_generator
        if alias_generator is not None:
            self._apply_alias_generator_to_computed_field_info(
                alias_generator=alias_generator, computed_field_info=d.info, computed_field_name=d.cls_var_name
            )
        self._apply_field_title_generator_to_field_info(self._config_wrapper, d.info, d.cls_var_name)

        pydantic_js_updates, pydantic_js_extra = _extract_json_schema_info_from_field_info(d.info)
        core_metadata: dict[str, Any] = {}
        update_core_metadata(
            core_metadata,
            pydantic_js_updates={'readOnly': True, **(pydantic_js_updates if pydantic_js_updates else {})},
            pydantic_js_extra=pydantic_js_extra,
        )
        return core_schema.computed_field(
            d.cls_var_name, return_schema=return_type_schema, alias=d.info.alias, metadata=core_metadata
        )

    def _annotated_schema(self, annotated_type: Any) -> core_schema.CoreSchema:
        """Generate schema for an Annotated type, e.g. `Annotated[int, Field(...)]` or `Annotated[int, Gt(0)]`."""
        FieldInfo = import_cached_field_info()

        source_type, *annotations = self._get_args_resolving_forward_refs(
            annotated_type,
            required=True,
        )
        schema = self._apply_annotations(source_type, annotations)
        # put the default validator last so that TypeAdapter.get_default_value() works
        # even if there are function validators involved
        for annotation in annotations:
            if isinstance(annotation, FieldInfo):
                schema = wrap_default(annotation, schema)
        return schema

    def _get_prepare_pydantic_annotations_for_known_type(
        self, obj: Any, annotations: tuple[Any, ...]
    ) -> tuple[Any, list[Any]] | None:
        from ._std_types_schema import (
            deque_schema_prepare_pydantic_annotations,
            mapping_like_prepare_pydantic_annotations,
            path_schema_prepare_pydantic_annotations,
        )

        # Check for hashability
        try:
            hash(obj)
        except TypeError:
            # obj is definitely not a known type if this fails
            return None

        # TODO: I'd rather we didn't handle the generic nature in the annotations prep, but the same way we do other
        # generic types like list[str] via _match_generic_type, but I'm not sure if we can do that because this is
        # not always called from match_type, but sometimes from _apply_annotations
        obj_origin = get_origin(obj) or obj

        if obj_origin in PATH_TYPES:
            return path_schema_prepare_pydantic_annotations(obj, annotations)
        elif obj_origin in DEQUE_TYPES:
            return deque_schema_prepare_pydantic_annotations(obj, annotations)
        elif obj_origin in MAPPING_TYPES:
            return mapping_like_prepare_pydantic_annotations(obj, annotations)
        else:
            return None

    def _apply_annotations(
        self,
        source_type: Any,
        annotations: list[Any],
        transform_inner_schema: Callable[[CoreSchema], CoreSchema] = lambda x: x,
    ) -> CoreSchema:
        """Apply arguments from `Annotated` or from `FieldInfo` to a schema.

        This gets called by `GenerateSchema._annotated_schema` but differs from it in that it does
        not expect `source_type` to be an `Annotated` object, it expects it to be  the first argument of that
        (in other words, `GenerateSchema._annotated_schema` just unpacks `Annotated`, this process it).
        """
        annotations = list(_known_annotated_metadata.expand_grouped_metadata(annotations))
        res = self._get_prepare_pydantic_annotations_for_known_type(source_type, tuple(annotations))
        if res is not None:
            source_type, annotations = res

        pydantic_js_annotation_functions: list[GetJsonSchemaFunction] = []

        def inner_handler(obj: Any) -> CoreSchema:
            from_property = self._generate_schema_from_property(obj, source_type)
            if from_property is None:
                schema = self._generate_schema_inner(obj)
            else:
                schema = from_property
            metadata_js_function = _extract_get_pydantic_json_schema(obj, schema)
            if metadata_js_function is not None:
                metadata_schema = resolve_original_schema(schema, self.defs.definitions)
                if metadata_schema is not None:
                    self._add_js_function(metadata_schema, metadata_js_function)
            return transform_inner_schema(schema)

        get_inner_schema = CallbackGetCoreSchemaHandler(inner_handler, self)

        for annotation in annotations:
            if annotation is None:
                continue
            get_inner_schema = self._get_wrapped_inner_schema(
                get_inner_schema, annotation, pydantic_js_annotation_functions
            )

        schema = get_inner_schema(source_type)
        if pydantic_js_annotation_functions:
            core_metadata = schema.setdefault('metadata', {})
            update_core_metadata(core_metadata, pydantic_js_annotation_functions=pydantic_js_annotation_functions)
        return _add_custom_serialization_from_json_encoders(self._config_wrapper.json_encoders, source_type, schema)

    def _apply_single_annotation(self, schema: core_schema.CoreSchema, metadata: Any) -> core_schema.CoreSchema:
        FieldInfo = import_cached_field_info()

        if isinstance(metadata, FieldInfo):
            for field_metadata in metadata.metadata:
                schema = self._apply_single_annotation(schema, field_metadata)

            if metadata.discriminator is not None:
                schema = self._apply_discriminator_to_union(schema, metadata.discriminator)
            return schema

        if schema['type'] == 'nullable':
            # for nullable schemas, metadata is automatically applied to the inner schema
            inner = schema.get('schema', core_schema.any_schema())
            inner = self._apply_single_annotation(inner, metadata)
            if inner:
                schema['schema'] = inner
            return schema

        original_schema = schema
        ref = schema.get('ref', None)
        if ref is not None:
            schema = schema.copy()
            new_ref = ref + f'_{repr(metadata)}'
            if new_ref in self.defs.definitions:
                return self.defs.definitions[new_ref]
            schema['ref'] = new_ref  # type: ignore
        elif schema['type'] == 'definition-ref':
            ref = schema['schema_ref']
            if ref in self.defs.definitions:
                schema = self.defs.definitions[ref].copy()
                new_ref = ref + f'_{repr(metadata)}'
                if new_ref in self.defs.definitions:
                    return self.defs.definitions[new_ref]
                schema['ref'] = new_ref  # type: ignore

        maybe_updated_schema = _known_annotated_metadata.apply_known_metadata(metadata, schema.copy())

        if maybe_updated_schema is not None:
            return maybe_updated_schema
        return original_schema

    def _apply_single_annotation_json_schema(
        self, schema: core_schema.CoreSchema, metadata: Any
    ) -> core_schema.CoreSchema:
        FieldInfo = import_cached_field_info()

        if isinstance(metadata, FieldInfo):
            for field_metadata in metadata.metadata:
                schema = self._apply_single_annotation_json_schema(schema, field_metadata)

            pydantic_js_updates, pydantic_js_extra = _extract_json_schema_info_from_field_info(metadata)
            core_metadata = schema.setdefault('metadata', {})
            update_core_metadata(
                core_metadata, pydantic_js_updates=pydantic_js_updates, pydantic_js_extra=pydantic_js_extra
            )
        return schema

    def _get_wrapped_inner_schema(
        self,
        get_inner_schema: GetCoreSchemaHandler,
        annotation: Any,
        pydantic_js_annotation_functions: list[GetJsonSchemaFunction],
    ) -> CallbackGetCoreSchemaHandler:
        metadata_get_schema: GetCoreSchemaFunction = getattr(annotation, '__get_pydantic_core_schema__', None) or (
            lambda source, handler: handler(source)
        )

        def new_handler(source: Any) -> core_schema.CoreSchema:
            schema = metadata_get_schema(source, get_inner_schema)
            schema = self._apply_single_annotation(schema, annotation)
            schema = self._apply_single_annotation_json_schema(schema, annotation)

            metadata_js_function = _extract_get_pydantic_json_schema(annotation, schema)
            if metadata_js_function is not None:
                pydantic_js_annotation_functions.append(metadata_js_function)
            return schema

        return CallbackGetCoreSchemaHandler(new_handler, self)

    def _apply_field_serializers(
        self,
        schema: core_schema.CoreSchema,
        serializers: list[Decorator[FieldSerializerDecoratorInfo]],
    ) -> core_schema.CoreSchema:
        """Apply field serializers to a schema."""
        if serializers:
            schema = copy(schema)
            if schema['type'] == 'definitions':
                inner_schema = schema['schema']
                schema['schema'] = self._apply_field_serializers(inner_schema, serializers)
                return schema
            else:
                ref = typing.cast('str|None', schema.get('ref', None))
                if ref is not None:
                    self.defs.definitions[ref] = schema
                    schema = core_schema.definition_reference_schema(ref)

            # use the last serializer to make it easy to override a serializer set on a parent model
            serializer = serializers[-1]
            is_field_serializer, info_arg = inspect_field_serializer(serializer.func, serializer.info.mode)

            try:
                # Do not pass in globals as the function could be defined in a different module.
                # Instead, let `get_function_return_type` infer the globals to use, but still pass
                # in locals that may contain a parent/rebuild namespace:
                return_type = _decorators.get_function_return_type(
                    serializer.func, serializer.info.return_type, localns=self._types_namespace.locals
                )
            except NameError as e:
                raise PydanticUndefinedAnnotation.from_name_error(e) from e

            if return_type is PydanticUndefined:
                return_schema = None
            else:
                return_schema = self.generate_schema(return_type)

            if serializer.info.mode == 'wrap':
                schema['serialization'] = core_schema.wrap_serializer_function_ser_schema(
                    serializer.func,
                    is_field_serializer=is_field_serializer,
                    info_arg=info_arg,
                    return_schema=return_schema,
                    when_used=serializer.info.when_used,
                )
            else:
                assert serializer.info.mode == 'plain'
                schema['serialization'] = core_schema.plain_serializer_function_ser_schema(
                    serializer.func,
                    is_field_serializer=is_field_serializer,
                    info_arg=info_arg,
                    return_schema=return_schema,
                    when_used=serializer.info.when_used,
                )
        return schema

    def _apply_model_serializers(
        self, schema: core_schema.CoreSchema, serializers: Iterable[Decorator[ModelSerializerDecoratorInfo]]
    ) -> core_schema.CoreSchema:
        """Apply model serializers to a schema."""
        ref: str | None = schema.pop('ref', None)  # type: ignore
        if serializers:
            serializer = list(serializers)[-1]
            info_arg = inspect_model_serializer(serializer.func, serializer.info.mode)

            try:
                # Do not pass in globals as the function could be defined in a different module.
                # Instead, let `get_function_return_type` infer the globals to use, but still pass
                # in locals that may contain a parent/rebuild namespace:
                return_type = _decorators.get_function_return_type(
                    serializer.func, serializer.info.return_type, localns=self._types_namespace.locals
                )
            except NameError as e:
                raise PydanticUndefinedAnnotation.from_name_error(e) from e
            if return_type is PydanticUndefined:
                return_schema = None
            else:
                return_schema = self.generate_schema(return_type)

            if serializer.info.mode == 'wrap':
                ser_schema: core_schema.SerSchema = core_schema.wrap_serializer_function_ser_schema(
                    serializer.func,
                    info_arg=info_arg,
                    return_schema=return_schema,
                    when_used=serializer.info.when_used,
                )
            else:
                # plain
                ser_schema = core_schema.plain_serializer_function_ser_schema(
                    serializer.func,
                    info_arg=info_arg,
                    return_schema=return_schema,
                    when_used=serializer.info.when_used,
                )
            schema['serialization'] = ser_schema
        if ref:
            schema['ref'] = ref  # type: ignore
        return schema


_VALIDATOR_F_MATCH: Mapping[
    tuple[FieldValidatorModes, Literal['no-info', 'with-info']],
    Callable[[Callable[..., Any], core_schema.CoreSchema, str | None], core_schema.CoreSchema],
] = {
    ('before', 'no-info'): lambda f, schema, _: core_schema.no_info_before_validator_function(f, schema),
    ('after', 'no-info'): lambda f, schema, _: core_schema.no_info_after_validator_function(f, schema),
    ('plain', 'no-info'): lambda f, _1, _2: core_schema.no_info_plain_validator_function(f),
    ('wrap', 'no-info'): lambda f, schema, _: core_schema.no_info_wrap_validator_function(f, schema),
    ('before', 'with-info'): lambda f, schema, field_name: core_schema.with_info_before_validator_function(
        f, schema, field_name=field_name
    ),
    ('after', 'with-info'): lambda f, schema, field_name: core_schema.with_info_after_validator_function(
        f, schema, field_name=field_name
    ),
    ('plain', 'with-info'): lambda f, _, field_name: core_schema.with_info_plain_validator_function(
        f, field_name=field_name
    ),
    ('wrap', 'with-info'): lambda f, schema, field_name: core_schema.with_info_wrap_validator_function(
        f, schema, field_name=field_name
    ),
}


# TODO V3: this function is only used for deprecated decorators. It should
# be removed once we drop support for those.
def apply_validators(
    schema: core_schema.CoreSchema,
    validators: Iterable[Decorator[RootValidatorDecoratorInfo]]
    | Iterable[Decorator[ValidatorDecoratorInfo]]
    | Iterable[Decorator[FieldValidatorDecoratorInfo]],
    field_name: str | None,
) -> core_schema.CoreSchema:
    """Apply validators to a schema.

    Args:
        schema: The schema to apply validators on.
        validators: An iterable of validators.
        field_name: The name of the field if validators are being applied to a model field.

    Returns:
        The updated schema.
    """
    for validator in validators:
        info_arg = inspect_validator(validator.func, validator.info.mode)
        val_type = 'with-info' if info_arg else 'no-info'

        schema = _VALIDATOR_F_MATCH[(validator.info.mode, val_type)](validator.func, schema, field_name)
    return schema


def _validators_require_validate_default(validators: Iterable[Decorator[ValidatorDecoratorInfo]]) -> bool:
    """In v1, if any of the validators for a field had `always=True`, the default value would be validated.

    This serves as an auxiliary function for re-implementing that logic, by looping over a provided
    collection of (v1-style) ValidatorDecoratorInfo's and checking if any of them have `always=True`.

    We should be able to drop this function and the associated logic calling it once we drop support
    for v1-style validator decorators. (Or we can extend it and keep it if we add something equivalent
    to the v1-validator `always` kwarg to `field_validator`.)
    """
    for validator in validators:
        if validator.info.always:
            return True
    return False


def apply_model_validators(
    schema: core_schema.CoreSchema,
    validators: Iterable[Decorator[ModelValidatorDecoratorInfo]],
    mode: Literal['inner', 'outer', 'all'],
) -> core_schema.CoreSchema:
    """Apply model validators to a schema.

    If mode == 'inner', only "before" validators are applied
    If mode == 'outer', validators other than "before" are applied
    If mode == 'all', all validators are applied

    Args:
        schema: The schema to apply validators on.
        validators: An iterable of validators.
        mode: The validator mode.

    Returns:
        The updated schema.
    """
    ref: str | None = schema.pop('ref', None)  # type: ignore
    for validator in validators:
        if mode == 'inner' and validator.info.mode != 'before':
            continue
        if mode == 'outer' and validator.info.mode == 'before':
            continue
        info_arg = inspect_validator(validator.func, validator.info.mode)
        if validator.info.mode == 'wrap':
            if info_arg:
                schema = core_schema.with_info_wrap_validator_function(function=validator.func, schema=schema)
            else:
                schema = core_schema.no_info_wrap_validator_function(function=validator.func, schema=schema)
        elif validator.info.mode == 'before':
            if info_arg:
                schema = core_schema.with_info_before_validator_function(function=validator.func, schema=schema)
            else:
                schema = core_schema.no_info_before_validator_function(function=validator.func, schema=schema)
        else:
            assert validator.info.mode == 'after'
            if info_arg:
                schema = core_schema.with_info_after_validator_function(function=validator.func, schema=schema)
            else:
                schema = core_schema.no_info_after_validator_function(function=validator.func, schema=schema)
    if ref:
        schema['ref'] = ref  # type: ignore
    return schema


def wrap_default(field_info: FieldInfo, schema: core_schema.CoreSchema) -> core_schema.CoreSchema:
    """Wrap schema with default schema if default value or `default_factory` are available.

    Args:
        field_info: The field info object.
        schema: The schema to apply default on.

    Returns:
        Updated schema by default value or `default_factory`.
    """
    if field_info.default_factory:
        return core_schema.with_default_schema(
            schema,
            default_factory=field_info.default_factory,
            default_factory_takes_data=takes_validated_data_argument(field_info.default_factory),
            validate_default=field_info.validate_default,
        )
    elif field_info.default is not PydanticUndefined:
        return core_schema.with_default_schema(
            schema, default=field_info.default, validate_default=field_info.validate_default
        )
    else:
        return schema


def _extract_get_pydantic_json_schema(tp: Any, schema: CoreSchema) -> GetJsonSchemaFunction | None:
    """Extract `__get_pydantic_json_schema__` from a type, handling the deprecated `__modify_schema__`."""
    js_modify_function = getattr(tp, '__get_pydantic_json_schema__', None)

    if hasattr(tp, '__modify_schema__'):
        BaseModel = import_cached_base_model()

        has_custom_v2_modify_js_func = (
            js_modify_function is not None
            and BaseModel.__get_pydantic_json_schema__.__func__  # type: ignore
            not in (js_modify_function, getattr(js_modify_function, '__func__', None))
        )

        if not has_custom_v2_modify_js_func:
            cls_name = getattr(tp, '__name__', None)
            raise PydanticUserError(
                f'The `__modify_schema__` method is not supported in Pydantic v2. '
                f'Use `__get_pydantic_json_schema__` instead{f" in class `{cls_name}`" if cls_name else ""}.',
                code='custom-json-schema',
            )

    # handle GenericAlias' but ignore Annotated which "lies" about its origin (in this case it would be `int`)
    if hasattr(tp, '__origin__') and not _typing_extra.is_annotated(tp):
        return _extract_get_pydantic_json_schema(tp.__origin__, schema)

    if js_modify_function is None:
        return None

    return js_modify_function


class _CommonField(TypedDict):
    schema: core_schema.CoreSchema
    validation_alias: str | list[str | int] | list[list[str | int]] | None
    serialization_alias: str | None
    serialization_exclude: bool | None
    frozen: bool | None
    metadata: dict[str, Any]


def _common_field(
    schema: core_schema.CoreSchema,
    *,
    validation_alias: str | list[str | int] | list[list[str | int]] | None = None,
    serialization_alias: str | None = None,
    serialization_exclude: bool | None = None,
    frozen: bool | None = None,
    metadata: Any = None,
) -> _CommonField:
    return {
        'schema': schema,
        'validation_alias': validation_alias,
        'serialization_alias': serialization_alias,
        'serialization_exclude': serialization_exclude,
        'frozen': frozen,
        'metadata': metadata,
    }


class _Definitions:
    """Keeps track of references and definitions."""

    def __init__(self) -> None:
        self.seen: set[str] = set()
        self.definitions: dict[str, core_schema.CoreSchema] = {}

    @contextmanager
    def get_schema_or_ref(self, tp: Any) -> Iterator[tuple[str, None] | tuple[str, CoreSchema]]:
        """Get a definition for `tp` if one exists.

        If a definition exists, a tuple of `(ref_string, CoreSchema)` is returned.
        If no definition exists yet, a tuple of `(ref_string, None)` is returned.

        Note that the returned `CoreSchema` will always be a `DefinitionReferenceSchema`,
        not the actual definition itself.

        This should be called for any type that can be identified by reference.
        This includes any recursive types.

        At present the following types can be named/recursive:

        - BaseModel
        - Dataclasses
        - TypedDict
        - TypeAliasType
        """
        ref = get_type_ref(tp)
        # return the reference if we're either (1) in a cycle or (2) it was already defined
        if ref in self.seen or ref in self.definitions:
            yield (ref, core_schema.definition_reference_schema(ref))
        else:
            self.seen.add(ref)
            try:
                yield (ref, None)
            finally:
                self.seen.discard(ref)


def resolve_original_schema(schema: CoreSchema, definitions: dict[str, CoreSchema]) -> CoreSchema | None:
    if schema['type'] == 'definition-ref':
        return definitions.get(schema['schema_ref'], None)
    elif schema['type'] == 'definitions':
        return schema['schema']
    else:
        return schema


class _FieldNameStack:
    __slots__ = ('_stack',)

    def __init__(self) -> None:
        self._stack: list[str] = []

    @contextmanager
    def push(self, field_name: str) -> Iterator[None]:
        self._stack.append(field_name)
        yield
        self._stack.pop()

    def get(self) -> str | None:
        if self._stack:
            return self._stack[-1]
        else:
            return None


class _ModelTypeStack:
    __slots__ = ('_stack',)

    def __init__(self) -> None:
        self._stack: list[type] = []

    @contextmanager
    def push(self, type_obj: type) -> Iterator[None]:
        self._stack.append(type_obj)
        yield
        self._stack.pop()

    def get(self) -> type | None:
        if self._stack:
            return self._stack[-1]
        else:
            return None
