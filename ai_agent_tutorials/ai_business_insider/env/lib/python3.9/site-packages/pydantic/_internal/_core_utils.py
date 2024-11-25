from __future__ import annotations

import os
from collections import defaultdict
from typing import Any, Callable, Hashable, TypeVar, Union

from pydantic_core import CoreSchema, core_schema
from pydantic_core import validate_core_schema as _validate_core_schema
from typing_extensions import TypeGuard, get_args, get_origin

from ..errors import PydanticUserError
from . import _repr
from ._core_metadata import CoreMetadata
from ._typing_extra import is_generic_alias, is_type_alias_type

AnyFunctionSchema = Union[
    core_schema.AfterValidatorFunctionSchema,
    core_schema.BeforeValidatorFunctionSchema,
    core_schema.WrapValidatorFunctionSchema,
    core_schema.PlainValidatorFunctionSchema,
]


FunctionSchemaWithInnerSchema = Union[
    core_schema.AfterValidatorFunctionSchema,
    core_schema.BeforeValidatorFunctionSchema,
    core_schema.WrapValidatorFunctionSchema,
]

CoreSchemaField = Union[
    core_schema.ModelField, core_schema.DataclassField, core_schema.TypedDictField, core_schema.ComputedField
]
CoreSchemaOrField = Union[core_schema.CoreSchema, CoreSchemaField]

_CORE_SCHEMA_FIELD_TYPES = {'typed-dict-field', 'dataclass-field', 'model-field', 'computed-field'}
_FUNCTION_WITH_INNER_SCHEMA_TYPES = {'function-before', 'function-after', 'function-wrap'}
_LIST_LIKE_SCHEMA_WITH_ITEMS_TYPES = {'list', 'set', 'frozenset'}

TAGGED_UNION_TAG_KEY = 'pydantic.internal.tagged_union_tag'
"""
Used in a `Tag` schema to specify the tag used for a discriminated union.
"""


def is_core_schema(
    schema: CoreSchemaOrField,
) -> TypeGuard[CoreSchema]:
    return schema['type'] not in _CORE_SCHEMA_FIELD_TYPES


def is_core_schema_field(
    schema: CoreSchemaOrField,
) -> TypeGuard[CoreSchemaField]:
    return schema['type'] in _CORE_SCHEMA_FIELD_TYPES


def is_function_with_inner_schema(
    schema: CoreSchemaOrField,
) -> TypeGuard[FunctionSchemaWithInnerSchema]:
    return schema['type'] in _FUNCTION_WITH_INNER_SCHEMA_TYPES


def is_list_like_schema_with_items_schema(
    schema: CoreSchema,
) -> TypeGuard[core_schema.ListSchema | core_schema.SetSchema | core_schema.FrozenSetSchema]:
    return schema['type'] in _LIST_LIKE_SCHEMA_WITH_ITEMS_TYPES


def get_type_ref(type_: type[Any], args_override: tuple[type[Any], ...] | None = None) -> str:
    """Produces the ref to be used for this type by pydantic_core's core schemas.

    This `args_override` argument was added for the purpose of creating valid recursive references
    when creating generic models without needing to create a concrete class.
    """
    origin = get_origin(type_) or type_

    args = get_args(type_) if is_generic_alias(type_) else (args_override or ())
    generic_metadata = getattr(type_, '__pydantic_generic_metadata__', None)
    if generic_metadata:
        origin = generic_metadata['origin'] or origin
        args = generic_metadata['args'] or args

    module_name = getattr(origin, '__module__', '<No __module__>')
    if is_type_alias_type(origin):
        type_ref = f'{module_name}.{origin.__name__}:{id(origin)}'
    else:
        try:
            qualname = getattr(origin, '__qualname__', f'<No __qualname__: {origin}>')
        except Exception:
            qualname = getattr(origin, '__qualname__', '<No __qualname__>')
        type_ref = f'{module_name}.{qualname}:{id(origin)}'

    arg_refs: list[str] = []
    for arg in args:
        if isinstance(arg, str):
            # Handle string literals as a special case; we may be able to remove this special handling if we
            # wrap them in a ForwardRef at some point.
            arg_ref = f'{arg}:str-{id(arg)}'
        else:
            arg_ref = f'{_repr.display_as_type(arg)}:{id(arg)}'
        arg_refs.append(arg_ref)
    if arg_refs:
        type_ref = f'{type_ref}[{",".join(arg_refs)}]'
    return type_ref


