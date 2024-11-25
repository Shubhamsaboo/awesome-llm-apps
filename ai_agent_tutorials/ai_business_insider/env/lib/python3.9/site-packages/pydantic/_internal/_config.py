from __future__ import annotations as _annotations

import warnings
from contextlib import contextmanager
from re import Pattern
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    cast,
)

from pydantic_core import core_schema
from typing_extensions import (
    Literal,
    Self,
)

from ..aliases import AliasGenerator
from ..config import ConfigDict, ExtraValues, JsonDict, JsonEncoder, JsonSchemaExtraCallable
from ..errors import PydanticUserError
from ..warnings import PydanticDeprecatedSince20, PydanticDeprecatedSince210

if not TYPE_CHECKING:
    # See PyCharm issues https://youtrack.jetbrains.com/issue/PY-21915
    # and https://youtrack.jetbrains.com/issue/PY-51428
    DeprecationWarning = PydanticDeprecatedSince20

if TYPE_CHECKING:
    from .._internal._schema_generation_shared import GenerateSchema
    from ..fields import ComputedFieldInfo, FieldInfo

DEPRECATION_MESSAGE = 'Support for class-based `config` is deprecated, use ConfigDict instead.'


class ConfigWrapper:
    """Internal wrapper for Config which exposes ConfigDict items as attributes."""

    __slots__ = ('config_dict',)

    config_dict: ConfigDict

    # all annotations are copied directly from ConfigDict, and should be kept up to date, a test will fail if they
    # stop matching
    title: str | None
    str_to_lower: bool
    str_to_upper: bool
    str_strip_whitespace: bool
    str_min_length: int
    str_max_length: int | None
    extra: ExtraValues | None
    frozen: bool
    populate_by_name: bool
    use_enum_values: bool
    validate_assignment: bool
    arbitrary_types_allowed: bool
    from_attributes: bool
    # whether to use the actual key provided in the data (e.g. alias or first alias for "field required" errors) instead of field_names
    # to construct error `loc`s, default `True`
    loc_by_alias: bool
    alias_generator: Callable[[str], str] | AliasGenerator | None
    model_title_generator: Callable[[type], str] | None
    field_title_generator: Callable[[str, FieldInfo | ComputedFieldInfo], str] | None
    ignored_types: tuple[type, ...]
    allow_inf_nan: bool
    json_schema_extra: JsonDict | JsonSchemaExtraCallable | None
    json_encoders: dict[type[object], JsonEncoder] | None

    # new in V2
    strict: bool
    # whether instances of models and dataclasses (including subclass instances) should re-validate, default 'never'
    revalidate_instances: Literal['always', 'never', 'subclass-instances']
    ser_json_timedelta: Literal['iso8601', 'float']
    ser_json_bytes: Literal['utf8', 'base64', 'hex']
    val_json_bytes: Literal['utf8', 'base64', 'hex']
    ser_json_inf_nan: Literal['null', 'constants', 'strings']
    # whether to validate default values during validation, default False
    validate_default: bool
    validate_return: bool
    protected_namespaces: tuple[str | Pattern[str], ...]
    hide_input_in_errors: bool
    defer_build: bool
    plugin_settings: dict[str, object] | None
    schema_generator: type[GenerateSchema] | None
    json_schema_serialization_defaults_required: bool
    json_schema_mode_override: Literal['validation', 'serialization', None]
    coerce_numbers_to_str: bool
    regex_engine: Literal['rust-regex', 'python-re']
    validation_error_cause: bool
    use_attribute_docstrings: bool
    cache_strings: bool | Literal['all', 'keys', 'none']

    def __init__(self, config: ConfigDict | dict[str, Any] | type[Any] | None, *, check: bool = True):
        if check:
            self.config_dict = prepare_config(config)
        else:
            self.config_dict = cast(ConfigDict, config)

    @classmethod
    def for_model(cls, bases: tuple[type[Any], ...], namespace: dict[str, Any], kwargs: dict[str, Any]) -> Self:
        """Build a new `ConfigWrapper` instance for a `BaseModel`.

        The config wrapper built based on (in descending order of priority):
        - options from `kwargs`
        - options from the `namespace`
        - options from the base classes (`bases`)

        Args:
            bases: A tuple of base classes.
            namespace: The namespace of the class being created.
            kwargs: The kwargs passed to the class being created.

        Returns:
            A `ConfigWrapper` instance for `BaseModel`.
        """
        config_new = ConfigDict()
        for base in bases:
            config = getattr(base, 'model_config', None)
            if config:
                config_new.update(config.copy())

        config_class_from_namespace = namespace.get('Config')
        config_dict_from_namespace = namespace.get('model_config')

        raw_annotations = namespace.get('__annotations__', {})
        if raw_annotations.get('model_config') and config_dict_from_namespace is None:
            raise PydanticUserError(
                '`model_config` cannot be used as a model field name. Use `model_config` for model configuration.',
                code='model-config-invalid-field-name',
            )

        if config_class_from_namespace and config_dict_from_namespace:
            raise PydanticUserError('"Config" and "model_config" cannot be used together', code='config-both')

        config_from_namespace = config_dict_from_namespace or prepare_config(config_class_from_namespace)

        config_new.update(config_from_namespace)

        for k in list(kwargs.keys()):
            if k in config_keys:
                config_new[k] = kwargs.pop(k)

        return cls(config_new)

    # we don't show `__getattr__` to type checkers so missing attributes cause errors
    if not TYPE_CHECKING:  # pragma: no branch

        def __getattr__(self, name: str) -> Any:
            try:
                return self.config_dict[name]
            except KeyError:
                try:
                    return config_defaults[name]
                except KeyError:
                    raise AttributeError(f'Config has no attribute {name!r}') from None

    def core_config(self, title: str | None) -> core_schema.CoreConfig:
        """Create a pydantic-core config.

        We don't use getattr here since we don't want to populate with defaults.

        Args:
            title: The title to use if not set in config.

        Returns:
            A `CoreConfig` object created from config.
        """
        config = self.config_dict

        if config.get('schema_generator') is not None:
            warnings.warn(
                'The `schema_generator` setting has been deprecated since v2.10. This setting no longer has any effect.',
                PydanticDeprecatedSince210,
                stacklevel=2,
            )

        core_config_values = {
            'title': config.get('title') or title or None,
            'extra_fields_behavior': config.get('extra'),
            'allow_inf_nan': config.get('allow_inf_nan'),
            'populate_by_name': config.get('populate_by_name'),
            'str_strip_whitespace': config.get('str_strip_whitespace'),
            'str_to_lower': config.get('str_to_lower'),
            'str_to_upper': config.get('str_to_upper'),
            'strict': config.get('strict'),
            'ser_json_timedelta': config.get('ser_json_timedelta'),
            'ser_json_bytes': config.get('ser_json_bytes'),
            'val_json_bytes': config.get('val_json_bytes'),
            'ser_json_inf_nan': config.get('ser_json_inf_nan'),
            'from_attributes': config.get('from_attributes'),
            'loc_by_alias': config.get('loc_by_alias'),
            'revalidate_instances': config.get('revalidate_instances'),
            'validate_default': config.get('validate_default'),
            'str_max_length': config.get('str_max_length'),
            'str_min_length': config.get('str_min_length'),
            'hide_input_in_errors': config.get('hide_input_in_errors'),
            'coerce_numbers_to_str': config.get('coerce_numbers_to_str'),
            'regex_engine': config.get('regex_engine'),
            'validation_error_cause': config.get('validation_error_cause'),
            'cache_strings': config.get('cache_strings'),
        }

        return core_schema.CoreConfig(**{k: v for k, v in core_config_values.items() if v is not None})

    def __repr__(self):
        c = ', '.join(f'{k}={v!r}' for k, v in self.config_dict.items())
        return f'ConfigWrapper({c})'


