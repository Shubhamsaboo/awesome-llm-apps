"""Logic for V1 validators, e.g. `@validator` and `@root_validator`."""

from __future__ import annotations as _annotations

from inspect import Parameter, signature
from typing import Any, Dict, Tuple, Union, cast

from pydantic_core import core_schema
from typing_extensions import Protocol

from ..errors import PydanticUserError
from ._utils import can_be_positional


class V1OnlyValueValidator(Protocol):
    """A simple validator, supported for V1 validators and V2 validators."""

    def __call__(self, __value: Any) -> Any: ...


class V1ValidatorWithValues(Protocol):
    """A validator with `values` argument, supported for V1 validators and V2 validators."""

    def __call__(self, __value: Any, values: dict[str, Any]) -> Any: ...


class V1ValidatorWithValuesKwOnly(Protocol):
    """A validator with keyword only `values` argument, supported for V1 validators and V2 validators."""

    def __call__(self, __value: Any, *, values: dict[str, Any]) -> Any: ...


class V1ValidatorWithKwargs(Protocol):
    """A validator with `kwargs` argument, supported for V1 validators and V2 validators."""

    def __call__(self, __value: Any, **kwargs: Any) -> Any: ...


class V1ValidatorWithValuesAndKwargs(Protocol):
    """A validator with `values` and `kwargs` arguments, supported for V1 validators and V2 validators."""

    def __call__(self, __value: Any, values: dict[str, Any], **kwargs: Any) -> Any: ...


V1Validator = Union[
    V1ValidatorWithValues, V1ValidatorWithValuesKwOnly, V1ValidatorWithKwargs, V1ValidatorWithValuesAndKwargs
]


def can_be_keyword(param: Parameter) -> bool:
    return param.kind in (Parameter.POSITIONAL_OR_KEYWORD, Parameter.KEYWORD_ONLY)


def make_generic_v1_field_validator(validator: V1Validator) -> core_schema.WithInfoValidatorFunction:
    """Wrap a V1 style field validator for V2 compatibility.

    Args:
        validator: The V1 style field validator.

    Returns:
        A wrapped V2 style field validator.

    Raises:
        PydanticUserError: If the signature is not supported or the parameters are
            not available in Pydantic V2.
    """
    sig = signature(validator)

    needs_values_kw = False

    for param_num, (param_name, parameter) in enumerate(sig.parameters.items()):
        if can_be_keyword(parameter) and param_name in ('field', 'config'):
            raise PydanticUserError(
                'The `field` and `config` parameters are not available in Pydantic V2, '
                'please use the `info` parameter instead.',
                code='validator-field-config-info',
            )
        if parameter.kind is Parameter.VAR_KEYWORD:
            needs_values_kw = True
        elif can_be_keyword(parameter) and param_name == 'values':
            needs_values_kw = True
        elif can_be_positional(parameter) and param_num == 0:
            # value
            continue
        elif parameter.default is Parameter.empty:  # ignore params with defaults e.g. bound by functools.partial
            raise PydanticUserError(
                f'Unsupported signature for V1 style validator {validator}: {sig} is not supported.',
                code='validator-v1-signature',
            )

    if needs_values_kw:
        # (v, **kwargs), (v, values, **kwargs), (v, *, values, **kwargs) or (v, *, values)
        val1 = cast(V1ValidatorWithValues, validator)

        def wrapper1(value: Any, info: core_schema.ValidationInfo) -> Any:
            return val1(value, values=info.data)

        return wrapper1
    else:
        val2 = cast(V1OnlyValueValidator, validator)

        def wrapper2(value: Any, _: core_schema.ValidationInfo) -> Any:
            return val2(value)

        return wrapper2


RootValidatorValues = Dict[str, Any]
# technically tuple[model_dict, model_extra, fields_set] | tuple[dataclass_dict, init_vars]
RootValidatorFieldsTuple = Tuple[Any, ...]


class V1RootValidatorFunction(Protocol):
    """A simple root validator, supported for V1 validators and V2 validators."""

    def __call__(self, __values: RootValidatorValues) -> RootValidatorValues: ...


class V2CoreBeforeRootValidator(Protocol):
    """V2 validator with mode='before'."""

    def __call__(self, __values: RootValidatorValues, __info: core_schema.ValidationInfo) -> RootValidatorValues: ...


class V2CoreAfterRootValidator(Protocol):
    """V2 validator with mode='after'."""

    def __call__(
        self, __fields_tuple: RootValidatorFieldsTuple, __info: core_schema.ValidationInfo
    ) -> RootValidatorFieldsTuple: ...


def make_v1_generic_root_validator(
    validator: V1RootValidatorFunction, pre: bool
) -> V2CoreBeforeRootValidator | V2CoreAfterRootValidator:
    """Wrap a V1 style root validator for V2 compatibility.

    Args:
        validator: The V1 style field validator.
        pre: Whether the validator is a pre validator.

    Returns:
        A wrapped V2 style validator.
    """
    if pre is True:
        # mode='before' for pydantic-core
        def _wrapper1(values: RootValidatorValues, _: core_schema.ValidationInfo) -> RootValidatorValues:
            return validator(values)

        return _wrapper1

    # mode='after' for pydantic-core
    def _wrapper2(fields_tuple: RootValidatorFieldsTuple, _: core_schema.ValidationInfo) -> RootValidatorFieldsTuple:
        if len(fields_tuple) == 2:
            # dataclass, this is easy
            values, init_vars = fields_tuple
            values = validator(values)
            return values, init_vars
        else:
            # ugly hack: to match v1 behaviour, we merge values and model_extra, then split them up based on fields
            # afterwards
            model_dict, model_extra, fields_set = fields_tuple
            if model_extra:
                fields = set(model_dict.keys())
                model_dict.update(model_extra)
                model_dict_new = validator(model_dict)
                for k in list(model_dict_new.keys()):
                    if k not in fields:
                        model_extra[k] = model_dict_new.pop(k)
            else:
                model_dict_new = validator(model_dict)
            return model_dict_new, model_extra, fields_set

    return _wrapper2