def get_ref(s: core_schema.CoreSchema) -> None | str:
    """Get the ref from the schema if it has one.
    This exists just for type checking to work correctly.
    """
    return s.get('ref', None)


def collect_definitions(schema: core_schema.CoreSchema) -> dict[str, core_schema.CoreSchema]:
    defs: dict[str, CoreSchema] = {}

    def _record_valid_refs(s: core_schema.CoreSchema, recurse: Recurse) -> core_schema.CoreSchema:
        ref = get_ref(s)
        if ref:
            defs[ref] = s
        return recurse(s, _record_valid_refs)

    walk_core_schema(schema, _record_valid_refs, copy=False)

    return defs


def define_expected_missing_refs(
    schema: core_schema.CoreSchema, allowed_missing_refs: set[str]
) -> core_schema.CoreSchema | None:
    if not allowed_missing_refs:
        # in this case, there are no missing refs to potentially substitute, so there's no need to walk the schema
        # this is a common case (will be hit for all non-generic models), so it's worth optimizing for
        return None

    refs = collect_definitions(schema).keys()

    expected_missing_refs = allowed_missing_refs.difference(refs)
    if expected_missing_refs:
        definitions: list[core_schema.CoreSchema] = [
            core_schema.invalid_schema(ref=ref) for ref in expected_missing_refs
        ]
        return core_schema.definitions_schema(schema, definitions)
    return None


def collect_invalid_schemas(schema: core_schema.CoreSchema) -> bool:
    invalid = False

    def _is_schema_valid(s: core_schema.CoreSchema, recurse: Recurse) -> core_schema.CoreSchema:
        nonlocal invalid

        if s['type'] == 'invalid':
            invalid = True
            return s

        return recurse(s, _is_schema_valid)

    walk_core_schema(schema, _is_schema_valid, copy=False)
    return invalid


T = TypeVar('T')


Recurse = Callable[[core_schema.CoreSchema, 'Walk'], core_schema.CoreSchema]
Walk = Callable[[core_schema.CoreSchema, Recurse], core_schema.CoreSchema]

# TODO: Should we move _WalkCoreSchema into pydantic_core proper?
#   Issue: https://github.com/pydantic/pydantic-core/issues/615

CoreSchemaT = TypeVar('CoreSchemaT')


