"""Logic for interacting with type annotations, mostly extensions, shims and hacks to wrap Python's typing module."""

from __future__ import annotations

import collections.abc
import re
import sys
import types
import typing
import warnings
from functools import lru_cache, partial
from typing import Any, Callable

import typing_extensions
from typing_extensions import TypeIs, deprecated, get_args, get_origin

from ._namespace_utils import GlobalsNamespace, MappingNamespace, NsResolver, get_module_ns_of

if sys.version_info < (3, 10):
    NoneType = type(None)
    EllipsisType = type(Ellipsis)
else:
    from types import EllipsisType as EllipsisType
    from types import NoneType as NoneType


# See https://typing-extensions.readthedocs.io/en/latest/#runtime-use-of-types:


@lru_cache(maxsize=None)
def _get_typing_objects_by_name_of(name: str) -> tuple[Any, ...]:
    """Get the member named `name` from both `typing` and `typing-extensions` (if it exists)."""
    result = tuple(getattr(module, name) for module in (typing, typing_extensions) if hasattr(module, name))
    if not result:
        raise ValueError(f'Neither `typing` nor `typing_extensions` has an object called {name!r}')
    return result


# As suggested by the `typing-extensions` documentation, we could apply caching to this method,
# but it doesn't seem to improve performance. This also requires `obj` to be hashable, which
# might not be always the case:
def _is_typing_name(obj: object, name: str) -> bool:
    """Return whether `obj` is the member of the typing modules (includes the `typing-extensions` one) named `name`."""
    # Using `any()` is slower:
    for thing in _get_typing_objects_by_name_of(name):
        if obj is thing:
            return True
    return False


def is_any(tp: Any, /) -> bool:
    """Return whether the provided argument is the `Any` special form.

    ```python {test="skip" lint="skip"}
    is_any(Any)
    #> True
    ```
    """
    return _is_typing_name(tp, name='Any')


def is_union(tp: Any, /) -> bool:
    """Return whether the provided argument is a `Union` special form.

    ```python {test="skip" lint="skip"}
    is_union(Union[int, str])
    #> True
    is_union(int | str)
    #> False
    ```
    """
    return _is_typing_name(get_origin(tp), name='Union')


def is_literal(tp: Any, /) -> bool:
    """Return whether the provided argument is a `Literal` special form.

    ```python {test="skip" lint="skip"}
    is_literal(Literal[42])
    #> True
    ```
    """
    return _is_typing_name(get_origin(tp), name='Literal')


# TODO remove and replace with `get_args` when we drop support for Python 3.8
# (see https://docs.python.org/3/whatsnew/3.9.html#id4).
def literal_values(tp: Any, /) -> list[Any]:
    """Return the values contained in the provided `Literal` special form."""
    if not is_literal(tp):
        return [tp]

    values = get_args(tp)
    return [x for value in values for x in literal_values(value)]


def is_annotated(tp: Any, /) -> bool:
    """Return whether the provided argument is a `Annotated` special form.

    ```python {test="skip" lint="skip"}
    is_annotated(Annotated[int, ...])
    #> True
    ```
    """
    return _is_typing_name(get_origin(tp), name='Annotated')


def annotated_type(tp: Any, /) -> Any | None:
    """Return the type of the `Annotated` special form, or `None`."""
    return get_args(tp)[0] if is_annotated(tp) else None


def is_unpack(tp: Any, /) -> bool:
    """Return whether the provided argument is a `Unpack` special form.

    ```python {test="skip" lint="skip"}
    is_unpack(Unpack[Ts])
    #> True
    ```
    """
    return _is_typing_name(get_origin(tp), name='Unpack')


def unpack_type(tp: Any, /) -> Any | None:
    """Return the type wrapped by the `Unpack` special form, or `None`."""
    return get_args(tp)[0] if is_unpack(tp) else None


def is_self(tp: Any, /) -> bool:
    """Return whether the provided argument is the `Self` special form.

    ```python {test="skip" lint="skip"}
    is_self(Self)
    #> True
    ```
    """
    return _is_typing_name(tp, name='Self')


