"""Private logic for creating pydantic dataclasses."""

from __future__ import annotations as _annotations

import dataclasses
import typing
import warnings
from functools import partial, wraps
from typing import Any, ClassVar

from pydantic_core import (
    ArgsKwargs,
    SchemaSerializer,
    SchemaValidator,
    core_schema,
)
from typing_extensions import TypeGuard

from ..errors import PydanticUndefinedAnnotation
from ..plugin._schema_validator import PluggableSchemaValidator, create_schema_validator
from ..warnings import PydanticDeprecatedSince20
from . import _config, _decorators
from ._fields import collect_dataclass_fields
from ._generate_schema import GenerateSchema
from ._generics import get_standard_typevars_map
from ._mock_val_ser import set_dataclass_mocks
from ._namespace_utils import NsResolver
from ._schema_generation_shared import CallbackGetCoreSchemaHandler
from ._signature import generate_pydantic_signature
from ._utils import LazyClassAttribute

if typing.TYPE_CHECKING:
    from _typeshed import DataclassInstance as StandardDataclass

    from ..config import ConfigDict
    from ..fields import FieldInfo

    class PydanticDataclass(StandardDataclass, typing.Protocol):
        """A protocol containing attributes only available once a class has been decorated as a Pydantic dataclass.

        Attributes:
            __pydantic_config__: Pydantic-specific configuration settings for the dataclass.
            __pydantic_complete__: Whether dataclass building is completed, or if there are still undefined fields.
            __pydantic_core_schema__: The pydantic-core schema used to build the SchemaValidator and SchemaSerializer.
            __pydantic_decorators__: Metadata containing the decorators defined on the dataclass.
            __pydantic_fields__: Metadata about the fields defined on the dataclass.
            __pydantic_serializer__: The pydantic-core SchemaSerializer used to dump instances of the dataclass.
            __pydantic_validator__: The pydantic-core SchemaValidator used to validate instances of the dataclass.
        """

        __pydantic_config__: ClassVar[ConfigDict]
        __pydantic_complete__: ClassVar[bool]
        __pydantic_core_schema__: ClassVar[core_schema.CoreSchema]
        __pydantic_decorators__: ClassVar[_decorators.DecoratorInfos]
        __pydantic_fields__: ClassVar[dict[str, FieldInfo]]
        __pydantic_serializer__: ClassVar[SchemaSerializer]
        __pydantic_validator__: ClassVar[SchemaValidator | PluggableSchemaValidator]

else:
    # See PyCharm issues https://youtrack.jetbrains.com/issue/PY-21915
    # and https://youtrack.jetbrains.com/issue/PY-51428
    DeprecationWarning = PydanticDeprecatedSince20


def set_dataclass_fields(
    cls: type[StandardDataclass],
    ns_resolver: NsResolver | None = None,
    config_wrapper: _config.ConfigWrapper | None = None,
) -> None:
    """Collect and set `cls.__pydantic_fields__`.

    Args:
        cls: The class.
        ns_resolver: Namespace resolver to use when getting dataclass annotations.
        config_wrapper: The config wrapper instance, defaults to `None`.
    """
    typevars_map = get_standard_typevars_map(cls)
    fields = collect_dataclass_fields(
        cls, ns_resolver=ns_resolver, typevars_map=typevars_map, config_wrapper=config_wrapper
    )

    cls.__pydantic_fields__ = fields  # type: ignore


