from __future__ import annotations

import dataclasses
from inspect import Parameter, Signature, signature
from typing import TYPE_CHECKING, Any, Callable

from pydantic_core import PydanticUndefined

from ._utils import is_valid_identifier

if TYPE_CHECKING:
    from ..config import ExtraValues
    from ..fields import FieldInfo


# Copied over from stdlib dataclasses
class _HAS_DEFAULT_FACTORY_CLASS:
    def __repr__(self):
        return '<factory>'


_HAS_DEFAULT_FACTORY = _HAS_DEFAULT_FACTORY_CLASS()


def _field_name_for_signature(field_name: str, field_info: FieldInfo) -> str:
    """Extract the correct name to use for the field when generating a signature.

    Assuming the field has a valid alias, this will return the alias. Otherwise, it will return the field name.
    First priority is given to the alias, then the validation_alias, then the field name.

    Args:
        field_name: The name of the field
        field_info: The corresponding FieldInfo object.

    Returns:
        The correct name to use when generating a signature.
    """
    if isinstance(field_info.alias, str) and is_valid_identifier(field_info.alias):
        return field_info.alias
    if isinstance(field_info.validation_alias, str) and is_valid_identifier(field_info.validation_alias):
        return field_info.validation_alias

    return field_name


def _process_param_defaults(param: Parameter) -> Parameter:
    """Modify the signature for a parameter in a dataclass where the default value is a FieldInfo instance.

    Args:
        param (Parameter): The parameter

    Returns:
        Parameter: The custom processed parameter
    """
    from ..fields import FieldInfo

    param_default = param.default
    if isinstance(param_default, FieldInfo):
        annotation = param.annotation
        # Replace the annotation if appropriate
        # inspect does "clever" things to show annotations as strings because we have
        # `from __future__ import annotations` in main, we don't want that
        if annotation == 'Any':
            annotation = Any

        # Replace the field default
        default = param_default.default
        if default is PydanticUndefined:
            if param_default.default_factory is PydanticUndefined:
                default = Signature.empty
            else:
                # this is used by dataclasses to indicate a factory exists:
                default = dataclasses._HAS_DEFAULT_FACTORY  # type: ignore
        return param.replace(
            annotation=annotation, name=_field_name_for_signature(param.name, param_default), default=default
        )
    return param


def _generate_signature_parameters(  # noqa: C901 (ignore complexity, could use a refactor)
    init: Callable[..., None],
    fields: dict[str, FieldInfo],
    populate_by_name: bool,
    extra: ExtraValues | None,
) -> dict[str, Parameter]:
    """Generate a mapping of parameter names to Parameter objects for a pydantic BaseModel or dataclass."""
    from itertools import islice

    present_params = signature(init).parameters.values()
    merged_params: dict[str, Parameter] = {}
    var_kw = None
    use_var_kw = False

    for param in islice(present_params, 1, None):  # skip self arg
        # inspect does "clever" things to show annotations as strings because we have
        # `from __future__ import annotations` in main, we don't want that
        if fields.get(param.name):
            # exclude params with init=False
            if getattr(fields[param.name], 'init', True) is False:
                continue
            param = param.replace(name=_field_name_for_signature(param.name, fields[param.name]))
        if param.annotation == 'Any':
            param = param.replace(annotation=Any)
        if param.kind is param.VAR_KEYWORD:
            var_kw = param
            continue
        merged_params[param.name] = param

    if var_kw:  # if custom init has no var_kw, fields which are not declared in it cannot be passed through
        allow_names = populate_by_name
        for field_name, field in fields.items():
            # when alias is a str it should be used for signature generation
            param_name = _field_name_for_signature(field_name, field)

            if field_name in merged_params or param_name in merged_params:
                continue

            if not is_valid_identifier(param_name):
                if allow_names:
                    param_name = field_name
                else:
                    use_var_kw = True
                    continue

            if field.is_required():
                default = Parameter.empty
            elif field.default_factory is not None:
                # Mimics stdlib dataclasses:
                default = _HAS_DEFAULT_FACTORY
            else:
                default = field.default
            merged_params[param_name] = Parameter(
                param_name,
                Parameter.KEYWORD_ONLY,
                annotation=field.rebuild_annotation(),
                default=default,
            )

    if extra == 'allow':
        use_var_kw = True

    if var_kw and use_var_kw:
        # Make sure the parameter for extra kwargs
        # does not have the same name as a field
        default_model_signature = [
            ('self', Parameter.POSITIONAL_ONLY),
            ('data', Parameter.VAR_KEYWORD),
        ]
        if [(p.name, p.kind) for p in present_params] == default_model_signature:
            # if this is the standard model signature, use extra_data as the extra args name
            var_kw_name = 'extra_data'
        else:
            # else start from var_kw
            var_kw_name = var_kw.name

        # generate a name that's definitely unique
        while var_kw_name in fields:
            var_kw_name += '_'
        merged_params[var_kw_name] = var_kw.replace(name=var_kw_name)

    return merged_params


def generate_pydantic_signature(
    init: Callable[..., None],
    fields: dict[str, FieldInfo],
    populate_by_name: bool,
    extra: ExtraValues | None,
    is_dataclass: bool = False,
) -> Signature:
    """Generate signature for a pydantic BaseModel or dataclass.

    Args:
        init: The class init.
        fields: The model fields.
        populate_by_name: The `populate_by_name` value of the config.
        extra: The `extra` value of the config.
        is_dataclass: Whether the model is a dataclass.

    Returns:
        The dataclass/BaseModel subclass signature.
    """
    merged_params = _generate_signature_parameters(init, fields, populate_by_name, extra)

    if is_dataclass:
        merged_params = {k: _process_param_defaults(v) for k, v in merged_params.items()}

    return Signature(parameters=list(merged_params.values()), return_annotation=None)
