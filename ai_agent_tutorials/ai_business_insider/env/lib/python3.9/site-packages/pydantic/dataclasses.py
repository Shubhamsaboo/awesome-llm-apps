"""Provide an enhanced dataclass that performs validation."""

from __future__ import annotations as _annotations

import dataclasses
import sys
import types
from typing import TYPE_CHECKING, Any, Callable, Generic, NoReturn, TypeVar, overload
from warnings import warn

from typing_extensions import Literal, TypeGuard, dataclass_transform

from ._internal import _config, _decorators, _namespace_utils, _typing_extra
from ._internal import _dataclasses as _pydantic_dataclasses
from ._migration import getattr_migration
from .config import ConfigDict
from .errors import PydanticUserError
from .fields import Field, FieldInfo, PrivateAttr

if TYPE_CHECKING:
    from ._internal._dataclasses import PydanticDataclass
    from ._internal._namespace_utils import MappingNamespace

__all__ = 'dataclass', 'rebuild_dataclass'

_T = TypeVar('_T')

if sys.version_info >= (3, 10):

    @dataclass_transform(field_specifiers=(dataclasses.field, Field, PrivateAttr))
    @overload
    def dataclass(
        *,
        init: Literal[False] = False,
        repr: bool = True,
        eq: bool = True,
        order: bool = False,
        unsafe_hash: bool = False,
        frozen: bool = False,
        config: ConfigDict | type[object] | None = None,
        validate_on_init: bool | None = None,
        kw_only: bool = ...,
        slots: bool = ...,
    ) -> Callable[[type[_T]], type[PydanticDataclass]]:  # type: ignore
        ...

    @dataclass_transform(field_specifiers=(dataclasses.field, Field, PrivateAttr))
    @overload
    def dataclass(
        _cls: type[_T],  # type: ignore
        *,
        init: Literal[False] = False,
        repr: bool = True,
        eq: bool = True,
        order: bool = False,
        unsafe_hash: bool = False,
        frozen: bool | None = None,
        config: ConfigDict | type[object] | None = None,
        validate_on_init: bool | None = None,
        kw_only: bool = ...,
        slots: bool = ...,
    ) -> type[PydanticDataclass]: ...

else:

    @dataclass_transform(field_specifiers=(dataclasses.field, Field, PrivateAttr))
    @overload
    def dataclass(
        *,
        init: Literal[False] = False,
        repr: bool = True,
        eq: bool = True,
        order: bool = False,
        unsafe_hash: bool = False,
        frozen: bool | None = None,
        config: ConfigDict | type[object] | None = None,
        validate_on_init: bool | None = None,
    ) -> Callable[[type[_T]], type[PydanticDataclass]]:  # type: ignore
        ...

    @dataclass_transform(field_specifiers=(dataclasses.field, Field, PrivateAttr))
    @overload
    def dataclass(
        _cls: type[_T],  # type: ignore
        *,
        init: Literal[False] = False,
        repr: bool = True,
        eq: bool = True,
        order: bool = False,
        unsafe_hash: bool = False,
        frozen: bool | None = None,
        config: ConfigDict | type[object] | None = None,
        validate_on_init: bool | None = None,
    ) -> type[PydanticDataclass]: ...


