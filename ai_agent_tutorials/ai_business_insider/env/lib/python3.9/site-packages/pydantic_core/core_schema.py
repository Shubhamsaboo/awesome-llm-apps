"""
This module contains definitions to build schemas which `pydantic_core` can
validate and serialize.
"""

from __future__ import annotations as _annotations

import sys
import warnings
from collections.abc import Mapping
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Callable, Dict, Hashable, List, Pattern, Set, Tuple, Type, Union

from typing_extensions import deprecated

if sys.version_info < (3, 12):
    from typing_extensions import TypedDict
else:
    from typing import TypedDict

if sys.version_info < (3, 11):
    from typing_extensions import Protocol, Required, TypeAlias
else:
    from typing import Protocol, Required, TypeAlias

if sys.version_info < (3, 9):
    from typing_extensions import Literal
else:
    from typing import Literal

if TYPE_CHECKING:
    from pydantic_core import PydanticUndefined
else:
    # The initial build of pydantic_core requires PydanticUndefined to generate
    # the core schema; so we need to conditionally skip it. mypy doesn't like
    # this at all, hence the TYPE_CHECKING branch above.
    try:
        from pydantic_core import PydanticUndefined
    except ImportError:
        PydanticUndefined = object()


ExtraBehavior = Literal['allow', 'forbid', 'ignore']


class CoreConfig(TypedDict, total=False):
    """
    Base class for schema configuration options.

    Attributes:
        title: The name of the configuration.
        strict: Whether the configuration should strictly adhere to specified rules.
        extra_fields_behavior: The behavior for handling extra fields.
        typed_dict_total: Whether the TypedDict should be considered total. Default is `True`.
        from_attributes: Whether to use attributes for models, dataclasses, and tagged union keys.
        loc_by_alias: Whether to use the used alias (or first alias for "field required" errors) instead of
            `field_names` to construct error `loc`s. Default is `True`.
        revalidate_instances: Whether instances of models and dataclasses should re-validate. Default is 'never'.
        validate_default: Whether to validate default values during validation. Default is `False`.
        populate_by_name: Whether an aliased field may be populated by its name as given by the model attribute,
            as well as the alias. (Replaces 'allow_population_by_field_name' in Pydantic v1.) Default is `False`.
        str_max_length: The maximum length for string fields.
        str_min_length: The minimum length for string fields.
        str_strip_whitespace: Whether to strip whitespace from string fields.
        str_to_lower: Whether to convert string fields to lowercase.
        str_to_upper: Whether to convert string fields to uppercase.
        allow_inf_nan: Whether to allow infinity and NaN values for float fields. Default is `True`.
        ser_json_timedelta: The serialization option for `timedelta` values. Default is 'iso8601'.
        ser_json_bytes: The serialization option for `bytes` values. Default is 'utf8'.
        ser_json_inf_nan: The serialization option for infinity and NaN values
            in float fields. Default is 'null'.
        val_json_bytes: The validation option for `bytes` values, complementing ser_json_bytes. Default is 'utf8'.
        hide_input_in_errors: Whether to hide input data from `ValidationError` representation.
        validation_error_cause: Whether to add user-python excs to the __cause__ of a ValidationError.
            Requires exceptiongroup backport pre Python 3.11.
        coerce_numbers_to_str: Whether to enable coercion of any `Number` type to `str` (not applicable in `strict` mode).
        regex_engine: The regex engine to use for regex pattern validation. Default is 'rust-regex'. See `StringSchema`.
        cache_strings: Whether to cache strings. Default is `True`, `True` or `'all'` is required to cache strings
            during general validation since validators don't know if they're in a key or a value.
    """

    title: str
    strict: bool
    # settings related to typed dicts, model fields, dataclass fields
    extra_fields_behavior: ExtraBehavior
    typed_dict_total: bool  # default: True
    # used for models, dataclasses, and tagged union keys
    from_attributes: bool
    # whether to use the used alias (or first alias for "field required" errors) instead of field_names
    # to construct error `loc`s, default True
    loc_by_alias: bool
    # whether instances of models and dataclasses (including subclass instances) should re-validate, default 'never'
    revalidate_instances: Literal['always', 'never', 'subclass-instances']
    # whether to validate default values during validation, default False
    validate_default: bool
    # used on typed-dicts and arguments
    populate_by_name: bool  # replaces `allow_population_by_field_name` in pydantic v1
    # fields related to string fields only
    str_max_length: int
    str_min_length: int
    str_strip_whitespace: bool
    str_to_lower: bool
    str_to_upper: bool
    # fields related to float fields only
    allow_inf_nan: bool  # default: True
    # the config options are used to customise serialization to JSON
    ser_json_timedelta: Literal['iso8601', 'float']  # default: 'iso8601'
    ser_json_bytes: Literal['utf8', 'base64', 'hex']  # default: 'utf8'
    ser_json_inf_nan: Literal['null', 'constants', 'strings']  # default: 'null'
    val_json_bytes: Literal['utf8', 'base64', 'hex']  # default: 'utf8'
    # used to hide input data from ValidationError repr
    hide_input_in_errors: bool
    validation_error_cause: bool  # default: False
    coerce_numbers_to_str: bool  # default: False
    regex_engine: Literal['rust-regex', 'python-re']  # default: 'rust-regex'
    cache_strings: Union[bool, Literal['all', 'keys', 'none']]  # default: 'True'


IncExCall: TypeAlias = 'set[int | str] | dict[int | str, IncExCall] | None'


class SerializationInfo(Protocol):
    @property
    def include(self) -> IncExCall: ...

    @property
    def exclude(self) -> IncExCall: ...

    @property
    def context(self) -> Any | None:
        """Current serialization context."""

    @property
    def mode(self) -> str: ...

    @property
    def by_alias(self) -> bool: ...

    @property
    def exclude_unset(self) -> bool: ...

    @property
    def exclude_defaults(self) -> bool: ...

    @property
    def exclude_none(self) -> bool: ...

    @property
    def serialize_as_any(self) -> bool: ...

    def round_trip(self) -> bool: ...

    def mode_is_json(self) -> bool: ...

    def __str__(self) -> str: ...

    def __repr__(self) -> str: ...


class FieldSerializationInfo(SerializationInfo, Protocol):
    @property
    def field_name(self) -> str: ...


class ValidationInfo(Protocol):
    """
    Argument passed to validation functions.
    """

    @property
    def context(self) -> Any | None:
        """Current validation context."""
        ...

    @property
    def config(self) -> CoreConfig | None:
        """The CoreConfig that applies to this validation."""
        ...

    @property
    def mode(self) -> Literal['python', 'json']:
        """The type of input data we are currently validating"""
        ...

    @property
    def data(self) -> Dict[str, Any]:
        """The data being validated for this model."""
        ...

    @property
    def field_name(self) -> str | None:
        """
        The name of the current field being validated if this validator is
        attached to a model field.
        """
        ...


ExpectedSerializationTypes = Literal[
    'none',
    'int',
    'bool',
    'float',
    'str',
    'bytes',
    'bytearray',
    'list',
    'tuple',
    'set',
    'frozenset',
    'generator',
    'dict',
    'datetime',
    'date',
    'time',
    'timedelta',
    'url',
    'multi-host-url',
    'json',
    'uuid',
    'any',
]


class SimpleSerSchema(TypedDict, total=False):
    type: Required[ExpectedSerializationTypes]


def simple_ser_schema(type: ExpectedSerializationTypes) -> SimpleSerSchema:
    """
    Returns a schema for serialization with a custom type.

    Args:
        type: The type to use for serialization
    """
    return SimpleSerSchema(type=type)


# (input_value: Any, /) -> Any
GeneralPlainNoInfoSerializerFunction = Callable[[Any], Any]
# (input_value: Any, info: FieldSerializationInfo, /) -> Any
GeneralPlainInfoSerializerFunction = Callable[[Any, SerializationInfo], Any]
# (model: Any, input_value: Any, /) -> Any
FieldPlainNoInfoSerializerFunction = Callable[[Any, Any], Any]
# (model: Any, input_value: Any, info: FieldSerializationInfo, /) -> Any
FieldPlainInfoSerializerFunction = Callable[[Any, Any, FieldSerializationInfo], Any]
SerializerFunction = Union[
    GeneralPlainNoInfoSerializerFunction,
    GeneralPlainInfoSerializerFunction,
    FieldPlainNoInfoSerializerFunction,
    FieldPlainInfoSerializerFunction,
]

WhenUsed = Literal['always', 'unless-none', 'json', 'json-unless-none']
"""
Values have the following meanings:

* `'always'` means always use
* `'unless-none'` means use unless the value is `None`
* `'json'` means use when serializing to JSON
* `'json-unless-none'` means use when serializing to JSON and the value is not `None`
"""


class PlainSerializerFunctionSerSchema(TypedDict, total=False):
    type: Required[Literal['function-plain']]
    function: Required[SerializerFunction]
    is_field_serializer: bool  # default False
    info_arg: bool  # default False
    return_schema: CoreSchema  # if omitted, AnySchema is used
    when_used: WhenUsed  # default: 'always'


def plain_serializer_function_ser_schema(
    function: SerializerFunction,
    *,
    is_field_serializer: bool | None = None,
    info_arg: bool | None = None,
    return_schema: CoreSchema | None = None,
    when_used: WhenUsed = 'always',
) -> PlainSerializerFunctionSerSchema:
    """
    Returns a schema for serialization with a function, can be either a "general" or "field" function.

    Args:
        function: The function to use for serialization
        is_field_serializer: Whether the serializer is for a field, e.g. takes `model` as the first argument,
            and `info` includes `field_name`
        info_arg: Whether the function takes an `info` argument
        return_schema: Schema to use for serializing return value
        when_used: When the function should be called
    """
    if when_used == 'always':
        # just to avoid extra elements in schema, and to use the actual default defined in rust
        when_used = None  # type: ignore
    return _dict_not_none(
        type='function-plain',
        function=function,
        is_field_serializer=is_field_serializer,
        info_arg=info_arg,
        return_schema=return_schema,
        when_used=when_used,
    )


class SerializerFunctionWrapHandler(Protocol):  # pragma: no cover
    def __call__(self, input_value: Any, index_key: int | str | None = None, /) -> Any: ...


# (input_value: Any, serializer: SerializerFunctionWrapHandler, /) -> Any
GeneralWrapNoInfoSerializerFunction = Callable[[Any, SerializerFunctionWrapHandler], Any]
# (input_value: Any, serializer: SerializerFunctionWrapHandler, info: SerializationInfo, /) -> Any
GeneralWrapInfoSerializerFunction = Callable[[Any, SerializerFunctionWrapHandler, SerializationInfo], Any]
# (model: Any, input_value: Any, serializer: SerializerFunctionWrapHandler, /) -> Any
FieldWrapNoInfoSerializerFunction = Callable[[Any, Any, SerializerFunctionWrapHandler], Any]
# (model: Any, input_value: Any, serializer: SerializerFunctionWrapHandler, info: FieldSerializationInfo, /) -> Any
FieldWrapInfoSerializerFunction = Callable[[Any, Any, SerializerFunctionWrapHandler, FieldSerializationInfo], Any]
WrapSerializerFunction = Union[
    GeneralWrapNoInfoSerializerFunction,
    GeneralWrapInfoSerializerFunction,
    FieldWrapNoInfoSerializerFunction,
    FieldWrapInfoSerializerFunction,
]


class WrapSerializerFunctionSerSchema(TypedDict, total=False):
    type: Required[Literal['function-wrap']]
    function: Required[WrapSerializerFunction]
    is_field_serializer: bool  # default False
    info_arg: bool  # default False
    schema: CoreSchema  # if omitted, the schema on which this serializer is defined is used
    return_schema: CoreSchema  # if omitted, AnySchema is used
    when_used: WhenUsed  # default: 'always'


def wrap_serializer_function_ser_schema(
    function: WrapSerializerFunction,
    *,
    is_field_serializer: bool | None = None,
    info_arg: bool | None = None,
    schema: CoreSchema | None = None,
    return_schema: CoreSchema | None = None,
    when_used: WhenUsed = 'always',
) -> WrapSerializerFunctionSerSchema:
    """
    Returns a schema for serialization with a wrap function, can be either a "general" or "field" function.

    Args:
        function: The function to use for serialization
        is_field_serializer: Whether the serializer is for a field, e.g. takes `model` as the first argument,
            and `info` includes `field_name`
        info_arg: Whether the function takes an `info` argument
        schema: The schema to use for the inner serialization
        return_schema: Schema to use for serializing return value
        when_used: When the function should be called
    """
    if when_used == 'always':
        # just to avoid extra elements in schema, and to use the actual default defined in rust
        when_used = None  # type: ignore
    return _dict_not_none(
        type='function-wrap',
        function=function,
        is_field_serializer=is_field_serializer,
        info_arg=info_arg,
        schema=schema,
        return_schema=return_schema,
        when_used=when_used,
    )


class FormatSerSchema(TypedDict, total=False):
    type: Required[Literal['format']]
    formatting_string: Required[str]
    when_used: WhenUsed  # default: 'json-unless-none'


def format_ser_schema(formatting_string: str, *, when_used: WhenUsed = 'json-unless-none') -> FormatSerSchema:
    """
    Returns a schema for serialization using python's `format` method.

    Args:
        formatting_string: String defining the format to use
        when_used: Same meaning as for [general_function_plain_ser_schema], but with a different default
    """
    if when_used == 'json-unless-none':
        # just to avoid extra elements in schema, and to use the actual default defined in rust
        when_used = None  # type: ignore
    return _dict_not_none(type='format', formatting_string=formatting_string, when_used=when_used)