def complete_dataclass(
    cls: type[Any],
    config_wrapper: _config.ConfigWrapper,
    *,
    raise_errors: bool = True,
    ns_resolver: NsResolver | None = None,
    _force_build: bool = False,
) -> bool:
    """Finish building a pydantic dataclass.

    This logic is called on a class which has already been wrapped in `dataclasses.dataclass()`.

    This is somewhat analogous to `pydantic._internal._model_construction.complete_model_class`.

    Args:
        cls: The class.
        config_wrapper: The config wrapper instance.
        raise_errors: Whether to raise errors, defaults to `True`.
        ns_resolver: The namespace resolver instance to use when collecting dataclass fields
            and during schema building.
        _force_build: Whether to force building the dataclass, no matter if
            [`defer_build`][pydantic.config.ConfigDict.defer_build] is set.

    Returns:
        `True` if building a pydantic dataclass is successfully completed, `False` otherwise.

    Raises:
        PydanticUndefinedAnnotation: If `raise_error` is `True` and there is an undefined annotations.
    """
    original_init = cls.__init__

    # dataclass.__init__ must be defined here so its `__qualname__` can be changed since functions can't be copied,
    # and so that the mock validator is used if building was deferred:
    def __init__(__dataclass_self__: PydanticDataclass, *args: Any, **kwargs: Any) -> None:
        __tracebackhide__ = True
        s = __dataclass_self__
        s.__pydantic_validator__.validate_python(ArgsKwargs(args, kwargs), self_instance=s)

    __init__.__qualname__ = f'{cls.__qualname__}.__init__'

    cls.__init__ = __init__  # type: ignore
    cls.__pydantic_config__ = config_wrapper.config_dict  # type: ignore

    if not _force_build and config_wrapper.defer_build:
        set_dataclass_mocks(cls, cls.__name__)
        return False

    if hasattr(cls, '__post_init_post_parse__'):
        warnings.warn(
            'Support for `__post_init_post_parse__` has been dropped, the method will not be called', DeprecationWarning
        )

    set_dataclass_fields(cls, ns_resolver, config_wrapper=config_wrapper)

    typevars_map = get_standard_typevars_map(cls)
    gen_schema = GenerateSchema(
        config_wrapper,
        ns_resolver=ns_resolver,
        typevars_map=typevars_map,
    )

    # set __signature__ attr only for model class, but not for its instances
    # (because instances can define `__call__`, and `inspect.signature` shouldn't
    # use the `__signature__` attribute and instead generate from `__call__`).
    cls.__signature__ = LazyClassAttribute(
        '__signature__',
        partial(
            generate_pydantic_signature,
            # It's' important that we reference the original_init here
            init=original_init,
            fields=cls.__pydantic_fields__,  # type: ignore
            populate_by_name=config_wrapper.populate_by_name,
            extra=config_wrapper.extra,
            is_dataclass=True,
        ),
    )
    get_core_schema = getattr(cls, '__get_pydantic_core_schema__', None)
    try:
        if get_core_schema:
            schema = get_core_schema(
                cls,
                CallbackGetCoreSchemaHandler(
                    partial(gen_schema.generate_schema, from_dunder_get_core_schema=False),
                    gen_schema,
                    ref_mode='unpack',
                ),
            )
        else:
            schema = gen_schema.generate_schema(cls, from_dunder_get_core_schema=False)
    except PydanticUndefinedAnnotation as e:
        if raise_errors:
            raise
        set_dataclass_mocks(cls, cls.__name__, f'`{e.name}`')
        return False

    core_config = config_wrapper.core_config(title=cls.__name__)

    try:
        schema = gen_schema.clean_schema(schema)
    except gen_schema.CollectedInvalid:
        set_dataclass_mocks(cls, cls.__name__, 'all referenced types')
        return False

    # We are about to set all the remaining required properties expected for this cast;
    # __pydantic_decorators__ and __pydantic_fields__ should already be set
    cls = typing.cast('type[PydanticDataclass]', cls)
    # debug(schema)

    cls.__pydantic_core_schema__ = schema
    cls.__pydantic_validator__ = validator = create_schema_validator(
        schema, cls, cls.__module__, cls.__qualname__, 'dataclass', core_config, config_wrapper.plugin_settings
    )
    cls.__pydantic_serializer__ = SchemaSerializer(schema, core_config)

    if config_wrapper.validate_assignment:

        @wraps(cls.__setattr__)
        def validated_setattr(instance: Any, field: str, value: str, /) -> None:
            validator.validate_assignment(instance, field, value)

        cls.__setattr__ = validated_setattr.__get__(None, cls)  # type: ignore

    cls.__pydantic_complete__ = True
    return True


def is_builtin_dataclass(_cls: type[Any]) -> TypeGuard[type[StandardDataclass]]:
    """Returns True if a class is a stdlib dataclass and *not* a pydantic dataclass.

    We check that
    - `_cls` is a dataclass
    - `_cls` does not inherit from a processed pydantic dataclass (and thus have a `__pydantic_validator__`)
    - `_cls` does not have any annotations that are not dataclass fields
    e.g.
    ```python
    import dataclasses

    import pydantic.dataclasses

    @dataclasses.dataclass
    class A:
        x: int

    @pydantic.dataclasses.dataclass
    class B(A):
        y: int
    ```
    In this case, when we first check `B`, we make an extra check and look at the annotations ('y'),
    which won't be a superset of all the dataclass fields (only the stdlib fields i.e. 'x')

    Args:
        cls: The class.

    Returns:
        `True` if the class is a stdlib dataclass, `False` otherwise.
    """
    return (
        dataclasses.is_dataclass(_cls)
        and not hasattr(_cls, '__pydantic_validator__')
        and set(_cls.__dataclass_fields__).issuperset(set(getattr(_cls, '__annotations__', {})))
    )
