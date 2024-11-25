import datetime
from collections.abc import Mapping
from typing import Any, Callable, Generic, Literal, TypeVar, final

from _typeshed import SupportsAllComparisons
from typing_extensions import LiteralString, Self, TypeAlias

from pydantic_core import ErrorDetails, ErrorTypeInfo, InitErrorDetails, MultiHostHost
from pydantic_core.core_schema import CoreConfig, CoreSchema, ErrorType

__all__ = [
    '__version__',
    'build_profile',
    'build_info',
    '_recursion_limit',
    'ArgsKwargs',
    'SchemaValidator',
    'SchemaSerializer',
    'Url',
    'MultiHostUrl',
    'SchemaError',
    'ValidationError',
    'PydanticCustomError',
    'PydanticKnownError',
    'PydanticOmit',
    'PydanticUseDefault',
    'PydanticSerializationError',
    'PydanticSerializationUnexpectedValue',
    'PydanticUndefined',
    'PydanticUndefinedType',
    'Some',
    'to_json',
    'from_json',
    'to_jsonable_python',
    'list_all_errors',
    'TzInfo',
    'validate_core_schema',
]
__version__: str
build_profile: str
build_info: str
_recursion_limit: int

_T = TypeVar('_T', default=Any, covariant=True)

_StringInput: TypeAlias = 'dict[str, _StringInput]'

@final
class Some(Generic[_T]):
    """
    Similar to Rust's [`Option::Some`](https://doc.rust-lang.org/std/option/enum.Option.html) type, this
    identifies a value as being present, and provides a way to access it.

    Generally used in a union with `None` to different between "some value which could be None" and no value.
    """

    __match_args__ = ('value',)

    @property
    def value(self) -> _T:
        """
        Returns the value wrapped by `Some`.
        """
    @classmethod
    def __class_getitem__(cls, item: Any, /) -> type[Self]: ...

