"""Logic related to validators applied to models etc. via the `@field_validator` and `@model_validator` decorators."""

from __future__ import annotations as _annotations

from collections import deque
from dataclasses import dataclass, field
from functools import cached_property, partial, partialmethod
from inspect import Parameter, Signature, isdatadescriptor, ismethoddescriptor, signature
from itertools import islice
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Generic, Iterable, TypeVar, Union

from pydantic_core import PydanticUndefined, core_schema
from typing_extensions import Literal, TypeAlias, is_typeddict

from ..errors import PydanticUserError
from ._core_utils import get_type_ref
from ._internal_dataclass import slots_true
from ._namespace_utils import GlobalsNamespace, MappingNamespace
from ._typing_extra import get_function_type_hints
from ._utils import can_be_positional

if TYPE_CHECKING:
    from ..fields import ComputedFieldInfo
    from ..functional_validators import FieldValidatorModes


@dataclass(**slots_true)
class ValidatorDecoratorInfo:
    """A container for data from `@validator` so that we can access it
    while building the pydantic-core schema.

    Attributes:
        decorator_repr: A class variable representing the decorator string, '@validator'.
        fields: A tuple of field names the validator should be called on.
        mode: The proposed validator mode.
        each_item: For complex objects (sets, lists etc.) whether to validate individual
            elements rather than the whole object.
        always: Whether this method and other validators should be called even if the value is missing.
        check_fields: Whether to check that the fields actually exist on the model.
    """

    decorator_repr: ClassVar[str] = '@validator'

    fields: tuple[str, ...]
    mode: Literal['before', 'after']
    each_item: bool
    always: bool
    check_fields: bool | None


@dataclass(**slots_true)
class FieldValidatorDecoratorInfo:
    """A container for data from `@field_validator` so that we can access it
    while building the pydantic-core schema.

    Attributes:
        decorator_repr: A class variable representing the decorator string, '@field_validator'.
        fields: A tuple of field names the validator should be called on.
        mode: The proposed validator mode.
        check_fields: Whether to check that the fields actually exist on the model.
        json_schema_input_type: The input type of the function. This is only used to generate
            the appropriate JSON Schema (in validation mode) and can only specified
            when `mode` is either `'before'`, `'plain'` or `'wrap'`.
    """

    decorator_repr: ClassVar[str] = '@field_validator'

    fields: tuple[str, ...]
    mode: FieldValidatorModes
    check_fields: bool | None
    json_schema_input_type: Any


@dataclass(**slots_true)
class RootValidatorDecoratorInfo:
    """A container for data from `@root_validator` so that we can access it
    while building the pydantic-core schema.

    Attributes:
        decorator_repr: A class variable representing the decorator string, '@root_validator'.
        mode: The proposed validator mode.
    """

    decorator_repr: ClassVar[str] = '@root_validator'
    mode: Literal['before', 'after']


@dataclass(**slots_true)
class FieldSerializerDecoratorInfo:
    """A container for data from `@field_serializer` so that we can access it
    while building the pydantic-core schema.

    Attributes:
        decorator_repr: A class variable representing the decorator string, '@field_serializer'.
        fields: A tuple of field names the serializer should be called on.
        mode: The proposed serializer mode.
        return_type: The type of the serializer's return value.
        when_used: The serialization condition. Accepts a string with values `'always'`, `'unless-none'`, `'json'`,
            and `'json-unless-none'`.
        check_fields: Whether to check that the fields actually exist on the model.
    """

    decorator_repr: ClassVar[str] = '@field_serializer'
    fields: tuple[str, ...]
    mode: Literal['plain', 'wrap']
    return_type: Any
    when_used: core_schema.WhenUsed
    check_fields: bool | None


@dataclass(**slots_true)
class ModelSerializerDecoratorInfo:
    """A container for data from `@model_serializer` so that we can access it
    while building the pydantic-core schema.

    Attributes:
        decorator_repr: A class variable representing the decorator string, '@model_serializer'.
        mode: The proposed serializer mode.
        return_type: The type of the serializer's return value.
        when_used: The serialization condition. Accepts a string with values `'always'`, `'unless-none'`, `'json'`,
            and `'json-unless-none'`.
    """

    decorator_repr: ClassVar[str] = '@model_serializer'
    mode: Literal['plain', 'wrap']
    return_type: Any
    when_used: core_schema.WhenUsed


