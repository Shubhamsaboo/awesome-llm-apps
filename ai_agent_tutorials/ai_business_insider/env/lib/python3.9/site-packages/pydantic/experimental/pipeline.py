"""Experimental pipeline API functionality. Be careful with this API, it's subject to change."""

from __future__ import annotations

import datetime
import operator
import re
import sys
from collections import deque
from collections.abc import Container
from dataclasses import dataclass
from decimal import Decimal
from functools import cached_property, partial
from typing import TYPE_CHECKING, Any, Callable, Generic, Pattern, Protocol, TypeVar, Union, overload

import annotated_types
from typing_extensions import Annotated

if TYPE_CHECKING:
    from pydantic_core import core_schema as cs

    from pydantic import GetCoreSchemaHandler

from pydantic._internal._internal_dataclass import slots_true as _slots_true

if sys.version_info < (3, 10):
    EllipsisType = type(Ellipsis)
else:
    from types import EllipsisType

__all__ = ['validate_as', 'validate_as_deferred', 'transform']

_slots_frozen = {**_slots_true, 'frozen': True}


@dataclass(**_slots_frozen)
class _ValidateAs:
    tp: type[Any]
    strict: bool = False


@dataclass
class _ValidateAsDefer:
    func: Callable[[], type[Any]]

    @cached_property
    def tp(self) -> type[Any]:
        return self.func()


@dataclass(**_slots_frozen)
class _Transform:
    func: Callable[[Any], Any]


@dataclass(**_slots_frozen)
class _PipelineOr:
    left: _Pipeline[Any, Any]
    right: _Pipeline[Any, Any]


@dataclass(**_slots_frozen)
class _PipelineAnd:
    left: _Pipeline[Any, Any]
    right: _Pipeline[Any, Any]


@dataclass(**_slots_frozen)
class _Eq:
    value: Any


@dataclass(**_slots_frozen)
class _NotEq:
    value: Any


@dataclass(**_slots_frozen)
class _In:
    values: Container[Any]


@dataclass(**_slots_frozen)
class _NotIn:
    values: Container[Any]


_ConstraintAnnotation = Union[
    annotated_types.Le,
    annotated_types.Ge,
    annotated_types.Lt,
    annotated_types.Gt,
    annotated_types.Len,
    annotated_types.MultipleOf,
    annotated_types.Timezone,
    annotated_types.Interval,
    annotated_types.Predicate,
    # common predicates not included in annotated_types
    _Eq,
    _NotEq,
    _In,
    _NotIn,
    # regular expressions
    Pattern[str],
]


@dataclass(**_slots_frozen)
class _Constraint:
    constraint: _ConstraintAnnotation


_Step = Union[_ValidateAs, _ValidateAsDefer, _Transform, _PipelineOr, _PipelineAnd, _Constraint]

_InT = TypeVar('_InT')
_OutT = TypeVar('_OutT')
_NewOutT = TypeVar('_NewOutT')


class _FieldTypeMarker:
    pass