@final
class SchemaValidator:
    """
    `SchemaValidator` is the Python wrapper for `pydantic-core`'s Rust validation logic, internally it owns one
    `CombinedValidator` which may in turn own more `CombinedValidator`s which make up the full schema validator.
    """

    # note: pyo3 currently supports __new__, but not __init__, though we include __init__ stubs
    # and docstrings here (and in the following classes) for documentation purposes

    def __init__(self, schema: CoreSchema, config: CoreConfig | None = None) -> None:
        """Initializes the `SchemaValidator`.

        Arguments:
            schema: The `CoreSchema` to use for validation.
            config: Optionally a [`CoreConfig`][pydantic_core.core_schema.CoreConfig] to configure validation.
        """

    def __new__(cls, schema: CoreSchema, config: CoreConfig | None = None) -> Self: ...
    @property
    def title(self) -> str:
        """
        The title of the schema, as used in the heading of [`ValidationError.__str__()`][pydantic_core.ValidationError].
        """
    def validate_python(
        self,
        input: Any,
        *,
        strict: bool | None = None,
        from_attributes: bool | None = None,
        context: Any | None = None,
        self_instance: Any | None = None,
        allow_partial: bool | Literal['off', 'on', 'trailing-strings'] = False,
    ) -> Any:
        """
        Validate a Python object against the schema and return the validated object.

        Arguments:
            input: The Python object to validate.
            strict: Whether to validate the object in strict mode.
                If `None`, the value of [`CoreConfig.strict`][pydantic_core.core_schema.CoreConfig] is used.
            from_attributes: Whether to validate objects as inputs to models by extracting attributes.
                If `None`, the value of [`CoreConfig.from_attributes`][pydantic_core.core_schema.CoreConfig] is used.
            context: The context to use for validation, this is passed to functional validators as
                [`info.context`][pydantic_core.core_schema.ValidationInfo.context].
            self_instance: An instance of a model set attributes on from validation, this is used when running
                validation from the `__init__` method of a model.
            allow_partial: Whether to allow partial validation; if `True` errors in the last element of sequences
                and mappings are ignored.
                `'trailing-strings'` means any final unfinished JSON string is included in the result.

        Raises:
            ValidationError: If validation fails.
            Exception: Other error types maybe raised if internal errors occur.

        Returns:
            The validated object.
        """
    def isinstance_python(
        self,
        input: Any,
        *,
        strict: bool | None = None,
        from_attributes: bool | None = None,
        context: Any | None = None,
        self_instance: Any | None = None,
    ) -> bool:
        """
        Similar to [`validate_python()`][pydantic_core.SchemaValidator.validate_python] but returns a boolean.

        Arguments match `validate_python()`. This method will not raise `ValidationError`s but will raise internal
        errors.

        Returns:
            `True` if validation succeeds, `False` if validation fails.
        """
    def validate_json(
        self,
        input: str | bytes | bytearray,
        *,
        strict: bool | None = None,
        context: Any | None = None,
        self_instance: Any | None = None,
        allow_partial: bool | Literal['off', 'on', 'trailing-strings'] = False,
    ) -> Any:
        """
        Validate JSON data directly against the schema and return the validated Python object.

        This method should be significantly faster than `validate_python(json.loads(json_data))` as it avoids the
        need to create intermediate Python objects

        It also handles constructing the correct Python type even in strict mode, where
        `validate_python(json.loads(json_data))` would fail validation.

        Arguments:
            input: The JSON data to validate.
            strict: Whether to validate the object in strict mode.
                If `None`, the value of [`CoreConfig.strict`][pydantic_core.core_schema.CoreConfig] is used.
            context: The context to use for validation, this is passed to functional validators as
                [`info.context`][pydantic_core.core_schema.ValidationInfo.context].
            self_instance: An instance of a model set attributes on from validation.
            allow_partial: Whether to allow partial validation; if `True` incomplete JSON will be parsed successfully
                and errors in the last element of sequences and mappings are ignored.
                `'trailing-strings'` means any final unfinished JSON string is included in the result.

        Raises:
            ValidationError: If validation fails or if the JSON data is invalid.
            Exception: Other error types maybe raised if internal errors occur.

        Returns:
            The validated Python object.
        """
    def validate_strings(
        self,
        input: _StringInput,
        *,
        strict: bool | None = None,
        context: Any | None = None,
        allow_partial: bool | Literal['off', 'on', 'trailing-strings'] = False,
    ) -> Any:
        """
        Validate a string against the schema and return the validated Python object.

        This is similar to `validate_json` but applies to scenarios where the input will be a string but not
        JSON data, e.g. URL fragments, query parameters, etc.

        Arguments:
            input: The input as a string, or bytes/bytearray if `strict=False`.
            strict: Whether to validate the object in strict mode.
                If `None`, the value of [`CoreConfig.strict`][pydantic_core.core_schema.CoreConfig] is used.
            context: The context to use for validation, this is passed to functional validators as
                [`info.context`][pydantic_core.core_schema.ValidationInfo.context].
            allow_partial: Whether to allow partial validation; if `True` errors in the last element of sequences
                and mappings are ignored.
                `'trailing-strings'` means any final unfinished JSON string is included in the result.

        Raises:
            ValidationError: If validation fails or if the JSON data is invalid.
            Exception: Other error types maybe raised if internal errors occur.

        Returns:
            The validated Python object.
        """
    def validate_assignment(
        self,
        obj: Any,
        field_name: str,
        field_value: Any,
        *,
        strict: bool | None = None,
        from_attributes: bool | None = None,
        context: Any | None = None,
    ) -> dict[str, Any] | tuple[dict[str, Any], dict[str, Any] | None, set[str]]:
        """
        Validate an assignment to a field on a model.

        Arguments:
            obj: The model instance being assigned to.
            field_name: The name of the field to validate assignment for.
            field_value: The value to assign to the field.
            strict: Whether to validate the object in strict mode.
                If `None`, the value of [`CoreConfig.strict`][pydantic_core.core_schema.CoreConfig] is used.
            from_attributes: Whether to validate objects as inputs to models by extracting attributes.
                If `None`, the value of [`CoreConfig.from_attributes`][pydantic_core.core_schema.CoreConfig] is used.
            context: The context to use for validation, this is passed to functional validators as
                [`info.context`][pydantic_core.core_schema.ValidationInfo.context].

        Raises:
            ValidationError: If validation fails.
            Exception: Other error types maybe raised if internal errors occur.

        Returns:
            Either the model dict or a tuple of `(model_data, model_extra, fields_set)`
        """
    def get_default_value(self, *, strict: bool | None = None, context: Any = None) -> Some | None:
        """
        Get the default value for the schema, including running default value validation.

        Arguments:
            strict: Whether to validate the default value in strict mode.
                If `None`, the value of [`CoreConfig.strict`][pydantic_core.core_schema.CoreConfig] is used.
            context: The context to use for validation, this is passed to functional validators as
                [`info.context`][pydantic_core.core_schema.ValidationInfo.context].

        Raises:
            ValidationError: If validation fails.
            Exception: Other error types maybe raised if internal errors occur.

        Returns:
            `None` if the schema has no default value, otherwise a [`Some`][pydantic_core.Some] containing the default.
        """