@dataclass(**slots_true)
class ModelValidatorDecoratorInfo:
    """A container for data from `@model_validator` so that we can access it
    while building the pydantic-core schema.

    Attributes:
        decorator_repr: A class variable representing the decorator string, '@model_validator'.
        mode: The proposed serializer mode.
    """

    decorator_repr: ClassVar[str] = '@model_validator'
    mode: Literal['wrap', 'before', 'after']


DecoratorInfo: TypeAlias = """Union[
    ValidatorDecoratorInfo,
    FieldValidatorDecoratorInfo,
    RootValidatorDecoratorInfo,
    FieldSerializerDecoratorInfo,
    ModelSerializerDecoratorInfo,
    ModelValidatorDecoratorInfo,
    ComputedFieldInfo,
]"""

ReturnType = TypeVar('ReturnType')
DecoratedType: TypeAlias = (
    'Union[classmethod[Any, Any, ReturnType], staticmethod[Any, ReturnType], Callable[..., ReturnType], property]'
)


@dataclass  # can't use slots here since we set attributes on `__post_init__`
class PydanticDescriptorProxy(Generic[ReturnType]):
    """Wrap a classmethod, staticmethod, property or unbound function
    and act as a descriptor that allows us to detect decorated items
    from the class' attributes.

    This class' __get__ returns the wrapped item's __get__ result,
    which makes it transparent for classmethods and staticmethods.

    Attributes:
        wrapped: The decorator that has to be wrapped.
        decorator_info: The decorator info.
        shim: A wrapper function to wrap V1 style function.
    """

    wrapped: DecoratedType[ReturnType]
    decorator_info: DecoratorInfo
    shim: Callable[[Callable[..., Any]], Callable[..., Any]] | None = None

    def __post_init__(self):
        for attr in 'setter', 'deleter':
            if hasattr(self.wrapped, attr):
                f = partial(self._call_wrapped_attr, name=attr)
                setattr(self, attr, f)

    def _call_wrapped_attr(self, func: Callable[[Any], None], *, name: str) -> PydanticDescriptorProxy[ReturnType]:
        self.wrapped = getattr(self.wrapped, name)(func)
        if isinstance(self.wrapped, property):
            # update ComputedFieldInfo.wrapped_property
            from ..fields import ComputedFieldInfo

            if isinstance(self.decorator_info, ComputedFieldInfo):
                self.decorator_info.wrapped_property = self.wrapped
        return self

    def __get__(self, obj: object | None, obj_type: type[object] | None = None) -> PydanticDescriptorProxy[ReturnType]:
        try:
            return self.wrapped.__get__(obj, obj_type)
        except AttributeError:
            # not a descriptor, e.g. a partial object
            return self.wrapped  # type: ignore[return-value]

    def __set_name__(self, instance: Any, name: str) -> None:
        if hasattr(self.wrapped, '__set_name__'):
            self.wrapped.__set_name__(instance, name)  # pyright: ignore[reportFunctionMemberAccess]

    def __getattr__(self, __name: str) -> Any:
        """Forward checks for __isabstractmethod__ and such."""
        return getattr(self.wrapped, __name)


DecoratorInfoType = TypeVar('DecoratorInfoType', bound=DecoratorInfo)