def is_new_type(tp: Any, /) -> bool:
    """Return whether the provided argument is a `NewType`.

    ```python {test="skip" lint="skip"}
    is_new_type(NewType('MyInt', int))
    #> True
    ```
    """
    if sys.version_info < (3, 10):
        # On Python < 3.10, `typing.NewType` is a function
        return hasattr(tp, '__supertype__')
    else:
        return _is_typing_name(type(tp), name='NewType')


def is_hashable(tp: Any, /) -> bool:
    """Return whether the provided argument is the `Hashable` class.

    ```python {test="skip" lint="skip"}
    is_hashable(Hashable)
    #> True
    ```
    """
    # `get_origin` is documented as normalizing any typing-module aliases to `collections` classes,
    # hence the second check:
    return tp is collections.abc.Hashable or get_origin(tp) is collections.abc.Hashable


def is_callable(tp: Any, /) -> bool:
    """Return whether the provided argument is a `Callable`, parametrized or not.

    ```python {test="skip" lint="skip"}
    is_callable(Callable[[int], str])
    #> True
    is_callable(typing.Callable)
    #> True
    is_callable(collections.abc.Callable)
    #> True
    ```
    """
    # `get_origin` is documented as normalizing any typing-module aliases to `collections` classes,
    # hence the second check:
    return tp is collections.abc.Callable or get_origin(tp) is collections.abc.Callable


_PARAMSPEC_TYPES: tuple[type[typing_extensions.ParamSpec], ...] = (typing_extensions.ParamSpec,)
if sys.version_info >= (3, 10):
    _PARAMSPEC_TYPES = (*_PARAMSPEC_TYPES, typing.ParamSpec)  # pyright: ignore[reportAssignmentType]


def is_paramspec(tp: Any, /) -> bool:
    """Return whether the provided argument is a `ParamSpec`.

    ```python {test="skip" lint="skip"}
    P = ParamSpec('P')
    is_paramspec(P)
    #> True
    ```
    """
    return isinstance(tp, _PARAMSPEC_TYPES)


_TYPE_ALIAS_TYPES: tuple[type[typing_extensions.TypeAliasType], ...] = (typing_extensions.TypeAliasType,)
if sys.version_info >= (3, 12):
    _TYPE_ALIAS_TYPES = (*_TYPE_ALIAS_TYPES, typing.TypeAliasType)


def is_type_alias_type(tp: Any, /) -> TypeIs[typing_extensions.TypeAliasType]:
    """Return whether the provided argument is an instance of `TypeAliasType`.

    ```python {test="skip" lint="skip"}
    type Int = int
    is_type_alias_type(Int)
    #> True
    Str = TypeAliasType('Str', str)
    is_type_alias_type(Str)
    #> True
    ```
    """
    return isinstance(tp, _TYPE_ALIAS_TYPES)


def is_classvar(tp: Any, /) -> bool:
    """Return whether the provided argument is a `ClassVar` special form, parametrized or not.

    Note that in most cases, you will want to use the `is_classvar_annotation` function,
    which is used to check if an annotation (in the context of a Pydantic model or dataclass)
    should be treated as being a class variable.

    ```python {test="skip" lint="skip"}
    is_classvar(ClassVar[int])
    #> True
    is_classvar(ClassVar)
    #> True
    """
    # ClassVar is not necessarily parametrized:
    return _is_typing_name(tp, name='ClassVar') or _is_typing_name(get_origin(tp), name='ClassVar')


_classvar_re = re.compile(r'((\w+\.)?Annotated\[)?(\w+\.)?ClassVar\[')


def is_classvar_annotation(tp: Any, /) -> bool:
    """Return whether the provided argument represents a class variable annotation.

    Although not explicitly stated by the typing specification, `ClassVar` can be used
    inside `Annotated` and as such, this function checks for this specific scenario.

    Because this function is used to detect class variables before evaluating forward references
    (or because evaluation failed), we also implement a naive regex match implementation. This is
    required because class variables are inspected before fields are collected, so we try to be
    as accurate as possible.
    """
    if is_classvar(tp) or (anntp := annotated_type(tp)) is not None and is_classvar(anntp):
        return True

    str_ann: str | None = None
    if isinstance(tp, typing.ForwardRef):
        str_ann = tp.__forward_arg__
    if isinstance(tp, str):
        str_ann = tp

    if str_ann is not None and _classvar_re.match(str_ann):
        # stdlib dataclasses do something similar, although a bit more advanced
        # (see `dataclass._is_type`).
        return True

    return False