# In reality, `bool` should be replaced by `Literal[True]` but mypy fails to correctly apply bidirectional type inference
# (e.g. when using `{'a': {'b': True}}`).
_IncEx: TypeAlias = set[int] | set[str] | Mapping[int, _IncEx | bool] | Mapping[str, _IncEx | bool]

@final
class SchemaSerializer:
    """
    `SchemaSerializer` is the Python wrapper for `pydantic-core`'s Rust serialization logic, internally it owns one
    `CombinedSerializer` which may in turn own more `CombinedSerializer`s which make up the full schema serializer.
    """

    def __init__(self, schema: CoreSchema, config: CoreConfig | None = None) -> None:
        """Initializes the `SchemaSerializer`.

        Arguments:
            schema: The `CoreSchema` to use for serialization.
            config: Optionally a [`CoreConfig`][pydantic_core.core_schema.CoreConfig] to to configure serialization.
        """

    def __new__(cls, schema: CoreSchema, config: CoreConfig | None = None) -> Self: ...
    def to_python(
        self,
        value: Any,
        *,
        mode: str | None = None,
        include: _IncEx | None = None,
        exclude: _IncEx | None = None,
        by_alias: bool = True,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool | Literal['none', 'warn', 'error'] = True,
        fallback: Callable[[Any], Any] | None = None,
        serialize_as_any: bool = False,
        context: Any | None = None,
    ) -> Any:
        """
        Serialize/marshal a Python object to a Python object including transforming and filtering data.

        Arguments:
            value: The Python object to serialize.
            mode: The serialization mode to use, either `'python'` or `'json'`, defaults to `'python'`. In JSON mode,
                all values are converted to JSON compatible types, e.g. `None`, `int`, `float`, `str`, `list`, `dict`.
            include: A set of fields to include, if `None` all fields are included.
            exclude: A set of fields to exclude, if `None` no fields are excluded.
            by_alias: Whether to use the alias names of fields.
            exclude_unset: Whether to exclude fields that are not set,
                e.g. are not included in `__pydantic_fields_set__`.
            exclude_defaults: Whether to exclude fields that are equal to their default value.
            exclude_none: Whether to exclude fields that have a value of `None`.
            round_trip: Whether to enable serialization and validation round-trip support.
            warnings: How to handle invalid fields. False/"none" ignores them, True/"warn" logs errors,
                "error" raises a [`PydanticSerializationError`][pydantic_core.PydanticSerializationError].
            fallback: A function to call when an unknown value is encountered,
                if `None` a [`PydanticSerializationError`][pydantic_core.PydanticSerializationError] error is raised.
            serialize_as_any: Whether to serialize fields with duck-typing serialization behavior.
            context: The context to use for serialization, this is passed to functional serializers as
                [`info.context`][pydantic_core.core_schema.SerializationInfo.context].

        Raises:
            PydanticSerializationError: If serialization fails and no `fallback` function is provided.

        Returns:
            The serialized Python object.
        """
    def to_json(
        self,
        value: Any,
        *,
        indent: int | None = None,
        include: _IncEx | None = None,
        exclude: _IncEx | None = None,
        by_alias: bool = True,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool | Literal['none', 'warn', 'error'] = True,
        fallback: Callable[[Any], Any] | None = None,
        serialize_as_any: bool = False,
        context: Any | None = None,
    ) -> bytes:
        """
        Serialize a Python object to JSON including transforming and filtering data.

        Arguments:
            value: The Python object to serialize.
            indent: If `None`, the JSON will be compact, otherwise it will be pretty-printed with the indent provided.
            include: A set of fields to include, if `None` all fields are included.
            exclude: A set of fields to exclude, if `None` no fields are excluded.
            by_alias: Whether to use the alias names of fields.
            exclude_unset: Whether to exclude fields that are not set,
                e.g. are not included in `__pydantic_fields_set__`.
            exclude_defaults: Whether to exclude fields that are equal to their default value.
            exclude_none: Whether to exclude fields that have a value of `None`.
            round_trip: Whether to enable serialization and validation round-trip support.
            warnings: How to handle invalid fields. False/"none" ignores them, True/"warn" logs errors,
                "error" raises a [`PydanticSerializationError`][pydantic_core.PydanticSerializationError].
            fallback: A function to call when an unknown value is encountered,
                if `None` a [`PydanticSerializationError`][pydantic_core.PydanticSerializationError] error is raised.
            serialize_as_any: Whether to serialize fields with duck-typing serialization behavior.
            context: The context to use for serialization, this is passed to functional serializers as
                [`info.context`][pydantic_core.core_schema.SerializationInfo.context].

        Raises:
            PydanticSerializationError: If serialization fails and no `fallback` function is provided.

        Returns:
           JSON bytes.
        """

