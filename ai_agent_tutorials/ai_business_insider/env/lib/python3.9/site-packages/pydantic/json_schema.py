"""
Usage docs: https://docs.pydantic.dev/2.5/concepts/json_schema/

The `json_schema` module contains classes and functions to allow the way [JSON Schema](https://json-schema.org/)
is generated to be customized.

In general you shouldn't need to use this module directly; instead, you can use
[`BaseModel.model_json_schema`][pydantic.BaseModel.model_json_schema] and
[`TypeAdapter.json_schema`][pydantic.TypeAdapter.json_schema].
"""

from __future__ import annotations as _annotations

import dataclasses
import inspect
import math
import os
import re
import warnings
from collections import defaultdict
from copy import deepcopy
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Counter,
    Dict,
    Hashable,
    Iterable,
    NewType,
    Pattern,
    Sequence,
    Tuple,
    TypeVar,
    Union,
    cast,
    overload,
)

import pydantic_core
from pydantic_core import CoreSchema, PydanticOmit, core_schema, to_jsonable_python
from pydantic_core.core_schema import ComputedField
from typing_extensions import Annotated, Literal, TypeAlias, assert_never, deprecated, final

from pydantic.warnings import PydanticDeprecatedSince26, PydanticDeprecatedSince29

from ._internal import (
    _config,
    _core_metadata,
    _core_utils,
    _decorators,
    _internal_dataclass,
    _mock_val_ser,
    _schema_generation_shared,
    _typing_extra,
)
from .annotated_handlers import GetJsonSchemaHandler
from .config import JsonDict, JsonValue
from .errors import PydanticInvalidForJsonSchema, PydanticSchemaGenerationError, PydanticUserError

if TYPE_CHECKING:
    from . import ConfigDict
    from ._internal._core_utils import CoreSchemaField, CoreSchemaOrField
    from ._internal._dataclasses import PydanticDataclass
    from ._internal._schema_generation_shared import GetJsonSchemaFunction
    from .main import BaseModel


CoreSchemaOrFieldType = Literal[core_schema.CoreSchemaType, core_schema.CoreSchemaFieldType]
"""
A type alias for defined schema types that represents a union of
`core_schema.CoreSchemaType` and
`core_schema.CoreSchemaFieldType`.
"""

JsonSchemaValue = Dict[str, Any]
"""
A type alias for a JSON schema value. This is a dictionary of string keys to arbitrary JSON values.
"""

JsonSchemaMode = Literal['validation', 'serialization']
"""
A type alias that represents the mode of a JSON schema; either 'validation' or 'serialization'.

For some types, the inputs to validation differ from the outputs of serialization. For example,
computed fields will only be present when serializing, and should not be provided when
validating. This flag provides a way to indicate whether you want the JSON schema required
for validation inputs, or that will be matched by serialization outputs.
"""

_MODE_TITLE_MAPPING: dict[JsonSchemaMode, str] = {'validation': 'Input', 'serialization': 'Output'}


JsonSchemaWarningKind = Literal['skipped-choice', 'non-serializable-default', 'skipped-discriminator']
"""
A type alias representing the kinds of warnings that can be emitted during JSON schema generation.

See [`GenerateJsonSchema.render_warning_message`][pydantic.json_schema.GenerateJsonSchema.render_warning_message]
for more details.
"""


class PydanticJsonSchemaWarning(UserWarning):
    """This class is used to emit warnings produced during JSON schema generation.
    See the [`GenerateJsonSchema.emit_warning`][pydantic.json_schema.GenerateJsonSchema.emit_warning] and
    [`GenerateJsonSchema.render_warning_message`][pydantic.json_schema.GenerateJsonSchema.render_warning_message]
    methods for more details; these can be overridden to control warning behavior.
    """


# ##### JSON Schema Generation #####
DEFAULT_REF_TEMPLATE = '#/$defs/{model}'
"""The default format string used to generate reference names."""

# There are three types of references relevant to building JSON schemas:
#   1. core_schema "ref" values; these are not exposed as part of the JSON schema
#       * these might look like the fully qualified path of a model, its id, or something similar
CoreRef = NewType('CoreRef', str)
#   2. keys of the "definitions" object that will eventually go into the JSON schema
#       * by default, these look like "MyModel", though may change in the presence of collisions
#       * eventually, we may want to make it easier to modify the way these names are generated
DefsRef = NewType('DefsRef', str)
#   3. the values corresponding to the "$ref" key in the schema
#       * By default, these look like "#/$defs/MyModel", as in {"$ref": "#/$defs/MyModel"}
JsonRef = NewType('JsonRef', str)

CoreModeRef = Tuple[CoreRef, JsonSchemaMode]
JsonSchemaKeyT = TypeVar('JsonSchemaKeyT', bound=Hashable)


@dataclasses.dataclass(**_internal_dataclass.slots_true)
class _DefinitionsRemapping:
    defs_remapping: dict[DefsRef, DefsRef]
    json_remapping: dict[JsonRef, JsonRef]

    @staticmethod
    def from_prioritized_choices(
        prioritized_choices: dict[DefsRef, list[DefsRef]],
        defs_to_json: dict[DefsRef, JsonRef],
        definitions: dict[DefsRef, JsonSchemaValue],
    ) -> _DefinitionsRemapping:
        """
        This function should produce a remapping that replaces complex DefsRef with the simpler ones from the
        prioritized_choices such that applying the name remapping would result in an equivalent JSON schema.
        """
        # We need to iteratively simplify the definitions until we reach a fixed point.
        # The reason for this is that outer definitions may reference inner definitions that get simplified
        # into an equivalent reference, and the outer definitions won't be equivalent until we've simplified
        # the inner definitions.
        copied_definitions = deepcopy(definitions)
        definitions_schema = {'$defs': copied_definitions}
        for _iter in range(100):  # prevent an infinite loop in the case of a bug, 100 iterations should be enough
            # For every possible remapped DefsRef, collect all schemas that that DefsRef might be used for:
            schemas_for_alternatives: dict[DefsRef, list[JsonSchemaValue]] = defaultdict(list)
            for defs_ref in copied_definitions:
                alternatives = prioritized_choices[defs_ref]
                for alternative in alternatives:
                    schemas_for_alternatives[alternative].append(copied_definitions[defs_ref])

            # Deduplicate the schemas for each alternative; the idea is that we only want to remap to a new DefsRef
            # if it introduces no ambiguity, i.e., there is only one distinct schema for that DefsRef.
            for defs_ref in schemas_for_alternatives:
                schemas_for_alternatives[defs_ref] = _deduplicate_schemas(schemas_for_alternatives[defs_ref])

            # Build the remapping
            defs_remapping: dict[DefsRef, DefsRef] = {}
            json_remapping: dict[JsonRef, JsonRef] = {}
            for original_defs_ref in definitions:
                alternatives = prioritized_choices[original_defs_ref]
                # Pick the first alternative that has only one schema, since that means there is no collision
                remapped_defs_ref = next(x for x in alternatives if len(schemas_for_alternatives[x]) == 1)
                defs_remapping[original_defs_ref] = remapped_defs_ref
                json_remapping[defs_to_json[original_defs_ref]] = defs_to_json[remapped_defs_ref]
            remapping = _DefinitionsRemapping(defs_remapping, json_remapping)
            new_definitions_schema = remapping.remap_json_schema({'$defs': copied_definitions})
            if definitions_schema == new_definitions_schema:
                # We've reached the fixed point
                return remapping
            definitions_schema = new_definitions_schema

        raise PydanticInvalidForJsonSchema('Failed to simplify the JSON schema definitions')

    def remap_defs_ref(self, ref: DefsRef) -> DefsRef:
        return self.defs_remapping.get(ref, ref)

    def remap_json_ref(self, ref: JsonRef) -> JsonRef:
        return self.json_remapping.get(ref, ref)

    def remap_json_schema(self, schema: Any) -> Any:
        """
        Recursively update the JSON schema replacing all $refs
        """
        if isinstance(schema, str):
            # Note: this may not really be a JsonRef; we rely on having no collisions between JsonRefs and other strings
            return self.remap_json_ref(JsonRef(schema))
        elif isinstance(schema, list):
            return [self.remap_json_schema(item) for item in schema]
        elif isinstance(schema, dict):
            for key, value in schema.items():
                if key == '$ref' and isinstance(value, str):
                    schema['$ref'] = self.remap_json_ref(JsonRef(value))
                elif key == '$defs':
                    schema['$defs'] = {
                        self.remap_defs_ref(DefsRef(key)): self.remap_json_schema(value)
                        for key, value in schema['$defs'].items()
                    }
                else:
                    schema[key] = self.remap_json_schema(value)
        return schema


