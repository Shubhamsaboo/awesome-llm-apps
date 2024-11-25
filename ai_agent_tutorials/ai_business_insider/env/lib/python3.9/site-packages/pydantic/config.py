"""Configuration for Pydantic models."""

from __future__ import annotations as _annotations

from re import Pattern
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Type, TypeVar, Union

from typing_extensions import Literal, TypeAlias, TypedDict

from ._migration import getattr_migration
from .aliases import AliasGenerator
from .errors import PydanticUserError

if TYPE_CHECKING:
    from ._internal._generate_schema import GenerateSchema as _GenerateSchema
    from .fields import ComputedFieldInfo, FieldInfo

__all__ = ('ConfigDict', 'with_config')


JsonValue: TypeAlias = Union[int, float, str, bool, None, List['JsonValue'], 'JsonDict']
JsonDict: TypeAlias = Dict[str, JsonValue]

JsonEncoder = Callable[[Any], Any]

JsonSchemaExtraCallable: TypeAlias = Union[
    Callable[[JsonDict], None],
    Callable[[JsonDict, Type[Any]], None],
]

ExtraValues = Literal['allow', 'ignore', 'forbid']


class ConfigDict(TypedDict, total=False):
    """A TypedDict for configuring Pydantic behaviour."""

    title: str | None
    """The title for the generated JSON schema, defaults to the model's name"""

    model_title_generator: Callable[[type], str] | None
    """A callable that takes a model class and returns the title for it. Defaults to `None`."""

    field_title_generator: Callable[[str, FieldInfo | ComputedFieldInfo], str] | None
    """A callable that takes a field's name and info and returns title for it. Defaults to `None`."""

    str_to_lower: bool
    """Whether to convert all characters to lowercase for str types. Defaults to `False`."""

    str_to_upper: bool
    """Whether to convert all characters to uppercase for str types. Defaults to `False`."""

    str_strip_whitespace: bool
    """Whether to strip leading and trailing whitespace for str types."""

    str_min_length: int
    """The minimum length for str types. Defaults to `None`."""

    str_max_length: int | None
    """The maximum length for str types. Defaults to `None`."""

    extra: ExtraValues | None
    """
    Whether to ignore, allow, or forbid extra attributes during model initialization. Defaults to `'ignore'`.

    You can configure how pydantic handles the attributes that are not defined in the model:

    * `allow` - Allow any extra attributes.
    * `forbid` - Forbid any extra attributes.
    * `ignore` - Ignore any extra attributes.

    ```python
    from pydantic import BaseModel, ConfigDict

    class User(BaseModel):
        model_config = ConfigDict(extra='ignore')  # (1)!

        name: str

    user = User(name='John Doe', age=20)  # (2)!
    print(user)
    #> name='John Doe'
    ```

    1. This is the default behaviour.
    2. The `age` argument is ignored.

    Instead, with `extra='allow'`, the `age` argument is included:

    ```python
    from pydantic import BaseModel, ConfigDict

    class User(BaseModel):
        model_config = ConfigDict(extra='allow')

        name: str

    user = User(name='John Doe', age=20)  # (1)!
    print(user)
    #> name='John Doe' age=20
    ```

    1. The `age` argument is included.

    With `extra='forbid'`, an error is raised:

    ```python
    from pydantic import BaseModel, ConfigDict, ValidationError

    class User(BaseModel):
        model_config = ConfigDict(extra='forbid')

        name: str

    try:
        User(name='John Doe', age=20)
    except ValidationError as e:
        print(e)
        '''
        1 validation error for User
        age
          Extra inputs are not permitted [type=extra_forbidden, input_value=20, input_type=int]
        '''
    ```
    """

    frozen: bool
    """
    Whether models are faux-immutable, i.e. whether `__setattr__` is allowed, and also generates
    a `__hash__()` method for the model. This makes instances of the model potentially hashable if all the
    attributes are hashable. Defaults to `False`.

    Note:
        On V1, the inverse of this setting was called `allow_mutation`, and was `True` by default.
    """

    populate_by_name: bool
    """
    Whether an aliased field may be populated by its name as given by the model
    attribute, as well as the alias. Defaults to `False`.

    Note:
        The name of this configuration setting was changed in **v2.0** from
        `allow_population_by_field_name` to `populate_by_name`.

    ```python
    from pydantic import BaseModel, ConfigDict, Field

    class User(BaseModel):
        model_config = ConfigDict(populate_by_name=True)

        name: str = Field(alias='full_name')  # (1)!
        age: int

    user = User(full_name='John Doe', age=20)  # (2)!
    print(user)
    #> name='John Doe' age=20
    user = User(name='John Doe', age=20)  # (3)!
    print(user)
    #> name='John Doe' age=20
    ```

    1. The field `'name'` has an alias `'full_name'`.
    2. The model is populated by the alias `'full_name'`.
    3. The model is populated by the field name `'name'`.
    """

    use_enum_values: bool
    """
    Whether to populate models with the `value` property of enums, rather than the raw enum.
    This may be useful if you want to serialize `model.model_dump()` later. Defaults to `False`.

    !!! note
        If you have an `Optional[Enum]` value that you set a default for, you need to use `validate_default=True`
        for said Field to ensure that the `use_enum_values` flag takes effect on the default, as extracting an
        enum's value occurs during validation, not serialization.

    ```python
    from enum import Enum
    from typing import Optional

    from pydantic import BaseModel, ConfigDict, Field

    class SomeEnum(Enum):
        FOO = 'foo'
        BAR = 'bar'
        BAZ = 'baz'

    class SomeModel(BaseModel):
        model_config = ConfigDict(use_enum_values=True)

        some_enum: SomeEnum
        another_enum: Optional[SomeEnum] = Field(
            default=SomeEnum.FOO, validate_default=True
        )

    model1 = SomeModel(some_enum=SomeEnum.BAR)
    print(model1.model_dump())
    #> {'some_enum': 'bar', 'another_enum': 'foo'}

    model2 = SomeModel(some_enum=SomeEnum.BAR, another_enum=SomeEnum.BAZ)
    print(model2.model_dump())
    #> {'some_enum': 'bar', 'another_enum': 'baz'}
    ```
    """

    validate_assignment: bool
    """
    Whether to validate the data when the model is changed. Defaults to `False`.

    The default behavior of Pydantic is to validate the data when the model is created.

    In case the user changes the data after the model is created, the model is _not_ revalidated.

    ```python
    from pydantic import BaseModel

    class User(BaseModel):
        name: str

    user = User(name='John Doe')  # (1)!
    print(user)
    #> name='John Doe'
    user.name = 123  # (1)!
    print(user)
    #> name=123
    ```

    1. The validation happens only when the model is created.
    2. The validation does not happen when the data is changed.

    In case you want to revalidate the model when the data is changed, you can use `validate_assignment=True`:

    ```python
    from pydantic import BaseModel, ValidationError

    class User(BaseModel, validate_assignment=True):  # (1)!
        name: str

    user = User(name='John Doe')  # (2)!
    print(user)
    #> name='John Doe'
    try:
        user.name = 123  # (3)!
    except ValidationError as e:
        print(e)
        '''
        1 validation error for User
        name
          Input should be a valid string [type=string_type, input_value=123, input_type=int]
        '''
    ```

    1. You can either use class keyword arguments, or `model_config` to set `validate_assignment=True`.
    2. The validation happens when the model is created.
    3. The validation _also_ happens when the data is changed.
    """

    arbitrary_types_allowed: bool
    """
    Whether arbitrary types are allowed for field types. Defaults to `False`.

    ```python
    from pydantic import BaseModel, ConfigDict, ValidationError

    # This is not a pydantic model, it's an arbitrary class
    class Pet:
        def __init__(self, name: str):
            self.name = name

    class Model(BaseModel):
        model_config = ConfigDict(arbitrary_types_allowed=True)

        pet: Pet
        owner: str

    pet = Pet(name='Hedwig')
    # A simple check of instance type is used to validate the data
    model = Model(owner='Harry', pet=pet)
    print(model)
    #> pet=<__main__.Pet object at 0x0123456789ab> owner='Harry'
    print(model.pet)
    #> <__main__.Pet object at 0x0123456789ab>
    print(model.pet.name)
    #> Hedwig
    print(type(model.pet))
    #> <class '__main__.Pet'>
    try:
        # If the value is not an instance of the type, it's invalid
        Model(owner='Harry', pet='Hedwig')
    except ValidationError as e:
        print(e)
        '''
        1 validation error for Model
        pet
          Input should be an instance of Pet [type=is_instance_of, input_value='Hedwig', input_type=str]
        '''

    # Nothing in the instance of the arbitrary type is checked
    # Here name probably should have been a str, but it's not validated
    pet2 = Pet(name=42)
    model2 = Model(owner='Harry', pet=pet2)
    print(model2)
    #> pet=<__main__.Pet object at 0x0123456789ab> owner='Harry'
    print(model2.pet)
    #> <__main__.Pet object at 0x0123456789ab>
    print(model2.pet.name)
    #> 42
    print(type(model2.pet))
    #> <class '__main__.Pet'>
    ```
    """

    from_attributes: bool
    """
    Whether to build models and look up discriminators of tagged unions using python object attributes.
    """

    loc_by_alias: bool
    """Whether to use the actual key provided in the data (e.g. alias) for error `loc`s rather than the field's name. Defaults to `True`."""

    alias_generator: Callable[[str], str] | AliasGenerator | None
    """
    A callable that takes a field name and returns an alias for it
    or an instance of [`AliasGenerator`][pydantic.aliases.AliasGenerator]. Defaults to `None`.

    When using a callable, the alias generator is used for both validation and serialization.
    If you want to use different alias generators for validation and serialization, you can use
    [`AliasGenerator`][pydantic.aliases.AliasGenerator] instead.

    If data source field names do not match your code style (e. g. CamelCase fields),
    you can automatically generate aliases using `alias_generator`. Here's an example with
    a basic callable:

    ```python
    from pydantic import BaseModel, ConfigDict
    from pydantic.alias_generators import to_pascal

    class Voice(BaseModel):
        model_config = ConfigDict(alias_generator=to_pascal)

        name: str
        language_code: str

    voice = Voice(Name='Filiz', LanguageCode='tr-TR')
    print(voice.language_code)
    #> tr-TR
    print(voice.model_dump(by_alias=True))
    #> {'Name': 'Filiz', 'LanguageCode': 'tr-TR'}
    ```

    If you want to use different alias generators for validation and serialization, you can use
    [`AliasGenerator`][pydantic.aliases.AliasGenerator].

    ```python
    from pydantic import AliasGenerator, BaseModel, ConfigDict
    from pydantic.alias_generators import to_camel, to_pascal

    class Athlete(BaseModel):
        first_name: str
        last_name: str
        sport: str

        model_config = ConfigDict(
            alias_generator=AliasGenerator(
                validation_alias=to_camel,
                serialization_alias=to_pascal,
            )
        )

    athlete = Athlete(firstName='John', lastName='Doe', sport='track')
    print(athlete.model_dump(by_alias=True))
    #> {'FirstName': 'John', 'LastName': 'Doe', 'Sport': 'track'}
    ```

    Note:
        Pydantic offers three built-in alias generators: [`to_pascal`][pydantic.alias_generators.to_pascal],
        [`to_camel`][pydantic.alias_generators.to_camel], and [`to_snake`][pydantic.alias_generators.to_snake].
    """

    ignored_types: tuple[type, ...]
    """A tuple of types that may occur as values of class attributes without annotations. This is
    typically used for custom descriptors (classes that behave like `property`). If an attribute is set on a
    class without an annotation and has a type that is not in this tuple (or otherwise recognized by
    _pydantic_), an error will be raised. Defaults to `()`.
    """

    allow_inf_nan: bool
    """Whether to allow infinity (`+inf` an `-inf`) and NaN values to float and decimal fields. Defaults to `True`."""

    json_schema_extra: JsonDict | JsonSchemaExtraCallable | None
    """A dict or callable to provide extra JSON schema properties. Defaults to `None`."""

    json_encoders: dict[type[object], JsonEncoder] | None
    """
    A `dict` of custom JSON encoders for specific types. Defaults to `None`.

    !!! warning "Deprecated"
        This config option is a carryover from v1.
        We originally planned to remove it in v2 but didn't have a 1:1 replacement so we are keeping it for now.
        It is still deprecated and will likely be removed in the future.
    """

    # new in V2
    strict: bool
    """
    _(new in V2)_ If `True`, strict validation is applied to all fields on the model.

    By default, Pydantic attempts to coerce values to the correct type, when possible.

    There are situations in which you may want to disable this behavior, and instead raise an error if a value's type
    does not match the field's type annotation.

    To configure strict mode for all fields on a model, you can set `strict=True` on the model.

    ```python
    from pydantic import BaseModel, ConfigDict

    class Model(BaseModel):
        model_config = ConfigDict(strict=True)

        name: str
        age: int
    ```

    See [Strict Mode](../concepts/strict_mode.md) for more details.

    See the [Conversion Table](../concepts/conversion_table.md) for more details on how Pydantic converts data in both
    strict and lax modes.
    """
    # whether instances of models and dataclasses (including subclass instances) should re-validate, default 'never'
    revalidate_instances: Literal['always', 'never', 'subclass-instances']
    """
    When and how to revalidate models and dataclasses during validation. Accepts the string
    values of `'never'`, `'always'` and `'subclass-instances'`. Defaults to `'never'`.

    - `'never'` will not revalidate models and dataclasses during validation
    - `'always'` will revalidate models and dataclasses during validation
    - `'subclass-instances'` will revalidate models and dataclasses during validation if the instance is a
        subclass of the model or dataclass

    By default, model and dataclass instances are not revalidated during validation.

    ```python
    from typing import List

    from pydantic import BaseModel

    class User(BaseModel, revalidate_instances='never'):  # (1)!
        hobbies: List[str]

    class SubUser(User):
        sins: List[str]

    class Transaction(BaseModel):
        user: User

    my_user = User(hobbies=['reading'])
    t = Transaction(user=my_user)
    print(t)
    #> user=User(hobbies=['reading'])

    my_user.hobbies = [1]  # (2)!
    t = Transaction(user=my_user)  # (3)!
    print(t)
    #> user=User(hobbies=[1])

    my_sub_user = SubUser(hobbies=['scuba diving'], sins=['lying'])
    t = Transaction(user=my_sub_user)
    print(t)
    #> user=SubUser(hobbies=['scuba diving'], sins=['lying'])
    ```

    1. `revalidate_instances` is set to `'never'` by **default.
    2. The assignment is not validated, unless you set `validate_assignment` to `True` in the model's config.
    3. Since `revalidate_instances` is set to `never`, this is not revalidated.

    If you want to revalidate instances during validation, you can set `revalidate_instances` to `'always'`
    in the model's config.

    ```python
    from typing import List

    from pydantic import BaseModel, ValidationError

    class User(BaseModel, revalidate_instances='always'):  # (1)!
        hobbies: List[str]

    class SubUser(User):
        sins: List[str]

    class Transaction(BaseModel):
        user: User

    my_user = User(hobbies=['reading'])
    t = Transaction(user=my_user)
    print(t)
    #> user=User(hobbies=['reading'])

    my_user.hobbies = [1]
    try:
        t = Transaction(user=my_user)  # (2)!
    except ValidationError as e:
        print(e)
        '''
        1 validation error for Transaction
        user.hobbies.0
          Input should be a valid string [type=string_type, input_value=1, input_type=int]
        '''

    my_sub_user = SubUser(hobbies=['scuba diving'], sins=['lying'])
    t = Transaction(user=my_sub_user)
    print(t)  # (3)!
    #> user=User(hobbies=['scuba diving'])
    ```

    1. `revalidate_instances` is set to `'always'`.
    2. The model is revalidated, since `revalidate_instances` is set to `'always'`.
    3. Using `'never'` we would have gotten `user=SubUser(hobbies=['scuba diving'], sins=['lying'])`.

    It's also possible to set `revalidate_instances` to `'subclass-instances'` to only revalidate instances
    of subclasses of the model.

    ```python
    from typing import List

    from pydantic import BaseModel

    class User(BaseModel, revalidate_instances='subclass-instances'):  # (1)!
        hobbies: List[str]

    class SubUser(User):
        sins: List[str]

    class Transaction(BaseModel):
        user: User

    my_user = User(hobbies=['reading'])
    t = Transaction(user=my_user)
    print(t)
    #> user=User(hobbies=['reading'])

    my_user.hobbies = [1]
    t = Transaction(user=my_user)  # (2)!
    print(t)
    #> user=User(hobbies=[1])

    my_sub_user = SubUser(hobbies=['scuba diving'], sins=['lying'])
    t = Transaction(user=my_sub_user)
    print(t)  # (3)!
    #> user=User(hobbies=['scuba diving'])
    ```

    1. `revalidate_instances` is set to `'subclass-instances'`.
    2. This is not revalidated, since `my_user` is not a subclass of `User`.
    3. Using `'never'` we would have gotten `user=SubUser(hobbies=['scuba diving'], sins=['lying'])`.
    """

    ser_json_timedelta: Literal['iso8601', 'float']
    """
    The format of JSON serialized timedeltas. Accepts the string values of `'iso8601'` and
    `'float'`. Defaults to `'iso8601'`.

    - `'iso8601'` will serialize timedeltas to ISO 8601 durations.
    - `'float'` will serialize timedeltas to the total number of seconds.
    """

    ser_json_bytes: Literal['utf8', 'base64', 'hex']
    """
    The encoding of JSON serialized bytes. Defaults to `'utf8'`.
    Set equal to `val_json_bytes` to get back an equal value after serialization round trip.

    - `'utf8'` will serialize bytes to UTF-8 strings.
    - `'base64'` will serialize bytes to URL safe base64 strings.
    - `'hex'` will serialize bytes to hexadecimal strings.
    """

    val_json_bytes: Literal['utf8', 'base64', 'hex']
    """
    The encoding of JSON serialized bytes to decode. Defaults to `'utf8'`.
    Set equal to `ser_json_bytes` to get back an equal value after serialization round trip.

    - `'utf8'` will deserialize UTF-8 strings to bytes.
    - `'base64'` will deserialize URL safe base64 strings to bytes.
    - `'hex'` will deserialize hexadecimal strings to bytes.
    """

    ser_json_inf_nan: Literal['null', 'constants', 'strings']
    """
    The encoding of JSON serialized infinity and NaN float values. Defaults to `'null'`.

    - `'null'` will serialize infinity and NaN values as `null`.
    - `'constants'` will serialize infinity and NaN values as `Infinity` and `NaN`.
    - `'strings'` will serialize infinity as string `"Infinity"` and NaN as string `"NaN"`.
    """

    # whether to validate default values during validation, default False
    validate_default: bool
    """Whether to validate default values during validation. Defaults to `False`."""

    validate_return: bool
    """Whether to validate the return value from call validators. Defaults to `False`."""

    protected_namespaces: tuple[str | Pattern[str], ...]
    """
    A `tuple` of strings and/or patterns that prevent models from having fields with names that conflict with them.
    For strings, we match on a prefix basis. Ex, if 'dog' is in the protected namespace, 'dog_name' will be protected.
    For patterns, we match on the entire field name. Ex, if `re.compile(r'^dog$')` is in the protected namespace, 'dog' will be protected, but 'dog_name' will not be.
    Defaults to `('model_validate', 'model_dump',)`.

    The reason we've selected these is to prevent collisions with other validation / dumping formats
    in the future - ex, `model_validate_{some_newly_supported_format}`.

    Before v2.10, Pydantic used `('model_',)` as the default value for this setting to
    prevent collisions between model attributes and `BaseModel`'s own methods. This was changed
    in v2.10 given feedback that this restriction was limiting in AI and data science contexts,
    where it is common to have fields with names like `model_id`, `model_input`, `model_output`, etc.

    For more details, see https://github.com/pydantic/pydantic/issues/10315.

    ```python
    import warnings

    from pydantic import BaseModel

    warnings.filterwarnings('error')  # Raise warnings as errors

    try:

        class Model(BaseModel):
            model_dump_something: str

    except UserWarning as e:
        print(e)
        '''
        Field "model_dump_something" in Model has conflict with protected namespace "model_dump".

        You may be able to resolve this warning by setting `model_config['protected_namespaces'] = ('model_validate',)`.
        '''
    ```

    You can customize this behavior using the `protected_namespaces` setting:

    ```python {test="skip"}
    import re
    import warnings

    from pydantic import BaseModel, ConfigDict

    with warnings.catch_warnings(record=True) as caught_warnings:
        warnings.simplefilter('always')  # Catch all warnings

        class Model(BaseModel):
            safe_field: str
            also_protect_field: str
            protect_this: str

            model_config = ConfigDict(
                protected_namespaces=(
                    'protect_me_',
                    'also_protect_',
                    re.compile('^protect_this$'),
                )
            )

    for warning in caught_warnings:
        print(f'{warning.message}')
        '''
        Field "also_protect_field" in Model has conflict with protected namespace "also_protect_".
        You may be able to resolve this warning by setting `model_config['protected_namespaces'] = ('protect_me_', re.compile('^protect_this$'))`.

        Field "protect_this" in Model has conflict with protected namespace "re.compile('^protect_this$')".
        You may be able to resolve this warning by setting `model_config['protected_namespaces'] = ('protect_me_', 'also_protect_')`.
        '''
    ```

    While Pydantic will only emit a warning when an item is in a protected namespace but does not actually have a collision,
    an error _is_ raised if there is an actual collision with an existing attribute:

    ```python
    from pydantic import BaseModel, ConfigDict

    try:

        class Model(BaseModel):
            model_validate: str

            model_config = ConfigDict(protected_namespaces=('model_',))

    except NameError as e:
        print(e)
        '''
        Field "model_validate" conflicts with member <bound method BaseModel.model_validate of <class 'pydantic.main.BaseModel'>> of protected namespace "model_".
        '''
    ```
    """

    hide_input_in_errors: bool
    """
    Whether to hide inputs when printing errors. Defaults to `False`.

    Pydantic shows the input value and type when it raises `ValidationError` during the validation.

    ```python
    from pydantic import BaseModel, ValidationError

    class Model(BaseModel):
        a: str

    try:
        Model(a=123)
    except ValidationError as e:
        print(e)
        '''
        1 validation error for Model
        a
          Input should be a valid string [type=string_type, input_value=123, input_type=int]
        '''
    ```

    You can hide the input value and type by setting the `hide_input_in_errors` config to `True`.

    ```python
    from pydantic import BaseModel, ConfigDict, ValidationError

    class Model(BaseModel):
        a: str
        model_config = ConfigDict(hide_input_in_errors=True)

    try:
        Model(a=123)
    except ValidationError as e:
        print(e)
        '''
        1 validation error for Model
        a
          Input should be a valid string [type=string_type]
        '''
    ```
    """

    defer_build: bool
    """
    Whether to defer model validator and serializer construction until the first model validation. Defaults to False.

    This can be useful to avoid the overhead of building models which are only
    used nested within other models, or when you want to manually define type namespace via
    [`Model.model_rebuild(_types_namespace=...)`][pydantic.BaseModel.model_rebuild].

    Since v2.10, this setting also applies to pydantic dataclasses and TypeAdapter instances.
    """

    plugin_settings: dict[str, object] | None
    """A `dict` of settings for plugins. Defaults to `None`."""

    schema_generator: type[_GenerateSchema] | None
    """
    !!! warning
        `schema_generator` is deprecated in v2.10.

        Prior to v2.10, this setting was advertised as highly subject to change.
        It's possible that this interface may once again become public once the internal core schema generation
        API is more stable, but that will likely come after significant performance improvements have been made.
    """

    json_schema_serialization_defaults_required: bool
    """
    Whether fields with default values should be marked as required in the serialization schema. Defaults to `False`.

    This ensures that the serialization schema will reflect the fact a field with a default will always be present
    when serializing the model, even though it is not required for validation.

    However, there are scenarios where this may be undesirable — in particular, if you want to share the schema
    between validation and serialization, and don't mind fields with defaults being marked as not required during
    serialization. See [#7209](https://github.com/pydantic/pydantic/issues/7209) for more details.

    ```python
    from pydantic import BaseModel, ConfigDict

    class Model(BaseModel):
        a: str = 'a'

        model_config = ConfigDict(json_schema_serialization_defaults_required=True)

    print(Model.model_json_schema(mode='validation'))
    '''
    {
        'properties': {'a': {'default': 'a', 'title': 'A', 'type': 'string'}},
        'title': 'Model',
        'type': 'object',
    }
    '''
    print(Model.model_json_schema(mode='serialization'))
    '''
    {
        'properties': {'a': {'default': 'a', 'title': 'A', 'type': 'string'}},
        'required': ['a'],
        'title': 'Model',
        'type': 'object',
    }
    '''
    ```
    """

    json_schema_mode_override: Literal['validation', 'serialization', None]
    """
    If not `None`, the specified mode will be used to generate the JSON schema regardless of what `mode` was passed to
    the function call. Defaults to `None`.

    This provides a way to force the JSON schema generation to reflect a specific mode, e.g., to always use the
    validation schema.

    It can be useful when using frameworks (such as FastAPI) that may generate different schemas for validation
    and serialization that must both be referenced from the same schema; when this happens, we automatically append
    `-Input` to the definition reference for the validation schema and `-Output` to the definition reference for the
    serialization schema. By specifying a `json_schema_mode_override` though, this prevents the conflict between
    the validation and serialization schemas (since both will use the specified schema), and so prevents the suffixes
    from being added to the definition references.

    ```python
    from pydantic import BaseModel, ConfigDict, Json

    class Model(BaseModel):
        a: Json[int]  # requires a string to validate, but will dump an int

    print(Model.model_json_schema(mode='serialization'))
    '''
    {
        'properties': {'a': {'title': 'A', 'type': 'integer'}},
        'required': ['a'],
        'title': 'Model',
        'type': 'object',
    }
    '''

    class ForceInputModel(Model):
        # the following ensures that even with mode='serialization', we
        # will get the schema that would be generated for validation.
        model_config = ConfigDict(json_schema_mode_override='validation')

    print(ForceInputModel.model_json_schema(mode='serialization'))
    '''
    {
        'properties': {
            'a': {
                'contentMediaType': 'application/json',
                'contentSchema': {'type': 'integer'},
                'title': 'A',
                'type': 'string',
            }
        },
        'required': ['a'],
        'title': 'ForceInputModel',
        'type': 'object',
    }
    '''
    ```
    """

    coerce_numbers_to_str: bool
    """
    If `True`, enables automatic coercion of any `Number` type to `str` in "lax" (non-strict) mode. Defaults to `False`.

    Pydantic doesn't allow number types (`int`, `float`, `Decimal`) to be coerced as type `str` by default.

    ```python
    from decimal import Decimal

    from pydantic import BaseModel, ConfigDict, ValidationError

    class Model(BaseModel):
        value: str

    try:
        print(Model(value=42))
    except ValidationError as e:
        print(e)
        '''
        1 validation error for Model
        value
          Input should be a valid string [type=string_type, input_value=42, input_type=int]
        '''

    class Model(BaseModel):
        model_config = ConfigDict(coerce_numbers_to_str=True)

        value: str

    repr(Model(value=42).value)
    #> "42"
    repr(Model(value=42.13).value)
    #> "42.13"
    repr(Model(value=Decimal('42.13')).value)
    #> "42.13"
    ```
    """

    regex_engine: Literal['rust-regex', 'python-re']
    """
    The regex engine to be used for pattern validation.
    Defaults to `'rust-regex'`.

    - `rust-regex` uses the [`regex`](https://docs.rs/regex) Rust crate,
      which is non-backtracking and therefore more DDoS resistant, but does not support all regex features.
    - `python-re` use the [`re`](https://docs.python.org/3/library/re.html) module,
      which supports all regex features, but may be slower.

    !!! note
        If you use a compiled regex pattern, the python-re engine will be used regardless of this setting.
        This is so that flags such as `re.IGNORECASE` are respected.

    ```python
    from pydantic import BaseModel, ConfigDict, Field, ValidationError

    class Model(BaseModel):
        model_config = ConfigDict(regex_engine='python-re')

        value: str = Field(pattern=r'^abc(?=def)')

    print(Model(value='abcdef').value)
    #> abcdef

    try:
        print(Model(value='abxyzcdef'))
    except ValidationError as e:
        print(e)
        '''
        1 validation error for Model
        value
          String should match pattern '^abc(?=def)' [type=string_pattern_mismatch, input_value='abxyzcdef', input_type=str]
        '''
    ```
    """

    validation_error_cause: bool
    """
    If `True`, Python exceptions that were part of a validation failure will be shown as an exception group as a cause. Can be useful for debugging. Defaults to `False`.

    Note:
        Python 3.10 and older don't support exception groups natively. <=3.10, backport must be installed: `pip install exceptiongroup`.

    Note:
        The structure of validation errors are likely to change in future Pydantic versions. Pydantic offers no guarantees about their structure. Should be used for visual traceback debugging only.
    """

    use_attribute_docstrings: bool
    '''
    Whether docstrings of attributes (bare string literals immediately following the attribute declaration)
    should be used for field descriptions. Defaults to `False`.

    Available in Pydantic v2.7+.

    ```python
    from pydantic import BaseModel, ConfigDict, Field


    class Model(BaseModel):
        model_config = ConfigDict(use_attribute_docstrings=True)

        x: str
        """
        Example of an attribute docstring
        """

        y: int = Field(description="Description in Field")
        """
        Description in Field overrides attribute docstring
        """


    print(Model.model_fields["x"].description)
    # > Example of an attribute docstring
    print(Model.model_fields["y"].description)
    # > Description in Field
    ```
    This requires the source code of the class to be available at runtime.

    !!! warning "Usage with `TypedDict`"
        Due to current limitations, attribute docstrings detection may not work as expected when using `TypedDict`
        (in particular when multiple `TypedDict` classes have the same name in the same source file). The behavior
        can be different depending on the Python version used.
    '''

    cache_strings: bool | Literal['all', 'keys', 'none']
    """
    Whether to cache strings to avoid constructing new Python objects. Defaults to True.

    Enabling this setting should significantly improve validation performance while increasing memory usage slightly.

    - `True` or `'all'` (the default): cache all strings
    - `'keys'`: cache only dictionary keys
    - `False` or `'none'`: no caching

    !!! note
        `True` or `'all'` is required to cache strings during general validation because
        validators don't know if they're in a key or a value.

    !!! tip
        If repeated strings are rare, it's recommended to use `'keys'` or `'none'` to reduce memory usage,
        as the performance difference is minimal if repeated strings are rare.
    """