def to_json(
    value: Any,
    *,
    indent: int | None = None,
    include: _IncEx | None = None,
    exclude: _IncEx | None = None,
    by_alias: bool = True,
    exclude_none: bool = False,
    round_trip: bool = False,
    timedelta_mode: Literal['iso8601', 'float'] = 'iso8601',
    bytes_mode: Literal['utf8', 'base64', 'hex'] = 'utf8',
    inf_nan_mode: Literal['null', 'constants', 'strings'] = 'constants',
    serialize_unknown: bool = False,
    fallback: Callable[[Any], Any] | None = None,
    serialize_as_any: bool = False,
    context: Any | None = None,
) -> bytes:
    """
    Serialize a Python object to JSON including transforming and filtering data.

    This is effectively a standalone version of [`SchemaSerializer.to_json`][pydantic_core.SchemaSerializer.to_json].

    Arguments:
        value: The Python object to serialize.
        indent: If `None`, the JSON will be compact, otherwise it will be pretty-printed with the indent provided.
        include: A set of fields to include, if `None` all fields are included.
        exclude: A set of fields to exclude, if `None` no fields are excluded.
        by_alias: Whether to use the alias names of fields.
        exclude_none: Whether to exclude fields that have a value of `None`.
        round_trip: Whether to enable serialization and validation round-trip support.
        timedelta_mode: How to serialize `timedelta` objects, either `'iso8601'` or `'float'`.
        bytes_mode: How to serialize `bytes` objects, either `'utf8'`, `'base64'`, or `'hex'`.
        inf_nan_mode: How to serialize `Infinity`, `-Infinity` and `NaN` values, either `'null'`, `'constants'`, or `'strings'`.
        serialize_unknown: Attempt to serialize unknown types, `str(value)` will be used, if that fails
            `"<Unserializable {value_type} object>"` will be used.
        fallback: A function to call when an unknown value is encountered,
            if `None` a [`PydanticSerializationError`][pydantic_core.PydanticSerializationError] error is raised.
        serialize_as_any: Whether to serialize fields with duck-typing serialization behavior.
        context: The context to use for serialization, this is passed to functional serializers as
            [`info.context`][pydantic_core.core_schema.SerializationInfo.context].

    Raises:
        PydanticSerializationError: If serialization fails and no `fallback` function is provided.

    Returns:
       JSON bytes.
    """

def from_json(
    data: str | bytes | bytearray,
    *,
    allow_inf_nan: bool = True,
    cache_strings: bool | Literal['all', 'keys', 'none'] = True,
    allow_partial: bool | Literal['off', 'on', 'trailing-strings'] = False,
) -> Any:
    """
    Deserialize JSON data to a Python object.

    This is effectively a faster version of `json.loads()`, with some extra functionality.

    Arguments:
        data: The JSON data to deserialize.
        allow_inf_nan: Whether to allow `Infinity`, `-Infinity` and `NaN` values as `json.loads()` does by default.
        cache_strings: Whether to cache strings to avoid constructing new Python objects,
            this should have a significant impact on performance while increasing memory usage slightly,
            `all/True` means cache all strings, `keys` means cache only dict keys, `none/False` means no caching.
        allow_partial: Whether to allow partial deserialization, if `True` JSON data is returned if the end of the
            input is reached before the full object is deserialized, e.g. `["aa", "bb", "c` would return `['aa', 'bb']`.
            `'trailing-strings'` means any final unfinished JSON string is included in the result.

    Raises:
        ValueError: If deserialization fails.

    Returns:
        The deserialized Python object.
    """