# TODO implement `is_finalvar_annotation` as Final can be wrapped with other special forms:
def is_finalvar(tp: Any, /) -> bool:
    """Return whether the provided argument is a `Final` special form, parametrized or not.

    ```python {test="skip" lint="skip"}
    is_finalvar(Final[int])
    #> True
    is_finalvar(Final)
    #> True
    """
    # Final is not necessarily parametrized:
    return _is_typing_name(tp, name='Final') or _is_typing_name(get_origin(tp), name='Final')


def is_required(tp: Any, /) -> bool:
    """Return whether the provided argument is a `Required` special form.

    ```python {test="skip" lint="skip"}
    is_required(Required[int])
    #> True
    """
    return _is_typing_name(get_origin(tp), name='Required')


def is_not_required(tp: Any, /) -> bool:
    """Return whether the provided argument is a `NotRequired` special form.

    ```python {test="skip" lint="skip"}
    is_required(Required[int])
    #> True
    """
    return _is_typing_name(get_origin(tp), name='NotRequired')


def is_no_return(tp: Any, /) -> bool:
    """Return whether the provided argument is the `NoReturn` special form.

    ```python {test="skip" lint="skip"}
    is_no_return(NoReturn)
    #> True
    ```
    """
    return _is_typing_name(tp, name='NoReturn')


def is_never(tp: Any, /) -> bool:
    """Return whether the provided argument is the `Never` special form.

    ```python {test="skip" lint="skip"}
    is_never(Never)
    #> True
    ```
    """
    return _is_typing_name(tp, name='Never')


_DEPRECATED_TYPES: tuple[type[typing_extensions.deprecated], ...] = (typing_extensions.deprecated,)
if hasattr(warnings, 'deprecated'):
    _DEPRECATED_TYPES = (*_DEPRECATED_TYPES, warnings.deprecated)  # pyright: ignore[reportAttributeAccessIssue]


def is_deprecated_instance(obj: Any, /) -> TypeIs[deprecated]:
    """Return whether the argument is an instance of the `warnings.deprecated` class or the `typing_extensions` backport."""
    return isinstance(obj, _DEPRECATED_TYPES)


_NONE_TYPES: tuple[Any, ...] = (None, NoneType, typing.Literal[None], typing_extensions.Literal[None])


def is_none_type(tp: Any, /) -> bool:
    """Return whether the argument represents the `None` type as part of an annotation.

    ```python {test="skip" lint="skip"}
    is_none_type(None)
    #> True
    is_none_type(NoneType)
    #> True
    is_none_type(Literal[None])
    #> True
    is_none_type(type[None])
    #> False
    """
    return tp in _NONE_TYPES


def is_namedtuple(tp: Any, /) -> bool:
    """Return whether the provided argument is a named tuple class.

    The class can be created using `typing.NamedTuple` or `collections.namedtuple`.
    Parametrized generic classes are *not* assumed to be named tuples.
    """
    from ._utils import lenient_issubclass  # circ. import

    return lenient_issubclass(tp, tuple) and hasattr(tp, '_fields')


if sys.version_info < (3, 9):

    def is_zoneinfo_type(tp: Any, /) -> bool:
        """Return whether the provided argument is the `zoneinfo.ZoneInfo` type."""
        return False

else:
    from zoneinfo import ZoneInfo

    def is_zoneinfo_type(tp: Any, /) -> TypeIs[type[ZoneInfo]]:
        """Return whether the provided argument is the `zoneinfo.ZoneInfo` type."""
        return tp is ZoneInfo