class _WalkCoreSchema:
    def __init__(self, *, copy: bool = True):
        self._schema_type_to_method = self._build_schema_type_to_method()
        self._copy = copy

    def _copy_schema(self, schema: CoreSchemaT) -> CoreSchemaT:
        return schema.copy() if self._copy else schema  # pyright: ignore[reportAttributeAccessIssue]

    def _build_schema_type_to_method(self) -> dict[core_schema.CoreSchemaType, Recurse]:
        mapping: dict[core_schema.CoreSchemaType, Recurse] = {}
        key: core_schema.CoreSchemaType
        for key in get_args(core_schema.CoreSchemaType):
            method_name = f"handle_{key.replace('-', '_')}_schema"
            mapping[key] = getattr(self, method_name, self._handle_other_schemas)
        return mapping

    def walk(self, schema: core_schema.CoreSchema, f: Walk) -> core_schema.CoreSchema:
        return f(schema, self._walk)

    def _walk(self, schema: core_schema.CoreSchema, f: Walk) -> core_schema.CoreSchema:
        schema = self._schema_type_to_method[schema['type']](self._copy_schema(schema), f)
        ser_schema: core_schema.SerSchema | None = schema.get('serialization')  # type: ignore
        if ser_schema:
            schema['serialization'] = self._handle_ser_schemas(ser_schema, f)
        return schema

    def _handle_other_schemas(self, schema: core_schema.CoreSchema, f: Walk) -> core_schema.CoreSchema:
        sub_schema = schema.get('schema', None)
        if sub_schema is not None:
            schema['schema'] = self.walk(sub_schema, f)  # type: ignore
        return schema

    def _handle_ser_schemas(self, ser_schema: core_schema.SerSchema, f: Walk) -> core_schema.SerSchema:
        schema: core_schema.CoreSchema | None = ser_schema.get('schema', None)
        return_schema: core_schema.CoreSchema | None = ser_schema.get('return_schema', None)
        if schema is not None or return_schema is not None:
            ser_schema = self._copy_schema(ser_schema)
            if schema is not None:
                ser_schema['schema'] = self.walk(schema, f)  # type: ignore
            if return_schema is not None:
                ser_schema['return_schema'] = self.walk(return_schema, f)  # type: ignore
        return ser_schema

    def handle_definitions_schema(self, schema: core_schema.DefinitionsSchema, f: Walk) -> core_schema.CoreSchema:
        new_definitions: list[core_schema.CoreSchema] = []
        for definition in schema['definitions']:
            if 'schema_ref' in definition and 'ref' in definition:
                # This indicates a purposely indirect reference
                # We want to keep such references around for implications related to JSON schema, etc.:
                new_definitions.append(definition)
                # However, we still need to walk the referenced definition:
                self.walk(definition, f)
                continue

            updated_definition = self.walk(definition, f)
            if 'ref' in updated_definition:
                # If the updated definition schema doesn't have a 'ref', it shouldn't go in the definitions
                # This is most likely to happen due to replacing something with a definition reference, in
                # which case it should certainly not go in the definitions list
                new_definitions.append(updated_definition)
        new_inner_schema = self.walk(schema['schema'], f)

        if not new_definitions and len(schema) == 3:
            # This means we'd be returning a "trivial" definitions schema that just wrapped the inner schema
            return new_inner_schema

        new_schema = self._copy_schema(schema)
        new_schema['schema'] = new_inner_schema
        new_schema['definitions'] = new_definitions
        return new_schema

    def handle_list_schema(self, schema: core_schema.ListSchema, f: Walk) -> core_schema.CoreSchema:
        items_schema = schema.get('items_schema')
        if items_schema is not None:
            schema['items_schema'] = self.walk(items_schema, f)
        return schema

    def handle_set_schema(self, schema: core_schema.SetSchema, f: Walk) -> core_schema.CoreSchema:
        items_schema = schema.get('items_schema')
        if items_schema is not None:
            schema['items_schema'] = self.walk(items_schema, f)
        return schema

    def handle_frozenset_schema(self, schema: core_schema.FrozenSetSchema, f: Walk) -> core_schema.CoreSchema:
        items_schema = schema.get('items_schema')
        if items_schema is not None:
            schema['items_schema'] = self.walk(items_schema, f)
        return schema

    def handle_generator_schema(self, schema: core_schema.GeneratorSchema, f: Walk) -> core_schema.CoreSchema:
        items_schema = schema.get('items_schema')
        if items_schema is not None:
            schema['items_schema'] = self.walk(items_schema, f)
        return schema

    def handle_tuple_schema(self, schema: core_schema.TupleSchema, f: Walk) -> core_schema.CoreSchema:
        schema['items_schema'] = [self.walk(v, f) for v in schema['items_schema']]
        return schema

    def handle_dict_schema(self, schema: core_schema.DictSchema, f: Walk) -> core_schema.CoreSchema:
        keys_schema = schema.get('keys_schema')
        if keys_schema is not None:
            schema['keys_schema'] = self.walk(keys_schema, f)
        values_schema = schema.get('values_schema')
        if values_schema:
            schema['values_schema'] = self.walk(values_schema, f)
        return schema

    def handle_function_schema(self, schema: AnyFunctionSchema, f: Walk) -> core_schema.CoreSchema:
        if not is_function_with_inner_schema(schema):
            return schema
        schema['schema'] = self.walk(schema['schema'], f)
        return schema

    def handle_union_schema(self, schema: core_schema.UnionSchema, f: Walk) -> core_schema.CoreSchema:
        new_choices: list[CoreSchema | tuple[CoreSchema, str]] = []
        for v in schema['choices']:
            if isinstance(v, tuple):
                new_choices.append((self.walk(v[0], f), v[1]))
            else:
                new_choices.append(self.walk(v, f))
        schema['choices'] = new_choices
        return schema

    def handle_tagged_union_schema(self, schema: core_schema.TaggedUnionSchema, f: Walk) -> core_schema.CoreSchema:
        new_choices: dict[Hashable, core_schema.CoreSchema] = {}
        for k, v in schema['choices'].items():
            new_choices[k] = v if isinstance(v, (str, int)) else self.walk(v, f)
        schema['choices'] = new_choices
        return schema

    def handle_chain_schema(self, schema: core_schema.ChainSchema, f: Walk) -> core_schema.CoreSchema:
        schema['steps'] = [self.walk(v, f) for v in schema['steps']]
        return schema

    def handle_lax_or_strict_schema(self, schema: core_schema.LaxOrStrictSchema, f: Walk) -> core_schema.CoreSchema:
        schema['lax_schema'] = self.walk(schema['lax_schema'], f)
        schema['strict_schema'] = self.walk(schema['strict_schema'], f)
        return schema

    def handle_json_or_python_schema(self, schema: core_schema.JsonOrPythonSchema, f: Walk) -> core_schema.CoreSchema:
        schema['json_schema'] = self.walk(schema['json_schema'], f)
        schema['python_schema'] = self.walk(schema['python_schema'], f)
        return schema

    def handle_model_fields_schema(self, schema: core_schema.ModelFieldsSchema, f: Walk) -> core_schema.CoreSchema:
        extras_schema = schema.get('extras_schema')
        if extras_schema is not None:
            schema['extras_schema'] = self.walk(extras_schema, f)
        replaced_fields: dict[str, core_schema.ModelField] = {}
        replaced_computed_fields: list[core_schema.ComputedField] = []
        for computed_field in schema.get('computed_fields', ()):
            replaced_field = self._copy_schema(computed_field)
            replaced_field['return_schema'] = self.walk(computed_field['return_schema'], f)
            replaced_computed_fields.append(replaced_field)
        if replaced_computed_fields:
            schema['computed_fields'] = replaced_computed_fields
        for k, v in schema['fields'].items():
            replaced_field = self._copy_schema(v)
            replaced_field['schema'] = self.walk(v['schema'], f)
            replaced_fields[k] = replaced_field
        schema['fields'] = replaced_fields
        return schema

    def handle_typed_dict_schema(self, schema: core_schema.TypedDictSchema, f: Walk) -> core_schema.CoreSchema:
        extras_schema = schema.get('extras_schema')
        if extras_schema is not None:
            schema['extras_schema'] = self.walk(extras_schema, f)
        replaced_computed_fields: list[core_schema.ComputedField] = []
        for computed_field in schema.get('computed_fields', ()):
            replaced_field = self._copy_schema(computed_field)
            replaced_field['return_schema'] = self.walk(computed_field['return_schema'], f)
            replaced_computed_fields.append(replaced_field)
        if replaced_computed_fields:
            schema['computed_fields'] = replaced_computed_fields
        replaced_fields: dict[str, core_schema.TypedDictField] = {}
        for k, v in schema['fields'].items():
            replaced_field = self._copy_schema(v)
            replaced_field['schema'] = self.walk(v['schema'], f)
            replaced_fields[k] = replaced_field
        schema['fields'] = replaced_fields
        return schema

    def handle_dataclass_args_schema(self, schema: core_schema.DataclassArgsSchema, f: Walk) -> core_schema.CoreSchema:
        replaced_fields: list[core_schema.DataclassField] = []
        replaced_computed_fields: list[core_schema.ComputedField] = []
        for computed_field in schema.get('computed_fields', ()):
            replaced_field = self._copy_schema(computed_field)
            replaced_field['return_schema'] = self.walk(computed_field['return_schema'], f)
            replaced_computed_fields.append(replaced_field)
        if replaced_computed_fields:
            schema['computed_fields'] = replaced_computed_fields
        for field in schema['fields']:
            replaced_field = self._copy_schema(field)
            replaced_field['schema'] = self.walk(field['schema'], f)
            replaced_fields.append(replaced_field)
        schema['fields'] = replaced_fields
        return schema

    def handle_arguments_schema(self, schema: core_schema.ArgumentsSchema, f: Walk) -> core_schema.CoreSchema:
        replaced_arguments_schema: list[core_schema.ArgumentsParameter] = []
        for param in schema['arguments_schema']:
            replaced_param = self._copy_schema(param)
            replaced_param['schema'] = self.walk(param['schema'], f)
            replaced_arguments_schema.append(replaced_param)
        schema['arguments_schema'] = replaced_arguments_schema
        if 'var_args_schema' in schema:
            schema['var_args_schema'] = self.walk(schema['var_args_schema'], f)
        if 'var_kwargs_schema' in schema:
            schema['var_kwargs_schema'] = self.walk(schema['var_kwargs_schema'], f)
        return schema

    def handle_call_schema(self, schema: core_schema.CallSchema, f: Walk) -> core_schema.CoreSchema:
        schema['arguments_schema'] = self.walk(schema['arguments_schema'], f)
        if 'return_schema' in schema:
            schema['return_schema'] = self.walk(schema['return_schema'], f)
        return schema