class GenerateJsonSchema:
    """Usage docs: https://docs.pydantic.dev/2.10/concepts/json_schema/#customizing-the-json-schema-generation-process

    A class for generating JSON schemas.

    This class generates JSON schemas based on configured parameters. The default schema dialect
    is [https://json-schema.org/draft/2020-12/schema](https://json-schema.org/draft/2020-12/schema).
    The class uses `by_alias` to configure how fields with
    multiple names are handled and `ref_template` to format reference names.

    Attributes:
        schema_dialect: The JSON schema dialect used to generate the schema. See
            [Declaring a Dialect](https://json-schema.org/understanding-json-schema/reference/schema.html#id4)
            in the JSON Schema documentation for more information about dialects.
        ignored_warning_kinds: Warnings to ignore when generating the schema. `self.render_warning_message` will
            do nothing if its argument `kind` is in `ignored_warning_kinds`;
            this value can be modified on subclasses to easily control which warnings are emitted.
        by_alias: Whether to use field aliases when generating the schema.
        ref_template: The format string used when generating reference names.
        core_to_json_refs: A mapping of core refs to JSON refs.
        core_to_defs_refs: A mapping of core refs to definition refs.
        defs_to_core_refs: A mapping of definition refs to core refs.
        json_to_defs_refs: A mapping of JSON refs to definition refs.
        definitions: Definitions in the schema.

    Args:
        by_alias: Whether to use field aliases in the generated schemas.
        ref_template: The format string to use when generating reference names.

    Raises:
        JsonSchemaError: If the instance of the class is inadvertently reused after generating a schema.
    """

    schema_dialect = 'https://json-schema.org/draft/2020-12/schema'

    # `self.render_warning_message` will do nothing if its argument `kind` is in `ignored_warning_kinds`;
    # this value can be modified on subclasses to easily control which warnings are emitted
    ignored_warning_kinds: set[JsonSchemaWarningKind] = {'skipped-choice'}

    def __init__(self, by_alias: bool = True, ref_template: str = DEFAULT_REF_TEMPLATE):
        self.by_alias = by_alias
        self.ref_template = ref_template

        self.core_to_json_refs: dict[CoreModeRef, JsonRef] = {}
        self.core_to_defs_refs: dict[CoreModeRef, DefsRef] = {}
        self.defs_to_core_refs: dict[DefsRef, CoreModeRef] = {}
        self.json_to_defs_refs: dict[JsonRef, DefsRef] = {}

        self.definitions: dict[DefsRef, JsonSchemaValue] = {}
        self._config_wrapper_stack = _config.ConfigWrapperStack(_config.ConfigWrapper({}))

        self._mode: JsonSchemaMode = 'validation'

        # The following includes a mapping of a fully-unique defs ref choice to a list of preferred
        # alternatives, which are generally simpler, such as only including the class name.
        # At the end of schema generation, we use these to produce a JSON schema with more human-readable
        # definitions, which would also work better in a generated OpenAPI client, etc.
        self._prioritized_defsref_choices: dict[DefsRef, list[DefsRef]] = {}
        self._collision_counter: dict[str, int] = defaultdict(int)
        self._collision_index: dict[str, int] = {}

        self._schema_type_to_method = self.build_schema_type_to_method()

        # When we encounter definitions we need to try to build them immediately
        # so that they are available schemas that reference them
        # But it's possible that CoreSchema was never going to be used
        # (e.g. because the CoreSchema that references short circuits is JSON schema generation without needing
        #  the reference) so instead of failing altogether if we can't build a definition we
        # store the error raised and re-throw it if we end up needing that def
        self._core_defs_invalid_for_json_schema: dict[DefsRef, PydanticInvalidForJsonSchema] = {}

        # This changes to True after generating a schema, to prevent issues caused by accidental reuse
        # of a single instance of a schema generator
        self._used = False

    @property
    def _config(self) -> _config.ConfigWrapper:
        return self._config_wrapper_stack.tail

    @property
    def mode(self) -> JsonSchemaMode:
        if self._config.json_schema_mode_override is not None:
            return self._config.json_schema_mode_override
        else:
            return self._mode

    def build_schema_type_to_method(
        self,
    ) -> dict[CoreSchemaOrFieldType, Callable[[CoreSchemaOrField], JsonSchemaValue]]:
        """Builds a dictionary mapping fields to methods for generating JSON schemas.

        Returns:
            A dictionary containing the mapping of `CoreSchemaOrFieldType` to a handler method.

        Raises:
            TypeError: If no method has been defined for generating a JSON schema for a given pydantic core schema type.
        """
        mapping: dict[CoreSchemaOrFieldType, Callable[[CoreSchemaOrField], JsonSchemaValue]] = {}
        core_schema_types: list[CoreSchemaOrFieldType] = _typing_extra.literal_values(
            CoreSchemaOrFieldType  # type: ignore
        )
        for key in core_schema_types:
            method_name = f"{key.replace('-', '_')}_schema"
            try:
                mapping[key] = getattr(self, method_name)
            except AttributeError as e:  # pragma: no cover
                if os.environ['PYDANTIC_PRIVATE_ALLOW_UNHANDLED_SCHEMA_TYPES'] == '1':
                    continue
                raise TypeError(
                    f'No method for generating JsonSchema for core_schema.type={key!r} '
                    f'(expected: {type(self).__name__}.{method_name})'
                ) from e
        return mapping

    def generate_definitions(
        self, inputs: Sequence[tuple[JsonSchemaKeyT, JsonSchemaMode, core_schema.CoreSchema]]
    ) -> tuple[dict[tuple[JsonSchemaKeyT, JsonSchemaMode], JsonSchemaValue], dict[DefsRef, JsonSchemaValue]]:
        """Generates JSON schema definitions from a list of core schemas, pairing the generated definitions with a
        mapping that links the input keys to the definition references.

        Args:
            inputs: A sequence of tuples, where:

                - The first element is a JSON schema key type.
                - The second element is the JSON mode: either 'validation' or 'serialization'.
                - The third element is a core schema.

        Returns:
            A tuple where:

                - The first element is a dictionary whose keys are tuples of JSON schema key type and JSON mode, and
                    whose values are the JSON schema corresponding to that pair of inputs. (These schemas may have
                    JsonRef references to definitions that are defined in the second returned element.)
                - The second element is a dictionary whose keys are definition references for the JSON schemas
                    from the first returned element, and whose values are the actual JSON schema definitions.

        Raises:
            PydanticUserError: Raised if the JSON schema generator has already been used to generate a JSON schema.
        """
        if self._used:
            raise PydanticUserError(
                'This JSON schema generator has already been used to generate a JSON schema. '
                f'You must create a new instance of {type(self).__name__} to generate a new JSON schema.',
                code='json-schema-already-used',
            )

        for _, mode, schema in inputs:
            self._mode = mode
            self.generate_inner(schema)

        definitions_remapping = self._build_definitions_remapping()

        json_schemas_map: dict[tuple[JsonSchemaKeyT, JsonSchemaMode], DefsRef] = {}
        for key, mode, schema in inputs:
            self._mode = mode
            json_schema = self.generate_inner(schema)
            json_schemas_map[(key, mode)] = definitions_remapping.remap_json_schema(json_schema)

        json_schema = {'$defs': self.definitions}
        json_schema = definitions_remapping.remap_json_schema(json_schema)
        self._used = True
        return json_schemas_map, self.sort(json_schema['$defs'])  # type: ignore

    def generate(self, schema: CoreSchema, mode: JsonSchemaMode = 'validation') -> JsonSchemaValue:
        """Generates a JSON schema for a specified schema in a specified mode.

        Args:
            schema: A Pydantic model.
            mode: The mode in which to generate the schema. Defaults to 'validation'.

        Returns:
            A JSON schema representing the specified schema.

        Raises:
            PydanticUserError: If the JSON schema generator has already been used to generate a JSON schema.
        """
        self._mode = mode
        if self._used:
            raise PydanticUserError(
                'This JSON schema generator has already been used to generate a JSON schema. '
                f'You must create a new instance of {type(self).__name__} to generate a new JSON schema.',
                code='json-schema-already-used',
            )

        json_schema: JsonSchemaValue = self.generate_inner(schema)
        json_ref_counts = self.get_json_ref_counts(json_schema)

        ref = cast(JsonRef, json_schema.get('$ref'))
        while ref is not None:  # may need to unpack multiple levels
            ref_json_schema = self.get_schema_from_definitions(ref)
            if json_ref_counts[ref] == 1 and ref_json_schema is not None and len(json_schema) == 1:
                # "Unpack" the ref since this is the only reference and there are no sibling keys
                json_schema = ref_json_schema.copy()  # copy to prevent recursive dict reference
                json_ref_counts[ref] -= 1
                ref = cast(JsonRef, json_schema.get('$ref'))
            ref = None

        self._garbage_collect_definitions(json_schema)
        definitions_remapping = self._build_definitions_remapping()

        if self.definitions:
            json_schema['$defs'] = self.definitions

        json_schema = definitions_remapping.remap_json_schema(json_schema)

        # For now, we will not set the $schema key. However, if desired, this can be easily added by overriding
        # this method and adding the following line after a call to super().generate(schema):
        # json_schema['$schema'] = self.schema_dialect

        self._used = True
        return self.sort(json_schema)

    def generate_inner(self, schema: CoreSchemaOrField) -> JsonSchemaValue:  # noqa: C901
        """Generates a JSON schema for a given core schema.

        Args:
            schema: The given core schema.

        Returns:
            The generated JSON schema.

        TODO: the nested function definitions here seem like bad practice, I'd like to unpack these
        in a future PR. It'd be great if we could shorten the call stack a bit for JSON schema generation,
        and I think there's potential for that here.
        """
        # If a schema with the same CoreRef has been handled, just return a reference to it
        # Note that this assumes that it will _never_ be the case that the same CoreRef is used
        # on types that should have different JSON schemas
        if 'ref' in schema:
            core_ref = CoreRef(schema['ref'])  # type: ignore[typeddict-item]
            core_mode_ref = (core_ref, self.mode)
            if core_mode_ref in self.core_to_defs_refs and self.core_to_defs_refs[core_mode_ref] in self.definitions:
                return {'$ref': self.core_to_json_refs[core_mode_ref]}

        def populate_defs(core_schema: CoreSchema, json_schema: JsonSchemaValue) -> JsonSchemaValue:
            if 'ref' in core_schema:
                core_ref = CoreRef(core_schema['ref'])  # type: ignore[typeddict-item]
                defs_ref, ref_json_schema = self.get_cache_defs_ref_schema(core_ref)
                json_ref = JsonRef(ref_json_schema['$ref'])
                # Replace the schema if it's not a reference to itself
                # What we want to avoid is having the def be just a ref to itself
                # which is what would happen if we blindly assigned any
                if json_schema.get('$ref', None) != json_ref:
                    self.definitions[defs_ref] = json_schema
                    self._core_defs_invalid_for_json_schema.pop(defs_ref, None)
                json_schema = ref_json_schema
            return json_schema

        def handler_func(schema_or_field: CoreSchemaOrField) -> JsonSchemaValue:
            """Generate a JSON schema based on the input schema.

            Args:
                schema_or_field: The core schema to generate a JSON schema from.

            Returns:
                The generated JSON schema.

            Raises:
                TypeError: If an unexpected schema type is encountered.
            """
            # Generate the core-schema-type-specific bits of the schema generation:
            json_schema: JsonSchemaValue | None = None
            if self.mode == 'serialization' and 'serialization' in schema_or_field:
                # In this case, we skip the JSON Schema generation of the schema
                # and use the `'serialization'` schema instead (canonical example:
                # `Annotated[int, PlainSerializer(str)]`).
                ser_schema = schema_or_field['serialization']  # type: ignore
                json_schema = self.ser_schema(ser_schema)

                # It might be that the 'serialization'` is skipped depending on `when_used`.
                # This is only relevant for `nullable` schemas though, so we special case here.
                if (
                    json_schema is not None
                    and ser_schema.get('when_used') in ('unless-none', 'json-unless-none')
                    and schema_or_field['type'] == 'nullable'
                ):
                    json_schema = self.get_flattened_anyof([{'type': 'null'}, json_schema])
            if json_schema is None:
                if _core_utils.is_core_schema(schema_or_field) or _core_utils.is_core_schema_field(schema_or_field):
                    generate_for_schema_type = self._schema_type_to_method[schema_or_field['type']]
                    json_schema = generate_for_schema_type(schema_or_field)
                else:
                    raise TypeError(f'Unexpected schema type: schema={schema_or_field}')
            if _core_utils.is_core_schema(schema_or_field):
                json_schema = populate_defs(schema_or_field, json_schema)
            return json_schema

        current_handler = _schema_generation_shared.GenerateJsonSchemaHandler(self, handler_func)

        metadata = cast(_core_metadata.CoreMetadata, schema.get('metadata', {}))

        # TODO: I dislike that we have to wrap these basic dict updates in callables, is there any way around this?

        if js_updates := metadata.get('pydantic_js_updates'):

            def js_updates_handler_func(
                schema_or_field: CoreSchemaOrField,
                current_handler: GetJsonSchemaHandler = current_handler,
            ) -> JsonSchemaValue:
                json_schema = {**current_handler(schema_or_field), **js_updates}
                return json_schema

            current_handler = _schema_generation_shared.GenerateJsonSchemaHandler(self, js_updates_handler_func)

        if js_extra := metadata.get('pydantic_js_extra'):

            def js_extra_handler_func(
                schema_or_field: CoreSchemaOrField,
                current_handler: GetJsonSchemaHandler = current_handler,
            ) -> JsonSchemaValue:
                json_schema = current_handler(schema_or_field)
                if isinstance(js_extra, dict):
                    json_schema.update(to_jsonable_python(js_extra))
                elif callable(js_extra):
                    # similar to typing issue in _update_class_schema when we're working with callable js extra
                    js_extra(json_schema)  # type: ignore
                return json_schema

            current_handler = _schema_generation_shared.GenerateJsonSchemaHandler(self, js_extra_handler_func)

        for js_modify_function in metadata.get('pydantic_js_functions', ()):

            def new_handler_func(
                schema_or_field: CoreSchemaOrField,
                current_handler: GetJsonSchemaHandler = current_handler,
                js_modify_function: GetJsonSchemaFunction = js_modify_function,
            ) -> JsonSchemaValue:
                json_schema = js_modify_function(schema_or_field, current_handler)
                if _core_utils.is_core_schema(schema_or_field):
                    json_schema = populate_defs(schema_or_field, json_schema)
                original_schema = current_handler.resolve_ref_schema(json_schema)
                ref = json_schema.pop('$ref', None)
                if ref and json_schema:
                    original_schema.update(json_schema)
                return original_schema

            current_handler = _schema_generation_shared.GenerateJsonSchemaHandler(self, new_handler_func)

        for js_modify_function in metadata.get('pydantic_js_annotation_functions', ()):

            def new_handler_func(
                schema_or_field: CoreSchemaOrField,
                current_handler: GetJsonSchemaHandler = current_handler,
                js_modify_function: GetJsonSchemaFunction = js_modify_function,
            ) -> JsonSchemaValue:
                json_schema = js_modify_function(schema_or_field, current_handler)
                if _core_utils.is_core_schema(schema_or_field):
                    json_schema = populate_defs(schema_or_field, json_schema)
                return json_schema

            current_handler = _schema_generation_shared.GenerateJsonSchemaHandler(self, new_handler_func)

        json_schema = current_handler(schema)
        if _core_utils.is_core_schema(schema):
            json_schema = populate_defs(schema, json_schema)
        return json_schema

    def sort(self, value: JsonSchemaValue, parent_key: str | None = None) -> JsonSchemaValue:
        """Override this method to customize the sorting of the JSON schema (e.g., don't sort at all, sort all keys unconditionally, etc.)

        By default, alphabetically sort the keys in the JSON schema, skipping the 'properties' and 'default' keys to preserve field definition order.
        This sort is recursive, so it will sort all nested dictionaries as well.
        """
        sorted_dict: dict[str, JsonSchemaValue] = {}
        keys = value.keys()
        if parent_key not in ('properties', 'default'):
            keys = sorted(keys)
        for key in keys:
            sorted_dict[key] = self._sort_recursive(value[key], parent_key=key)
        return sorted_dict

    def _sort_recursive(self, value: Any, parent_key: str | None = None) -> Any:
        """Recursively sort a JSON schema value."""
        if isinstance(value, dict):
            sorted_dict: dict[str, JsonSchemaValue] = {}
            keys = value.keys()
            if parent_key not in ('properties', 'default'):
                keys = sorted(keys)
            for key in keys:
                sorted_dict[key] = self._sort_recursive(value[key], parent_key=key)
            return sorted_dict
        elif isinstance(value, list):
            sorted_list: list[JsonSchemaValue] = []
            for item in value:
                sorted_list.append(self._sort_recursive(item, parent_key))
            return sorted_list
        else:
            return value

    # ### Schema generation methods

    def invalid_schema(self, schema: core_schema.InvalidSchema) -> JsonSchemaValue:
        """Placeholder - should never be called."""

        raise RuntimeError('Cannot generate schema for invalid_schema. This is a bug! Please report it.')

    def any_schema(self, schema: core_schema.AnySchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches any value.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        return {}

    def none_schema(self, schema: core_schema.NoneSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches `None`.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        return {'type': 'null'}

    def bool_schema(self, schema: core_schema.BoolSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a bool value.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        return {'type': 'boolean'}

    def int_schema(self, schema: core_schema.IntSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches an int value.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        json_schema: dict[str, Any] = {'type': 'integer'}
        self.update_with_validations(json_schema, schema, self.ValidationsMapping.numeric)
        json_schema = {k: v for k, v in json_schema.items() if v not in {math.inf, -math.inf}}
        return json_schema

    def float_schema(self, schema: core_schema.FloatSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a float value.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        json_schema: dict[str, Any] = {'type': 'number'}
        self.update_with_validations(json_schema, schema, self.ValidationsMapping.numeric)
        json_schema = {k: v for k, v in json_schema.items() if v not in {math.inf, -math.inf}}
        return json_schema

    def decimal_schema(self, schema: core_schema.DecimalSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a decimal value.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        json_schema = self.str_schema(core_schema.str_schema())
        if self.mode == 'validation':
            multiple_of = schema.get('multiple_of')
            le = schema.get('le')
            ge = schema.get('ge')
            lt = schema.get('lt')
            gt = schema.get('gt')
            json_schema = {
                'anyOf': [
                    self.float_schema(
                        core_schema.float_schema(
                            allow_inf_nan=schema.get('allow_inf_nan'),
                            multiple_of=None if multiple_of is None else float(multiple_of),
                            le=None if le is None else float(le),
                            ge=None if ge is None else float(ge),
                            lt=None if lt is None else float(lt),
                            gt=None if gt is None else float(gt),
                        )
                    ),
                    json_schema,
                ],
            }
        return json_schema

    def str_schema(self, schema: core_schema.StringSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a string value.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        json_schema = {'type': 'string'}
        self.update_with_validations(json_schema, schema, self.ValidationsMapping.string)
        if isinstance(json_schema.get('pattern'), Pattern):
            # TODO: should we add regex flags to the pattern?
            json_schema['pattern'] = json_schema.get('pattern').pattern  # type: ignore
        return json_schema

    def bytes_schema(self, schema: core_schema.BytesSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a bytes value.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        json_schema = {'type': 'string', 'format': 'base64url' if self._config.ser_json_bytes == 'base64' else 'binary'}
        self.update_with_validations(json_schema, schema, self.ValidationsMapping.bytes)
        return json_schema

    def date_schema(self, schema: core_schema.DateSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a date value.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        return {'type': 'string', 'format': 'date'}

    def time_schema(self, schema: core_schema.TimeSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a time value.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        return {'type': 'string', 'format': 'time'}

    def datetime_schema(self, schema: core_schema.DatetimeSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a datetime value.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        return {'type': 'string', 'format': 'date-time'}

    def timedelta_schema(self, schema: core_schema.TimedeltaSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a timedelta value.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        if self._config.ser_json_timedelta == 'float':
            return {'type': 'number'}
        return {'type': 'string', 'format': 'duration'}

    def literal_schema(self, schema: core_schema.LiteralSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a literal value.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        expected = [v.value if isinstance(v, Enum) else v for v in schema['expected']]
        # jsonify the expected values
        expected = [to_jsonable_python(v) for v in expected]

        result: dict[str, Any] = {}
        if len(expected) == 1:
            result['const'] = expected[0]
        else:
            result['enum'] = expected

        types = {type(e) for e in expected}
        if types == {str}:
            result['type'] = 'string'
        elif types == {int}:
            result['type'] = 'integer'
        elif types == {float}:
            result['type'] = 'number'
        elif types == {bool}:
            result['type'] = 'boolean'
        elif types == {list}:
            result['type'] = 'array'
        elif types == {type(None)}:
            result['type'] = 'null'
        return result

    def enum_schema(self, schema: core_schema.EnumSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches an Enum value.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        enum_type = schema['cls']
        description = None if not enum_type.__doc__ else inspect.cleandoc(enum_type.__doc__)
        if (
            description == 'An enumeration.'
        ):  # This is the default value provided by enum.EnumMeta.__new__; don't use it
            description = None
        result: dict[str, Any] = {'title': enum_type.__name__, 'description': description}
        result = {k: v for k, v in result.items() if v is not None}

        expected = [to_jsonable_python(v.value) for v in schema['members']]

        result['enum'] = expected

        types = {type(e) for e in expected}
        if isinstance(enum_type, str) or types == {str}:
            result['type'] = 'string'
        elif isinstance(enum_type, int) or types == {int}:
            result['type'] = 'integer'
        elif isinstance(enum_type, float) or types == {float}:
            result['type'] = 'number'
        elif types == {bool}:
            result['type'] = 'boolean'
        elif types == {list}:
            result['type'] = 'array'

        return result

    def is_instance_schema(self, schema: core_schema.IsInstanceSchema) -> JsonSchemaValue:
        """Handles JSON schema generation for a core schema that checks if a value is an instance of a class.

        Unless overridden in a subclass, this raises an error.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        return self.handle_invalid_for_json_schema(schema, f'core_schema.IsInstanceSchema ({schema["cls"]})')

    def is_subclass_schema(self, schema: core_schema.IsSubclassSchema) -> JsonSchemaValue:
        """Handles JSON schema generation for a core schema that checks if a value is a subclass of a class.

        For backwards compatibility with v1, this does not raise an error, but can be overridden to change this.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        # Note: This is for compatibility with V1; you can override if you want different behavior.
        return {}

    def callable_schema(self, schema: core_schema.CallableSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a callable value.

        Unless overridden in a subclass, this raises an error.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        return self.handle_invalid_for_json_schema(schema, 'core_schema.CallableSchema')

    def list_schema(self, schema: core_schema.ListSchema) -> JsonSchemaValue:
        """Returns a schema that matches a list schema.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        items_schema = {} if 'items_schema' not in schema else self.generate_inner(schema['items_schema'])
        json_schema = {'type': 'array', 'items': items_schema}
        self.update_with_validations(json_schema, schema, self.ValidationsMapping.array)
        return json_schema

    @deprecated('`tuple_positional_schema` is deprecated. Use `tuple_schema` instead.', category=None)
    @final
    def tuple_positional_schema(self, schema: core_schema.TupleSchema) -> JsonSchemaValue:
        """Replaced by `tuple_schema`."""
        warnings.warn(
            '`tuple_positional_schema` is deprecated. Use `tuple_schema` instead.',
            PydanticDeprecatedSince26,
            stacklevel=2,
        )
        return self.tuple_schema(schema)

    @deprecated('`tuple_variable_schema` is deprecated. Use `tuple_schema` instead.', category=None)
    @final
    def tuple_variable_schema(self, schema: core_schema.TupleSchema) -> JsonSchemaValue:
        """Replaced by `tuple_schema`."""
        warnings.warn(
            '`tuple_variable_schema` is deprecated. Use `tuple_schema` instead.',
            PydanticDeprecatedSince26,
            stacklevel=2,
        )
        return self.tuple_schema(schema)

    def tuple_schema(self, schema: core_schema.TupleSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a tuple schema e.g. `Tuple[int,
        str, bool]` or `Tuple[int, ...]`.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        json_schema: JsonSchemaValue = {'type': 'array'}
        if 'variadic_item_index' in schema:
            variadic_item_index = schema['variadic_item_index']
            if variadic_item_index > 0:
                json_schema['minItems'] = variadic_item_index
                json_schema['prefixItems'] = [
                    self.generate_inner(item) for item in schema['items_schema'][:variadic_item_index]
                ]
            if variadic_item_index + 1 == len(schema['items_schema']):
                # if the variadic item is the last item, then represent it faithfully
                json_schema['items'] = self.generate_inner(schema['items_schema'][variadic_item_index])
            else:
                # otherwise, 'items' represents the schema for the variadic
                # item plus the suffix, so just allow anything for simplicity
                # for now
                json_schema['items'] = True
        else:
            prefixItems = [self.generate_inner(item) for item in schema['items_schema']]
            if prefixItems:
                json_schema['prefixItems'] = prefixItems
            json_schema['minItems'] = len(prefixItems)
            json_schema['maxItems'] = len(prefixItems)
        self.update_with_validations(json_schema, schema, self.ValidationsMapping.array)
        return json_schema

    def set_schema(self, schema: core_schema.SetSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a set schema.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        return self._common_set_schema(schema)

    def frozenset_schema(self, schema: core_schema.FrozenSetSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a frozenset schema.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        return self._common_set_schema(schema)

    def _common_set_schema(self, schema: core_schema.SetSchema | core_schema.FrozenSetSchema) -> JsonSchemaValue:
        items_schema = {} if 'items_schema' not in schema else self.generate_inner(schema['items_schema'])
        json_schema = {'type': 'array', 'uniqueItems': True, 'items': items_schema}
        self.update_with_validations(json_schema, schema, self.ValidationsMapping.array)
        return json_schema

    def generator_schema(self, schema: core_schema.GeneratorSchema) -> JsonSchemaValue:
        """Returns a JSON schema that represents the provided GeneratorSchema.

        Args:
            schema: The schema.

        Returns:
            The generated JSON schema.
        """
        items_schema = {} if 'items_schema' not in schema else self.generate_inner(schema['items_schema'])
        json_schema = {'type': 'array', 'items': items_schema}
        self.update_with_validations(json_schema, schema, self.ValidationsMapping.array)
        return json_schema

    def dict_schema(self, schema: core_schema.DictSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a dict schema.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        json_schema: JsonSchemaValue = {'type': 'object'}

        keys_schema = self.resolve_ref_schema(
            self.generate_inner(schema['keys_schema']).copy() if 'keys_schema' in schema else {}
        )
        keys_pattern = keys_schema.pop('pattern', None)

        values_schema = self.generate_inner(schema['values_schema']).copy() if 'values_schema' in schema else {}
        # don't give a title to additionalProperties, patternProperties and propertyNames
        values_schema.pop('title', None)
        keys_schema.pop('title', None)
        if values_schema or keys_pattern is not None:  # don't add additionalProperties if it's empty
            if keys_pattern is None:
                json_schema['additionalProperties'] = values_schema
            else:
                json_schema['patternProperties'] = {keys_pattern: values_schema}

        # The len check indicates that constraints are probably present:
        if keys_schema.get('type') == 'string' and len(keys_schema) > 1:
            keys_schema.pop('type')
            json_schema['propertyNames'] = keys_schema

        self.update_with_validations(json_schema, schema, self.ValidationsMapping.object)
        return json_schema

    def function_before_schema(self, schema: core_schema.BeforeValidatorFunctionSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a function-before schema.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        if self._mode == 'validation' and (
            input_schema := schema.get('metadata', {}).get('pydantic_js_input_core_schema')
        ):
            return self.generate_inner(input_schema)

        return self.generate_inner(schema['schema'])

    def function_after_schema(self, schema: core_schema.AfterValidatorFunctionSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a function-after schema.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        return self.generate_inner(schema['schema'])

    def function_plain_schema(self, schema: core_schema.PlainValidatorFunctionSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a function-plain schema.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        if self._mode == 'validation' and (
            input_schema := schema.get('metadata', {}).get('pydantic_js_input_core_schema')
        ):
            return self.generate_inner(input_schema)

        return self.handle_invalid_for_json_schema(
            schema, f'core_schema.PlainValidatorFunctionSchema ({schema["function"]})'
        )

    def function_wrap_schema(self, schema: core_schema.WrapValidatorFunctionSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a function-wrap schema.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        if self._mode == 'validation' and (
            input_schema := schema.get('metadata', {}).get('pydantic_js_input_core_schema')
        ):
            return self.generate_inner(input_schema)

        return self.generate_inner(schema['schema'])

    def default_schema(self, schema: core_schema.WithDefaultSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema with a default value.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        json_schema = self.generate_inner(schema['schema'])

        if 'default' not in schema:
            return json_schema
        default = schema['default']
        # Note: if you want to include the value returned by the default_factory,
        # override this method and replace the code above with:
        # if 'default' in schema:
        #     default = schema['default']
        # elif 'default_factory' in schema:
        #     default = schema['default_factory']()
        # else:
        #     return json_schema

        # we reflect the application of custom plain, no-info serializers to defaults for
        # JSON Schemas viewed in serialization mode:
        # TODO: improvements along with https://github.com/pydantic/pydantic/issues/8208
        if (
            self.mode == 'serialization'
            and (ser_schema := schema['schema'].get('serialization'))
            and (ser_func := ser_schema.get('function'))
            and ser_schema.get('type') == 'function-plain'
            and not ser_schema.get('info_arg')
            and not (default is None and ser_schema.get('when_used') in ('unless-none', 'json-unless-none'))
        ):
            try:
                default = ser_func(default)  # type: ignore
            except Exception:
                # It might be that the provided default needs to be validated (read: parsed) first
                # (assuming `validate_default` is enabled). However, we can't perform
                # such validation during JSON Schema generation so we don't support
                # this pattern for now.
                # (One example is when using `foo: ByteSize = '1MB'`, which validates and
                # serializes as an int. In this case, `ser_func` is `int` and `int('1MB')` fails).
                self.emit_warning(
                    'non-serializable-default',
                    f'Unable to serialize value {default!r} with the plain serializer; excluding default from JSON schema',
                )
                return json_schema

        try:
            encoded_default = self.encode_default(default)
        except pydantic_core.PydanticSerializationError:
            self.emit_warning(
                'non-serializable-default',
                f'Default value {default} is not JSON serializable; excluding default from JSON schema',
            )
            # Return the inner schema, as though there was no default
            return json_schema

        json_schema['default'] = encoded_default
        return json_schema

    def nullable_schema(self, schema: core_schema.NullableSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that allows null values.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        null_schema = {'type': 'null'}
        inner_json_schema = self.generate_inner(schema['schema'])

        if inner_json_schema == null_schema:
            return null_schema
        else:
            # Thanks to the equality check against `null_schema` above, I think 'oneOf' would also be valid here;
            # I'll use 'anyOf' for now, but it could be changed it if it would work better with some external tooling
            return self.get_flattened_anyof([inner_json_schema, null_schema])

    def union_schema(self, schema: core_schema.UnionSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that allows values matching any of the given schemas.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        generated: list[JsonSchemaValue] = []

        choices = schema['choices']
        for choice in choices:
            # choice will be a tuple if an explicit label was provided
            choice_schema = choice[0] if isinstance(choice, tuple) else choice
            try:
                generated.append(self.generate_inner(choice_schema))
            except PydanticOmit:
                continue
            except PydanticInvalidForJsonSchema as exc:
                self.emit_warning('skipped-choice', exc.message)
        if len(generated) == 1:
            return generated[0]
        return self.get_flattened_anyof(generated)

    def tagged_union_schema(self, schema: core_schema.TaggedUnionSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that allows values matching any of the given schemas, where
        the schemas are tagged with a discriminator field that indicates which schema should be used to validate
        the value.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        generated: dict[str, JsonSchemaValue] = {}
        for k, v in schema['choices'].items():
            if isinstance(k, Enum):
                k = k.value
            try:
                # Use str(k) since keys must be strings for json; while not technically correct,
                # it's the closest that can be represented in valid JSON
                generated[str(k)] = self.generate_inner(v).copy()
            except PydanticOmit:
                continue
            except PydanticInvalidForJsonSchema as exc:
                self.emit_warning('skipped-choice', exc.message)

        one_of_choices = _deduplicate_schemas(generated.values())
        json_schema: JsonSchemaValue = {'oneOf': one_of_choices}

        # This reflects the v1 behavior; TODO: we should make it possible to exclude OpenAPI stuff from the JSON schema
        openapi_discriminator = self._extract_discriminator(schema, one_of_choices)
        if openapi_discriminator is not None:
            json_schema['discriminator'] = {
                'propertyName': openapi_discriminator,
                'mapping': {k: v.get('$ref', v) for k, v in generated.items()},
            }

        return json_schema

    def _extract_discriminator(
        self, schema: core_schema.TaggedUnionSchema, one_of_choices: list[JsonDict]
    ) -> str | None:
        """Extract a compatible OpenAPI discriminator from the schema and one_of choices that end up in the final
        schema."""
        openapi_discriminator: str | None = None

        if isinstance(schema['discriminator'], str):
            return schema['discriminator']

        if isinstance(schema['discriminator'], list):
            # If the discriminator is a single item list containing a string, that is equivalent to the string case
            if len(schema['discriminator']) == 1 and isinstance(schema['discriminator'][0], str):
                return schema['discriminator'][0]
            # When an alias is used that is different from the field name, the discriminator will be a list of single
            # str lists, one for the attribute and one for the actual alias. The logic here will work even if there is
            # more than one possible attribute, and looks for whether a single alias choice is present as a documented
            # property on all choices. If so, that property will be used as the OpenAPI discriminator.
            for alias_path in schema['discriminator']:
                if not isinstance(alias_path, list):
                    break  # this means that the discriminator is not a list of alias paths
                if len(alias_path) != 1:
                    continue  # this means that the "alias" does not represent a single field
                alias = alias_path[0]
                if not isinstance(alias, str):
                    continue  # this means that the "alias" does not represent a field
                alias_is_present_on_all_choices = True
                for choice in one_of_choices:
                    try:
                        choice = self.resolve_ref_schema(choice)
                    except RuntimeError as exc:
                        # TODO: fixme - this is a workaround for the fact that we can't always resolve refs
                        # for tagged union choices at this point in the schema gen process, we might need to do
                        # another pass at the end like we do for core schemas
                        self.emit_warning('skipped-discriminator', str(exc))
                        choice = {}
                    properties = choice.get('properties', {})
                    if not isinstance(properties, dict) or alias not in properties:
                        alias_is_present_on_all_choices = False
                        break
                if alias_is_present_on_all_choices:
                    openapi_discriminator = alias
                    break
        return openapi_discriminator

    def chain_schema(self, schema: core_schema.ChainSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a core_schema.ChainSchema.

        When generating a schema for validation, we return the validation JSON schema for the first step in the chain.
        For serialization, we return the serialization JSON schema for the last step in the chain.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        step_index = 0 if self.mode == 'validation' else -1  # use first step for validation, last for serialization
        return self.generate_inner(schema['steps'][step_index])

    def lax_or_strict_schema(self, schema: core_schema.LaxOrStrictSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that allows values matching either the lax schema or the
        strict schema.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        # TODO: Need to read the default value off of model config or whatever
        use_strict = schema.get('strict', False)  # TODO: replace this default False
        # If your JSON schema fails to generate it is probably
        # because one of the following two branches failed.
        if use_strict:
            return self.generate_inner(schema['strict_schema'])
        else:
            return self.generate_inner(schema['lax_schema'])

    def json_or_python_schema(self, schema: core_schema.JsonOrPythonSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that allows values matching either the JSON schema or the
        Python schema.

        The JSON schema is used instead of the Python schema. If you want to use the Python schema, you should override
        this method.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        return self.generate_inner(schema['json_schema'])

    def typed_dict_schema(self, schema: core_schema.TypedDictSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that defines a typed dict.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        total = schema.get('total', True)
        named_required_fields: list[tuple[str, bool, CoreSchemaField]] = [
            (name, self.field_is_required(field, total), field)
            for name, field in schema['fields'].items()
            if self.field_is_present(field)
        ]
        if self.mode == 'serialization':
            named_required_fields.extend(self._name_required_computed_fields(schema.get('computed_fields', [])))
        cls = schema.get('cls')
        config = _get_typed_dict_config(cls)
        with self._config_wrapper_stack.push(config):
            json_schema = self._named_required_fields_schema(named_required_fields)

        if cls is not None:
            self._update_class_schema(json_schema, cls, config)
        else:
            extra = config.get('extra')
            if extra == 'forbid':
                json_schema['additionalProperties'] = False
            elif extra == 'allow':
                json_schema['additionalProperties'] = True

        return json_schema

    @staticmethod
    def _name_required_computed_fields(
        computed_fields: list[ComputedField],
    ) -> list[tuple[str, bool, core_schema.ComputedField]]:
        return [(field['property_name'], True, field) for field in computed_fields]

    def _named_required_fields_schema(
        self, named_required_fields: Sequence[tuple[str, bool, CoreSchemaField]]
    ) -> JsonSchemaValue:
        properties: dict[str, JsonSchemaValue] = {}
        required_fields: list[str] = []
        for name, required, field in named_required_fields:
            if self.by_alias:
                name = self._get_alias_name(field, name)
            try:
                field_json_schema = self.generate_inner(field).copy()
            except PydanticOmit:
                continue
            if 'title' not in field_json_schema and self.field_title_should_be_set(field):
                title = self.get_title_from_name(name)
                field_json_schema['title'] = title
            field_json_schema = self.handle_ref_overrides(field_json_schema)
            properties[name] = field_json_schema
            if required:
                required_fields.append(name)

        json_schema = {'type': 'object', 'properties': properties}
        if required_fields:
            json_schema['required'] = required_fields
        return json_schema

    def _get_alias_name(self, field: CoreSchemaField, name: str) -> str:
        if field['type'] == 'computed-field':
            alias: Any = field.get('alias', name)
        elif self.mode == 'validation':
            alias = field.get('validation_alias', name)
        else:
            alias = field.get('serialization_alias', name)
        if isinstance(alias, str):
            name = alias
        elif isinstance(alias, list):
            alias = cast('list[str] | str', alias)
            for path in alias:
                if isinstance(path, list) and len(path) == 1 and isinstance(path[0], str):
                    # Use the first valid single-item string path; the code that constructs the alias array
                    # should ensure the first such item is what belongs in the JSON schema
                    name = path[0]
                    break
        else:
            assert_never(alias)
        return name

    def typed_dict_field_schema(self, schema: core_schema.TypedDictField) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that defines a typed dict field.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        return self.generate_inner(schema['schema'])

    def dataclass_field_schema(self, schema: core_schema.DataclassField) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that defines a dataclass field.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        return self.generate_inner(schema['schema'])

    def model_field_schema(self, schema: core_schema.ModelField) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that defines a model field.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        return self.generate_inner(schema['schema'])

    def computed_field_schema(self, schema: core_schema.ComputedField) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that defines a computed field.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        return self.generate_inner(schema['return_schema'])

    def model_schema(self, schema: core_schema.ModelSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that defines a model.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        # We do not use schema['model'].model_json_schema() here
        # because it could lead to inconsistent refs handling, etc.
        cls = cast('type[BaseModel]', schema['cls'])
        config = cls.model_config

        with self._config_wrapper_stack.push(config):
            json_schema = self.generate_inner(schema['schema'])

        self._update_class_schema(json_schema, cls, config)

        return json_schema

    def _update_class_schema(self, json_schema: JsonSchemaValue, cls: type[Any], config: ConfigDict) -> None:
        """Update json_schema with the following, extracted from `config` and `cls`:

        * title
        * description
        * additional properties
        * json_schema_extra
        * deprecated

        Done in place, hence there's no return value as the original json_schema is mutated.
        No ref resolving is involved here, as that's not appropriate for simple updates.
        """
        from .main import BaseModel
        from .root_model import RootModel

        if (config_title := config.get('title')) is not None:
            json_schema.setdefault('title', config_title)
        elif model_title_generator := config.get('model_title_generator'):
            title = model_title_generator(cls)
            if not isinstance(title, str):
                raise TypeError(f'model_title_generator {model_title_generator} must return str, not {title.__class__}')
            json_schema.setdefault('title', title)
        if 'title' not in json_schema:
            json_schema['title'] = cls.__name__

        # BaseModel and dataclasses; don't use cls.__doc__ as it will contain the verbose class signature by default
        docstring = None if cls is BaseModel or dataclasses.is_dataclass(cls) else cls.__doc__

        if docstring:
            json_schema.setdefault('description', inspect.cleandoc(docstring))
        elif issubclass(cls, RootModel) and (root_description := cls.__pydantic_fields__['root'].description):
            json_schema.setdefault('description', root_description)

        extra = config.get('extra')
        if 'additionalProperties' not in json_schema:
            if extra == 'allow':
                json_schema['additionalProperties'] = True
            elif extra == 'forbid':
                json_schema['additionalProperties'] = False

        json_schema_extra = config.get('json_schema_extra')
        if issubclass(cls, BaseModel) and cls.__pydantic_root_model__:
            root_json_schema_extra = cls.model_fields['root'].json_schema_extra
            if json_schema_extra and root_json_schema_extra:
                raise ValueError(
                    '"model_config[\'json_schema_extra\']" and "Field.json_schema_extra" on "RootModel.root"'
                    ' field must not be set simultaneously'
                )
            if root_json_schema_extra:
                json_schema_extra = root_json_schema_extra

        if isinstance(json_schema_extra, (staticmethod, classmethod)):
            # In older versions of python, this is necessary to ensure staticmethod/classmethods are callable
            json_schema_extra = json_schema_extra.__get__(cls)

        if isinstance(json_schema_extra, dict):
            json_schema.update(json_schema_extra)
        elif callable(json_schema_extra):
            # FIXME: why are there type ignores here? We support two signatures for json_schema_extra callables...
            if len(inspect.signature(json_schema_extra).parameters) > 1:
                json_schema_extra(json_schema, cls)  # type: ignore
            else:
                json_schema_extra(json_schema)  # type: ignore
        elif json_schema_extra is not None:
            raise ValueError(
                f"model_config['json_schema_extra']={json_schema_extra} should be a dict, callable, or None"
            )

        if hasattr(cls, '__deprecated__'):
            json_schema['deprecated'] = True

    def resolve_ref_schema(self, json_schema: JsonSchemaValue) -> JsonSchemaValue:
        """Resolve a JsonSchemaValue to the non-ref schema if it is a $ref schema.

        Args:
            json_schema: The schema to resolve.

        Returns:
            The resolved schema.
        """
        if '$ref' not in json_schema:
            return json_schema

        ref = json_schema['$ref']
        schema_to_update = self.get_schema_from_definitions(JsonRef(ref))
        if schema_to_update is None:
            raise RuntimeError(f'Cannot update undefined schema for $ref={ref}')
        return self.resolve_ref_schema(schema_to_update)

    def model_fields_schema(self, schema: core_schema.ModelFieldsSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that defines a model's fields.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        named_required_fields: list[tuple[str, bool, CoreSchemaField]] = [
            (name, self.field_is_required(field, total=True), field)
            for name, field in schema['fields'].items()
            if self.field_is_present(field)
        ]
        if self.mode == 'serialization':
            named_required_fields.extend(self._name_required_computed_fields(schema.get('computed_fields', [])))
        json_schema = self._named_required_fields_schema(named_required_fields)
        extras_schema = schema.get('extras_schema', None)
        if extras_schema is not None:
            schema_to_update = self.resolve_ref_schema(json_schema)
            schema_to_update['additionalProperties'] = self.generate_inner(extras_schema)
        return json_schema

    def field_is_present(self, field: CoreSchemaField) -> bool:
        """Whether the field should be included in the generated JSON schema.

        Args:
            field: The schema for the field itself.

        Returns:
            `True` if the field should be included in the generated JSON schema, `False` otherwise.
        """
        if self.mode == 'serialization':
            # If you still want to include the field in the generated JSON schema,
            # override this method and return True
            return not field.get('serialization_exclude')
        elif self.mode == 'validation':
            return True
        else:
            assert_never(self.mode)

    def field_is_required(
        self,
        field: core_schema.ModelField | core_schema.DataclassField | core_schema.TypedDictField,
        total: bool,
    ) -> bool:
        """Whether the field should be marked as required in the generated JSON schema.
        (Note that this is irrelevant if the field is not present in the JSON schema.).

        Args:
            field: The schema for the field itself.
            total: Only applies to `TypedDictField`s.
                Indicates if the `TypedDict` this field belongs to is total, in which case any fields that don't
                explicitly specify `required=False` are required.

        Returns:
            `True` if the field should be marked as required in the generated JSON schema, `False` otherwise.
        """
        if self.mode == 'serialization' and self._config.json_schema_serialization_defaults_required:
            return not field.get('serialization_exclude')
        else:
            if field['type'] == 'typed-dict-field':
                return field.get('required', total)
            else:
                return field['schema']['type'] != 'default'

    def dataclass_args_schema(self, schema: core_schema.DataclassArgsSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that defines a dataclass's constructor arguments.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        named_required_fields: list[tuple[str, bool, CoreSchemaField]] = [
            (field['name'], self.field_is_required(field, total=True), field)
            for field in schema['fields']
            if self.field_is_present(field)
        ]
        if self.mode == 'serialization':
            named_required_fields.extend(self._name_required_computed_fields(schema.get('computed_fields', [])))
        return self._named_required_fields_schema(named_required_fields)

    def dataclass_schema(self, schema: core_schema.DataclassSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that defines a dataclass.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        from ._internal._dataclasses import is_builtin_dataclass

        cls = schema['cls']
        config: ConfigDict = getattr(cls, '__pydantic_config__', cast('ConfigDict', {}))

        with self._config_wrapper_stack.push(config):
            json_schema = self.generate_inner(schema['schema']).copy()

        self._update_class_schema(json_schema, cls, config)

        # Dataclass-specific handling of description
        if is_builtin_dataclass(cls):
            # vanilla dataclass; don't use cls.__doc__ as it will contain the class signature by default
            description = None
        else:
            description = None if cls.__doc__ is None else inspect.cleandoc(cls.__doc__)
        if description:
            json_schema['description'] = description

        return json_schema

    def arguments_schema(self, schema: core_schema.ArgumentsSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that defines a function's arguments.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        prefer_positional = schema.get('metadata', {}).get('pydantic_js_prefer_positional_arguments')

        arguments = schema['arguments_schema']
        kw_only_arguments = [a for a in arguments if a.get('mode') == 'keyword_only']
        kw_or_p_arguments = [a for a in arguments if a.get('mode') in {'positional_or_keyword', None}]
        p_only_arguments = [a for a in arguments if a.get('mode') == 'positional_only']
        var_args_schema = schema.get('var_args_schema')
        var_kwargs_schema = schema.get('var_kwargs_schema')

        if prefer_positional:
            positional_possible = not kw_only_arguments and not var_kwargs_schema
            if positional_possible:
                return self.p_arguments_schema(p_only_arguments + kw_or_p_arguments, var_args_schema)

        keyword_possible = not p_only_arguments and not var_args_schema
        if keyword_possible:
            return self.kw_arguments_schema(kw_or_p_arguments + kw_only_arguments, var_kwargs_schema)

        if not prefer_positional:
            positional_possible = not kw_only_arguments and not var_kwargs_schema
            if positional_possible:
                return self.p_arguments_schema(p_only_arguments + kw_or_p_arguments, var_args_schema)

        raise PydanticInvalidForJsonSchema(
            'Unable to generate JSON schema for arguments validator with positional-only and keyword-only arguments'
        )

    def kw_arguments_schema(
        self, arguments: list[core_schema.ArgumentsParameter], var_kwargs_schema: CoreSchema | None
    ) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that defines a function's keyword arguments.

        Args:
            arguments: The core schema.

        Returns:
            The generated JSON schema.
        """
        properties: dict[str, JsonSchemaValue] = {}
        required: list[str] = []
        for argument in arguments:
            name = self.get_argument_name(argument)
            argument_schema = self.generate_inner(argument['schema']).copy()
            argument_schema['title'] = self.get_title_from_name(name)
            properties[name] = argument_schema

            if argument['schema']['type'] != 'default':
                # This assumes that if the argument has a default value,
                # the inner schema must be of type WithDefaultSchema.
                # I believe this is true, but I am not 100% sure
                required.append(name)

        json_schema: JsonSchemaValue = {'type': 'object', 'properties': properties}
        if required:
            json_schema['required'] = required

        if var_kwargs_schema:
            additional_properties_schema = self.generate_inner(var_kwargs_schema)
            if additional_properties_schema:
                json_schema['additionalProperties'] = additional_properties_schema
        else:
            json_schema['additionalProperties'] = False
        return json_schema

    def p_arguments_schema(
        self, arguments: list[core_schema.ArgumentsParameter], var_args_schema: CoreSchema | None
    ) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that defines a function's positional arguments.

        Args:
            arguments: The core schema.

        Returns:
            The generated JSON schema.
        """
        prefix_items: list[JsonSchemaValue] = []
        min_items = 0

        for argument in arguments:
            name = self.get_argument_name(argument)

            argument_schema = self.generate_inner(argument['schema']).copy()
            argument_schema['title'] = self.get_title_from_name(name)
            prefix_items.append(argument_schema)

            if argument['schema']['type'] != 'default':
                # This assumes that if the argument has a default value,
                # the inner schema must be of type WithDefaultSchema.
                # I believe this is true, but I am not 100% sure
                min_items += 1

        json_schema: JsonSchemaValue = {'type': 'array'}
        if prefix_items:
            json_schema['prefixItems'] = prefix_items
        if min_items:
            json_schema['minItems'] = min_items

        if var_args_schema:
            items_schema = self.generate_inner(var_args_schema)
            if items_schema:
                json_schema['items'] = items_schema
        else:
            json_schema['maxItems'] = len(prefix_items)

        return json_schema

    def get_argument_name(self, argument: core_schema.ArgumentsParameter) -> str:
        """Retrieves the name of an argument.

        Args:
            argument: The core schema.

        Returns:
            The name of the argument.
        """
        name = argument['name']
        if self.by_alias:
            alias = argument.get('alias')
            if isinstance(alias, str):
                name = alias
            else:
                pass  # might want to do something else?
        return name

    def call_schema(self, schema: core_schema.CallSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that defines a function call.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        return self.generate_inner(schema['arguments_schema'])

    def custom_error_schema(self, schema: core_schema.CustomErrorSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that defines a custom error.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        return self.generate_inner(schema['schema'])

    def json_schema(self, schema: core_schema.JsonSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that defines a JSON object.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        content_core_schema = schema.get('schema') or core_schema.any_schema()
        content_json_schema = self.generate_inner(content_core_schema)
        if self.mode == 'validation':
            return {'type': 'string', 'contentMediaType': 'application/json', 'contentSchema': content_json_schema}
        else:
            # self.mode == 'serialization'
            return content_json_schema

    def url_schema(self, schema: core_schema.UrlSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that defines a URL.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        json_schema = {'type': 'string', 'format': 'uri', 'minLength': 1}
        self.update_with_validations(json_schema, schema, self.ValidationsMapping.string)
        return json_schema

    def multi_host_url_schema(self, schema: core_schema.MultiHostUrlSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that defines a URL that can be used with multiple hosts.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        # Note: 'multi-host-uri' is a custom/pydantic-specific format, not part of the JSON Schema spec
        json_schema = {'type': 'string', 'format': 'multi-host-uri', 'minLength': 1}
        self.update_with_validations(json_schema, schema, self.ValidationsMapping.string)
        return json_schema

    def uuid_schema(self, schema: core_schema.UuidSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a UUID.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        return {'type': 'string', 'format': 'uuid'}

    def definitions_schema(self, schema: core_schema.DefinitionsSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that defines a JSON object with definitions.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        for definition in schema['definitions']:
            try:
                self.generate_inner(definition)
            except PydanticInvalidForJsonSchema as e:
                core_ref: CoreRef = CoreRef(definition['ref'])  # type: ignore
                self._core_defs_invalid_for_json_schema[self.get_defs_ref((core_ref, self.mode))] = e
                continue
        return self.generate_inner(schema['schema'])

    def definition_ref_schema(self, schema: core_schema.DefinitionReferenceSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that references a definition.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        core_ref = CoreRef(schema['schema_ref'])
        _, ref_json_schema = self.get_cache_defs_ref_schema(core_ref)
        return ref_json_schema

    def ser_schema(
        self, schema: core_schema.SerSchema | core_schema.IncExSeqSerSchema | core_schema.IncExDictSerSchema
    ) -> JsonSchemaValue | None:
        """Generates a JSON schema that matches a schema that defines a serialized object.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        schema_type = schema['type']
        if schema_type == 'function-plain' or schema_type == 'function-wrap':
            # PlainSerializerFunctionSerSchema or WrapSerializerFunctionSerSchema
            return_schema = schema.get('return_schema')
            if return_schema is not None:
                return self.generate_inner(return_schema)
        elif schema_type == 'format' or schema_type == 'to-string':
            # FormatSerSchema or ToStringSerSchema
            return self.str_schema(core_schema.str_schema())
        elif schema['type'] == 'model':
            # ModelSerSchema
            return self.generate_inner(schema['schema'])
        return None

    def complex_schema(self, schema: core_schema.ComplexSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a complex number.

        JSON has no standard way to represent complex numbers. Complex number is not a numeric
        type. Here we represent complex number as strings following the rule defined by Python.
        For instance, '1+2j' is an accepted complex string. Details can be found in
        [Python's `complex` documentation][complex].

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        return {'type': 'string'}

    # ### Utility methods

    def get_title_from_name(self, name: str) -> str:
        """Retrieves a title from a name.

        Args:
            name: The name to retrieve a title from.

        Returns:
            The title.
        """
        return name.title().replace('_', ' ').strip()

    def field_title_should_be_set(self, schema: CoreSchemaOrField) -> bool:
        """Returns true if a field with the given schema should have a title set based on the field name.

        Intuitively, we want this to return true for schemas that wouldn't otherwise provide their own title
        (e.g., int, float, str), and false for those that would (e.g., BaseModel subclasses).

        Args:
            schema: The schema to check.

        Returns:
            `True` if the field should have a title set, `False` otherwise.
        """
        if _core_utils.is_core_schema_field(schema):
            if schema['type'] == 'computed-field':
                field_schema = schema['return_schema']
            else:
                field_schema = schema['schema']
            return self.field_title_should_be_set(field_schema)

        elif _core_utils.is_core_schema(schema):
            if schema.get('ref'):  # things with refs, such as models and enums, should not have titles set
                return False
            if schema['type'] in {'default', 'nullable', 'definitions'}:
                return self.field_title_should_be_set(schema['schema'])  # type: ignore[typeddict-item]
            if _core_utils.is_function_with_inner_schema(schema):
                return self.field_title_should_be_set(schema['schema'])
            if schema['type'] == 'definition-ref':
                # Referenced schemas should not have titles set for the same reason
                # schemas with refs should not
                return False
            return True  # anything else should have title set

        else:
            raise PydanticInvalidForJsonSchema(f'Unexpected schema type: schema={schema}')  # pragma: no cover

    def normalize_name(self, name: str) -> str:
        """Normalizes a name to be used as a key in a dictionary.

        Args:
            name: The name to normalize.

        Returns:
            The normalized name.
        """
        return re.sub(r'[^a-zA-Z0-9.\-_]', '_', name).replace('.', '__')

    def get_defs_ref(self, core_mode_ref: CoreModeRef) -> DefsRef:
        """Override this method to change the way that definitions keys are generated from a core reference.

        Args:
            core_mode_ref: The core reference.

        Returns:
            The definitions key.
        """
        # Split the core ref into "components"; generic origins and arguments are each separate components
        core_ref, mode = core_mode_ref
        components = re.split(r'([\][,])', core_ref)
        # Remove IDs from each component
        components = [x.rsplit(':', 1)[0] for x in components]
        core_ref_no_id = ''.join(components)
        # Remove everything before the last period from each "component"
        components = [re.sub(r'(?:[^.[\]]+\.)+((?:[^.[\]]+))', r'\1', x) for x in components]
        short_ref = ''.join(components)

        mode_title = _MODE_TITLE_MAPPING[mode]

        # It is important that the generated defs_ref values be such that at least one choice will not
        # be generated for any other core_ref. Currently, this should be the case because we include
        # the id of the source type in the core_ref
        name = DefsRef(self.normalize_name(short_ref))
        name_mode = DefsRef(self.normalize_name(short_ref) + f'-{mode_title}')
        module_qualname = DefsRef(self.normalize_name(core_ref_no_id))
        module_qualname_mode = DefsRef(f'{module_qualname}-{mode_title}')
        module_qualname_id = DefsRef(self.normalize_name(core_ref))
        occurrence_index = self._collision_index.get(module_qualname_id)
        if occurrence_index is None:
            self._collision_counter[module_qualname] += 1
            occurrence_index = self._collision_index[module_qualname_id] = self._collision_counter[module_qualname]

        module_qualname_occurrence = DefsRef(f'{module_qualname}__{occurrence_index}')
        module_qualname_occurrence_mode = DefsRef(f'{module_qualname_mode}__{occurrence_index}')

        self._prioritized_defsref_choices[module_qualname_occurrence_mode] = [
            name,
            name_mode,
            module_qualname,
            module_qualname_mode,
            module_qualname_occurrence,
            module_qualname_occurrence_mode,
        ]

        return module_qualname_occurrence_mode

    def get_cache_defs_ref_schema(self, core_ref: CoreRef) -> tuple[DefsRef, JsonSchemaValue]:
        """This method wraps the get_defs_ref method with some cache-lookup/population logic,
        and returns both the produced defs_ref and the JSON schema that will refer to the right definition.

        Args:
            core_ref: The core reference to get the definitions reference for.

        Returns:
            A tuple of the definitions reference and the JSON schema that will refer to it.
        """
        core_mode_ref = (core_ref, self.mode)
        maybe_defs_ref = self.core_to_defs_refs.get(core_mode_ref)
        if maybe_defs_ref is not None:
            json_ref = self.core_to_json_refs[core_mode_ref]
            return maybe_defs_ref, {'$ref': json_ref}

        defs_ref = self.get_defs_ref(core_mode_ref)

        # populate the ref translation mappings
        self.core_to_defs_refs[core_mode_ref] = defs_ref
        self.defs_to_core_refs[defs_ref] = core_mode_ref

        json_ref = JsonRef(self.ref_template.format(model=defs_ref))
        self.core_to_json_refs[core_mode_ref] = json_ref
        self.json_to_defs_refs[json_ref] = defs_ref
        ref_json_schema = {'$ref': json_ref}
        return defs_ref, ref_json_schema

    def handle_ref_overrides(self, json_schema: JsonSchemaValue) -> JsonSchemaValue:
        """Remove any sibling keys that are redundant with the referenced schema.

        Args:
            json_schema: The schema to remove redundant sibling keys from.

        Returns:
            The schema with redundant sibling keys removed.
        """
        if '$ref' in json_schema:
            # prevent modifications to the input; this copy may be safe to drop if there is significant overhead
            json_schema = json_schema.copy()

            referenced_json_schema = self.get_schema_from_definitions(JsonRef(json_schema['$ref']))
            if referenced_json_schema is None:
                # This can happen when building schemas for models with not-yet-defined references.
                # It may be a good idea to do a recursive pass at the end of the generation to remove
                # any redundant override keys.
                return json_schema
            for k, v in list(json_schema.items()):
                if k == '$ref':
                    continue
                if k in referenced_json_schema and referenced_json_schema[k] == v:
                    del json_schema[k]  # redundant key

        return json_schema

    def get_schema_from_definitions(self, json_ref: JsonRef) -> JsonSchemaValue | None:
        try:
            def_ref = self.json_to_defs_refs[json_ref]
            if def_ref in self._core_defs_invalid_for_json_schema:
                raise self._core_defs_invalid_for_json_schema[def_ref]
            return self.definitions.get(def_ref, None)
        except KeyError:
            if json_ref.startswith(('http://', 'https://')):
                return None
            raise

    def encode_default(self, dft: Any) -> Any:
        """Encode a default value to a JSON-serializable value.

        This is used to encode default values for fields in the generated JSON schema.

        Args:
            dft: The default value to encode.

        Returns:
            The encoded default value.
        """
        from .type_adapter import TypeAdapter, _type_has_config

        config = self._config
        try:
            default = (
                dft
                if _type_has_config(type(dft))
                else TypeAdapter(type(dft), config=config.config_dict).dump_python(dft, mode='json')
            )
        except PydanticSchemaGenerationError:
            raise pydantic_core.PydanticSerializationError(f'Unable to encode default value {dft}')

        return pydantic_core.to_jsonable_python(
            default,
            timedelta_mode=config.ser_json_timedelta,
            bytes_mode=config.ser_json_bytes,
        )

    def update_with_validations(
        self, json_schema: JsonSchemaValue, core_schema: CoreSchema, mapping: dict[str, str]
    ) -> None:
        """Update the json_schema with the corresponding validations specified in the core_schema,
        using the provided mapping to translate keys in core_schema to the appropriate keys for a JSON schema.

        Args:
            json_schema: The JSON schema to update.
            core_schema: The core schema to get the validations from.
            mapping: A mapping from core_schema attribute names to the corresponding JSON schema attribute names.
        """
        for core_key, json_schema_key in mapping.items():
            if core_key in core_schema:
                json_schema[json_schema_key] = core_schema[core_key]

    class ValidationsMapping:
        """This class just contains mappings from core_schema attribute names to the corresponding
        JSON schema attribute names. While I suspect it is unlikely to be necessary, you can in
        principle override this class in a subclass of GenerateJsonSchema (by inheriting from
        GenerateJsonSchema.ValidationsMapping) to change these mappings.
        """

        numeric = {
            'multiple_of': 'multipleOf',
            'le': 'maximum',
            'ge': 'minimum',
            'lt': 'exclusiveMaximum',
            'gt': 'exclusiveMinimum',
        }
        bytes = {
            'min_length': 'minLength',
            'max_length': 'maxLength',
        }
        string = {
            'min_length': 'minLength',
            'max_length': 'maxLength',
            'pattern': 'pattern',
        }
        array = {
            'min_length': 'minItems',
            'max_length': 'maxItems',
        }
        object = {
            'min_length': 'minProperties',
            'max_length': 'maxProperties',
        }

    def get_flattened_anyof(self, schemas: list[JsonSchemaValue]) -> JsonSchemaValue:
        members = []
        for schema in schemas:
            if len(schema) == 1 and 'anyOf' in schema:
                members.extend(schema['anyOf'])
            else:
                members.append(schema)
        members = _deduplicate_schemas(members)
        if len(members) == 1:
            return members[0]
        return {'anyOf': members}

    def get_json_ref_counts(self, json_schema: JsonSchemaValue) -> dict[JsonRef, int]:
        """Get all values corresponding to the key '$ref' anywhere in the json_schema."""
        json_refs: dict[JsonRef, int] = Counter()

        def _add_json_refs(schema: Any) -> None:
            if isinstance(schema, dict):
                if '$ref' in schema:
                    json_ref = JsonRef(schema['$ref'])
                    if not isinstance(json_ref, str):
                        return  # in this case, '$ref' might have been the name of a property
                    already_visited = json_ref in json_refs
                    json_refs[json_ref] += 1
                    if already_visited:
                        return  # prevent recursion on a definition that was already visited
                    try:
                        defs_ref = self.json_to_defs_refs[json_ref]
                        if defs_ref in self._core_defs_invalid_for_json_schema:
                            raise self._core_defs_invalid_for_json_schema[defs_ref]
                        _add_json_refs(self.definitions[defs_ref])
                    except KeyError:
                        if not json_ref.startswith(('http://', 'https://')):
                            raise

                for k, v in schema.items():
                    if k == 'examples':
                        continue  # skip refs processing for examples, allow arbitrary values / refs
                    _add_json_refs(v)
            elif isinstance(schema, list):
                for v in schema:
                    _add_json_refs(v)

        _add_json_refs(json_schema)
        return json_refs

    def handle_invalid_for_json_schema(self, schema: CoreSchemaOrField, error_info: str) -> JsonSchemaValue:
        raise PydanticInvalidForJsonSchema(f'Cannot generate a JsonSchema for {error_info}')

    def emit_warning(self, kind: JsonSchemaWarningKind, detail: str) -> None:
        """This method simply emits PydanticJsonSchemaWarnings based on handling in the `warning_message` method."""
        message = self.render_warning_message(kind, detail)
        if message is not None:
            warnings.warn(message, PydanticJsonSchemaWarning)

    def render_warning_message(self, kind: JsonSchemaWarningKind, detail: str) -> str | None:
        """This method is responsible for ignoring warnings as desired, and for formatting the warning messages.

        You can override the value of `ignored_warning_kinds` in a subclass of GenerateJsonSchema
        to modify what warnings are generated. If you want more control, you can override this method;
        just return None in situations where you don't want warnings to be emitted.

        Args:
            kind: The kind of warning to render. It can be one of the following:

                - 'skipped-choice': A choice field was skipped because it had no valid choices.
                - 'non-serializable-default': A default value was skipped because it was not JSON-serializable.
            detail: A string with additional details about the warning.

        Returns:
            The formatted warning message, or `None` if no warning should be emitted.
        """
        if kind in self.ignored_warning_kinds:
            return None
        return f'{detail} [{kind}]'

    def _build_definitions_remapping(self) -> _DefinitionsRemapping:
        defs_to_json: dict[DefsRef, JsonRef] = {}
        for defs_refs in self._prioritized_defsref_choices.values():
            for defs_ref in defs_refs:
                json_ref = JsonRef(self.ref_template.format(model=defs_ref))
                defs_to_json[defs_ref] = json_ref

        return _DefinitionsRemapping.from_prioritized_choices(
            self._prioritized_defsref_choices, defs_to_json, self.definitions
        )

    def _garbage_collect_definitions(self, schema: JsonSchemaValue) -> None:
        visited_defs_refs: set[DefsRef] = set()
        unvisited_json_refs = _get_all_json_refs(schema)
        while unvisited_json_refs:
            next_json_ref = unvisited_json_refs.pop()
            try:
                next_defs_ref = self.json_to_defs_refs[next_json_ref]
                if next_defs_ref in visited_defs_refs:
                    continue
                visited_defs_refs.add(next_defs_ref)
                unvisited_json_refs.update(_get_all_json_refs(self.definitions[next_defs_ref]))
            except KeyError:
                if not next_json_ref.startswith(('http://', 'https://')):
                    raise

        self.definitions = {k: v for k, v in self.definitions.items() if k in visited_defs_refs}


# ##### Start JSON Schema Generation Functions #####


def model_json_schema(
    cls: type[BaseModel] | type[PydanticDataclass],
    by_alias: bool = True,
    ref_template: str = DEFAULT_REF_TEMPLATE,
    schema_generator: type[GenerateJsonSchema] = GenerateJsonSchema,
    mode: JsonSchemaMode = 'validation',
) -> dict[str, Any]:
    """Utility function to generate a JSON Schema for a model.

    Args:
        cls: The model class to generate a JSON Schema for.
        by_alias: If `True` (the default), fields will be serialized according to their alias.
            If `False`, fields will be serialized according to their attribute name.
        ref_template: The template to use for generating JSON Schema references.
        schema_generator: The class to use for generating the JSON Schema.
        mode: The mode to use for generating the JSON Schema. It can be one of the following:

            - 'validation': Generate a JSON Schema for validating data.
            - 'serialization': Generate a JSON Schema for serializing data.

    Returns:
        The generated JSON Schema.
    """
    from .main import BaseModel

    schema_generator_instance = schema_generator(by_alias=by_alias, ref_template=ref_template)

    if isinstance(cls.__pydantic_core_schema__, _mock_val_ser.MockCoreSchema):
        cls.__pydantic_core_schema__.rebuild()

    if cls is BaseModel:
        raise AttributeError('model_json_schema() must be called on a subclass of BaseModel, not BaseModel itself.')

    assert not isinstance(cls.__pydantic_core_schema__, _mock_val_ser.MockCoreSchema), 'this is a bug! please report it'
    return schema_generator_instance.generate(cls.__pydantic_core_schema__, mode=mode)


def models_json_schema(
    models: Sequence[tuple[type[BaseModel] | type[PydanticDataclass], JsonSchemaMode]],
    *,
    by_alias: bool = True,
    title: str | None = None,
    description: str | None = None,
    ref_template: str = DEFAULT_REF_TEMPLATE,
    schema_generator: type[GenerateJsonSchema] = GenerateJsonSchema,
) -> tuple[dict[tuple[type[BaseModel] | type[PydanticDataclass], JsonSchemaMode], JsonSchemaValue], JsonSchemaValue]:
    """Utility function to generate a JSON Schema for multiple models.

    Args:
        models: A sequence of tuples of the form (model, mode).
        by_alias: Whether field aliases should be used as keys in the generated JSON Schema.
        title: The title of the generated JSON Schema.
        description: The description of the generated JSON Schema.
        ref_template: The reference template to use for generating JSON Schema references.
        schema_generator: The schema generator to use for generating the JSON Schema.

    Returns:
        A tuple where:
            - The first element is a dictionary whose keys are tuples of JSON schema key type and JSON mode, and
                whose values are the JSON schema corresponding to that pair of inputs. (These schemas may have
                JsonRef references to definitions that are defined in the second returned element.)
            - The second element is a JSON schema containing all definitions referenced in the first returned
                    element, along with the optional title and description keys.
    """
    for cls, _ in models:
        if isinstance(cls.__pydantic_core_schema__, _mock_val_ser.MockCoreSchema):
            cls.__pydantic_core_schema__.rebuild()

    instance = schema_generator(by_alias=by_alias, ref_template=ref_template)
    inputs: list[tuple[type[BaseModel] | type[PydanticDataclass], JsonSchemaMode, CoreSchema]] = [
        (m, mode, m.__pydantic_core_schema__) for m, mode in models
    ]
    json_schemas_map, definitions = instance.generate_definitions(inputs)

    json_schema: dict[str, Any] = {}
    if definitions:
        json_schema['$defs'] = definitions
    if title:
        json_schema['title'] = title
    if description:
        json_schema['description'] = description

    return json_schemas_map, json_schema


# ##### End JSON Schema Generation Functions #####


_HashableJsonValue: TypeAlias = Union[
    int, float, str, bool, None, Tuple['_HashableJsonValue', ...], Tuple[Tuple[str, '_HashableJsonValue'], ...]
]


def _deduplicate_schemas(schemas: Iterable[JsonDict]) -> list[JsonDict]:
    return list({_make_json_hashable(schema): schema for schema in schemas}.values())


def _make_json_hashable(value: JsonValue) -> _HashableJsonValue:
    if isinstance(value, dict):
        return tuple(sorted((k, _make_json_hashable(v)) for k, v in value.items()))
    elif isinstance(value, list):
        return tuple(_make_json_hashable(v) for v in value)
    else:
        return value


@dataclasses.dataclass(**_internal_dataclass.slots_true)
class WithJsonSchema:
    """Usage docs: https://docs.pydantic.dev/2.10/concepts/json_schema/#withjsonschema-annotation

    Add this as an annotation on a field to override the (base) JSON schema that would be generated for that field.
    This provides a way to set a JSON schema for types that would otherwise raise errors when producing a JSON schema,
    such as Callable, or types that have an is-instance core schema, without needing to go so far as creating a
    custom subclass of pydantic.json_schema.GenerateJsonSchema.
    Note that any _modifications_ to the schema that would normally be made (such as setting the title for model fields)
    will still be performed.

    If `mode` is set this will only apply to that schema generation mode, allowing you
    to set different json schemas for validation and serialization.
    """

    json_schema: JsonSchemaValue | None
    mode: Literal['validation', 'serialization'] | None = None

    def __get_pydantic_json_schema__(
        self, core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        mode = self.mode or handler.mode
        if mode != handler.mode:
            return handler(core_schema)
        if self.json_schema is None:
            # This exception is handled in pydantic.json_schema.GenerateJsonSchema._named_required_fields_schema
            raise PydanticOmit
        else:
            return self.json_schema

    def __hash__(self) -> int:
        return hash(type(self.mode))


class Examples:
    """Add examples to a JSON schema.

    If the JSON Schema already contains examples, the provided examples
    will be appended.

    If `mode` is set this will only apply to that schema generation mode,
    allowing you to add different examples for validation and serialization.
    """

    @overload
    @deprecated('Using a dict for `examples` is deprecated since v2.9 and will be removed in v3.0. Use a list instead.')
    def __init__(
        self, examples: dict[str, Any], mode: Literal['validation', 'serialization'] | None = None
    ) -> None: ...

    @overload
    def __init__(self, examples: list[Any], mode: Literal['validation', 'serialization'] | None = None) -> None: ...

    def __init__(
        self, examples: dict[str, Any] | list[Any], mode: Literal['validation', 'serialization'] | None = None
    ) -> None:
        if isinstance(examples, dict):
            warnings.warn(
                'Using a dict for `examples` is deprecated, use a list instead.',
                PydanticDeprecatedSince29,
                stacklevel=2,
            )
        self.examples = examples
        self.mode = mode

    def __get_pydantic_json_schema__(
        self, core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        mode = self.mode or handler.mode
        json_schema = handler(core_schema)
        if mode != handler.mode:
            return json_schema
        examples = json_schema.get('examples')
        if examples is None:
            json_schema['examples'] = to_jsonable_python(self.examples)
        if isinstance(examples, dict):
            if isinstance(self.examples, list):
                warnings.warn(
                    'Updating existing JSON Schema examples of type dict with examples of type list. '
                    'Only the existing examples values will be retained. Note that dict support for '
                    'examples is deprecated and will be removed in v3.0.',
                    UserWarning,
                )
                json_schema['examples'] = to_jsonable_python(
                    [ex for value in examples.values() for ex in value] + self.examples
                )
            else:
                json_schema['examples'] = to_jsonable_python({**examples, **self.examples})
        if isinstance(examples, list):
            if isinstance(self.examples, list):
                json_schema['examples'] = to_jsonable_python(examples + self.examples)
            elif isinstance(self.examples, dict):
                warnings.warn(
                    'Updating existing JSON Schema examples of type list with examples of type dict. '
                    'Only the examples values will be retained. Note that dict support for '
                    'examples is deprecated and will be removed in v3.0.',
                    UserWarning,
                )
                json_schema['examples'] = to_jsonable_python(
                    examples + [ex for value in self.examples.values() for ex in value]
                )

        return json_schema

    def __hash__(self) -> int:
        return hash(type(self.mode))


def _get_all_json_refs(item: Any) -> set[JsonRef]:
    """Get all the definitions references from a JSON schema."""
    refs: set[JsonRef] = set()
    stack = [item]

    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            for key, value in current.items():
                if key == 'examples':
                    continue  # skip examples, allow arbitrary values / refs
                if key == '$ref' and isinstance(value, str):
                    refs.add(JsonRef(value))
                elif isinstance(value, dict):
                    stack.append(value)
                elif isinstance(value, list):
                    stack.extend(value)
        elif isinstance(current, list):
            stack.extend(current)

    return refs


AnyType = TypeVar('AnyType')

if TYPE_CHECKING:
    SkipJsonSchema = Annotated[AnyType, ...]
else:

    @dataclasses.dataclass(**_internal_dataclass.slots_true)
    class SkipJsonSchema:
        """Usage docs: https://docs.pydantic.dev/2.10/concepts/json_schema/#skipjsonschema-annotation

        Add this as an annotation on a field to skip generating a JSON schema for that field.

        Example:
            ```python
            from typing import Union

            from pydantic import BaseModel
            from pydantic.json_schema import SkipJsonSchema

            from pprint import pprint

            class Model(BaseModel):
                a: Union[int, None] = None  # (1)!
                b: Union[int, SkipJsonSchema[None]] = None  # (2)!
                c: SkipJsonSchema[Union[int, None]] = None  # (3)!

            pprint(Model.model_json_schema())
            '''
            {
                'properties': {
                    'a': {
                        'anyOf': [
                            {'type': 'integer'},
                            {'type': 'null'}
                        ],
                        'default': None,
                        'title': 'A'
                    },
                    'b': {
                        'default': None,
                        'title': 'B',
                        'type': 'integer'
                    }
                },
                'title': 'Model',
                'type': 'object'
            }
            '''
            ```

            1. The integer and null types are both included in the schema for `a`.
            2. The integer type is the only type included in the schema for `b`.
            3. The entirety of the `c` field is omitted from the schema.
        """

        def __class_getitem__(cls, item: AnyType) -> AnyType:
            return Annotated[item, cls()]

        def __get_pydantic_json_schema__(
            self, core_schema: CoreSchema, handler: GetJsonSchemaHandler
        ) -> JsonSchemaValue:
            raise PydanticOmit

        def __hash__(self) -> int:
            return hash(type(self))


def _get_typed_dict_config(cls: type[Any] | None) -> ConfigDict:
    if cls is not None:
        try:
            return _decorators.get_attribute_from_bases(cls, '__pydantic_config__')
        except AttributeError:
            pass
    return {}
