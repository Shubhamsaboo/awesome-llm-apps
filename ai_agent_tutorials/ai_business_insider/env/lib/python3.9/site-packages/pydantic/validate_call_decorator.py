"""Decorator for validating function calls."""

from __future__ import annotations as _annotations

import inspect
from functools import partial
from typing import TYPE_CHECKING, Any, Callable, TypeVar, cast, overload

from ._internal import _generate_schema, _typing_extra, _validate_call
from .errors import PydanticUserError

__all__ = ('validate_call',)

if TYPE_CHECKING:
    from .config import ConfigDict

    AnyCallableT = TypeVar('AnyCallableT', bound=Callable[..., Any])


_INVALID_TYPE_ERROR_CODE = 'validate-call-type'


def _check_function_type(function: object) -> None:
    """Check if the input function is a supported type for `validate_call`."""
    if isinstance(function, _generate_schema.VALIDATE_CALL_SUPPORTED_TYPES):
        try:
            inspect.signature(cast(_generate_schema.ValidateCallSupportedTypes, function))
        except ValueError:
            raise PydanticUserError(
                f"Input function `{function}` doesn't have a valid signature", code=_INVALID_TYPE_ERROR_CODE
            )

        if isinstance(function, partial):
            try:
                assert not isinstance(partial.func, partial), 'Partial of partial'
                _check_function_type(function.func)
            except PydanticUserError as e:
                raise PydanticUserError(
                    f'Partial of `{function.func}` is invalid because the type of `{function.func}` is not supported by `validate_call`',
                    code=_INVALID_TYPE_ERROR_CODE,
                ) from e

        return

    if isinstance(function, (classmethod, staticmethod, property)):
        name = type(function).__name__
        raise PydanticUserError(
            f'The `@{name}` decorator should be applied after `@validate_call` (put `@{name}` on top)',
            code=_INVALID_TYPE_ERROR_CODE,
        )

    if inspect.isclass(function):
        raise PydanticUserError(
            f'Unable to validate {function}: `validate_call` should be applied to functions, not classes (put `@validate_call` on top of `__init__` or `__new__` instead)',
            code=_INVALID_TYPE_ERROR_CODE,
        )
    if callable(function):
        raise PydanticUserError(
            f'Unable to validate {function}: `validate_call` should be applied to functions, not instances or other callables. Use `validate_call` explicitly on `__call__` instead.',
            code=_INVALID_TYPE_ERROR_CODE,
        )

    raise PydanticUserError(
        f'Unable to validate {function}: `validate_call` should be applied to one of the following: function, method, partial, or lambda',
        code=_INVALID_TYPE_ERROR_CODE,
    )


@overload
def validate_call(
    *, config: ConfigDict | None = None, validate_return: bool = False
) -> Callable[[AnyCallableT], AnyCallableT]: ...


@overload
def validate_call(func: AnyCallableT, /) -> AnyCallableT: ...


def validate_call(
    func: AnyCallableT | None = None,
    /,
    *,
    config: ConfigDict | None = None,
    validate_return: bool = False,
) -> AnyCallableT | Callable[[AnyCallableT], AnyCallableT]:
    """Usage docs: https://docs.pydantic.dev/2.10/concepts/validation_decorator/

    Returns a decorated wrapper around the function that validates the arguments and, optionally, the return value.

    Usage may be either as a plain decorator `@validate_call` or with arguments `@validate_call(...)`.

    Args:
        func: The function to be decorated.
        config: The configuration dictionary.
        validate_return: Whether to validate the return value.

    Returns:
        The decorated function.
    """
    parent_namespace = _typing_extra.parent_frame_namespace()

    def validate(function: AnyCallableT) -> AnyCallableT:
        _check_function_type(function)
        validate_call_wrapper = _validate_call.ValidateCallWrapper(
            cast(_generate_schema.ValidateCallSupportedTypes, function), config, validate_return, parent_namespace
        )
        return _validate_call.update_wrapper_attributes(function, validate_call_wrapper.__call__)  # type: ignore

    if func is not None:
        return validate(func)
    else:
        return validate