_dispatch = _WalkCoreSchema().walk
_dispatch_no_copy = _WalkCoreSchema(copy=False).walk


def walk_core_schema(schema: core_schema.CoreSchema, f: Walk, *, copy: bool = True) -> core_schema.CoreSchema:
    """Recursively traverse a CoreSchema.

    Args:
        schema (core_schema.CoreSchema): The CoreSchema to process, it will not be modified.
        f (Walk): A function to apply. This function takes two arguments:
          1. The current CoreSchema that is being processed
             (not the same one you passed into this function, one level down).
          2. The "next" `f` to call. This lets you for example use `f=functools.partial(some_method, some_context)`
             to pass data down the recursive calls without using globals or other mutable state.
        copy: Whether schema should be recursively copied.

    Returns:
        core_schema.CoreSchema: A processed CoreSchema.
    """
    return f(schema.copy() if copy else schema, _dispatch if copy else _dispatch_no_copy)


def simplify_schema_references(schema: core_schema.CoreSchema) -> core_schema.CoreSchema:  # noqa: C901
    definitions: dict[str, core_schema.CoreSchema] = {}
    ref_counts: dict[str, int] = defaultdict(int)
    involved_in_recursion: dict[str, bool] = {}
    current_recursion_ref_count: dict[str, int] = defaultdict(int)

    def collect_refs(s: core_schema.CoreSchema, recurse: Recurse) -> core_schema.CoreSchema:
        if s['type'] == 'definitions':
            for definition in s['definitions']:
                ref = get_ref(definition)
                assert ref is not None
                if ref not in definitions:
                    definitions[ref] = definition
                recurse(definition, collect_refs)
            return recurse(s['schema'], collect_refs)
        else:
            ref = get_ref(s)
            if ref is not None:
                new = recurse(s, collect_refs)
                new_ref = get_ref(new)
                if new_ref:
                    definitions[new_ref] = new
                return core_schema.definition_reference_schema(schema_ref=ref)
            else:
                return recurse(s, collect_refs)

    schema = walk_core_schema(schema, collect_refs)

    def count_refs(s: core_schema.CoreSchema, recurse: Recurse) -> core_schema.CoreSchema:
        if s['type'] != 'definition-ref':
            return recurse(s, count_refs)
        ref = s['schema_ref']
        ref_counts[ref] += 1

        if ref_counts[ref] >= 2:
            # If this model is involved in a recursion this should be detected
            # on its second encounter, we can safely stop the walk here.
            if current_recursion_ref_count[ref] != 0:
                involved_in_recursion[ref] = True
            return s

        current_recursion_ref_count[ref] += 1
        if 'serialization' in s:
            # Even though this is a `'definition-ref'` schema, there might
            # be more references inside the serialization schema:
            recurse(s, count_refs)

        next_s = definitions[ref]
        visited: set[str] = set()
        while next_s['type'] == 'definition-ref':
            if next_s['schema_ref'] in visited:
                raise PydanticUserError(
                    f'{ref} contains a circular reference to itself.', code='circular-reference-schema'
                )

            visited.add(next_s['schema_ref'])
            ref_counts[next_s['schema_ref']] += 1
            next_s = definitions[next_s['schema_ref']]

        recurse(next_s, count_refs)
        current_recursion_ref_count[ref] -= 1
        return s

    schema = walk_core_schema(schema, count_refs, copy=False)

    assert all(c == 0 for c in current_recursion_ref_count.values()), 'this is a bug! please report it'

    def can_be_inlined(s: core_schema.DefinitionReferenceSchema, ref: str) -> bool:
        if ref_counts[ref] > 1:
            return False
        if involved_in_recursion.get(ref, False):
            return False
        if 'serialization' in s:
            return False
        if 'metadata' in s:
            metadata = s['metadata']
            for k in [
                *CoreMetadata.__annotations__.keys(),
                'pydantic.internal.union_discriminator',
                'pydantic.internal.tagged_union_tag',
            ]:
                if k in metadata:
                    # we need to keep this as a ref
                    return False
        return True

    def inline_refs(s: core_schema.CoreSchema, recurse: Recurse) -> core_schema.CoreSchema:
        # Assume there are no infinite loops, because we already checked for that in `count_refs`
        while s['type'] == 'definition-ref':
            ref = s['schema_ref']

            # Check if the reference is only used once, not involved in recursion and does not have
            # any extra keys (like 'serialization')
            if can_be_inlined(s, ref):
                # Inline the reference by replacing the reference with the actual schema
                new = definitions.pop(ref)
                ref_counts[ref] -= 1  # because we just replaced it!
                # put all other keys that were on the def-ref schema into the inlined version
                # in particular this is needed for `serialization`
                if 'serialization' in s:
                    new['serialization'] = s['serialization']
                s = new
            else:
                break
        return recurse(s, inline_refs)

    schema = walk_core_schema(schema, inline_refs, copy=False)

    def_values = [v for v in definitions.values() if ref_counts[v['ref']] > 0]  # type: ignore

    if def_values:
        schema = core_schema.definitions_schema(schema=schema, definitions=def_values)
    return schema