if sys.version_info < (3, 10):

    def origin_is_union(tp: Any, /) -> bool:
        """Return whether the provided argument is the `Union` special form."""
        return _is_typing_name(tp, name='Union')

    def is_generic_alias(type_: type[Any]) -> bool:
        return isinstance(type_, typing._GenericAlias)  # pyright: ignore[reportAttributeAccessIssue]

else:

    def origin_is_union(tp: Any, /) -> bool:
        """Return whether the provided argument is the `Union` special form or the `UnionType`."""
        return _is_typing_name(tp, name='Union') or tp is types.UnionType

    def is_generic_alias(tp: Any, /) -> bool:
        return isinstance(tp, (types.GenericAlias, typing._GenericAlias))  # pyright: ignore[reportAttributeAccessIssue]


# TODO: Ideally, we should avoid relying on the private `typing` constructs:

if sys.version_info < (3, 9):
    WithArgsTypes: tuple[Any, ...] = (typing._GenericAlias,)  # pyright: ignore[reportAttributeAccessIssue]
elif sys.version_info < (3, 10):
    WithArgsTypes: tuple[Any, ...] = (typing._GenericAlias, types.GenericAlias)  # pyright: ignore[reportAttributeAccessIssue]
else:
    WithArgsTypes: tuple[Any, ...] = (typing._GenericAlias, types.GenericAlias, types.UnionType)  # pyright: ignore[reportAttributeAccessIssue]


# Similarly, we shouldn't rely on this `_Final` class, which is even more private than `_GenericAlias`:
typing_base: Any = typing._Final  # pyright: ignore[reportAttributeAccessIssue]


### Annotation evaluations functions:


def parent_frame_namespace(*, parent_depth: int = 2, force: bool = False) -> dict[str, Any] | None:
    """We allow use of items in parent namespace to get around the issue with `get_type_hints` only looking in the
    global module namespace. See https://github.com/pydantic/pydantic/issues/2678#issuecomment-1008139014 -> Scope
    and suggestion at the end of the next comment by @gvanrossum.

    WARNING 1: it matters exactly where this is called. By default, this function will build a namespace from the
    parent of where it is called.

    WARNING 2: this only looks in the parent namespace, not other parents since (AFAIK) there's no way to collect a
    dict of exactly what's in scope. Using `f_back` would work sometimes but would be very wrong and confusing in many
    other cases. See https://discuss.python.org/t/is-there-a-way-to-access-parent-nested-namespaces/20659.

    There are some cases where we want to force fetching the parent namespace, ex: during a `model_rebuild` call.
    In this case, we want both the namespace of the class' module, if applicable, and the parent namespace of the
    module where the rebuild is called.

    In other cases, like during initial schema build, if a class is defined at the top module level, we don't need to
    fetch that module's namespace, because the class' __module__ attribute can be used to access the parent namespace.
    This is done in `_namespace_utils.get_module_ns_of`. Thus, there's no need to cache the parent frame namespace in this case.
    """
    frame = sys._getframe(parent_depth)

    # note, we don't copy frame.f_locals here (or during the last return call), because we don't expect the namespace to be modified down the line
    # if this becomes a problem, we could implement some sort of frozen mapping structure to enforce this
    if force:
        return frame.f_locals

    # if either of the following conditions are true, the class is defined at the top module level
    # to better understand why we need both of these checks, see
    # https://github.com/pydantic/pydantic/pull/10113#discussion_r1714981531
    if frame.f_back is None or frame.f_code.co_name == '<module>':
        return None

    return frame.f_locals


def get_cls_type_hints(
    obj: type[Any], *, ns_resolver: NsResolver | None = None, lenient: bool = False
) -> dict[str, Any]:
    """Collect annotations from a class, including those from parent classes.

    Args:
        obj: The class to inspect.
        ns_resolver: A namespace resolver instance to use. Defaults to an empty instance.
        lenient: Whether to keep unresolvable annotations as is or re-raise the `NameError` exception. Default: re-raise.
    """
    hints = {}
    ns_resolver = ns_resolver or NsResolver()

    for base in reversed(obj.__mro__):
        ann: dict[str, Any] | None = base.__dict__.get('__annotations__')
        if not ann or isinstance(ann, types.GetSetDescriptorType):
            continue
        with ns_resolver.push(base):
            globalns, localns = ns_resolver.types_namespace
            for name, value in ann.items():
                hints[name] = eval_type(value, globalns, localns, lenient=lenient)
    return hints