# TODO: ultimately, make this public, see https://github.com/pydantic/pydantic/pull/9459#discussion_r1628197626
# Also, make this frozen eventually, but that doesn't work right now because of the generic base
# Which attempts to modify __orig_base__ and such.
# We could go with a manual freeze, but that seems overkill for now.
@dataclass(**_slots_true)
class _Pipeline(Generic[_InT, _OutT]):
    """Abstract representation of a chain of validation, transformation, and parsing steps."""

    _steps: tuple[_Step, ...]

    def transform(
        self,
        func: Callable[[_OutT], _NewOutT],
    ) -> _Pipeline[_InT, _NewOutT]:
        """Transform the output of the previous step.

        If used as the first step in a pipeline, the type of the field is used.
        That is, the transformation is applied to after the value is parsed to the field's type.
        """
        return _Pipeline[_InT, _NewOutT](self._steps + (_Transform(func),))

    @overload
    def validate_as(self, tp: type[_NewOutT], *, strict: bool = ...) -> _Pipeline[_InT, _NewOutT]: ...

    @overload
    def validate_as(self, tp: EllipsisType, *, strict: bool = ...) -> _Pipeline[_InT, Any]:  # type: ignore
        ...

    def validate_as(self, tp: type[_NewOutT] | EllipsisType, *, strict: bool = False) -> _Pipeline[_InT, Any]:  # type: ignore
        """Validate / parse the input into a new type.

        If no type is provided, the type of the field is used.

        Types are parsed in Pydantic's `lax` mode by default,
        but you can enable `strict` mode by passing `strict=True`.
        """
        if isinstance(tp, EllipsisType):
            return _Pipeline[_InT, Any](self._steps + (_ValidateAs(_FieldTypeMarker, strict=strict),))
        return _Pipeline[_InT, _NewOutT](self._steps + (_ValidateAs(tp, strict=strict),))

    def validate_as_deferred(self, func: Callable[[], type[_NewOutT]]) -> _Pipeline[_InT, _NewOutT]:
        """Parse the input into a new type, deferring resolution of the type until the current class
        is fully defined.

        This is useful when you need to reference the class in it's own type annotations.
        """
        return _Pipeline[_InT, _NewOutT](self._steps + (_ValidateAsDefer(func),))

    # constraints
    @overload
    def constrain(self: _Pipeline[_InT, _NewOutGe], constraint: annotated_types.Ge) -> _Pipeline[_InT, _NewOutGe]: ...

    @overload
    def constrain(self: _Pipeline[_InT, _NewOutGt], constraint: annotated_types.Gt) -> _Pipeline[_InT, _NewOutGt]: ...

    @overload
    def constrain(self: _Pipeline[_InT, _NewOutLe], constraint: annotated_types.Le) -> _Pipeline[_InT, _NewOutLe]: ...

    @overload
    def constrain(self: _Pipeline[_InT, _NewOutLt], constraint: annotated_types.Lt) -> _Pipeline[_InT, _NewOutLt]: ...

    @overload
    def constrain(
        self: _Pipeline[_InT, _NewOutLen], constraint: annotated_types.Len
    ) -> _Pipeline[_InT, _NewOutLen]: ...

    @overload
    def constrain(
        self: _Pipeline[_InT, _NewOutT], constraint: annotated_types.MultipleOf
    ) -> _Pipeline[_InT, _NewOutT]: ...

    @overload
    def constrain(
        self: _Pipeline[_InT, _NewOutDatetime], constraint: annotated_types.Timezone
    ) -> _Pipeline[_InT, _NewOutDatetime]: ...

    @overload
    def constrain(self: _Pipeline[_InT, _OutT], constraint: annotated_types.Predicate) -> _Pipeline[_InT, _OutT]: ...

    @overload
    def constrain(
        self: _Pipeline[_InT, _NewOutInterval], constraint: annotated_types.Interval
    ) -> _Pipeline[_InT, _NewOutInterval]: ...

    @overload
    def constrain(self: _Pipeline[_InT, _OutT], constraint: _Eq) -> _Pipeline[_InT, _OutT]: ...

    @overload
    def constrain(self: _Pipeline[_InT, _OutT], constraint: _NotEq) -> _Pipeline[_InT, _OutT]: ...

    @overload
    def constrain(self: _Pipeline[_InT, _OutT], constraint: _In) -> _Pipeline[_InT, _OutT]: ...

    @overload
    def constrain(self: _Pipeline[_InT, _OutT], constraint: _NotIn) -> _Pipeline[_InT, _OutT]: ...

    @overload
    def constrain(self: _Pipeline[_InT, _NewOutT], constraint: Pattern[str]) -> _Pipeline[_InT, _NewOutT]: ...

    def constrain(self, constraint: _ConstraintAnnotation) -> Any:
        """Constrain a value to meet a certain condition.

        We support most conditions from `annotated_types`, as well as regular expressions.

        Most of the time you'll be calling a shortcut method like `gt`, `lt`, `len`, etc
        so you don't need to call this directly.
        """
        return _Pipeline[_InT, _OutT](self._steps + (_Constraint(constraint),))

    def predicate(self: _Pipeline[_InT, _NewOutT], func: Callable[[_NewOutT], bool]) -> _Pipeline[_InT, _NewOutT]:
        """Constrain a value to meet a certain predicate."""
        return self.constrain(annotated_types.Predicate(func))

    def gt(self: _Pipeline[_InT, _NewOutGt], gt: _NewOutGt) -> _Pipeline[_InT, _NewOutGt]:
        """Constrain a value to be greater than a certain value."""
        return self.constrain(annotated_types.Gt(gt))

    def lt(self: _Pipeline[_InT, _NewOutLt], lt: _NewOutLt) -> _Pipeline[_InT, _NewOutLt]:
        """Constrain a value to be less than a certain value."""
        return self.constrain(annotated_types.Lt(lt))

    def ge(self: _Pipeline[_InT, _NewOutGe], ge: _NewOutGe) -> _Pipeline[_InT, _NewOutGe]:
        """Constrain a value to be greater than or equal to a certain value."""
        return self.constrain(annotated_types.Ge(ge))

    def le(self: _Pipeline[_InT, _NewOutLe], le: _NewOutLe) -> _Pipeline[_InT, _NewOutLe]:
        """Constrain a value to be less than or equal to a certain value."""
        return self.constrain(annotated_types.Le(le))

    def len(self: _Pipeline[_InT, _NewOutLen], min_len: int, max_len: int | None = None) -> _Pipeline[_InT, _NewOutLen]:
        """Constrain a value to have a certain length."""
        return self.constrain(annotated_types.Len(min_len, max_len))

    @overload
    def multiple_of(self: _Pipeline[_InT, _NewOutDiv], multiple_of: _NewOutDiv) -> _Pipeline[_InT, _NewOutDiv]: ...

    @overload
    def multiple_of(self: _Pipeline[_InT, _NewOutMod], multiple_of: _NewOutMod) -> _Pipeline[_InT, _NewOutMod]: ...

    def multiple_of(self: _Pipeline[_InT, Any], multiple_of: Any) -> _Pipeline[_InT, Any]:
        """Constrain a value to be a multiple of a certain number."""
        return self.constrain(annotated_types.MultipleOf(multiple_of))

    def eq(self: _Pipeline[_InT, _OutT], value: _OutT) -> _Pipeline[_InT, _OutT]:
        """Constrain a value to be equal to a certain value."""
        return self.constrain(_Eq(value))

    def not_eq(self: _Pipeline[_InT, _OutT], value: _OutT) -> _Pipeline[_InT, _OutT]:
        """Constrain a value to not be equal to a certain value."""
        return self.constrain(_NotEq(value))

    def in_(self: _Pipeline[_InT, _OutT], values: Container[_OutT]) -> _Pipeline[_InT, _OutT]:
        """Constrain a value to be in a certain set."""
        return self.constrain(_In(values))

    def not_in(self: _Pipeline[_InT, _OutT], values: Container[_OutT]) -> _Pipeline[_InT, _OutT]:
        """Constrain a value to not be in a certain set."""
        return self.constrain(_NotIn(values))

    # timezone methods
    def datetime_tz_naive(self: _Pipeline[_InT, datetime.datetime]) -> _Pipeline[_InT, datetime.datetime]:
        return self.constrain(annotated_types.Timezone(None))

    def datetime_tz_aware(self: _Pipeline[_InT, datetime.datetime]) -> _Pipeline[_InT, datetime.datetime]:
        return self.constrain(annotated_types.Timezone(...))

    def datetime_tz(
        self: _Pipeline[_InT, datetime.datetime], tz: datetime.tzinfo
    ) -> _Pipeline[_InT, datetime.datetime]:
        return self.constrain(annotated_types.Timezone(tz))  # type: ignore

    def datetime_with_tz(
        self: _Pipeline[_InT, datetime.datetime], tz: datetime.tzinfo | None
    ) -> _Pipeline[_InT, datetime.datetime]:
        return self.transform(partial(datetime.datetime.replace, tzinfo=tz))

    # string methods
    def str_lower(self: _Pipeline[_InT, str]) -> _Pipeline[_InT, str]:
        return self.transform(str.lower)

    def str_upper(self: _Pipeline[_InT, str]) -> _Pipeline[_InT, str]:
        return self.transform(str.upper)

    def str_title(self: _Pipeline[_InT, str]) -> _Pipeline[_InT, str]:
        return self.transform(str.title)

    def str_strip(self: _Pipeline[_InT, str]) -> _Pipeline[_InT, str]:
        return self.transform(str.strip)

    def str_pattern(self: _Pipeline[_InT, str], pattern: str) -> _Pipeline[_InT, str]:
        return self.constrain(re.compile(pattern))

    def str_contains(self: _Pipeline[_InT, str], substring: str) -> _Pipeline[_InT, str]:
        return self.predicate(lambda v: substring in v)

    def str_starts_with(self: _Pipeline[_InT, str], prefix: str) -> _Pipeline[_InT, str]:
        return self.predicate(lambda v: v.startswith(prefix))

    def str_ends_with(self: _Pipeline[_InT, str], suffix: str) -> _Pipeline[_InT, str]:
        return self.predicate(lambda v: v.endswith(suffix))

    # operators
    def otherwise(self, other: _Pipeline[_OtherIn, _OtherOut]) -> _Pipeline[_InT | _OtherIn, _OutT | _OtherOut]:
        """Combine two validation chains, returning the result of the first chain if it succeeds, and the second chain if it fails."""
        return _Pipeline((_PipelineOr(self, other),))

    __or__ = otherwise

    def then(self, other: _Pipeline[_OutT, _OtherOut]) -> _Pipeline[_InT, _OtherOut]:
        """Pipe the result of one validation chain into another."""
        return _Pipeline((_PipelineAnd(self, other),))

    __and__ = then

    def __get_pydantic_core_schema__(self, source_type: Any, handler: GetCoreSchemaHandler) -> cs.CoreSchema:
        from pydantic_core import core_schema as cs

        queue = deque(self._steps)

        s = None

        while queue:
            step = queue.popleft()
            s = _apply_step(step, s, handler, source_type)

        s = s or cs.any_schema()
        return s

    def __supports_type__(self, _: _OutT) -> bool:
        raise NotImplementedError