@dataclass(**slots_true)
class Decorator(Generic[DecoratorInfoType]):
    """A generic container class to join together the decorator metadata
    (metadata from decorator itself, which we have when the
    decorator is called but not when we are building the core-schema)
    and the bound function (which we have after the class itself is created).

    Attributes:
        cls_ref: The class ref.
        cls_var_name: The decorated function name.
        func: The decorated function.
        shim: A wrapper function to wrap V1 style function.
        info: The decorator info.
    """

    cls_ref: str
    cls_var_name: str
    func: Callable[..., Any]
    shim: Callable[[Any], Any] | None
    info: DecoratorInfoType

    @staticmethod
    def build(
        cls_: Any,
        *,
        cls_var_name: str,
        shim: Callable[[Any], Any] | None,
        info: DecoratorInfoType,
    ) -> Decorator[DecoratorInfoType]:
        """Build a new decorator.

        Args:
            cls_: The class.
            cls_var_name: The decorated function name.
            shim: A wrapper function to wrap V1 style function.
            info: The decorator info.

        Returns:
            The new decorator instance.
        """
        func = get_attribute_from_bases(cls_, cls_var_name)
        if shim is not None:
            func = shim(func)
        func = unwrap_wrapped_function(func, unwrap_partial=False)
        if not callable(func):
            # This branch will get hit for classmethod properties
            attribute = get_attribute_from_base_dicts(cls_, cls_var_name)  # prevents the binding call to `__get__`
            if isinstance(attribute, PydanticDescriptorProxy):
                func = unwrap_wrapped_function(attribute.wrapped)
        return Decorator(
            cls_ref=get_type_ref(cls_),
            cls_var_name=cls_var_name,
            func=func,
            shim=shim,
            info=info,
        )

    def bind_to_cls(self, cls: Any) -> Decorator[DecoratorInfoType]:
        """Bind the decorator to a class.

        Args:
            cls: the class.

        Returns:
            The new decorator instance.
        """
        return self.build(
            cls,
            cls_var_name=self.cls_var_name,
            shim=self.shim,
            info=self.info,
        )


def get_bases(tp: type[Any]) -> tuple[type[Any], ...]:
    """Get the base classes of a class or typeddict.

    Args:
        tp: The type or class to get the bases.

    Returns:
        The base classes.
    """
    if is_typeddict(tp):
        return tp.__orig_bases__  # type: ignore
    try:
        return tp.__bases__
    except AttributeError:
        return ()


def mro(tp: type[Any]) -> tuple[type[Any], ...]:
    """Calculate the Method Resolution Order of bases using the C3 algorithm.

    See https://www.python.org/download/releases/2.3/mro/
    """
    # try to use the existing mro, for performance mainly
    # but also because it helps verify the implementation below
    if not is_typeddict(tp):
        try:
            return tp.__mro__
        except AttributeError:
            # GenericAlias and some other cases
            pass

    bases = get_bases(tp)
    return (tp,) + mro_for_bases(bases)


def mro_for_bases(bases: tuple[type[Any], ...]) -> tuple[type[Any], ...]:
    def merge_seqs(seqs: list[deque[type[Any]]]) -> Iterable[type[Any]]:
        while True:
            non_empty = [seq for seq in seqs if seq]
            if not non_empty:
                # Nothing left to process, we're done.
                return
            candidate: type[Any] | None = None
            for seq in non_empty:  # Find merge candidates among seq heads.
                candidate = seq[0]
                not_head = [s for s in non_empty if candidate in islice(s, 1, None)]
                if not_head:
                    # Reject the candidate.
                    candidate = None
                else:
                    break
            if not candidate:
                raise TypeError('Inconsistent hierarchy, no C3 MRO is possible')
            yield candidate
            for seq in non_empty:
                # Remove candidate.
                if seq[0] == candidate:
                    seq.popleft()

    seqs = [deque(mro(base)) for base in bases] + [deque(bases)]
    return tuple(merge_seqs(seqs))


_sentinel = object()


def get_attribute_from_bases(tp: type[Any] | tuple[type[Any], ...], name: str) -> Any:
    """Get the attribute from the next class in the MRO that has it,
    aiming to simulate calling the method on the actual class.

    The reason for iterating over the mro instead of just getting
    the attribute (which would do that for us) is to support TypedDict,
    which lacks a real __mro__, but can have a virtual one constructed
    from its bases (as done here).

    Args:
        tp: The type or class to search for the attribute. If a tuple, this is treated as a set of base classes.
        name: The name of the attribute to retrieve.

    Returns:
        Any: The attribute value, if found.

    Raises:
        AttributeError: If the attribute is not found in any class in the MRO.
    """
    if isinstance(tp, tuple):
        for base in mro_for_bases(tp):
            attribute = base.__dict__.get(name, _sentinel)
            if attribute is not _sentinel:
                attribute_get = getattr(attribute, '__get__', None)
                if attribute_get is not None:
                    return attribute_get(None, tp)
                return attribute
        raise AttributeError(f'{name} not found in {tp}')
    else:
        try:
            return getattr(tp, name)
        except AttributeError:
            return get_attribute_from_bases(mro(tp), name)