def eval_type(
    value: Any,
    globalns: GlobalsNamespace | None = None,
    localns: MappingNamespace | None = None,
    *,
    lenient: bool = False,
) -> Any:
    """Evaluate the annotation using the provided namespaces.

    Args:
        value: The value to evaluate. If `None`, it will be replaced by `type[None]`. If an instance
            of `str`, it will be converted to a `ForwardRef`.
        localns: The global namespace to use during annotation evaluation.
        globalns: The local namespace to use during annotation evaluation.
        lenient: Whether to keep unresolvable annotations as is or re-raise the `NameError` exception. Default: re-raise.
    """
    if value is None:
        value = NoneType
    elif isinstance(value, str):
        value = _make_forward_ref(value, is_argument=False, is_class=True)

    try:
        return eval_type_backport(value, globalns, localns)
    except NameError:
        if not lenient:
            raise
        # the point of this function is to be tolerant to this case
        return value


@deprecated(
    '`eval_type_lenient` is deprecated, use `eval_type` with `lenient=True` instead.',
    category=None,
)
def eval_type_lenient(
    value: Any,
    globalns: GlobalsNamespace | None = None,
    localns: MappingNamespace | None = None,
) -> Any:
    return eval_type(value, globalns, localns, lenient=True)


def eval_type_backport(
    value: Any,
    globalns: GlobalsNamespace | None = None,
    localns: MappingNamespace | None = None,
    type_params: tuple[Any, ...] | None = None,
) -> Any:
    """An enhanced version of `typing._eval_type` which will fall back to using the `eval_type_backport`
    package if it's installed to let older Python versions use newer typing constructs.

    Specifically, this transforms `X | Y` into `typing.Union[X, Y]` and `list[X]` into `typing.List[X]`
    (as well as all the types made generic in PEP 585) if the original syntax is not supported in the
    current Python version.

    This function will also display a helpful error if the value passed fails to evaluate.
    """
    try:
        return _eval_type_backport(value, globalns, localns, type_params)
    except TypeError as e:
        if 'Unable to evaluate type annotation' in str(e):
            raise

        # If it is a `TypeError` and value isn't a `ForwardRef`, it would have failed during annotation definition.
        # Thus we assert here for type checking purposes:
        assert isinstance(value, typing.ForwardRef)

        message = f'Unable to evaluate type annotation {value.__forward_arg__!r}.'
        if sys.version_info >= (3, 11):
            e.add_note(message)
            raise
        else:
            raise TypeError(message) from e


def _eval_type_backport(
    value: Any,
    globalns: GlobalsNamespace | None = None,
    localns: MappingNamespace | None = None,
    type_params: tuple[Any, ...] | None = None,
) -> Any:
    try:
        return _eval_type(value, globalns, localns, type_params)
    except TypeError as e:
        if not (isinstance(value, typing.ForwardRef) and is_backport_fixable_error(e)):
            raise

        try:
            from eval_type_backport import eval_type_backport
        except ImportError:
            raise TypeError(
                f'Unable to evaluate type annotation {value.__forward_arg__!r}. If you are making use '
                'of the new typing syntax (unions using `|` since Python 3.10 or builtins subscripting '
                'since Python 3.9), you should either replace the use of new syntax with the existing '
                '`typing` constructs or install the `eval_type_backport` package.'
            ) from e

        return eval_type_backport(
            value,
            globalns,
            localns,  # pyright: ignore[reportArgumentType], waiting on a new `eval_type_backport` release.
            try_default=False,
        )


def _eval_type(
    value: Any,
    globalns: GlobalsNamespace | None = None,
    localns: MappingNamespace | None = None,
    type_params: tuple[Any, ...] | None = None,
) -> Any:
    if sys.version_info >= (3, 13):
        return typing._eval_type(  # type: ignore
            value, globalns, localns, type_params=type_params
        )
    else:
        return typing._eval_type(  # type: ignore
            value, globalns, localns
        )


