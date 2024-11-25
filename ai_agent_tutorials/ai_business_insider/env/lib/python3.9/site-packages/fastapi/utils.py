import re
import warnings
from dataclasses import is_dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    MutableMapping,
    Optional,
    Set,
    Type,
    Union,
    cast,
)
from weakref import WeakKeyDictionary

import fastapi
from fastapi._compat import (
    PYDANTIC_V2,
    BaseConfig,
    ModelField,
    PydanticSchemaGenerationError,
    Undefined,
    UndefinedType,
    Validator,
    lenient_issubclass,
)
from fastapi.datastructures import DefaultPlaceholder, DefaultType
from pydantic import BaseModel, create_model
from pydantic.fields import FieldInfo
from typing_extensions import Literal

if TYPE_CHECKING:  # pragma: nocover
    from .routing import APIRoute

# Cache for `create_cloned_field`
_CLONED_TYPES_CACHE: MutableMapping[Type[BaseModel], Type[BaseModel]] = (
    WeakKeyDictionary()
)


def is_body_allowed_for_status_code(status_code: Union[int, str, None]) -> bool:
    if status_code is None:
        return True
    # Ref: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.0.md#patterned-fields-1
    if status_code in {
        "default",
        "1XX",
        "2XX",
        "3XX",
        "4XX",
        "5XX",
    }:
        return True
    current_status_code = int(status_code)
    return not (current_status_code < 200 or current_status_code in {204, 205, 304})


def get_path_param_names(path: str) -> Set[str]:
    return set(re.findall("{(.*?)}", path))


def create_model_field(
    name: str,
    type_: Any,
    class_validators: Optional[Dict[str, Validator]] = None,
    default: Optional[Any] = Undefined,
    required: Union[bool, UndefinedType] = Undefined,
    model_config: Type[BaseConfig] = BaseConfig,
    field_info: Optional[FieldInfo] = None,
    alias: Optional[str] = None,
    mode: Literal["validation", "serialization"] = "validation",
) -> ModelField:
    class_validators = class_validators or {}
    if PYDANTIC_V2:
        field_info = field_info or FieldInfo(
            annotation=type_, default=default, alias=alias
        )
    else:
        field_info = field_info or FieldInfo()
    kwargs = {"name": name, "field_info": field_info}
    if PYDANTIC_V2:
        kwargs.update({"mode": mode})
    else:
        kwargs.update(
            {
                "type_": type_,
                "class_validators": class_validators,
                "default": default,
                "required": required,
                "model_config": model_config,
                "alias": alias,
            }
        )
    try:
        return ModelField(**kwargs)  # type: ignore[arg-type]
    except (RuntimeError, PydanticSchemaGenerationError):
        raise fastapi.exceptions.FastAPIError(
            "Invalid args for response field! Hint: "
            f"check that {type_} is a valid Pydantic field type. "
            "If you are using a return type annotation that is not a valid Pydantic "
            "field (e.g. Union[Response, dict, None]) you can disable generating the "
            "response model from the type annotation with the path operation decorator "
            "parameter response_model=None. Read more: "
            "https://fastapi.tiangolo.com/tutorial/response-model/"
        ) from None