def get_attribute_from_base_dicts(tp: type[Any], name: str) -> Any:
    """Get an attribute out of the `__dict__` following the MRO.
    This prevents the call to `__get__` on the descriptor, and allows
    us to get the original function for classmethod properties.

    Args:
        tp: The type or class to search for the attribute.
        name: The name of the attribute to retrieve.

    Returns:
        Any: The attribute value, if found.

    Raises:
        KeyError: If the attribute is not found in any class's `__dict__` in the MRO.
    """
    for base in reversed(mro(tp)):
        if name in base.__dict__:
            return base.__dict__[name]
    return tp.__dict__[name]  # raise the error


@dataclass(**slots_true)
class DecoratorInfos:
    """Mapping of name in the class namespace to decorator info.

    note that the name in the class namespace is the function or attribute name
    not the field name!
    """

    validators: dict[str, Decorator[ValidatorDecoratorInfo]] = field(default_factory=dict)
    field_validators: dict[str, Decorator[FieldValidatorDecoratorInfo]] = field(default_factory=dict)
    root_validators: dict[str, Decorator[RootValidatorDecoratorInfo]] = field(default_factory=dict)
    field_serializers: dict[str, Decorator[FieldSerializerDecoratorInfo]] = field(default_factory=dict)
    model_serializers: dict[str, Decorator[ModelSerializerDecoratorInfo]] = field(default_factory=dict)
    model_validators: dict[str, Decorator[ModelValidatorDecoratorInfo]] = field(default_factory=dict)
    computed_fields: dict[str, Decorator[ComputedFieldInfo]] = field(default_factory=dict)

    @staticmethod
    def build(model_dc: type[Any]) -> DecoratorInfos:  # noqa: C901 (ignore complexity)
        """We want to collect all DecFunc instances that exist as
        attributes in the namespace of the class (a BaseModel or dataclass)
        that called us
        But we want to collect these in the order of the bases
        So instead of getting them all from the leaf class (the class that called us),
        we traverse the bases from root (the oldest ancestor class) to leaf
        and collect all of the instances as we go, taking care to replace
        any duplicate ones with the last one we see to mimic how function overriding
        works with inheritance.
        If we do replace any functions we put the replacement into the position
        the replaced function was in; that is, we maintain the order.
        """
        # reminder: dicts are ordered and replacement does not alter the order
        res = DecoratorInfos()
        for base in reversed(mro(model_dc)[1:]):
            existing: DecoratorInfos | None = base.__dict__.get('__pydantic_decorators__')
            if existing is None:
                existing = DecoratorInfos.build(base)
            res.validators.update({k: v.bind_to_cls(model_dc) for k, v in existing.validators.items()})
            res.field_validators.update({k: v.bind_to_cls(model_dc) for k, v in existing.field_validators.items()})
            res.root_validators.update({k: v.bind_to_cls(model_dc) for k, v in existing.root_validators.items()})
            res.field_serializers.update({k: v.bind_to_cls(model_dc) for k, v in existing.field_serializers.items()})
            res.model_serializers.update({k: v.bind_to_cls(model_dc) for k, v in existing.model_serializers.items()})
            res.model_validators.update({k: v.bind_to_cls(model_dc) for k, v in existing.model_validators.items()})
            res.computed_fields.update({k: v.bind_to_cls(model_dc) for k, v in existing.computed_fields.items()})

        to_replace: list[tuple[str, Any]] = []

        for var_name, var_value in vars(model_dc).items():
            if isinstance(var_value, PydanticDescriptorProxy):
                info = var_value.decorator_info
                if isinstance(info, ValidatorDecoratorInfo):
                    res.validators[var_name] = Decorator.build(
                        model_dc, cls_var_name=var_name, shim=var_value.shim, info=info
                    )
                elif isinstance(info, FieldValidatorDecoratorInfo):
                    res.field_validators[var_name] = Decorator.build(
                        model_dc, cls_var_name=var_name, shim=var_value.shim, info=info
                    )
                elif isinstance(info, RootValidatorDecoratorInfo):
                    res.root_validators[var_name] = Decorator.build(
                        model_dc, cls_var_name=var_name, shim=var_value.shim, info=info
                    )
                elif isinstance(info, FieldSerializerDecoratorInfo):
                    # check whether a serializer function is already registered for fields
                    for field_serializer_decorator in res.field_serializers.values():
                        # check that each field has at most one serializer function.
                        # serializer functions for the same field in subclasses are allowed,
                        # and are treated as overrides
                        if field_serializer_decorator.cls_var_name == var_name:
                            continue
                        for f in info.fields:
                            if f in field_serializer_decorator.info.fields:
                                raise PydanticUserError(
                                    'Multiple field serializer functions were defined '
                                    f'for field {f!r}, this is not allowed.',
                                    code='multiple-field-serializers',
                                )
                    res.field_serializers[var_name] = Decorator.build(
                        model_dc, cls_var_name=var_name, shim=var_value.shim, info=info
                    )
                elif isinstance(info, ModelValidatorDecoratorInfo):
                    res.model_validators[var_name] = Decorator.build(
                        model_dc, cls_var_name=var_name, shim=var_value.shim, info=info
                    )
                elif isinstance(info, ModelSerializerDecoratorInfo):
                    res.model_serializers[var_name] = Decorator.build(
                        model_dc, cls_var_name=var_name, shim=var_value.shim, info=info
                    )
                else:
                    from ..fields import ComputedFieldInfo

                    isinstance(var_value, ComputedFieldInfo)
                    res.computed_fields[var_name] = Decorator.build(
                        model_dc, cls_var_name=var_name, shim=None, info=info
                    )
                to_replace.append((var_name, var_value.wrapped))
        if to_replace:
            # If we can save `__pydantic_decorators__` on the class we'll be able to check for it above
            # so then we don't need to re-process the type, which means we can discard our descriptor wrappers
            # and replace them with the thing they are wrapping (see the other setattr call below)
            # which allows validator class methods to also function as regular class methods
            model_dc.__pydantic_decorators__ = res
            for name, value in to_replace:
                setattr(model_dc, name, value)
        return res