def is_backport_fixable_error(e: TypeError) -> bool:
    msg = str(e)

    return (
        sys.version_info < (3, 10)
        and msg.startswith('unsupported operand type(s) for |: ')
        or sys.version_info < (3, 9)
        and "' object is not subscriptable" in msg
    )


def get_function_type_hints(
    function: Callable[..., Any],
    *,
    include_keys: set[str] | None = None,
    globalns: GlobalsNamespace | None = None,
    localns: MappingNamespace | None = None,
) -> dict[str, Any]:
    """Return type hints for a function.

    This is similar to the `typing.get_type_hints` function, with a few differences:
    - Support `functools.partial` by using the underlying `func` attribute.
    - If `function` happens to be a built-in type (e.g. `int`), assume it doesn't have annotations
      but specify the `return` key as being the actual type.
    - Do not wrap type annotation of a parameter with `Optional` if it has a default value of `None`
      (related bug: https://github.com/python/cpython/issues/90353, only fixed in 3.11+).
    """
    try:
        if isinstance(function, partial):
            annotations = function.func.__annotations__
        else:
            annotations = function.__annotations__
    except AttributeError:
        type_hints = get_type_hints(function)
        if isinstance(function, type):
            # `type[...]` is a callable, which returns an instance of itself.
            # At some point, we might even look into the return type of `__new__`
            # if it returns something else.
            type_hints.setdefault('return', function)
        return type_hints

    if globalns is None:
        globalns = get_module_ns_of(function)
    type_params: tuple[Any, ...] | None = None
    if localns is None:
        # If localns was specified, it is assumed to already contain type params. This is because
        # Pydantic has more advanced logic to do so (see `_namespace_utils.ns_for_function`).
        type_params = getattr(function, '__type_params__', ())

    type_hints = {}
    for name, value in annotations.items():
        if include_keys is not None and name not in include_keys:
            continue
        if value is None:
            value = NoneType
        elif isinstance(value, str):
            value = _make_forward_ref(value)

        type_hints[name] = eval_type_backport(value, globalns, localns, type_params)

    return type_hints


if sys.version_info < (3, 9, 8) or (3, 10) <= sys.version_info < (3, 10, 1):

    def _make_forward_ref(
        arg: Any,
        is_argument: bool = True,
        *,
        is_class: bool = False,
    ) -> typing.ForwardRef:
        """Wrapper for ForwardRef that accounts for the `is_class` argument missing in older versions.
        The `module` argument is omitted as it breaks <3.9.8, =3.10.0 and isn't used in the calls below.

        See https://github.com/python/cpython/pull/28560 for some background.
        The backport happened on 3.9.8, see:
        https://github.com/pydantic/pydantic/discussions/6244#discussioncomment-6275458,
        and on 3.10.1 for the 3.10 branch, see:
        https://github.com/pydantic/pydantic/issues/6912

        Implemented as EAFP with memory.
        """
        return typing.ForwardRef(arg, is_argument)

else:
    _make_forward_ref = typing.ForwardRef


if sys.version_info >= (3, 10):
    get_type_hints = typing.get_type_hints