def create_cloned_field(
    field: ModelField,
    *,
    cloned_types: Optional[MutableMapping[Type[BaseModel], Type[BaseModel]]] = None,
) -> ModelField:
    if PYDANTIC_V2:
        return field
    # cloned_types caches already cloned types to support recursive models and improve
    # performance by avoiding unnecessary cloning
    if cloned_types is None:
        cloned_types = _CLONED_TYPES_CACHE

    original_type = field.type_
    if is_dataclass(original_type) and hasattr(original_type, "__pydantic_model__"):
        original_type = original_type.__pydantic_model__
    use_type = original_type
    if lenient_issubclass(original_type, BaseModel):
        original_type = cast(Type[BaseModel], original_type)
        use_type = cloned_types.get(original_type)
        if use_type is None:
            use_type = create_model(original_type.__name__, __base__=original_type)
            cloned_types[original_type] = use_type
            for f in original_type.__fields__.values():
                use_type.__fields__[f.name] = create_cloned_field(
                    f, cloned_types=cloned_types
                )
    new_field = create_model_field(name=field.name, type_=use_type)
    new_field.has_alias = field.has_alias  # type: ignore[attr-defined]
    new_field.alias = field.alias  # type: ignore[misc]
    new_field.class_validators = field.class_validators  # type: ignore[attr-defined]
    new_field.default = field.default  # type: ignore[misc]
    new_field.required = field.required  # type: ignore[misc]
    new_field.model_config = field.model_config  # type: ignore[attr-defined]
    new_field.field_info = field.field_info
    new_field.allow_none = field.allow_none  # type: ignore[attr-defined]
    new_field.validate_always = field.validate_always  # type: ignore[attr-defined]
    if field.sub_fields:  # type: ignore[attr-defined]
        new_field.sub_fields = [  # type: ignore[attr-defined]
            create_cloned_field(sub_field, cloned_types=cloned_types)
            for sub_field in field.sub_fields  # type: ignore[attr-defined]
        ]
    if field.key_field:  # type: ignore[attr-defined]
        new_field.key_field = create_cloned_field(  # type: ignore[attr-defined]
            field.key_field,  # type: ignore[attr-defined]
            cloned_types=cloned_types,
        )
    new_field.validators = field.validators  # type: ignore[attr-defined]
    new_field.pre_validators = field.pre_validators  # type: ignore[attr-defined]
    new_field.post_validators = field.post_validators  # type: ignore[attr-defined]
    new_field.parse_json = field.parse_json  # type: ignore[attr-defined]
    new_field.shape = field.shape  # type: ignore[attr-defined]
    new_field.populate_validators()  # type: ignore[attr-defined]
    return new_field


def generate_operation_id_for_path(
    *, name: str, path: str, method: str
) -> str:  # pragma: nocover
    warnings.warn(
        "fastapi.utils.generate_operation_id_for_path() was deprecated, "
        "it is not used internally, and will be removed soon",
        DeprecationWarning,
        stacklevel=2,
    )
    operation_id = f"{name}{path}"
    operation_id = re.sub(r"\W", "_", operation_id)
    operation_id = f"{operation_id}_{method.lower()}"
    return operation_id


def generate_unique_id(route: "APIRoute") -> str:
    operation_id = f"{route.name}{route.path_format}"
    operation_id = re.sub(r"\W", "_", operation_id)
    assert route.methods
    operation_id = f"{operation_id}_{list(route.methods)[0].lower()}"
    return operation_id


def deep_dict_update(main_dict: Dict[Any, Any], update_dict: Dict[Any, Any]) -> None:
    for key, value in update_dict.items():
        if (
            key in main_dict
            and isinstance(main_dict[key], dict)
            and isinstance(value, dict)
        ):
            deep_dict_update(main_dict[key], value)
        elif (
            key in main_dict
            and isinstance(main_dict[key], list)
            and isinstance(update_dict[key], list)
        ):
            main_dict[key] = main_dict[key] + update_dict[key]
        else:
            main_dict[key] = value


def get_value_or_default(
    first_item: Union[DefaultPlaceholder, DefaultType],
    *extra_items: Union[DefaultPlaceholder, DefaultType],
) -> Union[DefaultPlaceholder, DefaultType]:
    """
    Pass items or `DefaultPlaceholder`s by descending priority.

    The first one to _not_ be a `DefaultPlaceholder` will be returned.

    Otherwise, the first item (a `DefaultPlaceholder`) will be returned.
    """
    items = (first_item,) + extra_items
    for item in items:
        if not isinstance(item, DefaultPlaceholder):
            return item
    return first_item