def inspect_validator(validator: Callable[..., Any], mode: FieldValidatorModes) -> bool:
    """Look at a field or model validator function and determine whether it takes an info argument.

    An error is raised if the function has an invalid signature.

    Args:
        validator: The validator function to inspect.
        mode: The proposed validator mode.

    Returns:
        Whether the validator takes an info argument.
    """
    try:
        sig = signature(validator)
    except (ValueError, TypeError):
        # `inspect.signature` might not be able to infer a signature, e.g. with C objects.
        # In this case, we assume no info argument is present:
        return False
    n_positional = count_positional_required_params(sig)
    if mode == 'wrap':
        if n_positional == 3:
            return True
        elif n_positional == 2:
            return False
    else:
        assert mode in {'before', 'after', 'plain'}, f"invalid mode: {mode!r}, expected 'before', 'after' or 'plain"
        if n_positional == 2:
            return True
        elif n_positional == 1:
            return False

    raise PydanticUserError(
        f'Unrecognized field_validator function signature for {validator} with `mode={mode}`:{sig}',
        code='validator-signature',
    )


def inspect_field_serializer(serializer: Callable[..., Any], mode: Literal['plain', 'wrap']) -> tuple[bool, bool]:
    """Look at a field serializer function and determine if it is a field serializer,
    and whether it takes an info argument.

    An error is raised if the function has an invalid signature.

    Args:
        serializer: The serializer function to inspect.
        mode: The serializer mode, either 'plain' or 'wrap'.

    Returns:
        Tuple of (is_field_serializer, info_arg).
    """
    try:
        sig = signature(serializer)
    except (ValueError, TypeError):
        # `inspect.signature` might not be able to infer a signature, e.g. with C objects.
        # In this case, we assume no info argument is present and this is not a method:
        return (False, False)

    first = next(iter(sig.parameters.values()), None)
    is_field_serializer = first is not None and first.name == 'self'

    n_positional = count_positional_required_params(sig)
    if is_field_serializer:
        # -1 to correct for self parameter
        info_arg = _serializer_info_arg(mode, n_positional - 1)
    else:
        info_arg = _serializer_info_arg(mode, n_positional)

    if info_arg is None:
        raise PydanticUserError(
            f'Unrecognized field_serializer function signature for {serializer} with `mode={mode}`:{sig}',
            code='field-serializer-signature',
        )

    return is_field_serializer, info_arg