def to_jsonable_python(
    value: Any,
    *,
    include: _IncEx | None = None,
    exclude: _IncEx | None = None,
    by_alias: bool = True,
    exclude_none: bool = False,
    round_trip: bool = False,
    timedelta_mode: Literal['iso8601', 'float'] = 'iso8601',
    bytes_mode: Literal['utf8', 'base64', 'hex'] = 'utf8',
    inf_nan_mode: Literal['null', 'constants', 'strings'] = 'constants',
    serialize_unknown: bool = False,
    fallback: Callable[[Any], Any] | None = None,
    serialize_as_any: bool = False,
    context: Any | None = None,
) -> Any:
    """
    Serialize/marshal a Python object to a JSON-serializable Python object including transforming and filtering data.

    This is effectively a standalone version of
    [`SchemaSerializer.to_python(mode='json')`][pydantic_core.SchemaSerializer.to_python].

    Args:
        value: The Python object to serialize.
        include: A set of fields to include, if `None` all fields are included.
        exclude: A set of fields to exclude, if `None` no fields are excluded.
        by_alias: Whether to use the alias names of fields.
        exclude_none: Whether to exclude fields that have a value of `None`.
        round_trip: Whether to enable serialization and validation round-trip support.
        timedelta_mode: How to serialize `timedelta` objects, either `'iso8601'` or `'float'`.
        bytes_mode: How to serialize `bytes` objects, either `'utf8'`, `'base64'`, or `'hex'`.
        inf_nan_mode: How to serialize `Infinity`, `-Infinity` and `NaN` values, either `'null'`, `'constants'`, or `'strings'`.
        serialize_unknown: Attempt to serialize unknown types, `str(value)` will be used, if that fails
            `"<Unserializable {value_type} object>"` will be used.
        fallback: A function to call when an unknown value is encountered,
            if `None` a [`PydanticSerializationError`][pydantic_core.PydanticSerializationError] error is raised.
        serialize_as_any: Whether to serialize fields with duck-typing serialization behavior.
        context: The context to use for serialization, this is passed to functional serializers as
            [`info.context`][pydantic_core.core_schema.SerializationInfo.context].

    Raises:
        PydanticSerializationError: If serialization fails and no `fallback` function is provided.

    Returns:
        The serialized Python object.
    """

class Url(SupportsAllComparisons):
    """
    A URL type, internal logic uses the [url rust crate](https://docs.rs/url/latest/url/) originally developed
    by Mozilla.
    """

    def __init__(self, url: str) -> None: ...
    def __new__(cls, url: str) -> Self: ...
    @property
    def scheme(self) -> str: ...
    @property
    def username(self) -> str | None: ...
    @property
    def password(self) -> str | None: ...
    @property
    def host(self) -> str | None: ...
    def unicode_host(self) -> str | None: ...
    @property
    def port(self) -> int | None: ...
    @property
    def path(self) -> str | None: ...
    @property
    def query(self) -> str | None: ...
    def query_params(self) -> list[tuple[str, str]]: ...
    @property
    def fragment(self) -> str | None: ...
    def unicode_string(self) -> str: ...
    def __repr__(self) -> str: ...
    def __str__(self) -> str: ...
    def __deepcopy__(self, memo: dict) -> str: ...
    @classmethod
    def build(
        cls,
        *,
        scheme: str,
        username: str | None = None,
        password: str | None = None,
        host: str,
        port: int | None = None,
        path: str | None = None,
        query: str | None = None,
        fragment: str | None = None,
    ) -> Self: ...

class MultiHostUrl(SupportsAllComparisons):
    """
    A URL type with support for multiple hosts, as used by some databases for DSNs, e.g. `https://foo.com,bar.com/path`.

    Internal URL logic uses the [url rust crate](https://docs.rs/url/latest/url/) originally developed
    by Mozilla.
    """

    def __init__(self, url: str) -> None: ...
    def __new__(cls, url: str) -> Self: ...
    @property
    def scheme(self) -> str: ...
    @property
    def path(self) -> str | None: ...
    @property
    def query(self) -> str | None: ...
    def query_params(self) -> list[tuple[str, str]]: ...
    @property
    def fragment(self) -> str | None: ...
    def hosts(self) -> list[MultiHostHost]: ...
    def unicode_string(self) -> str: ...
    def __repr__(self) -> str: ...
    def __str__(self) -> str: ...
    def __deepcopy__(self, memo: dict) -> Self: ...
    @classmethod
    def build(
        cls,
        *,
        scheme: str,
        hosts: list[MultiHostHost] | None = None,
        username: str | None = None,
        password: str | None = None,
        host: str | None = None,
        port: int | None = None,
        path: str | None = None,
        query: str | None = None,
        fragment: str | None = None,
    ) -> Self: ...

@final
class SchemaError(Exception):
    """
    Information about errors that occur while building a [`SchemaValidator`][pydantic_core.SchemaValidator]
    or [`SchemaSerializer`][pydantic_core.SchemaSerializer].
    """

    def error_count(self) -> int:
        """
        Returns:
            The number of errors in the schema.
        """
    def errors(self) -> list[ErrorDetails]:
        """
        Returns:
            A list of [`ErrorDetails`][pydantic_core.ErrorDetails] for each error in the schema.
        """