_TypeT = TypeVar('_TypeT', bound=type)


def with_config(config: ConfigDict) -> Callable[[_TypeT], _TypeT]:
    """Usage docs: https://docs.pydantic.dev/2.10/concepts/config/#configuration-with-dataclass-from-the-standard-library-or-typeddict

    A convenience decorator to set a [Pydantic configuration](config.md) on a `TypedDict` or a `dataclass` from the standard library.

    Although the configuration can be set using the `__pydantic_config__` attribute, it does not play well with type checkers,
    especially with `TypedDict`.

    !!! example "Usage"

        ```python
        from typing_extensions import TypedDict

        from pydantic import ConfigDict, TypeAdapter, with_config

        @with_config(ConfigDict(str_to_lower=True))
        class Model(TypedDict):
            x: str

        ta = TypeAdapter(Model)

        print(ta.validate_python({'x': 'ABC'}))
        #> {'x': 'abc'}
        ```
    """

    def inner(class_: _TypeT, /) -> _TypeT:
        # Ideally, we would check for `class_` to either be a `TypedDict` or a stdlib dataclass.
        # However, the `@with_config` decorator can be applied *after* `@dataclass`. To avoid
        # common mistakes, we at least check for `class_` to not be a Pydantic model.
        from ._internal._utils import is_model_class

        if is_model_class(class_):
            raise PydanticUserError(
                f'Cannot use `with_config` on {class_.__name__} as it is a Pydantic model',
                code='with-config-on-model',
            )
        class_.__pydantic_config__ = config
        return class_

    return inner


__getattr__ = getattr_migration(__name__)