def inspect_annotated_serializer(serializer: Callable[..., Any], mode: Literal['plain', 'wrap']) -> bool:
    """Look at a serializer function used via `Annotated` and determine whether it takes an info argument.

    An error is raised if the function has an invalid signature.

    Args:
        serializer: The serializer function to check.
        mode: The serializer mode, either 'plain' or 'wrap'.

    Returns:
        info_arg
    """
    try:
        sig = signature(serializer)
    except (ValueError, TypeError):
        # `inspect.signature` might not be able to infer a signature, e.g. with C objects.
        # In this case, we assume no info argument is present:
        return False
    info_arg = _serializer_info_arg(mode, count_positional_required_params(sig))
    if info_arg is None:
        raise PydanticUserError(
            f'Unrecognized field_serializer function signature for {serializer} with `mode={mode}`:{sig}',
            code='field-serializer-signature',
        )
    else:
        return info_arg


def inspect_model_serializer(serializer: Callable[..., Any], mode: Literal['plain', 'wrap']) -> bool:
    """Look at a model serializer function and determine whether it takes an info argument.

    An error is raised if the function has an invalid signature.

    Args:
        serializer: The serializer function to check.
        mode: The serializer mode, either 'plain' or 'wrap'.

    Returns:
        `info_arg` - whether the function expects an info argument.
    """
    if isinstance(serializer, (staticmethod, classmethod)) or not is_instance_method_from_sig(serializer):
        raise PydanticUserError(
            '`@model_serializer` must be applied to instance methods', code='model-serializer-instance-method'
        )

    sig = signature(serializer)
    info_arg = _serializer_info_arg(mode, count_positional_required_params(sig))
    if info_arg is None:
        raise PydanticUserError(
            f'Unrecognized model_serializer function signature for {serializer} with `mode={mode}`:{sig}',
            code='model-serializer-signature',
        )
    else:
        return info_arg


def _serializer_info_arg(mode: Literal['plain', 'wrap'], n_positional: int) -> bool | None:
    if mode == 'plain':
        if n_positional == 1:
            # (input_value: Any, /) -> Any
            return False
        elif n_positional == 2:
            # (model: Any, input_value: Any, /) -> Any
            return True
    else:
        assert mode == 'wrap', f"invalid mode: {mode!r}, expected 'plain' or 'wrap'"
        if n_positional == 2:
            # (input_value: Any, serializer: SerializerFunctionWrapHandler, /) -> Any
            return False
        elif n_positional == 3:
            # (input_value: Any, serializer: SerializerFunctionWrapHandler, info: SerializationInfo, /) -> Any
            return True

    return None


AnyDecoratorCallable: TypeAlias = (
    'Union[classmethod[Any, Any, Any], staticmethod[Any, Any], partialmethod[Any], Callable[..., Any]]'
)


def is_instance_method_from_sig(function: AnyDecoratorCallable) -> bool:
    """Whether the function is an instance method.

    It will consider a function as instance method if the first parameter of
    function is `self`.

    Args:
        function: The function to check.

    Returns:
        `True` if the function is an instance method, `False` otherwise.
    """
    sig = signature(unwrap_wrapped_function(function))
    first = next(iter(sig.parameters.values()), None)
    if first and first.name == 'self':
        return True
    return False