class ConfigWrapperStack:
    """A stack of `ConfigWrapper` instances."""

    def __init__(self, config_wrapper: ConfigWrapper):
        self._config_wrapper_stack: list[ConfigWrapper] = [config_wrapper]

    @property
    def tail(self) -> ConfigWrapper:
        return self._config_wrapper_stack[-1]

    @contextmanager
    def push(self, config_wrapper: ConfigWrapper | ConfigDict | None):
        if config_wrapper is None:
            yield
            return

        if not isinstance(config_wrapper, ConfigWrapper):
            config_wrapper = ConfigWrapper(config_wrapper, check=False)

        self._config_wrapper_stack.append(config_wrapper)
        try:
            yield
        finally:
            self._config_wrapper_stack.pop()


config_defaults = ConfigDict(
    title=None,
    str_to_lower=False,
    str_to_upper=False,
    str_strip_whitespace=False,
    str_min_length=0,
    str_max_length=None,
    # let the model / dataclass decide how to handle it
    extra=None,
    frozen=False,
    populate_by_name=False,
    use_enum_values=False,
    validate_assignment=False,
    arbitrary_types_allowed=False,
    from_attributes=False,
    loc_by_alias=True,
    alias_generator=None,
    model_title_generator=None,
    field_title_generator=None,
    ignored_types=(),
    allow_inf_nan=True,
    json_schema_extra=None,
    strict=False,
    revalidate_instances='never',
    ser_json_timedelta='iso8601',
    ser_json_bytes='utf8',
    val_json_bytes='utf8',
    ser_json_inf_nan='null',
    validate_default=False,
    validate_return=False,
    protected_namespaces=('model_validate', 'model_dump'),
    hide_input_in_errors=False,
    json_encoders=None,
    defer_build=False,
    schema_generator=None,
    plugin_settings=None,
    json_schema_serialization_defaults_required=False,
    json_schema_mode_override=None,
    coerce_numbers_to_str=False,
    regex_engine='rust-regex',
    validation_error_cause=False,
    use_attribute_docstrings=False,
    cache_strings=True,
)