class ValidationError(ValueError):
    """
    `ValidationError` is the exception raised by `pydantic-core` when validation fails, it contains a list of errors
    which detail why validation failed.
    """
    @classmethod
    def from_exception_data(
        cls,
        title: str,
        line_errors: list[InitErrorDetails],
        input_type: Literal['python', 'json'] = 'python',
        hide_input: bool = False,
    ) -> Self:
        """
        Python constructor for a Validation Error.

        The API for constructing validation errors will probably change in the future,
        hence the static method rather than `__init__`.

        Arguments:
            title: The title of the error, as used in the heading of `str(validation_error)`
            line_errors: A list of [`InitErrorDetails`][pydantic_core.InitErrorDetails] which contain information
                about errors that occurred during validation.
            input_type: Whether the error is for a Python object or JSON.
            hide_input: Whether to hide the input value in the error message.
        """
    @property
    def title(self) -> str:
        """
        The title of the error, as used in the heading of `str(validation_error)`.
        """
    def error_count(self) -> int:
        """
        Returns:
            The number of errors in the validation error.
        """
    def errors(
        self, *, include_url: bool = True, include_context: bool = True, include_input: bool = True
    ) -> list[ErrorDetails]:
        """
        Details about each error in the validation error.

        Args:
            include_url: Whether to include a URL to documentation on the error each error.
            include_context: Whether to include the context of each error.
            include_input: Whether to include the input value of each error.

        Returns:
            A list of [`ErrorDetails`][pydantic_core.ErrorDetails] for each error in the validation error.
        """
    def json(
        self,
        *,
        indent: int | None = None,
        include_url: bool = True,
        include_context: bool = True,
        include_input: bool = True,
    ) -> str:
        """
        Same as [`errors()`][pydantic_core.ValidationError.errors] but returns a JSON string.

        Args:
            indent: The number of spaces to indent the JSON by, or `None` for no indentation - compact JSON.
            include_url: Whether to include a URL to documentation on the error each error.
            include_context: Whether to include the context of each error.
            include_input: Whether to include the input value of each error.

        Returns:
            a JSON string.
        """

    def __repr__(self) -> str:
        """
        A string representation of the validation error.

        Whether or not documentation URLs are included in the repr is controlled by the
        environment variable `PYDANTIC_ERRORS_INCLUDE_URL` being set to `1` or
        `true`; by default, URLs are shown.

        Due to implementation details, this environment variable can only be set once,
        before the first validation error is created.
        """

class PydanticCustomError(ValueError):
    """A custom exception providing flexible error handling for Pydantic validators.

    You can raise this error in custom validators when you'd like flexibility in regards to the error type, message, and context.

    Example:
        ```py
        from pydantic_core import PydanticCustomError

        def custom_validator(v) -> None:
            if v <= 10:
                raise PydanticCustomError('custom_value_error', 'Value must be greater than {value}', {'value': 10, 'extra_context': 'extra_data'})
            return v
        ```
    """

    def __init__(
        self, error_type: LiteralString, message_template: LiteralString, context: dict[str, Any] | None = None
    ) -> None:
        """Initializes the `PydanticCustomError`.

        Arguments:
            error_type: The error type.
            message_template: The message template.
            context: The data to inject into the message template.
        """

    def __new__(
        cls, error_type: LiteralString, message_template: LiteralString, context: dict[str, Any] | None = None
    ) -> Self: ...
    @property
    def context(self) -> dict[str, Any] | None:
        """Values which are required to render the error message, and could hence be useful in passing error data forward."""

    @property
    def type(self) -> str:
        """The error type associated with the error. For consistency with Pydantic, this is typically a snake_case string."""

    @property
    def message_template(self) -> str:
        """The message template associated with the error. This is a string that can be formatted with context variables in `{curly_braces}`."""

    def message(self) -> str:
        """The formatted message associated with the error. This presents as the message template with context variables appropriately injected."""