validate_as = _Pipeline[Any, Any](()).validate_as
validate_as_deferred = _Pipeline[Any, Any](()).validate_as_deferred
transform = _Pipeline[Any, Any]((_ValidateAs(_FieldTypeMarker),)).transform


def _check_func(
    func: Callable[[Any], bool], predicate_err: str | Callable[[], str], s: cs.CoreSchema | None
) -> cs.CoreSchema:
    from pydantic_core import core_schema as cs

    def handler(v: Any) -> Any:
        if func(v):
            return v
        raise ValueError(f'Expected {predicate_err if isinstance(predicate_err, str) else predicate_err()}')

    if s is None:
        return cs.no_info_plain_validator_function(handler)
    else:
        return cs.no_info_after_validator_function(handler, s)


def _apply_step(step: _Step, s: cs.CoreSchema | None, handler: GetCoreSchemaHandler, source_type: Any) -> cs.CoreSchema:
    from pydantic_core import core_schema as cs

    if isinstance(step, _ValidateAs):
        s = _apply_parse(s, step.tp, step.strict, handler, source_type)
    elif isinstance(step, _ValidateAsDefer):
        s = _apply_parse(s, step.tp, False, handler, source_type)
    elif isinstance(step, _Transform):
        s = _apply_transform(s, step.func, handler)
    elif isinstance(step, _Constraint):
        s = _apply_constraint(s, step.constraint)
    elif isinstance(step, _PipelineOr):
        s = cs.union_schema([handler(step.left), handler(step.right)])
    else:
        assert isinstance(step, _PipelineAnd)
        s = cs.chain_schema([handler(step.left), handler(step.right)])
    return s