class ToStringSerSchema(TypedDict, total=False):
    type: Required[Literal['to-string']]
    when_used: WhenUsed  # default: 'json-unless-none'


def to_string_ser_schema(*, when_used: WhenUsed = 'json-unless-none') -> ToStringSerSchema:
    """
    Returns a schema for serialization using python's `str()` / `__str__` method.

    Args:
        when_used: Same meaning as for [general_function_plain_ser_schema], but with a different default
    """
    s = dict(type='to-string')
    if when_used != 'json-unless-none':
        # just to avoid extra elements in schema, and to use the actual default defined in rust
        s['when_used'] = when_used
    return s  # type: ignore


class ModelSerSchema(TypedDict, total=False):
    type: Required[Literal['model']]
    cls: Required[Type[Any]]
    schema: Required[CoreSchema]


def model_ser_schema(cls: Type[Any], schema: CoreSchema) -> ModelSerSchema:
    """
    Returns a schema for serialization using a model.

    Args:
        cls: The expected class type, used to generate warnings if the wrong type is passed
        schema: Internal schema to use to serialize the model dict
    """
    return ModelSerSchema(type='model', cls=cls, schema=schema)


SerSchema = Union[
    SimpleSerSchema,
    PlainSerializerFunctionSerSchema,
    WrapSerializerFunctionSerSchema,
    FormatSerSchema,
    ToStringSerSchema,
    ModelSerSchema,
]


class InvalidSchema(TypedDict, total=False):
    type: Required[Literal['invalid']]
    ref: str
    metadata: Dict[str, Any]
    # note, we never plan to use this, but include it for type checking purposes to match
    # all other CoreSchema union members
    serialization: SerSchema


def invalid_schema(ref: str | None = None, metadata: Dict[str, Any] | None = None) -> InvalidSchema:
    """
    Returns an invalid schema, used to indicate that a schema is invalid.

        Returns a schema that matches any value, e.g.:

    Args:
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
    """

    return _dict_not_none(type='invalid', ref=ref, metadata=metadata)


class ComputedField(TypedDict, total=False):
    type: Required[Literal['computed-field']]
    property_name: Required[str]
    return_schema: Required[CoreSchema]
    alias: str
    metadata: Dict[str, Any]


def computed_field(
    property_name: str, return_schema: CoreSchema, *, alias: str | None = None, metadata: Dict[str, Any] | None = None
) -> ComputedField:
    """
    ComputedFields are properties of a model or dataclass that are included in serialization.

    Args:
        property_name: The name of the property on the model or dataclass
        return_schema: The schema used for the type returned by the computed field
        alias: The name to use in the serialized output
        metadata: Any other information you want to include with the schema, not used by pydantic-core
    """
    return _dict_not_none(
        type='computed-field', property_name=property_name, return_schema=return_schema, alias=alias, metadata=metadata
    )


class AnySchema(TypedDict, total=False):
    type: Required[Literal['any']]
    ref: str
    metadata: Dict[str, Any]
    serialization: SerSchema


def any_schema(
    *, ref: str | None = None, metadata: Dict[str, Any] | None = None, serialization: SerSchema | None = None
) -> AnySchema:
    """
    Returns a schema that matches any value, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    schema = core_schema.any_schema()
    v = SchemaValidator(schema)
    assert v.validate_python(1) == 1
    ```

    Args:
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(type='any', ref=ref, metadata=metadata, serialization=serialization)


class NoneSchema(TypedDict, total=False):
    type: Required[Literal['none']]
    ref: str
    metadata: Dict[str, Any]
    serialization: SerSchema


def none_schema(
    *, ref: str | None = None, metadata: Dict[str, Any] | None = None, serialization: SerSchema | None = None
) -> NoneSchema:
    """
    Returns a schema that matches a None value, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    schema = core_schema.none_schema()
    v = SchemaValidator(schema)
    assert v.validate_python(None) is None
    ```

    Args:
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(type='none', ref=ref, metadata=metadata, serialization=serialization)


class BoolSchema(TypedDict, total=False):
    type: Required[Literal['bool']]
    strict: bool
    ref: str
    metadata: Dict[str, Any]
    serialization: SerSchema


def bool_schema(
    strict: bool | None = None,
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> BoolSchema:
    """
    Returns a schema that matches a bool value, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    schema = core_schema.bool_schema()
    v = SchemaValidator(schema)
    assert v.validate_python('True') is True
    ```

    Args:
        strict: Whether the value should be a bool or a value that can be converted to a bool
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(type='bool', strict=strict, ref=ref, metadata=metadata, serialization=serialization)


class IntSchema(TypedDict, total=False):
    type: Required[Literal['int']]
    multiple_of: int
    le: int
    ge: int
    lt: int
    gt: int
    strict: bool
    ref: str
    metadata: Dict[str, Any]
    serialization: SerSchema