@dataclass_transform(field_specifiers=(dataclasses.field, Field, PrivateAttr))
def dataclass(
    _cls: type[_T] | None = None,
    *,
    init: Literal[False] = False,
    repr: bool = True,
    eq: bool = True,
    order: bool = False,
    unsafe_hash: bool = False,
    frozen: bool | None = None,
    config: ConfigDict | type[object] | None = None,
    validate_on_init: bool | None = None,
    kw_only: bool = False,
    slots: bool = False,
) -> Callable[[type[_T]], type[PydanticDataclass]] | type[PydanticDataclass]:
    """Usage docs: https://docs.pydantic.dev/2.10/concepts/dataclasses/

    A decorator used to create a Pydantic-enhanced dataclass, similar to the standard Python `dataclass`,
    but with added validation.

    This function should be used similarly to `dataclasses.dataclass`.

    Args:
        _cls: The target `dataclass`.
        init: Included for signature compatibility with `dataclasses.dataclass`, and is passed through to
            `dataclasses.dataclass` when appropriate. If specified, must be set to `False`, as pydantic inserts its
            own  `__init__` function.
        repr: A boolean indicating whether to include the field in the `__repr__` output.
        eq: Determines if a `__eq__` method should be generated for the class.
        order: Determines if comparison magic methods should be generated, such as `__lt__`, but not `__eq__`.
        unsafe_hash: Determines if a `__hash__` method should be included in the class, as in `dataclasses.dataclass`.
        frozen: Determines if the generated class should be a 'frozen' `dataclass`, which does not allow its
            attributes to be modified after it has been initialized. If not set, the value from the provided `config` argument will be used (and will default to `False` otherwise).
        config: The Pydantic config to use for the `dataclass`.
        validate_on_init: A deprecated parameter included for backwards compatibility; in V2, all Pydantic dataclasses
            are validated on init.
        kw_only: Determines if `__init__` method parameters must be specified by keyword only. Defaults to `False`.
        slots: Determines if the generated class should be a 'slots' `dataclass`, which does not allow the addition of
            new attributes after instantiation.

    Returns:
        A decorator that accepts a class as its argument and returns a Pydantic `dataclass`.

    Raises:
        AssertionError: Raised if `init` is not `False` or `validate_on_init` is `False`.
    """
    assert init is False, 'pydantic.dataclasses.dataclass only supports init=False'
    assert validate_on_init is not False, 'validate_on_init=False is no longer supported'

    if sys.version_info >= (3, 10):
        kwargs = {'kw_only': kw_only, 'slots': slots}
    else:
        kwargs = {}

    def make_pydantic_fields_compatible(cls: type[Any]) -> None:
        """Make sure that stdlib `dataclasses` understands `Field` kwargs like `kw_only`
        To do that, we simply change
          `x: int = pydantic.Field(..., kw_only=True)`
        into
          `x: int = dataclasses.field(default=pydantic.Field(..., kw_only=True), kw_only=True)`
        """
        for annotation_cls in cls.__mro__:
            # In Python < 3.9, `__annotations__` might not be present if there are no fields.
            # we therefore need to use `getattr` to avoid an `AttributeError`.
            annotations = getattr(annotation_cls, '__annotations__', [])
            for field_name in annotations:
                field_value = getattr(cls, field_name, None)
                # Process only if this is an instance of `FieldInfo`.
                if not isinstance(field_value, FieldInfo):
                    continue

                # Initialize arguments for the standard `dataclasses.field`.
                field_args: dict = {'default': field_value}

                # Handle `kw_only` for Python 3.10+
                if sys.version_info >= (3, 10) and field_value.kw_only:
                    field_args['kw_only'] = True

                # Set `repr` attribute if it's explicitly specified to be not `True`.
                if field_value.repr is not True:
                    field_args['repr'] = field_value.repr

                setattr(cls, field_name, dataclasses.field(**field_args))
                # In Python 3.8, dataclasses checks cls.__dict__['__annotations__'] for annotations,
                # so we must make sure it's initialized before we add to it.
                if cls.__dict__.get('__annotations__') is None:
                    cls.__annotations__ = {}
                cls.__annotations__[field_name] = annotations[field_name]

    def create_dataclass(cls: type[Any]) -> type[PydanticDataclass]:
        """Create a Pydantic dataclass from a regular dataclass.

        Args:
            cls: The class to create the Pydantic dataclass from.

        Returns:
            A Pydantic dataclass.
        """
        from ._internal._utils import is_model_class

        if is_model_class(cls):
            raise PydanticUserError(
                f'Cannot create a Pydantic dataclass from {cls.__name__} as it is already a Pydantic model',
                code='dataclass-on-model',
            )

        original_cls = cls

        # we warn on conflicting config specifications, but only if the class doesn't have a dataclass base
        # because a dataclass base might provide a __pydantic_config__ attribute that we don't want to warn about
        has_dataclass_base = any(dataclasses.is_dataclass(base) for base in cls.__bases__)
        if not has_dataclass_base and config is not None and hasattr(cls, '__pydantic_config__'):
            warn(
                f'`config` is set via both the `dataclass` decorator and `__pydantic_config__` for dataclass {cls.__name__}. '
                f'The `config` specification from `dataclass` decorator will take priority.',
                category=UserWarning,
                stacklevel=2,
            )

        # if config is not explicitly provided, try to read it from the type
        config_dict = config if config is not None else getattr(cls, '__pydantic_config__', None)
        config_wrapper = _config.ConfigWrapper(config_dict)
        decorators = _decorators.DecoratorInfos.build(cls)

        # Keep track of the original __doc__ so that we can restore it after applying the dataclasses decorator
        # Otherwise, classes with no __doc__ will have their signature added into the JSON schema description,
        # since dataclasses.dataclass will set this as the __doc__
        original_doc = cls.__doc__

        if _pydantic_dataclasses.is_builtin_dataclass(cls):
            # Don't preserve the docstring for vanilla dataclasses, as it may include the signature
            # This matches v1 behavior, and there was an explicit test for it
            original_doc = None

            # We don't want to add validation to the existing std lib dataclass, so we will subclass it
            #   If the class is generic, we need to make sure the subclass also inherits from Generic
            #   with all the same parameters.
            bases = (cls,)
            if issubclass(cls, Generic):
                generic_base = Generic[cls.__parameters__]  # type: ignore
                bases = bases + (generic_base,)
            cls = types.new_class(cls.__name__, bases)

        make_pydantic_fields_compatible(cls)

        # Respect frozen setting from dataclass constructor and fallback to config setting if not provided
        if frozen is not None:
            frozen_ = frozen
            if config_wrapper.frozen:
                # It's not recommended to define both, as the setting from the dataclass decorator will take priority.
                warn(
                    f'`frozen` is set via both the `dataclass` decorator and `config` for dataclass {cls.__name__!r}.'
                    'This is not recommended. The `frozen` specification on `dataclass` will take priority.',
                    category=UserWarning,
                    stacklevel=2,
                )
        else:
            frozen_ = config_wrapper.frozen or False

        cls = dataclasses.dataclass(  # type: ignore[call-overload]
            cls,
            # the value of init here doesn't affect anything except that it makes it easier to generate a signature
            init=True,
            repr=repr,
            eq=eq,
            order=order,
            unsafe_hash=unsafe_hash,
            frozen=frozen_,
            **kwargs,
        )

        cls.__pydantic_decorators__ = decorators  # type: ignore
        cls.__doc__ = original_doc
        cls.__module__ = original_cls.__module__
        cls.__qualname__ = original_cls.__qualname__
        cls.__pydantic_complete__ = False  # `complete_dataclass` will set it to `True` if successful.
        # TODO `parent_namespace` is currently None, but we could do the same thing as Pydantic models:
        # fetch the parent ns using `parent_frame_namespace` (if the dataclass was defined in a function),
        # and possibly cache it (see the `__pydantic_parent_namespace__` logic for models).
        _pydantic_dataclasses.complete_dataclass(cls, config_wrapper, raise_errors=False)
        return cls

    return create_dataclass if _cls is None else create_dataclass(_cls)


