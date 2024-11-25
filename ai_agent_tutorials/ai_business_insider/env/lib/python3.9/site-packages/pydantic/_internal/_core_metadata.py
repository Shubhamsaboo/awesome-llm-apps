from __future__ import annotations as _annotations

from typing import TYPE_CHECKING, Any, TypedDict, cast
from warnings import warn

if TYPE_CHECKING:
    from pydantic_core import CoreSchema

    from ..config import JsonDict, JsonSchemaExtraCallable
    from ._schema_generation_shared import (
        GetJsonSchemaFunction,
    )


class CoreMetadata(TypedDict, total=False):
    """A `TypedDict` for holding the metadata dict of the schema.

    Attributes:
        pydantic_js_functions: List of JSON schema functions that resolve refs during application.
        pydantic_js_annotation_functions: List of JSON schema functions that don't resolve refs during application.
        pydantic_js_prefer_positional_arguments: Whether JSON schema generator will
            prefer positional over keyword arguments for an 'arguments' schema.
        pydantic_js_input_core_schema: Schema associated with the input value for the associated
            custom validation function. Only applies to before, plain, and wrap validators.
        pydantic_js_udpates: key / value pair updates to apply to the JSON schema for a type.
        pydantic_js_extra: WIP, either key/value pair updates to apply to the JSON schema, or a custom callable.

    TODO: Perhaps we should move this structure to pydantic-core. At the moment, though,
    it's easier to iterate on if we leave it in pydantic until we feel there is a semi-stable API.

    TODO: It's unfortunate how functionally oriented JSON schema generation is, especially that which occurs during
    the core schema generation process. It's inevitable that we need to store some json schema related information
    on core schemas, given that we generate JSON schemas directly from core schemas. That being said, debugging related
    issues is quite difficult when JSON schema information is disguised via dynamically defined functions.
    """

    pydantic_js_functions: list[GetJsonSchemaFunction]
    pydantic_js_annotation_functions: list[GetJsonSchemaFunction]
    pydantic_js_prefer_positional_arguments: bool
    pydantic_js_input_core_schema: CoreSchema
    pydantic_js_updates: JsonDict
    pydantic_js_extra: JsonDict | JsonSchemaExtraCallable


def update_core_metadata(
    core_metadata: Any,
    /,
    *,
    pydantic_js_functions: list[GetJsonSchemaFunction] | None = None,
    pydantic_js_annotation_functions: list[GetJsonSchemaFunction] | None = None,
    pydantic_js_updates: JsonDict | None = None,
    pydantic_js_extra: JsonDict | JsonSchemaExtraCallable | None = None,
) -> None:
    from ..json_schema import PydanticJsonSchemaWarning

    """Update CoreMetadata instance in place. When we make modifications in this function, they
    take effect on the `core_metadata` reference passed in as the first (and only) positional argument.

    First, cast to `CoreMetadata`, then finish with a cast to `dict[str, Any]` for core schema compatibility.
    We do this here, instead of before / after each call to this function so that this typing hack
    can be easily removed if/when we move `CoreMetadata` to `pydantic-core`.

    For parameter descriptions, see `CoreMetadata` above.
    """
    core_metadata = cast(CoreMetadata, core_metadata)

    if pydantic_js_functions:
        core_metadata.setdefault('pydantic_js_functions', []).extend(pydantic_js_functions)

    if pydantic_js_annotation_functions:
        core_metadata.setdefault('pydantic_js_annotation_functions', []).extend(pydantic_js_annotation_functions)

    if pydantic_js_updates:
        if (existing_updates := core_metadata.get('pydantic_js_updates')) is not None:
            core_metadata['pydantic_js_updates'] = {**existing_updates, **pydantic_js_updates}
        else:
            core_metadata['pydantic_js_updates'] = pydantic_js_updates

    if pydantic_js_extra is not None:
        existing_pydantic_js_extra = core_metadata.get('pydantic_js_extra')
        if existing_pydantic_js_extra is None:
            core_metadata['pydantic_js_extra'] = pydantic_js_extra
        if isinstance(existing_pydantic_js_extra, dict):
            if isinstance(pydantic_js_extra, dict):
                core_metadata['pydantic_js_extra'] = {**existing_pydantic_js_extra, **pydantic_js_extra}
            if callable(pydantic_js_extra):
                warn(
                    'Composing `dict` and `callable` type `json_schema_extra` is not supported.'
                    'The `callable` type is being ignored.'
                    "If you'd like support for this behavior, please open an issue on pydantic.",
                    PydanticJsonSchemaWarning,
                )
        if callable(existing_pydantic_js_extra):
            # if ever there's a case of a callable, we'll just keep the last json schema extra spec
            core_metadata['pydantic_js_extra'] = pydantic_js_extra