def int_schema(
    *,
    multiple_of: int | None = None,
    le: int | None = None,
    ge: int | None = None,
    lt: int | None = None,
    gt: int | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> IntSchema:
    """
    Returns a schema that matches a int value, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    schema = core_schema.int_schema(multiple_of=2, le=6, ge=2)
    v = SchemaValidator(schema)
    assert v.validate_python('4') == 4
    ```

    Args:
        multiple_of: The value must be a multiple of this number
        le: The value must be less than or equal to this number
        ge: The value must be greater than or equal to this number
        lt: The value must be strictly less than this number
        gt: The value must be strictly greater than this number
        strict: Whether the value should be a int or a value that can be converted to a int
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='int',
        multiple_of=multiple_of,
        le=le,
        ge=ge,
        lt=lt,
        gt=gt,
        strict=strict,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


class FloatSchema(TypedDict, total=False):
    type: Required[Literal['float']]
    allow_inf_nan: bool  # whether 'NaN', '+inf', '-inf' should be forbidden. default: True
    multiple_of: float
    le: float
    ge: float
    lt: float
    gt: float
    strict: bool
    ref: str
    metadata: Dict[str, Any]
    serialization: SerSchema


def float_schema(
    *,
    allow_inf_nan: bool | None = None,
    multiple_of: float | None = None,
    le: float | None = None,
    ge: float | None = None,
    lt: float | None = None,
    gt: float | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> FloatSchema:
    """
    Returns a schema that matches a float value, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    schema = core_schema.float_schema(le=0.8, ge=0.2)
    v = SchemaValidator(schema)
    assert v.validate_python('0.5') == 0.5
    ```

    Args:
        allow_inf_nan: Whether to allow inf and nan values
        multiple_of: The value must be a multiple of this number
        le: The value must be less than or equal to this number
        ge: The value must be greater than or equal to this number
        lt: The value must be strictly less than this number
        gt: The value must be strictly greater than this number
        strict: Whether the value should be a float or a value that can be converted to a float
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='float',
        allow_inf_nan=allow_inf_nan,
        multiple_of=multiple_of,
        le=le,
        ge=ge,
        lt=lt,
        gt=gt,
        strict=strict,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


class DecimalSchema(TypedDict, total=False):
    type: Required[Literal['decimal']]
    allow_inf_nan: bool  # whether 'NaN', '+inf', '-inf' should be forbidden. default: False
    multiple_of: Decimal
    le: Decimal
    ge: Decimal
    lt: Decimal
    gt: Decimal
    max_digits: int
    decimal_places: int
    strict: bool
    ref: str
    metadata: Dict[str, Any]
    serialization: SerSchema


def decimal_schema(
    *,
    allow_inf_nan: bool | None = None,
    multiple_of: Decimal | None = None,
    le: Decimal | None = None,
    ge: Decimal | None = None,
    lt: Decimal | None = None,
    gt: Decimal | None = None,
    max_digits: int | None = None,
    decimal_places: int | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> DecimalSchema:
    """
    Returns a schema that matches a decimal value, e.g.:

    ```py
    from decimal import Decimal
    from pydantic_core import SchemaValidator, core_schema

    schema = core_schema.decimal_schema(le=0.8, ge=0.2)
    v = SchemaValidator(schema)
    assert v.validate_python('0.5') == Decimal('0.5')
    ```

    Args:
        allow_inf_nan: Whether to allow inf and nan values
        multiple_of: The value must be a multiple of this number
        le: The value must be less than or equal to this number
        ge: The value must be greater than or equal to this number
        lt: The value must be strictly less than this number
        gt: The value must be strictly greater than this number
        max_digits: The maximum number of decimal digits allowed
        decimal_places: The maximum number of decimal places allowed
        strict: Whether the value should be a float or a value that can be converted to a float
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='decimal',
        gt=gt,
        ge=ge,
        lt=lt,
        le=le,
        max_digits=max_digits,
        decimal_places=decimal_places,
        multiple_of=multiple_of,
        allow_inf_nan=allow_inf_nan,
        strict=strict,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


class ComplexSchema(TypedDict, total=False):
    type: Required[Literal['complex']]
    strict: bool
    ref: str
    metadata: Dict[str, Any]
    serialization: SerSchema


def complex_schema(
    *,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> ComplexSchema:
    """
    Returns a schema that matches a complex value, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    schema = core_schema.complex_schema()
    v = SchemaValidator(schema)
    assert v.validate_python('1+2j') == complex(1, 2)
    assert v.validate_python(complex(1, 2)) == complex(1, 2)
    ```

    Args:
        strict: Whether the value should be a complex object instance or a value that can be converted to a complex object
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='complex',
        strict=strict,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


class StringSchema(TypedDict, total=False):
    type: Required[Literal['str']]
    pattern: Union[str, Pattern[str]]
    max_length: int
    min_length: int
    strip_whitespace: bool
    to_lower: bool
    to_upper: bool
    regex_engine: Literal['rust-regex', 'python-re']  # default: 'rust-regex'
    strict: bool
    coerce_numbers_to_str: bool
    ref: str
    metadata: Dict[str, Any]
    serialization: SerSchema


def str_schema(
    *,
    pattern: str | Pattern[str] | None = None,
    max_length: int | None = None,
    min_length: int | None = None,
    strip_whitespace: bool | None = None,
    to_lower: bool | None = None,
    to_upper: bool | None = None,
    regex_engine: Literal['rust-regex', 'python-re'] | None = None,
    strict: bool | None = None,
    coerce_numbers_to_str: bool | None = None,
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> StringSchema:
    """
    Returns a schema that matches a string value, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    schema = core_schema.str_schema(max_length=10, min_length=2)
    v = SchemaValidator(schema)
    assert v.validate_python('hello') == 'hello'
    ```

    Args:
        pattern: A regex pattern that the value must match
        max_length: The value must be at most this length
        min_length: The value must be at least this length
        strip_whitespace: Whether to strip whitespace from the value
        to_lower: Whether to convert the value to lowercase
        to_upper: Whether to convert the value to uppercase
        regex_engine: The regex engine to use for pattern validation. Default is 'rust-regex'.
            - `rust-regex` uses the [`regex`](https://docs.rs/regex) Rust
              crate, which is non-backtracking and therefore more DDoS
              resistant, but does not support all regex features.
            - `python-re` use the [`re`](https://docs.python.org/3/library/re.html) module,
              which supports all regex features, but may be slower.
        strict: Whether the value should be a string or a value that can be converted to a string
        coerce_numbers_to_str: Whether to enable coercion of any `Number` type to `str` (not applicable in `strict` mode).
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='str',
        pattern=pattern,
        max_length=max_length,
        min_length=min_length,
        strip_whitespace=strip_whitespace,
        to_lower=to_lower,
        to_upper=to_upper,
        regex_engine=regex_engine,
        strict=strict,
        coerce_numbers_to_str=coerce_numbers_to_str,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


class BytesSchema(TypedDict, total=False):
    type: Required[Literal['bytes']]
    max_length: int
    min_length: int
    strict: bool
    ref: str
    metadata: Dict[str, Any]
    serialization: SerSchema


def bytes_schema(
    *,
    max_length: int | None = None,
    min_length: int | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> BytesSchema:
    """
    Returns a schema that matches a bytes value, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    schema = core_schema.bytes_schema(max_length=10, min_length=2)
    v = SchemaValidator(schema)
    assert v.validate_python(b'hello') == b'hello'
    ```

    Args:
        max_length: The value must be at most this length
        min_length: The value must be at least this length
        strict: Whether the value should be a bytes or a value that can be converted to a bytes
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='bytes',
        max_length=max_length,
        min_length=min_length,
        strict=strict,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


class DateSchema(TypedDict, total=False):
    type: Required[Literal['date']]
    strict: bool
    le: date
    ge: date
    lt: date
    gt: date
    now_op: Literal['past', 'future']
    # defaults to current local utc offset from `time.localtime().tm_gmtoff`
    # value is restricted to -86_400 < offset < 86_400 by bounds in generate_self_schema.py
    now_utc_offset: int
    ref: str
    metadata: Dict[str, Any]
    serialization: SerSchema


def date_schema(
    *,
    strict: bool | None = None,
    le: date | None = None,
    ge: date | None = None,
    lt: date | None = None,
    gt: date | None = None,
    now_op: Literal['past', 'future'] | None = None,
    now_utc_offset: int | None = None,
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> DateSchema:
    """
    Returns a schema that matches a date value, e.g.:

    ```py
    from datetime import date
    from pydantic_core import SchemaValidator, core_schema

    schema = core_schema.date_schema(le=date(2020, 1, 1), ge=date(2019, 1, 1))
    v = SchemaValidator(schema)
    assert v.validate_python(date(2019, 6, 1)) == date(2019, 6, 1)
    ```

    Args:
        strict: Whether the value should be a date or a value that can be converted to a date
        le: The value must be less than or equal to this date
        ge: The value must be greater than or equal to this date
        lt: The value must be strictly less than this date
        gt: The value must be strictly greater than this date
        now_op: The value must be in the past or future relative to the current date
        now_utc_offset: The value must be in the past or future relative to the current date with this utc offset
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='date',
        strict=strict,
        le=le,
        ge=ge,
        lt=lt,
        gt=gt,
        now_op=now_op,
        now_utc_offset=now_utc_offset,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


class TimeSchema(TypedDict, total=False):
    type: Required[Literal['time']]
    strict: bool
    le: time
    ge: time
    lt: time
    gt: time
    tz_constraint: Union[Literal['aware', 'naive'], int]
    microseconds_precision: Literal['truncate', 'error']
    ref: str
    metadata: Dict[str, Any]
    serialization: SerSchema


def time_schema(
    *,
    strict: bool | None = None,
    le: time | None = None,
    ge: time | None = None,
    lt: time | None = None,
    gt: time | None = None,
    tz_constraint: Literal['aware', 'naive'] | int | None = None,
    microseconds_precision: Literal['truncate', 'error'] = 'truncate',
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> TimeSchema:
    """
    Returns a schema that matches a time value, e.g.:

    ```py
    from datetime import time
    from pydantic_core import SchemaValidator, core_schema

    schema = core_schema.time_schema(le=time(12, 0, 0), ge=time(6, 0, 0))
    v = SchemaValidator(schema)
    assert v.validate_python(time(9, 0, 0)) == time(9, 0, 0)
    ```

    Args:
        strict: Whether the value should be a time or a value that can be converted to a time
        le: The value must be less than or equal to this time
        ge: The value must be greater than or equal to this time
        lt: The value must be strictly less than this time
        gt: The value must be strictly greater than this time
        tz_constraint: The value must be timezone aware or naive, or an int to indicate required tz offset
        microseconds_precision: The behavior when seconds have more than 6 digits or microseconds is too large
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='time',
        strict=strict,
        le=le,
        ge=ge,
        lt=lt,
        gt=gt,
        tz_constraint=tz_constraint,
        microseconds_precision=microseconds_precision,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


class DatetimeSchema(TypedDict, total=False):
    type: Required[Literal['datetime']]
    strict: bool
    le: datetime
    ge: datetime
    lt: datetime
    gt: datetime
    now_op: Literal['past', 'future']
    tz_constraint: Union[Literal['aware', 'naive'], int]
    # defaults to current local utc offset from `time.localtime().tm_gmtoff`
    # value is restricted to -86_400 < offset < 86_400 by bounds in generate_self_schema.py
    now_utc_offset: int
    microseconds_precision: Literal['truncate', 'error']  # default: 'truncate'
    ref: str
    metadata: Dict[str, Any]
    serialization: SerSchema


def datetime_schema(
    *,
    strict: bool | None = None,
    le: datetime | None = None,
    ge: datetime | None = None,
    lt: datetime | None = None,
    gt: datetime | None = None,
    now_op: Literal['past', 'future'] | None = None,
    tz_constraint: Literal['aware', 'naive'] | int | None = None,
    now_utc_offset: int | None = None,
    microseconds_precision: Literal['truncate', 'error'] = 'truncate',
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> DatetimeSchema:
    """
    Returns a schema that matches a datetime value, e.g.:

    ```py
    from datetime import datetime
    from pydantic_core import SchemaValidator, core_schema

    schema = core_schema.datetime_schema()
    v = SchemaValidator(schema)
    now = datetime.now()
    assert v.validate_python(str(now)) == now
    ```

    Args:
        strict: Whether the value should be a datetime or a value that can be converted to a datetime
        le: The value must be less than or equal to this datetime
        ge: The value must be greater than or equal to this datetime
        lt: The value must be strictly less than this datetime
        gt: The value must be strictly greater than this datetime
        now_op: The value must be in the past or future relative to the current datetime
        tz_constraint: The value must be timezone aware or naive, or an int to indicate required tz offset
            TODO: use of a tzinfo where offset changes based on the datetime is not yet supported
        now_utc_offset: The value must be in the past or future relative to the current datetime with this utc offset
        microseconds_precision: The behavior when seconds have more than 6 digits or microseconds is too large
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='datetime',
        strict=strict,
        le=le,
        ge=ge,
        lt=lt,
        gt=gt,
        now_op=now_op,
        tz_constraint=tz_constraint,
        now_utc_offset=now_utc_offset,
        microseconds_precision=microseconds_precision,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


class TimedeltaSchema(TypedDict, total=False):
    type: Required[Literal['timedelta']]
    strict: bool
    le: timedelta
    ge: timedelta
    lt: timedelta
    gt: timedelta
    microseconds_precision: Literal['truncate', 'error']
    ref: str
    metadata: Dict[str, Any]
    serialization: SerSchema


def timedelta_schema(
    *,
    strict: bool | None = None,
    le: timedelta | None = None,
    ge: timedelta | None = None,
    lt: timedelta | None = None,
    gt: timedelta | None = None,
    microseconds_precision: Literal['truncate', 'error'] = 'truncate',
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> TimedeltaSchema:
    """
    Returns a schema that matches a timedelta value, e.g.:

    ```py
    from datetime import timedelta
    from pydantic_core import SchemaValidator, core_schema

    schema = core_schema.timedelta_schema(le=timedelta(days=1), ge=timedelta(days=0))
    v = SchemaValidator(schema)
    assert v.validate_python(timedelta(hours=12)) == timedelta(hours=12)
    ```

    Args:
        strict: Whether the value should be a timedelta or a value that can be converted to a timedelta
        le: The value must be less than or equal to this timedelta
        ge: The value must be greater than or equal to this timedelta
        lt: The value must be strictly less than this timedelta
        gt: The value must be strictly greater than this timedelta
        microseconds_precision: The behavior when seconds have more than 6 digits or microseconds is too large
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='timedelta',
        strict=strict,
        le=le,
        ge=ge,
        lt=lt,
        gt=gt,
        microseconds_precision=microseconds_precision,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


class LiteralSchema(TypedDict, total=False):
    type: Required[Literal['literal']]
    expected: Required[List[Any]]
    ref: str
    metadata: Dict[str, Any]
    serialization: SerSchema


def literal_schema(
    expected: list[Any],
    *,
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> LiteralSchema:
    """
    Returns a schema that matches a literal value, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    schema = core_schema.literal_schema(['hello', 'world'])
    v = SchemaValidator(schema)
    assert v.validate_python('hello') == 'hello'
    ```

    Args:
        expected: The value must be one of these values
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(type='literal', expected=expected, ref=ref, metadata=metadata, serialization=serialization)


class EnumSchema(TypedDict, total=False):
    type: Required[Literal['enum']]
    cls: Required[Any]
    members: Required[List[Any]]
    sub_type: Literal['str', 'int', 'float']
    missing: Callable[[Any], Any]
    strict: bool
    ref: str
    metadata: Dict[str, Any]
    serialization: SerSchema


def enum_schema(
    cls: Any,
    members: list[Any],
    *,
    sub_type: Literal['str', 'int', 'float'] | None = None,
    missing: Callable[[Any], Any] | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> EnumSchema:
    """
    Returns a schema that matches an enum value, e.g.:

    ```py
    from enum import Enum
    from pydantic_core import SchemaValidator, core_schema

    class Color(Enum):
        RED = 1
        GREEN = 2
        BLUE = 3

    schema = core_schema.enum_schema(Color, list(Color.__members__.values()))
    v = SchemaValidator(schema)
    assert v.validate_python(2) is Color.GREEN
    ```

    Args:
        cls: The enum class
        members: The members of the enum, generally `list(MyEnum.__members__.values())`
        sub_type: The type of the enum, either 'str' or 'int' or None for plain enums
        missing: A function to use when the value is not found in the enum, from `_missing_`
        strict: Whether to use strict mode, defaults to False
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='enum',
        cls=cls,
        members=members,
        sub_type=sub_type,
        missing=missing,
        strict=strict,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


# must match input/parse_json.rs::JsonType::try_from
JsonType = Literal['null', 'bool', 'int', 'float', 'str', 'list', 'dict']


class IsInstanceSchema(TypedDict, total=False):
    type: Required[Literal['is-instance']]
    cls: Required[Any]
    cls_repr: str
    ref: str
    metadata: Dict[str, Any]
    serialization: SerSchema


def is_instance_schema(
    cls: Any,
    *,
    cls_repr: str | None = None,
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> IsInstanceSchema:
    """
    Returns a schema that checks if a value is an instance of a class, equivalent to python's `isinstance` method, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    class A:
        pass

    schema = core_schema.is_instance_schema(cls=A)
    v = SchemaValidator(schema)
    v.validate_python(A())
    ```

    Args:
        cls: The value must be an instance of this class
        cls_repr: If provided this string is used in the validator name instead of `repr(cls)`
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='is-instance', cls=cls, cls_repr=cls_repr, ref=ref, metadata=metadata, serialization=serialization
    )


class IsSubclassSchema(TypedDict, total=False):
    type: Required[Literal['is-subclass']]
    cls: Required[Type[Any]]
    cls_repr: str
    ref: str
    metadata: Dict[str, Any]
    serialization: SerSchema


def is_subclass_schema(
    cls: Type[Any],
    *,
    cls_repr: str | None = None,
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> IsInstanceSchema:
    """
    Returns a schema that checks if a value is a subtype of a class, equivalent to python's `issubclass` method, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    class A:
        pass

    class B(A):
        pass

    schema = core_schema.is_subclass_schema(cls=A)
    v = SchemaValidator(schema)
    v.validate_python(B)
    ```

    Args:
        cls: The value must be a subclass of this class
        cls_repr: If provided this string is used in the validator name instead of `repr(cls)`
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='is-subclass', cls=cls, cls_repr=cls_repr, ref=ref, metadata=metadata, serialization=serialization
    )


class CallableSchema(TypedDict, total=False):
    type: Required[Literal['callable']]
    ref: str
    metadata: Dict[str, Any]
    serialization: SerSchema


def callable_schema(
    *, ref: str | None = None, metadata: Dict[str, Any] | None = None, serialization: SerSchema | None = None
) -> CallableSchema:
    """
    Returns a schema that checks if a value is callable, equivalent to python's `callable` method, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    schema = core_schema.callable_schema()
    v = SchemaValidator(schema)
    v.validate_python(min)
    ```

    Args:
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(type='callable', ref=ref, metadata=metadata, serialization=serialization)


class UuidSchema(TypedDict, total=False):
    type: Required[Literal['uuid']]
    version: Literal[1, 3, 4, 5]
    strict: bool
    ref: str
    metadata: Dict[str, Any]
    serialization: SerSchema


def uuid_schema(
    *,
    version: Literal[1, 3, 4, 5] | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> UuidSchema:
    return _dict_not_none(
        type='uuid', version=version, strict=strict, ref=ref, metadata=metadata, serialization=serialization
    )


class IncExSeqSerSchema(TypedDict, total=False):
    type: Required[Literal['include-exclude-sequence']]
    include: Set[int]
    exclude: Set[int]


def filter_seq_schema(*, include: Set[int] | None = None, exclude: Set[int] | None = None) -> IncExSeqSerSchema:
    return _dict_not_none(type='include-exclude-sequence', include=include, exclude=exclude)


IncExSeqOrElseSerSchema = Union[IncExSeqSerSchema, SerSchema]


class ListSchema(TypedDict, total=False):
    type: Required[Literal['list']]
    items_schema: CoreSchema
    min_length: int
    max_length: int
    fail_fast: bool
    strict: bool
    ref: str
    metadata: Dict[str, Any]
    serialization: IncExSeqOrElseSerSchema


def list_schema(
    items_schema: CoreSchema | None = None,
    *,
    min_length: int | None = None,
    max_length: int | None = None,
    fail_fast: bool | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: IncExSeqOrElseSerSchema | None = None,
) -> ListSchema:
    """
    Returns a schema that matches a list value, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    schema = core_schema.list_schema(core_schema.int_schema(), min_length=0, max_length=10)
    v = SchemaValidator(schema)
    assert v.validate_python(['4']) == [4]
    ```

    Args:
        items_schema: The value must be a list of items that match this schema
        min_length: The value must be a list with at least this many items
        max_length: The value must be a list with at most this many items
        fail_fast: Stop validation on the first error
        strict: The value must be a list with exactly this many items
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='list',
        items_schema=items_schema,
        min_length=min_length,
        max_length=max_length,
        fail_fast=fail_fast,
        strict=strict,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


# @deprecated('tuple_positional_schema is deprecated. Use pydantic_core.core_schema.tuple_schema instead.')
def tuple_positional_schema(
    items_schema: list[CoreSchema],
    *,
    extras_schema: CoreSchema | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: IncExSeqOrElseSerSchema | None = None,
) -> TupleSchema:
    """
    Returns a schema that matches a tuple of schemas, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    schema = core_schema.tuple_positional_schema(
        [core_schema.int_schema(), core_schema.str_schema()]
    )
    v = SchemaValidator(schema)
    assert v.validate_python((1, 'hello')) == (1, 'hello')
    ```

    Args:
        items_schema: The value must be a tuple with items that match these schemas
        extras_schema: The value must be a tuple with items that match this schema
            This was inspired by JSON schema's `prefixItems` and `items` fields.
            In python's `typing.Tuple`, you can't specify a type for "extra" items -- they must all be the same type
            if the length is variable. So this field won't be set from a `typing.Tuple` annotation on a pydantic model.
        strict: The value must be a tuple with exactly this many items
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    if extras_schema is not None:
        variadic_item_index = len(items_schema)
        items_schema = items_schema + [extras_schema]
    else:
        variadic_item_index = None
    return tuple_schema(
        items_schema=items_schema,
        variadic_item_index=variadic_item_index,
        strict=strict,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


# @deprecated('tuple_variable_schema is deprecated. Use pydantic_core.core_schema.tuple_schema instead.')
def tuple_variable_schema(
    items_schema: CoreSchema | None = None,
    *,
    min_length: int | None = None,
    max_length: int | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: IncExSeqOrElseSerSchema | None = None,
) -> TupleSchema:
    """
    Returns a schema that matches a tuple of a given schema, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    schema = core_schema.tuple_variable_schema(
        items_schema=core_schema.int_schema(), min_length=0, max_length=10
    )
    v = SchemaValidator(schema)
    assert v.validate_python(('1', 2, 3)) == (1, 2, 3)
    ```

    Args:
        items_schema: The value must be a tuple with items that match this schema
        min_length: The value must be a tuple with at least this many items
        max_length: The value must be a tuple with at most this many items
        strict: The value must be a tuple with exactly this many items
        ref: Optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return tuple_schema(
        items_schema=[items_schema or any_schema()],
        variadic_item_index=0,
        min_length=min_length,
        max_length=max_length,
        strict=strict,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


class TupleSchema(TypedDict, total=False):
    type: Required[Literal['tuple']]
    items_schema: Required[List[CoreSchema]]
    variadic_item_index: int
    min_length: int
    max_length: int
    fail_fast: bool
    strict: bool
    ref: str
    metadata: Dict[str, Any]
    serialization: IncExSeqOrElseSerSchema


def tuple_schema(
    items_schema: list[CoreSchema],
    *,
    variadic_item_index: int | None = None,
    min_length: int | None = None,
    max_length: int | None = None,
    fail_fast: bool | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: IncExSeqOrElseSerSchema | None = None,
) -> TupleSchema:
    """
    Returns a schema that matches a tuple of schemas, with an optional variadic item, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    schema = core_schema.tuple_schema(
        [core_schema.int_schema(), core_schema.str_schema(), core_schema.float_schema()],
        variadic_item_index=1,
    )
    v = SchemaValidator(schema)
    assert v.validate_python((1, 'hello', 'world', 1.5)) == (1, 'hello', 'world', 1.5)
    ```

    Args:
        items_schema: The value must be a tuple with items that match these schemas
        variadic_item_index: The index of the schema in `items_schema` to be treated as variadic (following PEP 646)
        min_length: The value must be a tuple with at least this many items
        max_length: The value must be a tuple with at most this many items
        fail_fast: Stop validation on the first error
        strict: The value must be a tuple with exactly this many items
        ref: Optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='tuple',
        items_schema=items_schema,
        variadic_item_index=variadic_item_index,
        min_length=min_length,
        max_length=max_length,
        fail_fast=fail_fast,
        strict=strict,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


class SetSchema(TypedDict, total=False):
    type: Required[Literal['set']]
    items_schema: CoreSchema
    min_length: int
    max_length: int
    fail_fast: bool
    strict: bool
    ref: str
    metadata: Dict[str, Any]
    serialization: SerSchema


def set_schema(
    items_schema: CoreSchema | None = None,
    *,
    min_length: int | None = None,
    max_length: int | None = None,
    fail_fast: bool | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> SetSchema:
    """
    Returns a schema that matches a set of a given schema, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    schema = core_schema.set_schema(
        items_schema=core_schema.int_schema(), min_length=0, max_length=10
    )
    v = SchemaValidator(schema)
    assert v.validate_python({1, '2', 3}) == {1, 2, 3}
    ```

    Args:
        items_schema: The value must be a set with items that match this schema
        min_length: The value must be a set with at least this many items
        max_length: The value must be a set with at most this many items
        fail_fast: Stop validation on the first error
        strict: The value must be a set with exactly this many items
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='set',
        items_schema=items_schema,
        min_length=min_length,
        max_length=max_length,
        fail_fast=fail_fast,
        strict=strict,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


class FrozenSetSchema(TypedDict, total=False):
    type: Required[Literal['frozenset']]
    items_schema: CoreSchema
    min_length: int
    max_length: int
    fail_fast: bool
    strict: bool
    ref: str
    metadata: Dict[str, Any]
    serialization: SerSchema


def frozenset_schema(
    items_schema: CoreSchema | None = None,
    *,
    min_length: int | None = None,
    max_length: int | None = None,
    fail_fast: bool | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> FrozenSetSchema:
    """
    Returns a schema that matches a frozenset of a given schema, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    schema = core_schema.frozenset_schema(
        items_schema=core_schema.int_schema(), min_length=0, max_length=10
    )
    v = SchemaValidator(schema)
    assert v.validate_python(frozenset(range(3))) == frozenset({0, 1, 2})
    ```

    Args:
        items_schema: The value must be a frozenset with items that match this schema
        min_length: The value must be a frozenset with at least this many items
        max_length: The value must be a frozenset with at most this many items
        fail_fast: Stop validation on the first error
        strict: The value must be a frozenset with exactly this many items
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='frozenset',
        items_schema=items_schema,
        min_length=min_length,
        max_length=max_length,
        fail_fast=fail_fast,
        strict=strict,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


class GeneratorSchema(TypedDict, total=False):
    type: Required[Literal['generator']]
    items_schema: CoreSchema
    min_length: int
    max_length: int
    ref: str
    metadata: Dict[str, Any]
    serialization: IncExSeqOrElseSerSchema


def generator_schema(
    items_schema: CoreSchema | None = None,
    *,
    min_length: int | None = None,
    max_length: int | None = None,
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: IncExSeqOrElseSerSchema | None = None,
) -> GeneratorSchema:
    """
    Returns a schema that matches a generator value, e.g.:

    ```py
    from typing import Iterator
    from pydantic_core import SchemaValidator, core_schema

    def gen() -> Iterator[int]:
        yield 1

    schema = core_schema.generator_schema(items_schema=core_schema.int_schema())
    v = SchemaValidator(schema)
    v.validate_python(gen())
    ```

    Unlike other types, validated generators do not raise ValidationErrors eagerly,
    but instead will raise a ValidationError when a violating value is actually read from the generator.
    This is to ensure that "validated" generators retain the benefit of lazy evaluation.

    Args:
        items_schema: The value must be a generator with items that match this schema
        min_length: The value must be a generator that yields at least this many items
        max_length: The value must be a generator that yields at most this many items
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='generator',
        items_schema=items_schema,
        min_length=min_length,
        max_length=max_length,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


IncExDict = Set[Union[int, str]]


class IncExDictSerSchema(TypedDict, total=False):
    type: Required[Literal['include-exclude-dict']]
    include: IncExDict
    exclude: IncExDict


def filter_dict_schema(*, include: IncExDict | None = None, exclude: IncExDict | None = None) -> IncExDictSerSchema:
    return _dict_not_none(type='include-exclude-dict', include=include, exclude=exclude)


IncExDictOrElseSerSchema = Union[IncExDictSerSchema, SerSchema]


class DictSchema(TypedDict, total=False):
    type: Required[Literal['dict']]
    keys_schema: CoreSchema  # default: AnySchema
    values_schema: CoreSchema  # default: AnySchema
    min_length: int
    max_length: int
    strict: bool
    ref: str
    metadata: Dict[str, Any]
    serialization: IncExDictOrElseSerSchema


def dict_schema(
    keys_schema: CoreSchema | None = None,
    values_schema: CoreSchema | None = None,
    *,
    min_length: int | None = None,
    max_length: int | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> DictSchema:
    """
    Returns a schema that matches a dict value, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    schema = core_schema.dict_schema(
        keys_schema=core_schema.str_schema(), values_schema=core_schema.int_schema()
    )
    v = SchemaValidator(schema)
    assert v.validate_python({'a': '1', 'b': 2}) == {'a': 1, 'b': 2}
    ```

    Args:
        keys_schema: The value must be a dict with keys that match this schema
        values_schema: The value must be a dict with values that match this schema
        min_length: The value must be a dict with at least this many items
        max_length: The value must be a dict with at most this many items
        strict: Whether the keys and values should be validated with strict mode
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='dict',
        keys_schema=keys_schema,
        values_schema=values_schema,
        min_length=min_length,
        max_length=max_length,
        strict=strict,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


# (input_value: Any, /) -> Any
NoInfoValidatorFunction = Callable[[Any], Any]


class NoInfoValidatorFunctionSchema(TypedDict):
    type: Literal['no-info']
    function: NoInfoValidatorFunction


# (input_value: Any, info: ValidationInfo, /) -> Any
WithInfoValidatorFunction = Callable[[Any, ValidationInfo], Any]


class WithInfoValidatorFunctionSchema(TypedDict, total=False):
    type: Required[Literal['with-info']]
    function: Required[WithInfoValidatorFunction]
    field_name: str


ValidationFunction = Union[NoInfoValidatorFunctionSchema, WithInfoValidatorFunctionSchema]


class _ValidatorFunctionSchema(TypedDict, total=False):
    function: Required[ValidationFunction]
    schema: Required[CoreSchema]
    ref: str
    metadata: Dict[str, Any]
    serialization: SerSchema


class BeforeValidatorFunctionSchema(_ValidatorFunctionSchema, total=False):
    type: Required[Literal['function-before']]


def no_info_before_validator_function(
    function: NoInfoValidatorFunction,
    schema: CoreSchema,
    *,
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> BeforeValidatorFunctionSchema:
    """
    Returns a schema that calls a validator function before validating, no `info` argument is provided, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    def fn(v: bytes) -> str:
        return v.decode() + 'world'

    func_schema = core_schema.no_info_before_validator_function(
        function=fn, schema=core_schema.str_schema()
    )
    schema = core_schema.typed_dict_schema({'a': core_schema.typed_dict_field(func_schema)})

    v = SchemaValidator(schema)
    assert v.validate_python({'a': b'hello '}) == {'a': 'hello world'}
    ```

    Args:
        function: The validator function to call
        schema: The schema to validate the output of the validator function
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='function-before',
        function={'type': 'no-info', 'function': function},
        schema=schema,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


def with_info_before_validator_function(
    function: WithInfoValidatorFunction,
    schema: CoreSchema,
    *,
    field_name: str | None = None,
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> BeforeValidatorFunctionSchema:
    """
    Returns a schema that calls a validator function before validation, the function is called with
    an `info` argument, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    def fn(v: bytes, info: core_schema.ValidationInfo) -> str:
        assert info.data is not None
        assert info.field_name is not None
        return v.decode() + 'world'

    func_schema = core_schema.with_info_before_validator_function(
        function=fn, schema=core_schema.str_schema(), field_name='a'
    )
    schema = core_schema.typed_dict_schema({'a': core_schema.typed_dict_field(func_schema)})

    v = SchemaValidator(schema)
    assert v.validate_python({'a': b'hello '}) == {'a': 'hello world'}
    ```

    Args:
        function: The validator function to call
        field_name: The name of the field
        schema: The schema to validate the output of the validator function
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='function-before',
        function=_dict_not_none(type='with-info', function=function, field_name=field_name),
        schema=schema,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


class AfterValidatorFunctionSchema(_ValidatorFunctionSchema, total=False):
    type: Required[Literal['function-after']]


def no_info_after_validator_function(
    function: NoInfoValidatorFunction,
    schema: CoreSchema,
    *,
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> AfterValidatorFunctionSchema:
    """
    Returns a schema that calls a validator function after validating, no `info` argument is provided, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    def fn(v: str) -> str:
        return v + 'world'

    func_schema = core_schema.no_info_after_validator_function(fn, core_schema.str_schema())
    schema = core_schema.typed_dict_schema({'a': core_schema.typed_dict_field(func_schema)})

    v = SchemaValidator(schema)
    assert v.validate_python({'a': b'hello '}) == {'a': 'hello world'}
    ```

    Args:
        function: The validator function to call after the schema is validated
        schema: The schema to validate before the validator function
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='function-after',
        function={'type': 'no-info', 'function': function},
        schema=schema,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


def with_info_after_validator_function(
    function: WithInfoValidatorFunction,
    schema: CoreSchema,
    *,
    field_name: str | None = None,
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> AfterValidatorFunctionSchema:
    """
    Returns a schema that calls a validator function after validation, the function is called with
    an `info` argument, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    def fn(v: str, info: core_schema.ValidationInfo) -> str:
        assert info.data is not None
        assert info.field_name is not None
        return v + 'world'

    func_schema = core_schema.with_info_after_validator_function(
        function=fn, schema=core_schema.str_schema(), field_name='a'
    )
    schema = core_schema.typed_dict_schema({'a': core_schema.typed_dict_field(func_schema)})

    v = SchemaValidator(schema)
    assert v.validate_python({'a': b'hello '}) == {'a': 'hello world'}
    ```

    Args:
        function: The validator function to call after the schema is validated
        schema: The schema to validate before the validator function
        field_name: The name of the field this validators is applied to, if any
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='function-after',
        function=_dict_not_none(type='with-info', function=function, field_name=field_name),
        schema=schema,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


class ValidatorFunctionWrapHandler(Protocol):
    def __call__(self, input_value: Any, outer_location: str | int | None = None, /) -> Any:  # pragma: no cover
        ...


# (input_value: Any, validator: ValidatorFunctionWrapHandler, /) -> Any
NoInfoWrapValidatorFunction = Callable[[Any, ValidatorFunctionWrapHandler], Any]


class NoInfoWrapValidatorFunctionSchema(TypedDict):
    type: Literal['no-info']
    function: NoInfoWrapValidatorFunction


# (input_value: Any, validator: ValidatorFunctionWrapHandler, info: ValidationInfo, /) -> Any
WithInfoWrapValidatorFunction = Callable[[Any, ValidatorFunctionWrapHandler, ValidationInfo], Any]


class WithInfoWrapValidatorFunctionSchema(TypedDict, total=False):
    type: Required[Literal['with-info']]
    function: Required[WithInfoWrapValidatorFunction]
    field_name: str


WrapValidatorFunction = Union[NoInfoWrapValidatorFunctionSchema, WithInfoWrapValidatorFunctionSchema]


class WrapValidatorFunctionSchema(TypedDict, total=False):
    type: Required[Literal['function-wrap']]
    function: Required[WrapValidatorFunction]
    schema: Required[CoreSchema]
    ref: str
    metadata: Dict[str, Any]
    serialization: SerSchema


def no_info_wrap_validator_function(
    function: NoInfoWrapValidatorFunction,
    schema: CoreSchema,
    *,
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> WrapValidatorFunctionSchema:
    """
    Returns a schema which calls a function with a `validator` callable argument which can
    optionally be used to call inner validation with the function logic, this is much like the
    "onion" implementation of middleware in many popular web frameworks, no `info` argument is passed, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    def fn(
        v: str,
        validator: core_schema.ValidatorFunctionWrapHandler,
    ) -> str:
        return validator(input_value=v) + 'world'

    schema = core_schema.no_info_wrap_validator_function(
        function=fn, schema=core_schema.str_schema()
    )
    v = SchemaValidator(schema)
    assert v.validate_python('hello ') == 'hello world'
    ```

    Args:
        function: The validator function to call
        schema: The schema to validate the output of the validator function
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='function-wrap',
        function={'type': 'no-info', 'function': function},
        schema=schema,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


def with_info_wrap_validator_function(
    function: WithInfoWrapValidatorFunction,
    schema: CoreSchema,
    *,
    field_name: str | None = None,
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> WrapValidatorFunctionSchema:
    """
    Returns a schema which calls a function with a `validator` callable argument which can
    optionally be used to call inner validation with the function logic, this is much like the
    "onion" implementation of middleware in many popular web frameworks, an `info` argument is also passed, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    def fn(
        v: str,
        validator: core_schema.ValidatorFunctionWrapHandler,
        info: core_schema.ValidationInfo,
    ) -> str:
        return validator(input_value=v) + 'world'

    schema = core_schema.with_info_wrap_validator_function(
        function=fn, schema=core_schema.str_schema()
    )
    v = SchemaValidator(schema)
    assert v.validate_python('hello ') == 'hello world'
    ```

    Args:
        function: The validator function to call
        schema: The schema to validate the output of the validator function
        field_name: The name of the field this validators is applied to, if any
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='function-wrap',
        function=_dict_not_none(type='with-info', function=function, field_name=field_name),
        schema=schema,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


class PlainValidatorFunctionSchema(TypedDict, total=False):
    type: Required[Literal['function-plain']]
    function: Required[ValidationFunction]
    ref: str
    metadata: Dict[str, Any]
    serialization: SerSchema


def no_info_plain_validator_function(
    function: NoInfoValidatorFunction,
    *,
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> PlainValidatorFunctionSchema:
    """
    Returns a schema that uses the provided function for validation, no `info` argument is passed, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    def fn(v: str) -> str:
        assert 'hello' in v
        return v + 'world'

    schema = core_schema.no_info_plain_validator_function(function=fn)
    v = SchemaValidator(schema)
    assert v.validate_python('hello ') == 'hello world'
    ```

    Args:
        function: The validator function to call
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='function-plain',
        function={'type': 'no-info', 'function': function},
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


def with_info_plain_validator_function(
    function: WithInfoValidatorFunction,
    *,
    field_name: str | None = None,
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> PlainValidatorFunctionSchema:
    """
    Returns a schema that uses the provided function for validation, an `info` argument is passed, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    def fn(v: str, info: core_schema.ValidationInfo) -> str:
        assert 'hello' in v
        return v + 'world'

    schema = core_schema.with_info_plain_validator_function(function=fn)
    v = SchemaValidator(schema)
    assert v.validate_python('hello ') == 'hello world'
    ```

    Args:
        function: The validator function to call
        field_name: The name of the field this validators is applied to, if any
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='function-plain',
        function=_dict_not_none(type='with-info', function=function, field_name=field_name),
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


class WithDefaultSchema(TypedDict, total=False):
    type: Required[Literal['default']]
    schema: Required[CoreSchema]
    default: Any
    default_factory: Union[Callable[[], Any], Callable[[Dict[str, Any]], Any]]
    default_factory_takes_data: bool
    on_error: Literal['raise', 'omit', 'default']  # default: 'raise'
    validate_default: bool  # default: False
    strict: bool
    ref: str
    metadata: Dict[str, Any]
    serialization: SerSchema


def with_default_schema(
    schema: CoreSchema,
    *,
    default: Any = PydanticUndefined,
    default_factory: Union[Callable[[], Any], Callable[[Dict[str, Any]], Any], None] = None,
    default_factory_takes_data: bool | None = None,
    on_error: Literal['raise', 'omit', 'default'] | None = None,
    validate_default: bool | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> WithDefaultSchema:
    """
    Returns a schema that adds a default value to the given schema, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    schema = core_schema.with_default_schema(core_schema.str_schema(), default='hello')
    wrapper_schema = core_schema.typed_dict_schema(
        {'a': core_schema.typed_dict_field(schema)}
    )
    v = SchemaValidator(wrapper_schema)
    assert v.validate_python({}) == v.validate_python({'a': 'hello'})
    ```

    Args:
        schema: The schema to add a default value to
        default: The default value to use
        default_factory: A callable that returns the default value to use
        default_factory_takes_data: Whether the default factory takes a validated data argument
        on_error: What to do if the schema validation fails. One of 'raise', 'omit', 'default'
        validate_default: Whether the default value should be validated
        strict: Whether the underlying schema should be validated with strict mode
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    s = _dict_not_none(
        type='default',
        schema=schema,
        default_factory=default_factory,
        default_factory_takes_data=default_factory_takes_data,
        on_error=on_error,
        validate_default=validate_default,
        strict=strict,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )
    if default is not PydanticUndefined:
        s['default'] = default
    return s


class NullableSchema(TypedDict, total=False):
    type: Required[Literal['nullable']]
    schema: Required[CoreSchema]
    strict: bool
    ref: str
    metadata: Dict[str, Any]
    serialization: SerSchema


def nullable_schema(
    schema: CoreSchema,
    *,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> NullableSchema:
    """
    Returns a schema that matches a nullable value, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    schema = core_schema.nullable_schema(core_schema.str_schema())
    v = SchemaValidator(schema)
    assert v.validate_python(None) is None
    ```

    Args:
        schema: The schema to wrap
        strict: Whether the underlying schema should be validated with strict mode
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='nullable', schema=schema, strict=strict, ref=ref, metadata=metadata, serialization=serialization
    )


class UnionSchema(TypedDict, total=False):
    type: Required[Literal['union']]
    choices: Required[List[Union[CoreSchema, Tuple[CoreSchema, str]]]]
    # default true, whether to automatically collapse unions with one element to the inner validator
    auto_collapse: bool
    custom_error_type: str
    custom_error_message: str
    custom_error_context: Dict[str, Union[str, int, float]]
    mode: Literal['smart', 'left_to_right']  # default: 'smart'
    strict: bool
    ref: str
    metadata: Dict[str, Any]
    serialization: SerSchema


def union_schema(
    choices: list[CoreSchema | tuple[CoreSchema, str]],
    *,
    auto_collapse: bool | None = None,
    custom_error_type: str | None = None,
    custom_error_message: str | None = None,
    custom_error_context: dict[str, str | int] | None = None,
    mode: Literal['smart', 'left_to_right'] | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> UnionSchema:
    """
    Returns a schema that matches a union value, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    schema = core_schema.union_schema([core_schema.str_schema(), core_schema.int_schema()])
    v = SchemaValidator(schema)
    assert v.validate_python('hello') == 'hello'
    assert v.validate_python(1) == 1
    ```

    Args:
        choices: The schemas to match. If a tuple, the second item is used as the label for the case.
        auto_collapse: whether to automatically collapse unions with one element to the inner validator, default true
        custom_error_type: The custom error type to use if the validation fails
        custom_error_message: The custom error message to use if the validation fails
        custom_error_context: The custom error context to use if the validation fails
        mode: How to select which choice to return
            * `smart` (default) will try to return the choice which is the closest match to the input value
            * `left_to_right` will return the first choice in `choices` which succeeds validation
        strict: Whether the underlying schemas should be validated with strict mode
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='union',
        choices=choices,
        auto_collapse=auto_collapse,
        custom_error_type=custom_error_type,
        custom_error_message=custom_error_message,
        custom_error_context=custom_error_context,
        mode=mode,
        strict=strict,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


class TaggedUnionSchema(TypedDict, total=False):
    type: Required[Literal['tagged-union']]
    choices: Required[Dict[Hashable, CoreSchema]]
    discriminator: Required[Union[str, List[Union[str, int]], List[List[Union[str, int]]], Callable[[Any], Hashable]]]
    custom_error_type: str
    custom_error_message: str
    custom_error_context: Dict[str, Union[str, int, float]]
    strict: bool
    from_attributes: bool  # default: True
    ref: str
    metadata: Dict[str, Any]
    serialization: SerSchema


def tagged_union_schema(
    choices: Dict[Any, CoreSchema],
    discriminator: str | list[str | int] | list[list[str | int]] | Callable[[Any], Any],
    *,
    custom_error_type: str | None = None,
    custom_error_message: str | None = None,
    custom_error_context: dict[str, int | str | float] | None = None,
    strict: bool | None = None,
    from_attributes: bool | None = None,
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> TaggedUnionSchema:
    """
    Returns a schema that matches a tagged union value, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    apple_schema = core_schema.typed_dict_schema(
        {
            'foo': core_schema.typed_dict_field(core_schema.str_schema()),
            'bar': core_schema.typed_dict_field(core_schema.int_schema()),
        }
    )
    banana_schema = core_schema.typed_dict_schema(
        {
            'foo': core_schema.typed_dict_field(core_schema.str_schema()),
            'spam': core_schema.typed_dict_field(
                core_schema.list_schema(items_schema=core_schema.int_schema())
            ),
        }
    )
    schema = core_schema.tagged_union_schema(
        choices={
            'apple': apple_schema,
            'banana': banana_schema,
        },
        discriminator='foo',
    )
    v = SchemaValidator(schema)
    assert v.validate_python({'foo': 'apple', 'bar': '123'}) == {'foo': 'apple', 'bar': 123}
    assert v.validate_python({'foo': 'banana', 'spam': [1, 2, 3]}) == {
        'foo': 'banana',
        'spam': [1, 2, 3],
    }
    ```

    Args:
        choices: The schemas to match
            When retrieving a schema from `choices` using the discriminator value, if the value is a str,
            it should be fed back into the `choices` map until a schema is obtained
            (This approach is to prevent multiple ownership of a single schema in Rust)
        discriminator: The discriminator to use to determine the schema to use
            * If `discriminator` is a str, it is the name of the attribute to use as the discriminator
            * If `discriminator` is a list of int/str, it should be used as a "path" to access the discriminator
            * If `discriminator` is a list of lists, each inner list is a path, and the first path that exists is used
            * If `discriminator` is a callable, it should return the discriminator when called on the value to validate;
              the callable can return `None` to indicate that there is no matching discriminator present on the input
        custom_error_type: The custom error type to use if the validation fails
        custom_error_message: The custom error message to use if the validation fails
        custom_error_context: The custom error context to use if the validation fails
        strict: Whether the underlying schemas should be validated with strict mode
        from_attributes: Whether to use the attributes of the object to retrieve the discriminator value
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='tagged-union',
        choices=choices,
        discriminator=discriminator,
        custom_error_type=custom_error_type,
        custom_error_message=custom_error_message,
        custom_error_context=custom_error_context,
        strict=strict,
        from_attributes=from_attributes,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


class ChainSchema(TypedDict, total=False):
    type: Required[Literal['chain']]
    steps: Required[List[CoreSchema]]
    ref: str
    metadata: Dict[str, Any]
    serialization: SerSchema


def chain_schema(
    steps: list[CoreSchema],
    *,
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> ChainSchema:
    """
    Returns a schema that chains the provided validation schemas, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    def fn(v: str, info: core_schema.ValidationInfo) -> str:
        assert 'hello' in v
        return v + ' world'

    fn_schema = core_schema.with_info_plain_validator_function(function=fn)
    schema = core_schema.chain_schema(
        [fn_schema, fn_schema, fn_schema, core_schema.str_schema()]
    )
    v = SchemaValidator(schema)
    assert v.validate_python('hello') == 'hello world world world'
    ```

    Args:
        steps: The schemas to chain
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(type='chain', steps=steps, ref=ref, metadata=metadata, serialization=serialization)


class LaxOrStrictSchema(TypedDict, total=False):
    type: Required[Literal['lax-or-strict']]
    lax_schema: Required[CoreSchema]
    strict_schema: Required[CoreSchema]
    strict: bool
    ref: str
    metadata: Dict[str, Any]
    serialization: SerSchema


def lax_or_strict_schema(
    lax_schema: CoreSchema,
    strict_schema: CoreSchema,
    *,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> LaxOrStrictSchema:
    """
    Returns a schema that uses the lax or strict schema, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    def fn(v: str, info: core_schema.ValidationInfo) -> str:
        assert 'hello' in v
        return v + ' world'

    lax_schema = core_schema.int_schema(strict=False)
    strict_schema = core_schema.int_schema(strict=True)

    schema = core_schema.lax_or_strict_schema(
        lax_schema=lax_schema, strict_schema=strict_schema, strict=True
    )
    v = SchemaValidator(schema)
    assert v.validate_python(123) == 123

    schema = core_schema.lax_or_strict_schema(
        lax_schema=lax_schema, strict_schema=strict_schema, strict=False
    )
    v = SchemaValidator(schema)
    assert v.validate_python('123') == 123
    ```

    Args:
        lax_schema: The lax schema to use
        strict_schema: The strict schema to use
        strict: Whether the strict schema should be used
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='lax-or-strict',
        lax_schema=lax_schema,
        strict_schema=strict_schema,
        strict=strict,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


class JsonOrPythonSchema(TypedDict, total=False):
    type: Required[Literal['json-or-python']]
    json_schema: Required[CoreSchema]
    python_schema: Required[CoreSchema]
    ref: str
    metadata: Dict[str, Any]
    serialization: SerSchema


def json_or_python_schema(
    json_schema: CoreSchema,
    python_schema: CoreSchema,
    *,
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> JsonOrPythonSchema:
    """
    Returns a schema that uses the Json or Python schema depending on the input:

    ```py
    from pydantic_core import SchemaValidator, ValidationError, core_schema

    v = SchemaValidator(
        core_schema.json_or_python_schema(
            json_schema=core_schema.int_schema(),
            python_schema=core_schema.int_schema(strict=True),
        )
    )

    assert v.validate_json('"123"') == 123

    try:
        v.validate_python('123')
    except ValidationError:
        pass
    else:
        raise AssertionError('Validation should have failed')
    ```

    Args:
        json_schema: The schema to use for Json inputs
        python_schema: The schema to use for Python inputs
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='json-or-python',
        json_schema=json_schema,
        python_schema=python_schema,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


class TypedDictField(TypedDict, total=False):
    type: Required[Literal['typed-dict-field']]
    schema: Required[CoreSchema]
    required: bool
    validation_alias: Union[str, List[Union[str, int]], List[List[Union[str, int]]]]
    serialization_alias: str
    serialization_exclude: bool  # default: False
    metadata: Dict[str, Any]


def typed_dict_field(
    schema: CoreSchema,
    *,
    required: bool | None = None,
    validation_alias: str | list[str | int] | list[list[str | int]] | None = None,
    serialization_alias: str | None = None,
    serialization_exclude: bool | None = None,
    metadata: Dict[str, Any] | None = None,
) -> TypedDictField:
    """
    Returns a schema that matches a typed dict field, e.g.:

    ```py
    from pydantic_core import core_schema

    field = core_schema.typed_dict_field(schema=core_schema.int_schema(), required=True)
    ```

    Args:
        schema: The schema to use for the field
        required: Whether the field is required, otherwise uses the value from `total` on the typed dict
        validation_alias: The alias(es) to use to find the field in the validation data
        serialization_alias: The alias to use as a key when serializing
        serialization_exclude: Whether to exclude the field when serializing
        metadata: Any other information you want to include with the schema, not used by pydantic-core
    """
    return _dict_not_none(
        type='typed-dict-field',
        schema=schema,
        required=required,
        validation_alias=validation_alias,
        serialization_alias=serialization_alias,
        serialization_exclude=serialization_exclude,
        metadata=metadata,
    )


class TypedDictSchema(TypedDict, total=False):
    type: Required[Literal['typed-dict']]
    fields: Required[Dict[str, TypedDictField]]
    cls: Type[Any]
    computed_fields: List[ComputedField]
    strict: bool
    extras_schema: CoreSchema
    # all these values can be set via config, equivalent fields have `typed_dict_` prefix
    extra_behavior: ExtraBehavior
    total: bool  # default: True
    populate_by_name: bool  # replaces `allow_population_by_field_name` in pydantic v1
    ref: str
    metadata: Dict[str, Any]
    serialization: SerSchema
    config: CoreConfig


def typed_dict_schema(
    fields: Dict[str, TypedDictField],
    *,
    cls: Type[Any] | None = None,
    computed_fields: list[ComputedField] | None = None,
    strict: bool | None = None,
    extras_schema: CoreSchema | None = None,
    extra_behavior: ExtraBehavior | None = None,
    total: bool | None = None,
    populate_by_name: bool | None = None,
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
    config: CoreConfig | None = None,
) -> TypedDictSchema:
    """
    Returns a schema that matches a typed dict, e.g.:

    ```py
    from typing_extensions import TypedDict

    from pydantic_core import SchemaValidator, core_schema

    class MyTypedDict(TypedDict):
        a: str

    wrapper_schema = core_schema.typed_dict_schema(
        {'a': core_schema.typed_dict_field(core_schema.str_schema())}, cls=MyTypedDict
    )
    v = SchemaValidator(wrapper_schema)
    assert v.validate_python({'a': 'hello'}) == {'a': 'hello'}
    ```

    Args:
        fields: The fields to use for the typed dict
        cls: The class to use for the typed dict
        computed_fields: Computed fields to use when serializing the model, only applies when directly inside a model
        strict: Whether the typed dict is strict
        extras_schema: The extra validator to use for the typed dict
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        extra_behavior: The extra behavior to use for the typed dict
        total: Whether the typed dict is total, otherwise uses `typed_dict_total` from config
        populate_by_name: Whether the typed dict should populate by name
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='typed-dict',
        fields=fields,
        cls=cls,
        computed_fields=computed_fields,
        strict=strict,
        extras_schema=extras_schema,
        extra_behavior=extra_behavior,
        total=total,
        populate_by_name=populate_by_name,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
        config=config,
    )


class ModelField(TypedDict, total=False):
    type: Required[Literal['model-field']]
    schema: Required[CoreSchema]
    validation_alias: Union[str, List[Union[str, int]], List[List[Union[str, int]]]]
    serialization_alias: str
    serialization_exclude: bool  # default: False
    frozen: bool
    metadata: Dict[str, Any]


def model_field(
    schema: CoreSchema,
    *,
    validation_alias: str | list[str | int] | list[list[str | int]] | None = None,
    serialization_alias: str | None = None,
    serialization_exclude: bool | None = None,
    frozen: bool | None = None,
    metadata: Dict[str, Any] | None = None,
) -> ModelField:
    """
    Returns a schema for a model field, e.g.:

    ```py
    from pydantic_core import core_schema

    field = core_schema.model_field(schema=core_schema.int_schema())
    ```

    Args:
        schema: The schema to use for the field
        validation_alias: The alias(es) to use to find the field in the validation data
        serialization_alias: The alias to use as a key when serializing
        serialization_exclude: Whether to exclude the field when serializing
        frozen: Whether the field is frozen
        metadata: Any other information you want to include with the schema, not used by pydantic-core
    """
    return _dict_not_none(
        type='model-field',
        schema=schema,
        validation_alias=validation_alias,
        serialization_alias=serialization_alias,
        serialization_exclude=serialization_exclude,
        frozen=frozen,
        metadata=metadata,
    )


class ModelFieldsSchema(TypedDict, total=False):
    type: Required[Literal['model-fields']]
    fields: Required[Dict[str, ModelField]]
    model_name: str
    computed_fields: List[ComputedField]
    strict: bool
    extras_schema: CoreSchema
    # all these values can be set via config, equivalent fields have `typed_dict_` prefix
    extra_behavior: ExtraBehavior
    populate_by_name: bool  # replaces `allow_population_by_field_name` in pydantic v1
    from_attributes: bool
    ref: str
    metadata: Dict[str, Any]
    serialization: SerSchema


def model_fields_schema(
    fields: Dict[str, ModelField],
    *,
    model_name: str | None = None,
    computed_fields: list[ComputedField] | None = None,
    strict: bool | None = None,
    extras_schema: CoreSchema | None = None,
    extra_behavior: ExtraBehavior | None = None,
    populate_by_name: bool | None = None,
    from_attributes: bool | None = None,
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> ModelFieldsSchema:
    """
    Returns a schema that matches a typed dict, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    wrapper_schema = core_schema.model_fields_schema(
        {'a': core_schema.model_field(core_schema.str_schema())}
    )
    v = SchemaValidator(wrapper_schema)
    print(v.validate_python({'a': 'hello'}))
    #> ({'a': 'hello'}, None, {'a'})
    ```

    Args:
        fields: The fields to use for the typed dict
        model_name: The name of the model, used for error messages, defaults to "Model"
        computed_fields: Computed fields to use when serializing the model, only applies when directly inside a model
        strict: Whether the typed dict is strict
        extras_schema: The extra validator to use for the typed dict
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        extra_behavior: The extra behavior to use for the typed dict
        populate_by_name: Whether the typed dict should populate by name
        from_attributes: Whether the typed dict should be populated from attributes
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='model-fields',
        fields=fields,
        model_name=model_name,
        computed_fields=computed_fields,
        strict=strict,
        extras_schema=extras_schema,
        extra_behavior=extra_behavior,
        populate_by_name=populate_by_name,
        from_attributes=from_attributes,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


class ModelSchema(TypedDict, total=False):
    type: Required[Literal['model']]
    cls: Required[Type[Any]]
    generic_origin: Type[Any]
    schema: Required[CoreSchema]
    custom_init: bool
    root_model: bool
    post_init: str
    revalidate_instances: Literal['always', 'never', 'subclass-instances']  # default: 'never'
    strict: bool
    frozen: bool
    extra_behavior: ExtraBehavior
    config: CoreConfig
    ref: str
    metadata: Dict[str, Any]
    serialization: SerSchema


def model_schema(
    cls: Type[Any],
    schema: CoreSchema,
    *,
    generic_origin: Type[Any] | None = None,
    custom_init: bool | None = None,
    root_model: bool | None = None,
    post_init: str | None = None,
    revalidate_instances: Literal['always', 'never', 'subclass-instances'] | None = None,
    strict: bool | None = None,
    frozen: bool | None = None,
    extra_behavior: ExtraBehavior | None = None,
    config: CoreConfig | None = None,
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> ModelSchema:
    """
    A model schema generally contains a typed-dict schema.
    It will run the typed dict validator, then create a new class
    and set the dict and fields set returned from the typed dict validator
    to `__dict__` and `__pydantic_fields_set__` respectively.

    Example:

    ```py
    from pydantic_core import CoreConfig, SchemaValidator, core_schema

    class MyModel:
        __slots__ = (
            '__dict__',
            '__pydantic_fields_set__',
            '__pydantic_extra__',
            '__pydantic_private__',
        )

    schema = core_schema.model_schema(
        cls=MyModel,
        config=CoreConfig(str_max_length=5),
        schema=core_schema.model_fields_schema(
            fields={'a': core_schema.model_field(core_schema.str_schema())},
        ),
    )
    v = SchemaValidator(schema)
    assert v.isinstance_python({'a': 'hello'}) is True
    assert v.isinstance_python({'a': 'too long'}) is False
    ```

    Args:
        cls: The class to use for the model
        schema: The schema to use for the model
        generic_origin: The origin type used for this model, if it's a parametrized generic. Ex,
            if this model schema represents `SomeModel[int]`, generic_origin is `SomeModel`
        custom_init: Whether the model has a custom init method
        root_model: Whether the model is a `RootModel`
        post_init: The call after init to use for the model
        revalidate_instances: whether instances of models and dataclasses (including subclass instances)
            should re-validate defaults to config.revalidate_instances, else 'never'
        strict: Whether the model is strict
        frozen: Whether the model is frozen
        extra_behavior: The extra behavior to use for the model, used in serialization
        config: The config to use for the model
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='model',
        cls=cls,
        generic_origin=generic_origin,
        schema=schema,
        custom_init=custom_init,
        root_model=root_model,
        post_init=post_init,
        revalidate_instances=revalidate_instances,
        strict=strict,
        frozen=frozen,
        extra_behavior=extra_behavior,
        config=config,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


class DataclassField(TypedDict, total=False):
    type: Required[Literal['dataclass-field']]
    name: Required[str]
    schema: Required[CoreSchema]
    kw_only: bool  # default: True
    init: bool  # default: True
    init_only: bool  # default: False
    frozen: bool  # default: False
    validation_alias: Union[str, List[Union[str, int]], List[List[Union[str, int]]]]
    serialization_alias: str
    serialization_exclude: bool  # default: False
    metadata: Dict[str, Any]


def dataclass_field(
    name: str,
    schema: CoreSchema,
    *,
    kw_only: bool | None = None,
    init: bool | None = None,
    init_only: bool | None = None,
    validation_alias: str | list[str | int] | list[list[str | int]] | None = None,
    serialization_alias: str | None = None,
    serialization_exclude: bool | None = None,
    metadata: Dict[str, Any] | None = None,
    frozen: bool | None = None,
) -> DataclassField:
    """
    Returns a schema for a dataclass field, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    field = core_schema.dataclass_field(
        name='a', schema=core_schema.str_schema(), kw_only=False
    )
    schema = core_schema.dataclass_args_schema('Foobar', [field])
    v = SchemaValidator(schema)
    assert v.validate_python({'a': 'hello'}) == ({'a': 'hello'}, None)
    ```

    Args:
        name: The name to use for the argument parameter
        schema: The schema to use for the argument parameter
        kw_only: Whether the field can be set with a positional argument as well as a keyword argument
        init: Whether the field should be validated during initialization
        init_only: Whether the field should be omitted  from `__dict__` and passed to `__post_init__`
        validation_alias: The alias(es) to use to find the field in the validation data
        serialization_alias: The alias to use as a key when serializing
        serialization_exclude: Whether to exclude the field when serializing
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        frozen: Whether the field is frozen
    """
    return _dict_not_none(
        type='dataclass-field',
        name=name,
        schema=schema,
        kw_only=kw_only,
        init=init,
        init_only=init_only,
        validation_alias=validation_alias,
        serialization_alias=serialization_alias,
        serialization_exclude=serialization_exclude,
        metadata=metadata,
        frozen=frozen,
    )


class DataclassArgsSchema(TypedDict, total=False):
    type: Required[Literal['dataclass-args']]
    dataclass_name: Required[str]
    fields: Required[List[DataclassField]]
    computed_fields: List[ComputedField]
    populate_by_name: bool  # default: False
    collect_init_only: bool  # default: False
    ref: str
    metadata: Dict[str, Any]
    serialization: SerSchema
    extra_behavior: ExtraBehavior


def dataclass_args_schema(
    dataclass_name: str,
    fields: list[DataclassField],
    *,
    computed_fields: List[ComputedField] | None = None,
    populate_by_name: bool | None = None,
    collect_init_only: bool | None = None,
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
    extra_behavior: ExtraBehavior | None = None,
) -> DataclassArgsSchema:
    """
    Returns a schema for validating dataclass arguments, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    field_a = core_schema.dataclass_field(
        name='a', schema=core_schema.str_schema(), kw_only=False
    )
    field_b = core_schema.dataclass_field(
        name='b', schema=core_schema.bool_schema(), kw_only=False
    )
    schema = core_schema.dataclass_args_schema('Foobar', [field_a, field_b])
    v = SchemaValidator(schema)
    assert v.validate_python({'a': 'hello', 'b': True}) == ({'a': 'hello', 'b': True}, None)
    ```

    Args:
        dataclass_name: The name of the dataclass being validated
        fields: The fields to use for the dataclass
        computed_fields: Computed fields to use when serializing the dataclass
        populate_by_name: Whether to populate by name
        collect_init_only: Whether to collect init only fields into a dict to pass to `__post_init__`
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
        extra_behavior: How to handle extra fields
    """
    return _dict_not_none(
        type='dataclass-args',
        dataclass_name=dataclass_name,
        fields=fields,
        computed_fields=computed_fields,
        populate_by_name=populate_by_name,
        collect_init_only=collect_init_only,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
        extra_behavior=extra_behavior,
    )


class DataclassSchema(TypedDict, total=False):
    type: Required[Literal['dataclass']]
    cls: Required[Type[Any]]
    generic_origin: Type[Any]
    schema: Required[CoreSchema]
    fields: Required[List[str]]
    cls_name: str
    post_init: bool  # default: False
    revalidate_instances: Literal['always', 'never', 'subclass-instances']  # default: 'never'
    strict: bool  # default: False
    frozen: bool  # default False
    ref: str
    metadata: Dict[str, Any]
    serialization: SerSchema
    slots: bool
    config: CoreConfig


def dataclass_schema(
    cls: Type[Any],
    schema: CoreSchema,
    fields: List[str],
    *,
    generic_origin: Type[Any] | None = None,
    cls_name: str | None = None,
    post_init: bool | None = None,
    revalidate_instances: Literal['always', 'never', 'subclass-instances'] | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
    frozen: bool | None = None,
    slots: bool | None = None,
    config: CoreConfig | None = None,
) -> DataclassSchema:
    """
    Returns a schema for a dataclass. As with `ModelSchema`, this schema can only be used as a field within
    another schema, not as the root type.

    Args:
        cls: The dataclass type, used to perform subclass checks
        schema: The schema to use for the dataclass fields
        fields: Fields of the dataclass, this is used in serialization and in validation during re-validation
            and while validating assignment
        generic_origin: The origin type used for this dataclass, if it's a parametrized generic. Ex,
            if this model schema represents `SomeDataclass[int]`, generic_origin is `SomeDataclass`
        cls_name: The name to use in error locs, etc; this is useful for generics (default: `cls.__name__`)
        post_init: Whether to call `__post_init__` after validation
        revalidate_instances: whether instances of models and dataclasses (including subclass instances)
            should re-validate defaults to config.revalidate_instances, else 'never'
        strict: Whether to require an exact instance of `cls`
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
        frozen: Whether the dataclass is frozen
        slots: Whether `slots=True` on the dataclass, means each field is assigned independently, rather than
            simply setting `__dict__`, default false
    """
    return _dict_not_none(
        type='dataclass',
        cls=cls,
        generic_origin=generic_origin,
        fields=fields,
        cls_name=cls_name,
        schema=schema,
        post_init=post_init,
        revalidate_instances=revalidate_instances,
        strict=strict,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
        frozen=frozen,
        slots=slots,
        config=config,
    )


class ArgumentsParameter(TypedDict, total=False):
    name: Required[str]
    schema: Required[CoreSchema]
    mode: Literal['positional_only', 'positional_or_keyword', 'keyword_only']  # default positional_or_keyword
    alias: Union[str, List[Union[str, int]], List[List[Union[str, int]]]]


def arguments_parameter(
    name: str,
    schema: CoreSchema,
    *,
    mode: Literal['positional_only', 'positional_or_keyword', 'keyword_only'] | None = None,
    alias: str | list[str | int] | list[list[str | int]] | None = None,
) -> ArgumentsParameter:
    """
    Returns a schema that matches an argument parameter, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    param = core_schema.arguments_parameter(
        name='a', schema=core_schema.str_schema(), mode='positional_only'
    )
    schema = core_schema.arguments_schema([param])
    v = SchemaValidator(schema)
    assert v.validate_python(('hello',)) == (('hello',), {})
    ```

    Args:
        name: The name to use for the argument parameter
        schema: The schema to use for the argument parameter
        mode: The mode to use for the argument parameter
        alias: The alias to use for the argument parameter
    """
    return _dict_not_none(name=name, schema=schema, mode=mode, alias=alias)


VarKwargsMode: TypeAlias = Literal['uniform', 'unpacked-typed-dict']


class ArgumentsSchema(TypedDict, total=False):
    type: Required[Literal['arguments']]
    arguments_schema: Required[List[ArgumentsParameter]]
    populate_by_name: bool
    var_args_schema: CoreSchema
    var_kwargs_mode: VarKwargsMode
    var_kwargs_schema: CoreSchema
    ref: str
    metadata: Dict[str, Any]
    serialization: SerSchema


def arguments_schema(
    arguments: list[ArgumentsParameter],
    *,
    populate_by_name: bool | None = None,
    var_args_schema: CoreSchema | None = None,
    var_kwargs_mode: VarKwargsMode | None = None,
    var_kwargs_schema: CoreSchema | None = None,
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> ArgumentsSchema:
    """
    Returns a schema that matches an arguments schema, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    param_a = core_schema.arguments_parameter(
        name='a', schema=core_schema.str_schema(), mode='positional_only'
    )
    param_b = core_schema.arguments_parameter(
        name='b', schema=core_schema.bool_schema(), mode='positional_only'
    )
    schema = core_schema.arguments_schema([param_a, param_b])
    v = SchemaValidator(schema)
    assert v.validate_python(('hello', True)) == (('hello', True), {})
    ```

    Args:
        arguments: The arguments to use for the arguments schema
        populate_by_name: Whether to populate by name
        var_args_schema: The variable args schema to use for the arguments schema
        var_kwargs_mode: The validation mode to use for variadic keyword arguments. If `'uniform'`, every value of the
            keyword arguments will be validated against the `var_kwargs_schema` schema. If `'unpacked-typed-dict'`,
            the `var_kwargs_schema` argument must be a [`typed_dict_schema`][pydantic_core.core_schema.typed_dict_schema]
        var_kwargs_schema: The variable kwargs schema to use for the arguments schema
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='arguments',
        arguments_schema=arguments,
        populate_by_name=populate_by_name,
        var_args_schema=var_args_schema,
        var_kwargs_mode=var_kwargs_mode,
        var_kwargs_schema=var_kwargs_schema,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


class CallSchema(TypedDict, total=False):
    type: Required[Literal['call']]
    arguments_schema: Required[CoreSchema]
    function: Required[Callable[..., Any]]
    function_name: str  # default function.__name__
    return_schema: CoreSchema
    ref: str
    metadata: Dict[str, Any]
    serialization: SerSchema


def call_schema(
    arguments: CoreSchema,
    function: Callable[..., Any],
    *,
    function_name: str | None = None,
    return_schema: CoreSchema | None = None,
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> CallSchema:
    """
    Returns a schema that matches an arguments schema, then calls a function, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    param_a = core_schema.arguments_parameter(
        name='a', schema=core_schema.str_schema(), mode='positional_only'
    )
    param_b = core_schema.arguments_parameter(
        name='b', schema=core_schema.bool_schema(), mode='positional_only'
    )
    args_schema = core_schema.arguments_schema([param_a, param_b])

    schema = core_schema.call_schema(
        arguments=args_schema,
        function=lambda a, b: a + str(not b),
        return_schema=core_schema.str_schema(),
    )
    v = SchemaValidator(schema)
    assert v.validate_python((('hello', True))) == 'helloFalse'
    ```

    Args:
        arguments: The arguments to use for the arguments schema
        function: The function to use for the call schema
        function_name: The function name to use for the call schema, if not provided `function.__name__` is used
        return_schema: The return schema to use for the call schema
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='call',
        arguments_schema=arguments,
        function=function,
        function_name=function_name,
        return_schema=return_schema,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


class CustomErrorSchema(TypedDict, total=False):
    type: Required[Literal['custom-error']]
    schema: Required[CoreSchema]
    custom_error_type: Required[str]
    custom_error_message: str
    custom_error_context: Dict[str, Union[str, int, float]]
    ref: str
    metadata: Dict[str, Any]
    serialization: SerSchema


def custom_error_schema(
    schema: CoreSchema,
    custom_error_type: str,
    *,
    custom_error_message: str | None = None,
    custom_error_context: dict[str, Any] | None = None,
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> CustomErrorSchema:
    """
    Returns a schema that matches a custom error value, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    schema = core_schema.custom_error_schema(
        schema=core_schema.int_schema(),
        custom_error_type='MyError',
        custom_error_message='Error msg',
    )
    v = SchemaValidator(schema)
    v.validate_python(1)
    ```

    Args:
        schema: The schema to use for the custom error schema
        custom_error_type: The custom error type to use for the custom error schema
        custom_error_message: The custom error message to use for the custom error schema
        custom_error_context: The custom error context to use for the custom error schema
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='custom-error',
        schema=schema,
        custom_error_type=custom_error_type,
        custom_error_message=custom_error_message,
        custom_error_context=custom_error_context,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


class JsonSchema(TypedDict, total=False):
    type: Required[Literal['json']]
    schema: CoreSchema
    ref: str
    metadata: Dict[str, Any]
    serialization: SerSchema


def json_schema(
    schema: CoreSchema | None = None,
    *,
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> JsonSchema:
    """
    Returns a schema that matches a JSON value, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    dict_schema = core_schema.model_fields_schema(
        {
            'field_a': core_schema.model_field(core_schema.str_schema()),
            'field_b': core_schema.model_field(core_schema.bool_schema()),
        },
    )

    class MyModel:
        __slots__ = (
            '__dict__',
            '__pydantic_fields_set__',
            '__pydantic_extra__',
            '__pydantic_private__',
        )
        field_a: str
        field_b: bool

    json_schema = core_schema.json_schema(schema=dict_schema)
    schema = core_schema.model_schema(cls=MyModel, schema=json_schema)
    v = SchemaValidator(schema)
    m = v.validate_python('{"field_a": "hello", "field_b": true}')
    assert isinstance(m, MyModel)
    ```

    Args:
        schema: The schema to use for the JSON schema
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(type='json', schema=schema, ref=ref, metadata=metadata, serialization=serialization)


class UrlSchema(TypedDict, total=False):
    type: Required[Literal['url']]
    max_length: int
    allowed_schemes: List[str]
    host_required: bool  # default False
    default_host: str
    default_port: int
    default_path: str
    strict: bool
    ref: str
    metadata: Dict[str, Any]
    serialization: SerSchema


def url_schema(
    *,
    max_length: int | None = None,
    allowed_schemes: list[str] | None = None,
    host_required: bool | None = None,
    default_host: str | None = None,
    default_port: int | None = None,
    default_path: str | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> UrlSchema:
    """
    Returns a schema that matches a URL value, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    schema = core_schema.url_schema()
    v = SchemaValidator(schema)
    print(v.validate_python('https://example.com'))
    #> https://example.com/
    ```

    Args:
        max_length: The maximum length of the URL
        allowed_schemes: The allowed URL schemes
        host_required: Whether the URL must have a host
        default_host: The default host to use if the URL does not have a host
        default_port: The default port to use if the URL does not have a port
        default_path: The default path to use if the URL does not have a path
        strict: Whether to use strict URL parsing
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='url',
        max_length=max_length,
        allowed_schemes=allowed_schemes,
        host_required=host_required,
        default_host=default_host,
        default_port=default_port,
        default_path=default_path,
        strict=strict,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


class MultiHostUrlSchema(TypedDict, total=False):
    type: Required[Literal['multi-host-url']]
    max_length: int
    allowed_schemes: List[str]
    host_required: bool  # default False
    default_host: str
    default_port: int
    default_path: str
    strict: bool
    ref: str
    metadata: Dict[str, Any]
    serialization: SerSchema


def multi_host_url_schema(
    *,
    max_length: int | None = None,
    allowed_schemes: list[str] | None = None,
    host_required: bool | None = None,
    default_host: str | None = None,
    default_port: int | None = None,
    default_path: str | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> MultiHostUrlSchema:
    """
    Returns a schema that matches a URL value with possibly multiple hosts, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    schema = core_schema.multi_host_url_schema()
    v = SchemaValidator(schema)
    print(v.validate_python('redis://localhost,0.0.0.0,127.0.0.1'))
    #> redis://localhost,0.0.0.0,127.0.0.1
    ```

    Args:
        max_length: The maximum length of the URL
        allowed_schemes: The allowed URL schemes
        host_required: Whether the URL must have a host
        default_host: The default host to use if the URL does not have a host
        default_port: The default port to use if the URL does not have a port
        default_path: The default path to use if the URL does not have a path
        strict: Whether to use strict URL parsing
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='multi-host-url',
        max_length=max_length,
        allowed_schemes=allowed_schemes,
        host_required=host_required,
        default_host=default_host,
        default_port=default_port,
        default_path=default_path,
        strict=strict,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


class DefinitionsSchema(TypedDict, total=False):
    type: Required[Literal['definitions']]
    schema: Required[CoreSchema]
    definitions: Required[List[CoreSchema]]
    metadata: Dict[str, Any]
    serialization: SerSchema


def definitions_schema(schema: CoreSchema, definitions: list[CoreSchema]) -> DefinitionsSchema:
    """
    Build a schema that contains both an inner schema and a list of definitions which can be used
    within the inner schema.

    ```py
    from pydantic_core import SchemaValidator, core_schema

    schema = core_schema.definitions_schema(
        core_schema.list_schema(core_schema.definition_reference_schema('foobar')),
        [core_schema.int_schema(ref='foobar')],
    )
    v = SchemaValidator(schema)
    assert v.validate_python([1, 2, '3']) == [1, 2, 3]
    ```

    Args:
        schema: The inner schema
        definitions: List of definitions which can be referenced within inner schema
    """
    return DefinitionsSchema(type='definitions', schema=schema, definitions=definitions)


class DefinitionReferenceSchema(TypedDict, total=False):
    type: Required[Literal['definition-ref']]
    schema_ref: Required[str]
    ref: str
    metadata: Dict[str, Any]
    serialization: SerSchema


def definition_reference_schema(
    schema_ref: str,
    ref: str | None = None,
    metadata: Dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> DefinitionReferenceSchema:
    """
    Returns a schema that points to a schema stored in "definitions", this is useful for nested recursive
    models and also when you want to define validators separately from the main schema, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    schema_definition = core_schema.definition_reference_schema('list-schema')
    schema = core_schema.definitions_schema(
        schema=schema_definition,
        definitions=[
            core_schema.list_schema(items_schema=schema_definition, ref='list-schema'),
        ],
    )
    v = SchemaValidator(schema)
    assert v.validate_python([()]) == [[]]
    ```

    Args:
        schema_ref: The schema ref to use for the definition reference schema
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='definition-ref', schema_ref=schema_ref, ref=ref, metadata=metadata, serialization=serialization
    )


MYPY = False
# See https://github.com/python/mypy/issues/14034 for details, in summary mypy is extremely slow to process this
# union which kills performance not just for pydantic, but even for code using pydantic
if not MYPY:
    CoreSchema = Union[
        InvalidSchema,
        AnySchema,
        NoneSchema,
        BoolSchema,
        IntSchema,
        FloatSchema,
        DecimalSchema,
        StringSchema,
        BytesSchema,
        DateSchema,
        TimeSchema,
        DatetimeSchema,
        TimedeltaSchema,
        LiteralSchema,
        EnumSchema,
        IsInstanceSchema,
        IsSubclassSchema,
        CallableSchema,
        ListSchema,
        TupleSchema,
        SetSchema,
        FrozenSetSchema,
        GeneratorSchema,
        DictSchema,
        AfterValidatorFunctionSchema,
        BeforeValidatorFunctionSchema,
        WrapValidatorFunctionSchema,
        PlainValidatorFunctionSchema,
        WithDefaultSchema,
        NullableSchema,
        UnionSchema,
        TaggedUnionSchema,
        ChainSchema,
        LaxOrStrictSchema,
        JsonOrPythonSchema,
        TypedDictSchema,
        ModelFieldsSchema,
        ModelSchema,
        DataclassArgsSchema,
        DataclassSchema,
        ArgumentsSchema,
        CallSchema,
        CustomErrorSchema,
        JsonSchema,
        UrlSchema,
        MultiHostUrlSchema,
        DefinitionsSchema,
        DefinitionReferenceSchema,
        UuidSchema,
        ComplexSchema,
    ]
elif False:
    CoreSchema: TypeAlias = Mapping[str, Any]


# to update this, call `pytest -k test_core_schema_type_literal` and copy the output
CoreSchemaType = Literal[
    'invalid',
    'any',
    'none',
    'bool',
    'int',
    'float',
    'decimal',
    'str',
    'bytes',
    'date',
    'time',
    'datetime',
    'timedelta',
    'literal',
    'enum',
    'is-instance',
    'is-subclass',
    'callable',
    'list',
    'tuple',
    'set',
    'frozenset',
    'generator',
    'dict',
    'function-after',
    'function-before',
    'function-wrap',
    'function-plain',
    'default',
    'nullable',
    'union',
    'tagged-union',
    'chain',
    'lax-or-strict',
    'json-or-python',
    'typed-dict',
    'model-fields',
    'model',
    'dataclass-args',
    'dataclass',
    'arguments',
    'call',
    'custom-error',
    'json',
    'url',
    'multi-host-url',
    'definitions',
    'definition-ref',
    'uuid',
    'complex',
]

CoreSchemaFieldType = Literal['model-field', 'dataclass-field', 'typed-dict-field', 'computed-field']


# used in _pydantic_core.pyi::PydanticKnownError
# to update this, call `pytest -k test_all_errors` and copy the output
ErrorType = Literal[
    'no_such_attribute',
    'json_invalid',
    'json_type',
    'needs_python_object',
    'recursion_loop',
    'missing',
    'frozen_field',
    'frozen_instance',
    'extra_forbidden',
    'invalid_key',
    'get_attribute_error',
    'model_type',
    'model_attributes_type',
    'dataclass_type',
    'dataclass_exact_type',
    'none_required',
    'greater_than',
    'greater_than_equal',
    'less_than',
    'less_than_equal',
    'multiple_of',
    'finite_number',
    'too_short',
    'too_long',
    'iterable_type',
    'iteration_error',
    'string_type',
    'string_sub_type',
    'string_unicode',
    'string_too_short',
    'string_too_long',
    'string_pattern_mismatch',
    'enum',
    'dict_type',
    'mapping_type',
    'list_type',
    'tuple_type',
    'set_type',
    'bool_type',
    'bool_parsing',
    'int_type',
    'int_parsing',
    'int_parsing_size',
    'int_from_float',
    'float_type',
    'float_parsing',
    'bytes_type',
    'bytes_too_short',
    'bytes_too_long',
    'bytes_invalid_encoding',
    'value_error',
    'assertion_error',
    'literal_error',
    'date_type',
    'date_parsing',
    'date_from_datetime_parsing',
    'date_from_datetime_inexact',
    'date_past',
    'date_future',
    'time_type',
    'time_parsing',
    'datetime_type',
    'datetime_parsing',
    'datetime_object_invalid',
    'datetime_from_date_parsing',
    'datetime_past',
    'datetime_future',
    'timezone_naive',
    'timezone_aware',
    'timezone_offset',
    'time_delta_type',
    'time_delta_parsing',
    'frozen_set_type',
    'is_instance_of',
    'is_subclass_of',
    'callable_type',
    'union_tag_invalid',
    'union_tag_not_found',
    'arguments_type',
    'missing_argument',
    'unexpected_keyword_argument',
    'missing_keyword_only_argument',
    'unexpected_positional_argument',
    'missing_positional_only_argument',
    'multiple_argument_values',
    'url_type',
    'url_parsing',
    'url_syntax_violation',
    'url_too_long',
    'url_scheme',
    'uuid_type',
    'uuid_parsing',
    'uuid_version',
    'decimal_type',
    'decimal_parsing',
    'decimal_max_digits',
    'decimal_max_places',
    'decimal_whole_digits',
    'complex_type',
    'complex_str_parsing',
]


def _dict_not_none(**kwargs: Any) -> Any:
    return {k: v for k, v in kwargs.items() if v is not None}


###############################################################################
# All this stuff is deprecated by #980 and will be removed eventually
# They're kept because some code external code will be using them


@deprecated('`field_before_validator_function` is deprecated, use `with_info_before_validator_function` instead.')
def field_before_validator_function(function: WithInfoValidatorFunction, field_name: str, schema: CoreSchema, **kwargs):
    warnings.warn(
        '`field_before_validator_function` is deprecated, use `with_info_before_validator_function` instead.',
        DeprecationWarning,
    )
    return with_info_before_validator_function(function, schema, field_name=field_name, **kwargs)


@deprecated('`general_before_validator_function` is deprecated, use `with_info_before_validator_function` instead.')
def general_before_validator_function(*args, **kwargs):
    warnings.warn(
        '`general_before_validator_function` is deprecated, use `with_info_before_validator_function` instead.',
        DeprecationWarning,
    )
    return with_info_before_validator_function(*args, **kwargs)


@deprecated('`field_after_validator_function` is deprecated, use `with_info_after_validator_function` instead.')
def field_after_validator_function(function: WithInfoValidatorFunction, field_name: str, schema: CoreSchema, **kwargs):
    warnings.warn(
        '`field_after_validator_function` is deprecated, use `with_info_after_validator_function` instead.',
        DeprecationWarning,
    )
    return with_info_after_validator_function(function, schema, field_name=field_name, **kwargs)


@deprecated('`general_after_validator_function` is deprecated, use `with_info_after_validator_function` instead.')
def general_after_validator_function(*args, **kwargs):
    warnings.warn(
        '`general_after_validator_function` is deprecated, use `with_info_after_validator_function` instead.',
        DeprecationWarning,
    )
    return with_info_after_validator_function(*args, **kwargs)


@deprecated('`field_wrap_validator_function` is deprecated, use `with_info_wrap_validator_function` instead.')
def field_wrap_validator_function(
    function: WithInfoWrapValidatorFunction, field_name: str, schema: CoreSchema, **kwargs
):
    warnings.warn(
        '`field_wrap_validator_function` is deprecated, use `with_info_wrap_validator_function` instead.',
        DeprecationWarning,
    )
    return with_info_wrap_validator_function(function, schema, field_name=field_name, **kwargs)


@deprecated('`general_wrap_validator_function` is deprecated, use `with_info_wrap_validator_function` instead.')
def general_wrap_validator_function(*args, **kwargs):
    warnings.warn(
        '`general_wrap_validator_function` is deprecated, use `with_info_wrap_validator_function` instead.',
        DeprecationWarning,
    )
    return with_info_wrap_validator_function(*args, **kwargs)


@deprecated('`field_plain_validator_function` is deprecated, use `with_info_plain_validator_function` instead.')
def field_plain_validator_function(function: WithInfoValidatorFunction, field_name: str, **kwargs):
    warnings.warn(
        '`field_plain_validator_function` is deprecated, use `with_info_plain_validator_function` instead.',
        DeprecationWarning,
    )
    return with_info_plain_validator_function(function, field_name=field_name, **kwargs)


@deprecated('`general_plain_validator_function` is deprecated, use `with_info_plain_validator_function` instead.')
def general_plain_validator_function(*args, **kwargs):
    warnings.warn(
        '`general_plain_validator_function` is deprecated, use `with_info_plain_validator_function` instead.',
        DeprecationWarning,
    )
    return with_info_plain_validator_function(*args, **kwargs)


_deprecated_import_lookup = {
    'FieldValidationInfo': ValidationInfo,
    'FieldValidatorFunction': WithInfoValidatorFunction,
    'GeneralValidatorFunction': WithInfoValidatorFunction,
    'FieldWrapValidatorFunction': WithInfoWrapValidatorFunction,
}

if TYPE_CHECKING:
    FieldValidationInfo = ValidationInfo


def __getattr__(attr_name: str) -> object:
    new_attr = _deprecated_import_lookup.get(attr_name)
    if new_attr is None:
        raise AttributeError(f"module 'pydantic_core' has no attribute '{attr_name}'")
    else:
        import warnings

        msg = f'`{attr_name}` is deprecated, use `{new_attr.__name__}` instead.'
        warnings.warn(msg, DeprecationWarning, stacklevel=1)
        return new_attr