@final
class PydanticKnownError(ValueError):
    """A helper class for raising exceptions that mimic Pydantic's built-in exceptions, with more flexibility in regards to context.

    Unlike [`PydanticCustomError`][pydantic_core.PydanticCustomError], the `error_type` argument must be a known `ErrorType`.

    Example:
        ```py
        from pydantic_core import PydanticKnownError

        def custom_validator(v) -> None:
            if v <= 10:
                raise PydanticKnownError(error_type='greater_than', context={'gt': 10})
            return v
        ```
    """

    def __init__(self, error_type: ErrorType, context: dict[str, Any] | None = None) -> None:
        """Initializes the `PydanticKnownError`.

        Arguments:
            error_type: The error type.
            context: The data to inject into the message template.
        """

    def __new__(cls, error_type: ErrorType, context: dict[str, Any] | None = None) -> Self: ...
    @property
    def context(self) -> dict[str, Any] | None:
        """Values which are required to render the error message, and could hence be useful in passing error data forward."""

    @property
    def type(self) -> ErrorType:
        """The type of the error."""

    @property
    def message_template(self) -> str:
        """The message template associated with the provided error type. This is a string that can be formatted with context variables in `{curly_braces}`."""

    def message(self) -> str:
        """The formatted message associated with the error. This presents as the message template with context variables appropriately injected."""

@final
class PydanticOmit(Exception):
    """An exception to signal that a field should be omitted from a generated result.

    This could span from omitting a field from a JSON Schema to omitting a field from a serialized result.
    Upcoming: more robust support for using PydanticOmit in custom serializers is still in development.
    Right now, this is primarily used in the JSON Schema generation process.

    Example:
        ```py
        from typing import Callable

        from pydantic_core import PydanticOmit

        from pydantic import BaseModel
        from pydantic.json_schema import GenerateJsonSchema, JsonSchemaValue


        class MyGenerateJsonSchema(GenerateJsonSchema):
            def handle_invalid_for_json_schema(self, schema, error_info) -> JsonSchemaValue:
                raise PydanticOmit


        class Predicate(BaseModel):
            name: str = 'no-op'
            func: Callable = lambda x: x


        instance_example = Predicate()

        validation_schema = instance_example.model_json_schema(schema_generator=MyGenerateJsonSchema, mode='validation')
        print(validation_schema)
        '''
        {'properties': {'name': {'default': 'no-op', 'title': 'Name', 'type': 'string'}}, 'title': 'Predicate', 'type': 'object'}
        '''
        ```

    For a more in depth example / explanation, see the [customizing JSON schema](../concepts/json_schema.md#customizing-the-json-schema-generation-process) docs.
    """

    def __new__(cls) -> Self: ...

@final
class PydanticUseDefault(Exception):
    """An exception to signal that standard validation either failed or should be skipped, and the default value should be used instead.

    This warning can be raised in custom valiation functions to redirect the flow of validation.

    Example:
        ```py
        from pydantic_core import PydanticUseDefault
        from datetime import datetime
        from pydantic import BaseModel, field_validator


        class Event(BaseModel):
            name: str = 'meeting'
            time: datetime

            @field_validator('name', mode='plain')
            def name_must_be_present(cls, v) -> str:
                if not v or not isinstance(v, str):
                    raise PydanticUseDefault()
                return v


        event1 = Event(name='party', time=datetime(2024, 1, 1, 12, 0, 0))
        print(repr(event1))
        # > Event(name='party', time=datetime.datetime(2024, 1, 1, 12, 0))
        event2 = Event(time=datetime(2024, 1, 1, 12, 0, 0))
        print(repr(event2))
        # > Event(name='meeting', time=datetime.datetime(2024, 1, 1, 12, 0))
        ```

    For an additional example, seethe [validating partial json data](../concepts/json.md#partial-json-parsing) section of the Pydantic documentation.
    """

    def __new__(cls) -> Self: ...

@final
class PydanticSerializationError(ValueError):
    """An error raised when an issue occurs during serialization.

    In custom serializers, this error can be used to indicate that serialization has failed.
    """

    def __init__(self, message: str) -> None:
        """Initializes the `PydanticSerializationError`.

        Arguments:
            message: The message associated with the error.
        """

    def __new__(cls, message: str) -> Self: ...