def _apply_parse(
    s: cs.CoreSchema | None,
    tp: type[Any],
    strict: bool,
    handler: GetCoreSchemaHandler,
    source_type: Any,
) -> cs.CoreSchema:
    from pydantic_core import core_schema as cs

    from pydantic import Strict

    if tp is _FieldTypeMarker:
        return handler(source_type)

    if strict:
        tp = Annotated[tp, Strict()]  # type: ignore

    if s and s['type'] == 'any':
        return handler(tp)
    else:
        return cs.chain_schema([s, handler(tp)]) if s else handler(tp)


def _apply_transform(
    s: cs.CoreSchema | None, func: Callable[[Any], Any], handler: GetCoreSchemaHandler
) -> cs.CoreSchema:
    from pydantic_core import core_schema as cs

    if s is None:
        return cs.no_info_plain_validator_function(func)

    if s['type'] == 'str':
        if func is str.strip:
            s = s.copy()
            s['strip_whitespace'] = True
            return s
        elif func is str.lower:
            s = s.copy()
            s['to_lower'] = True
            return s
        elif func is str.upper:
            s = s.copy()
            s['to_upper'] = True
            return s

    return cs.no_info_after_validator_function(func, s)


def _apply_constraint(  # noqa: C901
    s: cs.CoreSchema | None, constraint: _ConstraintAnnotation
) -> cs.CoreSchema:
    """Apply a single constraint to a schema."""
    if isinstance(constraint, annotated_types.Gt):
        gt = constraint.gt
        if s and s['type'] in {'int', 'float', 'decimal'}:
            s = s.copy()
            if s['type'] == 'int' and isinstance(gt, int):
                s['gt'] = gt
            elif s['type'] == 'float' and isinstance(gt, float):
                s['gt'] = gt
            elif s['type'] == 'decimal' and isinstance(gt, Decimal):
                s['gt'] = gt
        else:

            def check_gt(v: Any) -> bool:
                return v > gt

            s = _check_func(check_gt, f'> {gt}', s)
    elif isinstance(constraint, annotated_types.Ge):
        ge = constraint.ge
        if s and s['type'] in {'int', 'float', 'decimal'}:
            s = s.copy()
            if s['type'] == 'int' and isinstance(ge, int):
                s['ge'] = ge
            elif s['type'] == 'float' and isinstance(ge, float):
                s['ge'] = ge
            elif s['type'] == 'decimal' and isinstance(ge, Decimal):
                s['ge'] = ge

        def check_ge(v: Any) -> bool:
            return v >= ge

        s = _check_func(check_ge, f'>= {ge}', s)
    elif isinstance(constraint, annotated_types.Lt):
        lt = constraint.lt
        if s and s['type'] in {'int', 'float', 'decimal'}:
            s = s.copy()
            if s['type'] == 'int' and isinstance(lt, int):
                s['lt'] = lt
            elif s['type'] == 'float' and isinstance(lt, float):
                s['lt'] = lt
            elif s['type'] == 'decimal' and isinstance(lt, Decimal):
                s['lt'] = lt

        def check_lt(v: Any) -> bool:
            return v < lt

        s = _check_func(check_lt, f'< {lt}', s)
    elif isinstance(constraint, annotated_types.Le):
        le = constraint.le
        if s and s['type'] in {'int', 'float', 'decimal'}:
            s = s.copy()
            if s['type'] == 'int' and isinstance(le, int):
                s['le'] = le
            elif s['type'] == 'float' and isinstance(le, float):
                s['le'] = le
            elif s['type'] == 'decimal' and isinstance(le, Decimal):
                s['le'] = le

        def check_le(v: Any) -> bool:
            return v <= le

        s = _check_func(check_le, f'<= {le}', s)
    elif isinstance(constraint, annotated_types.Len):
        min_len = constraint.min_length
        max_len = constraint.max_length

        if s and s['type'] in {'str', 'list', 'tuple', 'set', 'frozenset', 'dict'}:
            assert (
                s['type'] == 'str'
                or s['type'] == 'list'
                or s['type'] == 'tuple'
                or s['type'] == 'set'
                or s['type'] == 'dict'
                or s['type'] == 'frozenset'
            )
            s = s.copy()
            if min_len != 0:
                s['min_length'] = min_len
            if max_len is not None:
                s['max_length'] = max_len

        def check_len(v: Any) -> bool:
            if max_len is not None:
                return (min_len <= len(v)) and (len(v) <= max_len)
            return min_len <= len(v)

        s = _check_func(check_len, f'length >= {min_len} and length <= {max_len}', s)
    elif isinstance(constraint, annotated_types.MultipleOf):
        multiple_of = constraint.multiple_of
        if s and s['type'] in {'int', 'float', 'decimal'}:
            s = s.copy()
            if s['type'] == 'int' and isinstance(multiple_of, int):
                s['multiple_of'] = multiple_of
            elif s['type'] == 'float' and isinstance(multiple_of, float):
                s['multiple_of'] = multiple_of
            elif s['type'] == 'decimal' and isinstance(multiple_of, Decimal):
                s['multiple_of'] = multiple_of

        def check_multiple_of(v: Any) -> bool:
            return v % multiple_of == 0

        s = _check_func(check_multiple_of, f'% {multiple_of} == 0', s)
    elif isinstance(constraint, annotated_types.Timezone):
        tz = constraint.tz

        if tz is ...:
            if s and s['type'] == 'datetime':
                s = s.copy()
                s['tz_constraint'] = 'aware'
            else:

                def check_tz_aware(v: object) -> bool:
                    assert isinstance(v, datetime.datetime)
                    return v.tzinfo is not None

                s = _check_func(check_tz_aware, 'timezone aware', s)
        elif tz is None:
            if s and s['type'] == 'datetime':
                s = s.copy()
                s['tz_constraint'] = 'naive'
            else:

                def check_tz_naive(v: object) -> bool:
                    assert isinstance(v, datetime.datetime)
                    return v.tzinfo is None

                s = _check_func(check_tz_naive, 'timezone naive', s)
        else:
            raise NotImplementedError('Constraining to a specific timezone is not yet supported')
    elif isinstance(constraint, annotated_types.Interval):
        if constraint.ge:
            s = _apply_constraint(s, annotated_types.Ge(constraint.ge))
        if constraint.gt:
            s = _apply_constraint(s, annotated_types.Gt(constraint.gt))
        if constraint.le:
            s = _apply_constraint(s, annotated_types.Le(constraint.le))
        if constraint.lt:
            s = _apply_constraint(s, annotated_types.Lt(constraint.lt))
        assert s is not None
    elif isinstance(constraint, annotated_types.Predicate):
        func = constraint.func

        if func.__name__ == '<lambda>':
            # attempt to extract the source code for a lambda function
            # to use as the function name in error messages
            # TODO: is there a better way? should we just not do this?
            import inspect

            try:
                # remove ')' suffix, can use removesuffix once we drop 3.8
                source = inspect.getsource(func).strip()
                if source.endswith(')'):
                    source = source[:-1]
                lambda_source_code = '`' + ''.join(''.join(source.split('lambda ')[1:]).split(':')[1:]).strip() + '`'
            except OSError:
                # stringified annotations
                lambda_source_code = 'lambda'

            s = _check_func(func, lambda_source_code, s)
        else:
            s = _check_func(func, func.__name__, s)
    elif isinstance(constraint, _NotEq):
        value = constraint.value

        def check_not_eq(v: Any) -> bool:
            return operator.__ne__(v, value)

        s = _check_func(check_not_eq, f'!= {value}', s)
    elif isinstance(constraint, _Eq):
        value = constraint.value

        def check_eq(v: Any) -> bool:
            return operator.__eq__(v, value)

        s = _check_func(check_eq, f'== {value}', s)
    elif isinstance(constraint, _In):
        values = constraint.values

        def check_in(v: Any) -> bool:
            return operator.__contains__(values, v)

        s = _check_func(check_in, f'in {values}', s)
    elif isinstance(constraint, _NotIn):
        values = constraint.values

        def check_not_in(v: Any) -> bool:
            return operator.__not__(operator.__contains__(values, v))

        s = _check_func(check_not_in, f'not in {values}', s)
    else:
        assert isinstance(constraint, Pattern)
        if s and s['type'] == 'str':
            s = s.copy()
            s['pattern'] = constraint.pattern
        else:

            def check_pattern(v: object) -> bool:
                assert isinstance(v, str)
                return constraint.match(v) is not None

            s = _check_func(check_pattern, f'~ {constraint.pattern}', s)
    return s


class _SupportsRange(annotated_types.SupportsLe, annotated_types.SupportsGe, Protocol):
    pass


class _SupportsLen(Protocol):
    def __len__(self) -> int: ...


_NewOutGt = TypeVar('_NewOutGt', bound=annotated_types.SupportsGt)
_NewOutGe = TypeVar('_NewOutGe', bound=annotated_types.SupportsGe)
_NewOutLt = TypeVar('_NewOutLt', bound=annotated_types.SupportsLt)
_NewOutLe = TypeVar('_NewOutLe', bound=annotated_types.SupportsLe)
_NewOutLen = TypeVar('_NewOutLen', bound=_SupportsLen)
_NewOutDiv = TypeVar('_NewOutDiv', bound=annotated_types.SupportsDiv)
_NewOutMod = TypeVar('_NewOutMod', bound=annotated_types.SupportsMod)
_NewOutDatetime = TypeVar('_NewOutDatetime', bound=datetime.datetime)
_NewOutInterval = TypeVar('_NewOutInterval', bound=_SupportsRange)
_OtherIn = TypeVar('_OtherIn')
_OtherOut = TypeVar('_OtherOut')