def _strip_metadata(schema: CoreSchema) -> CoreSchema:
    def strip_metadata(s: CoreSchema, recurse: Recurse) -> CoreSchema:
        s = s.copy()
        s.pop('metadata', None)
        if s['type'] == 'model-fields':
            s = s.copy()
            s['fields'] = {k: v.copy() for k, v in s['fields'].items()}
            for field_name, field_schema in s['fields'].items():
                field_schema.pop('metadata', None)
                s['fields'][field_name] = field_schema
            computed_fields = s.get('computed_fields', None)
            if computed_fields:
                s['computed_fields'] = [cf.copy() for cf in computed_fields]
                for cf in computed_fields:
                    cf.pop('metadata', None)
            else:
                s.pop('computed_fields', None)
        elif s['type'] == 'model':
            # remove some defaults
            if s.get('custom_init', True) is False:
                s.pop('custom_init')
            if s.get('root_model', True) is False:
                s.pop('root_model')
            if {'title'}.issuperset(s.get('config', {}).keys()):
                s.pop('config', None)

        return recurse(s, strip_metadata)

    return walk_core_schema(schema, strip_metadata)


def pretty_print_core_schema(
    schema: CoreSchema,
    include_metadata: bool = False,
) -> None:
    """Pretty print a CoreSchema using rich.
    This is intended for debugging purposes.

    Args:
        schema: The CoreSchema to print.
        include_metadata: Whether to include metadata in the output. Defaults to `False`.
    """
    from rich import print  # type: ignore  # install it manually in your dev env

    if not include_metadata:
        schema = _strip_metadata(schema)

    return print(schema)


def validate_core_schema(schema: CoreSchema) -> CoreSchema:
    if 'PYDANTIC_SKIP_VALIDATING_CORE_SCHEMAS' in os.environ:
        return schema
    return _validate_core_schema(schema)