def prepare_config(config: ConfigDict | dict[str, Any] | type[Any] | None) -> ConfigDict:
    """Create a `ConfigDict` instance from an existing dict, a class (e.g. old class-based config) or None.

    Args:
        config: The input config.

    Returns:
        A ConfigDict object created from config.
    """
    if config is None:
        return ConfigDict()

    if not isinstance(config, dict):
        warnings.warn(DEPRECATION_MESSAGE, DeprecationWarning)
        config = {k: getattr(config, k) for k in dir(config) if not k.startswith('__')}

    config_dict = cast(ConfigDict, config)
    check_deprecated(config_dict)
    return config_dict


config_keys = set(ConfigDict.__annotations__.keys())


V2_REMOVED_KEYS = {
    'allow_mutation',
    'error_msg_templates',
    'fields',
    'getter_dict',
    'smart_union',
    'underscore_attrs_are_private',
    'json_loads',
    'json_dumps',
    'copy_on_model_validation',
    'post_init_call',
}
V2_RENAMED_KEYS = {
    'allow_population_by_field_name': 'populate_by_name',
    'anystr_lower': 'str_to_lower',
    'anystr_strip_whitespace': 'str_strip_whitespace',
    'anystr_upper': 'str_to_upper',
    'keep_untouched': 'ignored_types',
    'max_anystr_length': 'str_max_length',
    'min_anystr_length': 'str_min_length',
    'orm_mode': 'from_attributes',
    'schema_extra': 'json_schema_extra',
    'validate_all': 'validate_default',
}


def check_deprecated(config_dict: ConfigDict) -> None:
    """Check for deprecated config keys and warn the user.

    Args:
        config_dict: The input config.
    """
    deprecated_removed_keys = V2_REMOVED_KEYS & config_dict.keys()
    deprecated_renamed_keys = V2_RENAMED_KEYS.keys() & config_dict.keys()
    if deprecated_removed_keys or deprecated_renamed_keys:
        renamings = {k: V2_RENAMED_KEYS[k] for k in sorted(deprecated_renamed_keys)}
        renamed_bullets = [f'* {k!r} has been renamed to {v!r}' for k, v in renamings.items()]
        removed_bullets = [f'* {k!r} has been removed' for k in sorted(deprecated_removed_keys)]
        message = '\n'.join(['Valid config keys have changed in V2:'] + renamed_bullets + removed_bullets)
        warnings.warn(message, UserWarning)