__getattr__ = getattr_migration(__name__)

if (3, 8) <= sys.version_info < (3, 11):
    # Monkeypatch dataclasses.InitVar so that typing doesn't error if it occurs as a type when evaluating type hints
    # Starting in 3.11, typing.get_type_hints will not raise an error if the retrieved type hints are not callable.

    def _call_initvar(*args: Any, **kwargs: Any) -> NoReturn:
        """This function does nothing but raise an error that is as similar as possible to what you'd get
        if you were to try calling `InitVar[int]()` without this monkeypatch. The whole purpose is just
        to ensure typing._type_check does not error if the type hint evaluates to `InitVar[<parameter>]`.
        """
        raise TypeError("'InitVar' object is not callable")

    dataclasses.InitVar.__call__ = _call_initvar


def rebuild_dataclass(
    cls: type[PydanticDataclass],
    *,
    force: bool = False,
    raise_errors: bool = True,
    _parent_namespace_depth: int = 2,
    _types_namespace: MappingNamespace | None = None,
) -> bool | None:
    """Try to rebuild the pydantic-core schema for the dataclass.

    This may be necessary when one of the annotations is a ForwardRef which could not be resolved during
    the initial attempt to build the schema, and automatic rebuilding fails.

    This is analogous to `BaseModel.model_rebuild`.

    Args:
        cls: The class to rebuild the pydantic-core schema for.
        force: Whether to force the rebuilding of the schema, defaults to `False`.
        raise_errors: Whether to raise errors, defaults to `True`.
        _parent_namespace_depth: The depth level of the parent namespace, defaults to 2.
        _types_namespace: The types namespace, defaults to `None`.

    Returns:
        Returns `None` if the schema is already "complete" and rebuilding was not required.
        If rebuilding _was_ required, returns `True` if rebuilding was successful, otherwise `False`.
    """
    if not force and cls.__pydantic_complete__:
        return None

    if '__pydantic_core_schema__' in cls.__dict__:
        delattr(cls, '__pydantic_core_schema__')  # delete cached value to ensure full rebuild happens

    if _types_namespace is not None:
        rebuild_ns = _types_namespace
    elif _parent_namespace_depth > 0:
        rebuild_ns = _typing_extra.parent_frame_namespace(parent_depth=_parent_namespace_depth, force=True) or {}
    else:
        rebuild_ns = {}

    ns_resolver = _namespace_utils.NsResolver(
        parent_namespace=rebuild_ns,
    )

    return _pydantic_dataclasses.complete_dataclass(
        cls,
        _config.ConfigWrapper(cls.__pydantic_config__, check=False),
        raise_errors=raise_errors,
        ns_resolver=ns_resolver,
        # We could provide a different config instead (with `'defer_build'` set to `True`)
        # of this explicit `_force_build` argument, but because config can come from the
        # decorator parameter or the `__pydantic_config__` attribute, `complete_dataclass`
        # will overwrite `__pydantic_config__` with the provided config above:
        _force_build=True,
    )


def is_pydantic_dataclass(class_: type[Any], /) -> TypeGuard[type[PydanticDataclass]]:
    """Whether a class is a pydantic dataclass.

    Args:
        class_: The class.

    Returns:
        `True` if the class is a pydantic dataclass, `False` otherwise.
    """
    try:
        return '__pydantic_validator__' in class_.__dict__ and dataclasses.is_dataclass(class_)
    except AttributeError:
        return False