else:
    """
    For older versions of python, we have a custom implementation of `get_type_hints` which is a close as possible to
    the implementation in CPython 3.10.8.
    """

    @typing.no_type_check
    def get_type_hints(  # noqa: C901
        obj: Any,
        globalns: dict[str, Any] | None = None,
        localns: dict[str, Any] | None = None,
        include_extras: bool = False,
    ) -> dict[str, Any]:  # pragma: no cover
        """Taken verbatim from python 3.10.8 unchanged, except:
        * type annotations of the function definition above.
        * prefixing `typing.` where appropriate
        * Use `_make_forward_ref` instead of `typing.ForwardRef` to handle the `is_class` argument.

        https://github.com/python/cpython/blob/aaaf5174241496afca7ce4d4584570190ff972fe/Lib/typing.py#L1773-L1875

        DO NOT CHANGE THIS METHOD UNLESS ABSOLUTELY NECESSARY.
        ======================================================

        Return type hints for an object.

        This is often the same as obj.__annotations__, but it handles
        forward references encoded as string literals, adds Optional[t] if a
        default value equal to None is set and recursively replaces all
        'Annotated[T, ...]' with 'T' (unless 'include_extras=True').

        The argument may be a module, class, method, or function. The annotations
        are returned as a dictionary. For classes, annotations include also
        inherited members.

        TypeError is raised if the argument is not of a type that can contain
        annotations, and an empty dictionary is returned if no annotations are
        present.

        BEWARE -- the behavior of globalns and localns is counterintuitive
        (unless you are familiar with how eval() and exec() work).  The
        search order is locals first, then globals.

        - If no dict arguments are passed, an attempt is made to use the
          globals from obj (or the respective module's globals for classes),
          and these are also used as the locals.  If the object does not appear
          to have globals, an empty dictionary is used.  For classes, the search
          order is globals first then locals.

        - If one dict argument is passed, it is used for both globals and
          locals.

        - If two dict arguments are passed, they specify globals and
          locals, respectively.
        """
        if getattr(obj, '__no_type_check__', None):
            return {}
        # Classes require a special treatment.
        if isinstance(obj, type):
            hints = {}
            for base in reversed(obj.__mro__):
                if globalns is None:
                    base_globals = getattr(sys.modules.get(base.__module__, None), '__dict__', {})
                else:
                    base_globals = globalns
                ann = base.__dict__.get('__annotations__', {})
                if isinstance(ann, types.GetSetDescriptorType):
                    ann = {}
                base_locals = dict(vars(base)) if localns is None else localns
                if localns is None and globalns is None:
                    # This is surprising, but required.  Before Python 3.10,
                    # get_type_hints only evaluated the globalns of
                    # a class.  To maintain backwards compatibility, we reverse
                    # the globalns and localns order so that eval() looks into
                    # *base_globals* first rather than *base_locals*.
                    # This only affects ForwardRefs.
                    base_globals, base_locals = base_locals, base_globals
                for name, value in ann.items():
                    if value is None:
                        value = type(None)
                    if isinstance(value, str):
                        value = _make_forward_ref(value, is_argument=False, is_class=True)

                    value = eval_type_backport(value, base_globals, base_locals)
                    hints[name] = value
            if not include_extras and hasattr(typing, '_strip_annotations'):
                return {
                    k: typing._strip_annotations(t)  # type: ignore
                    for k, t in hints.items()
                }
            else:
                return hints

        if globalns is None:
            if isinstance(obj, types.ModuleType):
                globalns = obj.__dict__
            else:
                nsobj = obj
                # Find globalns for the unwrapped object.
                while hasattr(nsobj, '__wrapped__'):
                    nsobj = nsobj.__wrapped__
                globalns = getattr(nsobj, '__globals__', {})
            if localns is None:
                localns = globalns
        elif localns is None:
            localns = globalns
        hints = getattr(obj, '__annotations__', None)
        if hints is None:
            # Return empty annotations for something that _could_ have them.
            if isinstance(obj, typing._allowed_types):  # type: ignore
                return {}
            else:
                raise TypeError(f'{obj!r} is not a module, class, method, ' 'or function.')
        defaults = typing._get_defaults(obj)  # type: ignore
        hints = dict(hints)
        for name, value in hints.items():
            if value is None:
                value = type(None)
            if isinstance(value, str):
                # class-level forward refs were handled above, this must be either
                # a module-level annotation or a function argument annotation

                value = _make_forward_ref(
                    value,
                    is_argument=not isinstance(obj, types.ModuleType),
                    is_class=False,
                )
            value = eval_type_backport(value, globalns, localns)
            if name in defaults and defaults[name] is None:
                value = typing.Optional[value]
            hints[name] = value
        return hints if include_extras else {k: typing._strip_annotations(t) for k, t in hints.items()}  # type: ignore