def ensure_classmethod_based_on_signature(function: AnyDecoratorCallable) -> Any:
    """Apply the `@classmethod` decorator on the function.

    Args:
        function: The function to apply the decorator on.

    Return:
        The `@classmethod` decorator applied function.
    """
    if not isinstance(
        unwrap_wrapped_function(function, unwrap_class_static_method=False), classmethod
    ) and _is_classmethod_from_sig(function):
        return classmethod(function)  # type: ignore[arg-type]
    return function


def _is_classmethod_from_sig(function: AnyDecoratorCallable) -> bool:
    sig = signature(unwrap_wrapped_function(function))
    first = next(iter(sig.parameters.values()), None)
    if first and first.name == 'cls':
        return True
    return False


def unwrap_wrapped_function(
    func: Any,
    *,
    unwrap_partial: bool = True,
    unwrap_class_static_method: bool = True,
) -> Any:
    """Recursively unwraps a wrapped function until the underlying function is reached.
    This handles property, functools.partial, functools.partialmethod, staticmethod, and classmethod.

    Args:
        func: The function to unwrap.
        unwrap_partial: If True (default), unwrap partial and partialmethod decorators.
        unwrap_class_static_method: If True (default), also unwrap classmethod and staticmethod
            decorators. If False, only unwrap partial and partialmethod decorators.

    Returns:
        The underlying function of the wrapped function.
    """
    # Define the types we want to check against as a single tuple.
    unwrap_types = (
        (property, cached_property)
        + ((partial, partialmethod) if unwrap_partial else ())
        + ((staticmethod, classmethod) if unwrap_class_static_method else ())
    )

    while isinstance(func, unwrap_types):
        if unwrap_class_static_method and isinstance(func, (classmethod, staticmethod)):
            func = func.__func__
        elif isinstance(func, (partial, partialmethod)):
            func = func.func
        elif isinstance(func, property):
            func = func.fget  # arbitrary choice, convenient for computed fields
        else:
            # Make coverage happy as it can only get here in the last possible case
            assert isinstance(func, cached_property)
            func = func.func  # type: ignore

    return func


def get_function_return_type(
    func: Any,
    explicit_return_type: Any,
    globalns: GlobalsNamespace | None = None,
    localns: MappingNamespace | None = None,
) -> Any:
    """Get the function return type.

    It gets the return type from the type annotation if `explicit_return_type` is `None`.
    Otherwise, it returns `explicit_return_type`.

    Args:
        func: The function to get its return type.
        explicit_return_type: The explicit return type.
        globalns: The globals namespace to use during type annotation evaluation.
        localns: The locals namespace to use during type annotation evaluation.

    Returns:
        The function return type.
    """
    if explicit_return_type is PydanticUndefined:
        # try to get it from the type annotation
        hints = get_function_type_hints(
            unwrap_wrapped_function(func),
            include_keys={'return'},
            globalns=globalns,
            localns=localns,
        )
        return hints.get('return', PydanticUndefined)
    else:
        return explicit_return_type


def count_positional_required_params(sig: Signature) -> int:
    """Get the number of positional (required) arguments of a signature.

    This function should only be used to inspect signatures of validation and serialization functions.
    The first argument (the value being serialized or validated) is counted as a required argument
    even if a default value exists.

    Returns:
        The number of positional arguments of a signature.
    """
    parameters = list(sig.parameters.values())
    return sum(
        1
        for param in parameters
        if can_be_positional(param)
        # First argument is the value being validated/serialized, and can have a default value
        # (e.g. `float`, which has signature `(x=0, /)`). We assume other parameters (the info arg
        # for instance) should be required, and thus without any default value.
        and (param.default is Parameter.empty or param is parameters[0])
    )


def ensure_property(f: Any) -> Any:
    """Ensure that a function is a `property` or `cached_property`, or is a valid descriptor.

    Args:
        f: The function to check.

    Returns:
        The function, or a `property` or `cached_property` instance wrapping the function.
    """
    if ismethoddescriptor(f) or isdatadescriptor(f):
        return f
    else:
        return property(f)