@final
class PydanticSerializationUnexpectedValue(ValueError):
    """An error raised when an unexpected value is encountered during serialization.

    This error is often caught and coerced into a warning, as `pydantic-core` generally makes a best attempt
    at serializing values, in contrast with validation where errors are eagerly raised.

    Example:
        ```py
        from pydantic import BaseModel, field_serializer
        from pydantic_core import PydanticSerializationUnexpectedValue

        class BasicPoint(BaseModel):
            x: int
            y: int

            @field_serializer('*')
            def serialize(self, v):
                if not isinstance(v, int):
                    raise PydanticSerializationUnexpectedValue(f'Expected type `int`, got {type(v)} with value {v}')
                return v

        point = BasicPoint(x=1, y=2)
        # some sort of mutation
        point.x = 'a'

        print(point.model_dump())
        '''
        UserWarning: Pydantic serializer warnings:
        PydanticSerializationUnexpectedValue(Expected type `int`, got <class 'str'> with value a)
        return self.__pydantic_serializer__.to_python(
        {'x': 'a', 'y': 2}
        '''
        ```

    This is often used internally in `pydantic-core` when unexpected types are encountered during serialization,
    but it can also be used by users in custom serializers, as seen above.
    """

    def __init__(self, message: str) -> None:
        """Initializes the `PydanticSerializationUnexpectedValue`.

        Arguments:
            message: The message associated with the unexpected value.
        """

    def __new__(cls, message: str | None = None) -> Self: ...

@final
class ArgsKwargs:
    """A construct used to store arguments and keyword arguments for a function call.

    This data structure is generally used to store information for core schemas associated with functions (like in an arguments schema).
    This data structure is also currently used for some validation against dataclasses.

    Example:
        ```py
        from pydantic.dataclasses import dataclass
        from pydantic import model_validator


        @dataclass
        class Model:
            a: int
            b: int

            @model_validator(mode="before")
            @classmethod
            def no_op_validator(cls, values):
                print(values)
                return values

        Model(1, b=2)
        #> ArgsKwargs((1,), {"b": 2})

        Model(1, 2)
        #> ArgsKwargs((1, 2), {})

        Model(a=1, b=2)
        #> ArgsKwargs((), {"a": 1, "b": 2})
        ```
    """

    def __init__(self, args: tuple[Any, ...], kwargs: dict[str, Any] | None = None) -> None:
        """Initializes the `ArgsKwargs`.

        Arguments:
            args: The arguments (inherently ordered) for a function call.
            kwargs: The keyword arguments for a function call
        """

    def __new__(cls, args: tuple[Any, ...], kwargs: dict[str, Any] | None = None) -> Self: ...
    @property
    def args(self) -> tuple[Any, ...]:
        """The arguments (inherently ordered) for a function call."""

    @property
    def kwargs(self) -> dict[str, Any] | None:
        """The keyword arguments for a function call."""

@final
class PydanticUndefinedType:
    """A type used as a sentinel for undefined values."""

    def __copy__(self) -> Self: ...
    def __deepcopy__(self, memo: Any) -> Self: ...

PydanticUndefined: PydanticUndefinedType

def list_all_errors() -> list[ErrorTypeInfo]:
    """
    Get information about all built-in errors.

    Returns:
        A list of `ErrorTypeInfo` typed dicts.
    """
@final
class TzInfo(datetime.tzinfo):
    """An `pydantic-core` implementation of the abstract [`datetime.tzinfo`] class."""

    # Docstrings for attributes sourced from the abstract base class, [`datetime.tzinfo`](https://docs.python.org/3/library/datetime.html#datetime.tzinfo).

    def tzname(self, dt: datetime.datetime | None) -> str | None:
        """Return the time zone name corresponding to the [`datetime`][datetime.datetime] object _dt_, as a string.

        For more info, see [`tzinfo.tzname`][datetime.tzinfo.tzname].
        """

    def utcoffset(self, dt: datetime.datetime | None) -> datetime.timedelta | None:
        """Return offset of local time from UTC, as a [`timedelta`][datetime.timedelta] object that is positive east of UTC. If local time is west of UTC, this should be negative.

        More info can be found at [`tzinfo.utcoffset`][datetime.tzinfo.utcoffset].
        """

    def dst(self, dt: datetime.datetime | None) -> datetime.timedelta | None:
        """Return the daylight saving time (DST) adjustment, as a [`timedelta`][datetime.timedelta] object or `None` if DST information isn’t known.

        More info can be found at[`tzinfo.dst`][datetime.tzinfo.dst]."""

    def fromutc(self, dt: datetime.datetime) -> datetime.datetime:
        """Adjust the date and time data associated datetime object _dt_, returning an equivalent datetime in self’s local time.

        More info can be found at [`tzinfo.fromutc`][datetime.tzinfo.fromutc]."""

    def __deepcopy__(self, _memo: dict[Any, Any]) -> TzInfo: ...

def validate_core_schema(schema: CoreSchema, *, strict: bool | None = None) -> CoreSchema:
    """Validate a core schema.

    This currently uses lax mode for validation (i.e. will coerce strings to dates and such)
    but may use strict mode in the future.
    We may also remove this function altogether, do not rely on it being present if you are
    using pydantic-core directly.
    """
