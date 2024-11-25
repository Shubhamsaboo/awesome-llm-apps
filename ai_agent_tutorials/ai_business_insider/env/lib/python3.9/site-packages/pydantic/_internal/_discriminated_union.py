from __future__ import annotations as _annotations

from typing import TYPE_CHECKING, Any, Hashable, Sequence

from pydantic_core import CoreSchema, core_schema

from ..errors import PydanticUserError
from . import _core_utils
from ._core_utils import (
    CoreSchemaField,
    collect_definitions,
)

if TYPE_CHECKING:
    from ..types import Discriminator

CORE_SCHEMA_METADATA_DISCRIMINATOR_PLACEHOLDER_KEY = 'pydantic.internal.union_discriminator'


class MissingDefinitionForUnionRef(Exception):
    """Raised when applying a discriminated union discriminator to a schema
    requires a definition that is not yet defined
    """

    def __init__(self, ref: str) -> None:
        self.ref = ref
        super().__init__(f'Missing definition for ref {self.ref!r}')


def set_discriminator_in_metadata(schema: CoreSchema, discriminator: Any) -> None:
    schema.setdefault('metadata', {})
    metadata = schema.get('metadata')
    assert metadata is not None
    metadata[CORE_SCHEMA_METADATA_DISCRIMINATOR_PLACEHOLDER_KEY] = discriminator


def apply_discriminators(schema: core_schema.CoreSchema) -> core_schema.CoreSchema:
    # We recursively walk through the `schema` passed to `apply_discriminators`, applying discriminators
    # where necessary at each level. During this recursion, we allow references to be resolved from the definitions
    # that are originally present on the original, outermost `schema`. Before `apply_discriminators` is called,
    # `simplify_schema_references` is called on the schema (in the `clean_schema` function),
    # which often puts the definitions in the outermost schema.
    global_definitions: dict[str, CoreSchema] = collect_definitions(schema)

    def inner(s: core_schema.CoreSchema, recurse: _core_utils.Recurse) -> core_schema.CoreSchema:
        nonlocal global_definitions

        s = recurse(s, inner)
        if s['type'] == 'tagged-union':
            return s

        metadata = s.get('metadata', {})
        discriminator = metadata.pop(CORE_SCHEMA_METADATA_DISCRIMINATOR_PLACEHOLDER_KEY, None)
        if discriminator is not None:
            s = apply_discriminator(s, discriminator, global_definitions)
        return s

    return _core_utils.walk_core_schema(schema, inner, copy=False)


def apply_discriminator(
    schema: core_schema.CoreSchema,
    discriminator: str | Discriminator,
    definitions: dict[str, core_schema.CoreSchema] | None = None,
) -> core_schema.CoreSchema:
    """Applies the discriminator and returns a new core schema.

    Args:
        schema: The input schema.
        discriminator: The name of the field which will serve as the discriminator.
        definitions: A mapping of schema ref to schema.

    Returns:
        The new core schema.

    Raises:
        TypeError:
            - If `discriminator` is used with invalid union variant.
            - If `discriminator` is used with `Union` type with one variant.
            - If `discriminator` value mapped to multiple choices.
        MissingDefinitionForUnionRef:
            If the definition for ref is missing.
        PydanticUserError:
            - If a model in union doesn't have a discriminator field.
            - If discriminator field has a non-string alias.
            - If discriminator fields have different aliases.
            - If discriminator field not of type `Literal`.
    """
    from ..types import Discriminator

    if isinstance(discriminator, Discriminator):
        if isinstance(discriminator.discriminator, str):
            discriminator = discriminator.discriminator
        else:
            return discriminator._convert_schema(schema)

    return _ApplyInferredDiscriminator(discriminator, definitions or {}).apply(schema)


class _ApplyInferredDiscriminator:
    """This class is used to convert an input schema containing a union schema into one where that union is
    replaced with a tagged-union, with all the associated debugging and performance benefits.

    This is done by:
    * Validating that the input schema is compatible with the provided discriminator
    * Introspecting the schema to determine which discriminator values should map to which union choices
    * Handling various edge cases such as 'definitions', 'default', 'nullable' schemas, and more

    I have chosen to implement the conversion algorithm in this class, rather than a function,
    to make it easier to maintain state while recursively walking the provided CoreSchema.
    """

    def __init__(self, discriminator: str, definitions: dict[str, core_schema.CoreSchema]):
        # `discriminator` should be the name of the field which will serve as the discriminator.
        # It must be the python name of the field, and *not* the field's alias. Note that as of now,
        # all members of a discriminated union _must_ use a field with the same name as the discriminator.
        # This may change if/when we expose a way to manually specify the TaggedUnionSchema's choices.
        self.discriminator = discriminator

        # `definitions` should contain a mapping of schema ref to schema for all schemas which might
        # be referenced by some choice
        self.definitions = definitions

        # `_discriminator_alias` will hold the value, if present, of the alias for the discriminator
        #
        # Note: following the v1 implementation, we currently disallow the use of different aliases
        # for different choices. This is not a limitation of pydantic_core, but if we try to handle
        # this, the inference logic gets complicated very quickly, and could result in confusing
        # debugging challenges for users making subtle mistakes.
        #
        # Rather than trying to do the most powerful inference possible, I think we should eventually
        # expose a way to more-manually control the way the TaggedUnionSchema is constructed through
        # the use of a new type which would be placed as an Annotation on the Union type. This would
        # provide the full flexibility/power of pydantic_core's TaggedUnionSchema where necessary for
        # more complex cases, without over-complicating the inference logic for the common cases.
        self._discriminator_alias: str | None = None

        # `_should_be_nullable` indicates whether the converted union has `None` as an allowed value.
        # If `None` is an acceptable value of the (possibly-wrapped) union, we ignore it while
        # constructing the TaggedUnionSchema, but set the `_should_be_nullable` attribute to True.
        # Once we have constructed the TaggedUnionSchema, if `_should_be_nullable` is True, we ensure
        # that the final schema gets wrapped as a NullableSchema. This has the same semantics on the
        # python side, but resolves the issue that `None` cannot correspond to any discriminator values.
        self._should_be_nullable = False

        # `_is_nullable` is used to track if the final produced schema will definitely be nullable;
        # we set it to True if the input schema is wrapped in a nullable schema that we know will be preserved
        # as an indication that, even if None is discovered as one of the union choices, we will not need to wrap
        # the final value in another nullable schema.
        #
        # This is more complicated than just checking for the final outermost schema having type 'nullable' thanks
        # to the possible presence of other wrapper schemas such as DefinitionsSchema, WithDefaultSchema, etc.
        self._is_nullable = False

        # `_choices_to_handle` serves as a stack of choices to add to the tagged union. Initially, choices
        # from the union in the wrapped schema will be appended to this list, and the recursive choice-handling
        # algorithm may add more choices to this stack as (nested) unions are encountered.
        self._choices_to_handle: list[core_schema.CoreSchema] = []

        # `_tagged_union_choices` is built during the call to `apply`, and will hold the choices to be included
        # in the output TaggedUnionSchema that will replace the union from the input schema
        self._tagged_union_choices: dict[Hashable, core_schema.CoreSchema] = {}

        # `_used` is changed to True after applying the discriminator to prevent accidental reuse
        self._used = False

    def apply(self, schema: core_schema.CoreSchema) -> core_schema.CoreSchema:
        """Return a new CoreSchema based on `schema` that uses a tagged-union with the discriminator provided
        to this class.

        Args:
            schema: The input schema.

        Returns:
            The new core schema.

        Raises:
            TypeError:
                - If `discriminator` is used with invalid union variant.
                - If `discriminator` is used with `Union` type with one variant.
                - If `discriminator` value mapped to multiple choices.
            ValueError:
                If the definition for ref is missing.
            PydanticUserError:
                - If a model in union doesn't have a discriminator field.
                - If discriminator field has a non-string alias.
                - If discriminator fields have different aliases.
                - If discriminator field not of type `Literal`.
        """
        assert not self._used
        schema = self._apply_to_root(schema)
        if self._should_be_nullable and not self._is_nullable:
            schema = core_schema.nullable_schema(schema)
        self._used = True
        return schema

    def _apply_to_root(self, schema: core_schema.CoreSchema) -> core_schema.CoreSchema:
        """This method handles the outer-most stage of recursion over the input schema:
        unwrapping nullable or definitions schemas, and calling the `_handle_choice`
        method iteratively on the choices extracted (recursively) from the possibly-wrapped union.
        """
        if schema['type'] == 'nullable':
            self._is_nullable = True
            wrapped = self._apply_to_root(schema['schema'])
            nullable_wrapper = schema.copy()
            nullable_wrapper['schema'] = wrapped
            return nullable_wrapper

        if schema['type'] == 'definitions':
            wrapped = self._apply_to_root(schema['schema'])
            definitions_wrapper = schema.copy()
            definitions_wrapper['schema'] = wrapped
            return definitions_wrapper

        if schema['type'] != 'union':
            # If the schema is not a union, it probably means it just had a single member and
            # was flattened by pydantic_core.
            # However, it still may make sense to apply the discriminator to this schema,
            # as a way to get discriminated-union-style error messages, so we allow this here.
            schema = core_schema.union_schema([schema])

        # Reverse the choices list before extending the stack so that they get handled in the order they occur
        choices_schemas = [v[0] if isinstance(v, tuple) else v for v in schema['choices'][::-1]]
        self._choices_to_handle.extend(choices_schemas)
        while self._choices_to_handle:
            choice = self._choices_to_handle.pop()
            self._handle_choice(choice)

        if self._discriminator_alias is not None and self._discriminator_alias != self.discriminator:
            # * We need to annotate `discriminator` as a union here to handle both branches of this conditional
            # * We need to annotate `discriminator` as list[list[str | int]] and not list[list[str]] due to the
            #   invariance of list, and because list[list[str | int]] is the type of the discriminator argument
            #   to tagged_union_schema below
            # * See the docstring of pydantic_core.core_schema.tagged_union_schema for more details about how to
            #   interpret the value of the discriminator argument to tagged_union_schema. (The list[list[str]] here
            #   is the appropriate way to provide a list of fallback attributes to check for a discriminator value.)
            discriminator: str | list[list[str | int]] = [[self.discriminator], [self._discriminator_alias]]
        else:
            discriminator = self.discriminator
        return core_schema.tagged_union_schema(
            choices=self._tagged_union_choices,
            discriminator=discriminator,
            custom_error_type=schema.get('custom_error_type'),
            custom_error_message=schema.get('custom_error_message'),
            custom_error_context=schema.get('custom_error_context'),
            strict=False,
            from_attributes=True,
            ref=schema.get('ref'),
            metadata=schema.get('metadata'),
            serialization=schema.get('serialization'),
        )

    def _handle_choice(self, choice: core_schema.CoreSchema) -> None:
        """This method handles the "middle" stage of recursion over the input schema.
        Specifically, it is responsible for handling each choice of the outermost union
        (and any "coalesced" choices obtained from inner unions).

        Here, "handling" entails:
        * Coalescing nested unions and compatible tagged-unions
        * Tracking the presence of 'none' and 'nullable' schemas occurring as choices
        * Validating that each allowed discriminator value maps to a unique choice
        * Updating the _tagged_union_choices mapping that will ultimately be used to build the TaggedUnionSchema.
        """
        if choice['type'] == 'definition-ref':
            if choice['schema_ref'] not in self.definitions:
                raise MissingDefinitionForUnionRef(choice['schema_ref'])

        if choice['type'] == 'none':
            self._should_be_nullable = True
        elif choice['type'] == 'definitions':
            self._handle_choice(choice['schema'])
        elif choice['type'] == 'nullable':
            self._should_be_nullable = True
            self._handle_choice(choice['schema'])  # unwrap the nullable schema
        elif choice['type'] == 'union':
            # Reverse the choices list before extending the stack so that they get handled in the order they occur
            choices_schemas = [v[0] if isinstance(v, tuple) else v for v in choice['choices'][::-1]]
            self._choices_to_handle.extend(choices_schemas)
        elif choice['type'] not in {
            'model',
            'typed-dict',
            'tagged-union',
            'lax-or-strict',
            'dataclass',
            'dataclass-args',
            'definition-ref',
        } and not _core_utils.is_function_with_inner_schema(choice):
            # We should eventually handle 'definition-ref' as well
            raise TypeError(
                f'{choice["type"]!r} is not a valid discriminated union variant;'
                ' should be a `BaseModel` or `dataclass`'
            )
        else:
            if choice['type'] == 'tagged-union' and self._is_discriminator_shared(choice):
                # In this case, this inner tagged-union is compatible with the outer tagged-union,
                # and its choices can be coalesced into the outer TaggedUnionSchema.
                subchoices = [x for x in choice['choices'].values() if not isinstance(x, (str, int))]
                # Reverse the choices list before extending the stack so that they get handled in the order they occur
                self._choices_to_handle.extend(subchoices[::-1])
                return

            inferred_discriminator_values = self._infer_discriminator_values_for_choice(choice, source_name=None)
            self._set_unique_choice_for_values(choice, inferred_discriminator_values)

    def _is_discriminator_shared(self, choice: core_schema.TaggedUnionSchema) -> bool:
        """This method returns a boolean indicating whether the discriminator for the `choice`
        is the same as that being used for the outermost tagged union. This is used to
        determine whether this TaggedUnionSchema choice should be "coalesced" into the top level,
        or whether it should be treated as a separate (nested) choice.
        """
        inner_discriminator = choice['discriminator']
        return inner_discriminator == self.discriminator or (
            isinstance(inner_discriminator, list)
            and (self.discriminator in inner_discriminator or [self.discriminator] in inner_discriminator)
        )

    def _infer_discriminator_values_for_choice(  # noqa C901
        self, choice: core_schema.CoreSchema, source_name: str | None
    ) -> list[str | int]:
        """This function recurses over `choice`, extracting all discriminator values that should map to this choice.

        `model_name` is accepted for the purpose of producing useful error messages.
        """
        if choice['type'] == 'definitions':
            return self._infer_discriminator_values_for_choice(choice['schema'], source_name=source_name)
        elif choice['type'] == 'function-plain':
            raise TypeError(
                f'{choice["type"]!r} is not a valid discriminated union variant;'
                ' should be a `BaseModel` or `dataclass`'
            )
        elif _core_utils.is_function_with_inner_schema(choice):
            return self._infer_discriminator_values_for_choice(choice['schema'], source_name=source_name)
        elif choice['type'] == 'lax-or-strict':
            return sorted(
                set(
                    self._infer_discriminator_values_for_choice(choice['lax_schema'], source_name=None)
                    + self._infer_discriminator_values_for_choice(choice['strict_schema'], source_name=None)
                )
            )

        elif choice['type'] == 'tagged-union':
            values: list[str | int] = []
            # Ignore str/int "choices" since these are just references to other choices
            subchoices = [x for x in choice['choices'].values() if not isinstance(x, (str, int))]
            for subchoice in subchoices:
                subchoice_values = self._infer_discriminator_values_for_choice(subchoice, source_name=None)
                values.extend(subchoice_values)
            return values

        elif choice['type'] == 'union':
            values = []
            for subchoice in choice['choices']:
                subchoice_schema = subchoice[0] if isinstance(subchoice, tuple) else subchoice
                subchoice_values = self._infer_discriminator_values_for_choice(subchoice_schema, source_name=None)
                values.extend(subchoice_values)
            return values

        elif choice['type'] == 'nullable':
            self._should_be_nullable = True
            return self._infer_discriminator_values_for_choice(choice['schema'], source_name=None)

        elif choice['type'] == 'model':
            return self._infer_discriminator_values_for_choice(choice['schema'], source_name=choice['cls'].__name__)

        elif choice['type'] == 'dataclass':
            return self._infer_discriminator_values_for_choice(choice['schema'], source_name=choice['cls'].__name__)

        elif choice['type'] == 'model-fields':
            return self._infer_discriminator_values_for_model_choice(choice, source_name=source_name)

        elif choice['type'] == 'dataclass-args':
            return self._infer_discriminator_values_for_dataclass_choice(choice, source_name=source_name)

        elif choice['type'] == 'typed-dict':
            return self._infer_discriminator_values_for_typed_dict_choice(choice, source_name=source_name)

        elif choice['type'] == 'definition-ref':
            schema_ref = choice['schema_ref']
            if schema_ref not in self.definitions:
                raise MissingDefinitionForUnionRef(schema_ref)
            return self._infer_discriminator_values_for_choice(self.definitions[schema_ref], source_name=source_name)
        else:
            raise TypeError(
                f'{choice["type"]!r} is not a valid discriminated union variant;'
                ' should be a `BaseModel` or `dataclass`'
            )

    def _infer_discriminator_values_for_typed_dict_choice(
        self, choice: core_schema.TypedDictSchema, source_name: str | None = None
    ) -> list[str | int]:
        """This method just extracts the _infer_discriminator_values_for_choice logic specific to TypedDictSchema
        for the sake of readability.
        """
        source = 'TypedDict' if source_name is None else f'TypedDict {source_name!r}'
        field = choice['fields'].get(self.discriminator)
        if field is None:
            raise PydanticUserError(
                f'{source} needs a discriminator field for key {self.discriminator!r}', code='discriminator-no-field'
            )
        return self._infer_discriminator_values_for_field(field, source)

    def _infer_discriminator_values_for_model_choice(
        self, choice: core_schema.ModelFieldsSchema, source_name: str | None = None
    ) -> list[str | int]:
        source = 'ModelFields' if source_name is None else f'Model {source_name!r}'
        field = choice['fields'].get(self.discriminator)
        if field is None:
            raise PydanticUserError(
                f'{source} needs a discriminator field for key {self.discriminator!r}', code='discriminator-no-field'
            )
        return self._infer_discriminator_values_for_field(field, source)

    def _infer_discriminator_values_for_dataclass_choice(
        self, choice: core_schema.DataclassArgsSchema, source_name: str | None = None
    ) -> list[str | int]:
        source = 'DataclassArgs' if source_name is None else f'Dataclass {source_name!r}'
        for field in choice['fields']:
            if field['name'] == self.discriminator:
                break
        else:
            raise PydanticUserError(
                f'{source} needs a discriminator field for key {self.discriminator!r}', code='discriminator-no-field'
            )
        return self._infer_discriminator_values_for_field(field, source)

    def _infer_discriminator_values_for_field(self, field: CoreSchemaField, source: str) -> list[str | int]:
        if field['type'] == 'computed-field':
            # This should never occur as a discriminator, as it is only relevant to serialization
            return []
        alias = field.get('validation_alias', self.discriminator)
        if not isinstance(alias, str):
            raise PydanticUserError(
                f'Alias {alias!r} is not supported in a discriminated union', code='discriminator-alias-type'
            )
        if self._discriminator_alias is None:
            self._discriminator_alias = alias
        elif self._discriminator_alias != alias:
            raise PydanticUserError(
                f'Aliases for discriminator {self.discriminator!r} must be the same '
                f'(got {alias}, {self._discriminator_alias})',
                code='discriminator-alias',
            )
        return self._infer_discriminator_values_for_inner_schema(field['schema'], source)

    def _infer_discriminator_values_for_inner_schema(
        self, schema: core_schema.CoreSchema, source: str
    ) -> list[str | int]:
        """When inferring discriminator values for a field, we typically extract the expected values from a literal
        schema. This function does that, but also handles nested unions and defaults.
        """
        if schema['type'] == 'literal':
            return schema['expected']

        elif schema['type'] == 'union':
            # Generally when multiple values are allowed they should be placed in a single `Literal`, but
            # we add this case to handle the situation where a field is annotated as a `Union` of `Literal`s.
            # For example, this lets us handle `Union[Literal['key'], Union[Literal['Key'], Literal['KEY']]]`
            values: list[Any] = []
            for choice in schema['choices']:
                choice_schema = choice[0] if isinstance(choice, tuple) else choice
                choice_values = self._infer_discriminator_values_for_inner_schema(choice_schema, source)
                values.extend(choice_values)
            return values

        elif schema['type'] == 'default':
            # This will happen if the field has a default value; we ignore it while extracting the discriminator values
            return self._infer_discriminator_values_for_inner_schema(schema['schema'], source)

        elif schema['type'] == 'function-after':
            # After validators don't affect the discriminator values
            return self._infer_discriminator_values_for_inner_schema(schema['schema'], source)

        elif schema['type'] in {'function-before', 'function-wrap', 'function-plain'}:
            validator_type = repr(schema['type'].split('-')[1])
            raise PydanticUserError(
                f'Cannot use a mode={validator_type} validator in the'
                f' discriminator field {self.discriminator!r} of {source}',
                code='discriminator-validator',
            )

        else:
            raise PydanticUserError(
                f'{source} needs field {self.discriminator!r} to be of type `Literal`',
                code='discriminator-needs-literal',
            )

    def _set_unique_choice_for_values(self, choice: core_schema.CoreSchema, values: Sequence[str | int]) -> None:
        """This method updates `self.tagged_union_choices` so that all provided (discriminator) `values` map to the
        provided `choice`, validating that none of these values already map to another (different) choice.
        """
        for discriminator_value in values:
            if discriminator_value in self._tagged_union_choices:
                # It is okay if `value` is already in tagged_union_choices as long as it maps to the same value.
                # Because tagged_union_choices may map values to other values, we need to walk the choices dict
                # until we get to a "real" choice, and confirm that is equal to the one assigned.
                existing_choice = self._tagged_union_choices[discriminator_value]
                if existing_choice != choice:
                    raise TypeError(
                        f'Value {discriminator_value!r} for discriminator '
                        f'{self.discriminator!r} mapped to multiple choices'
                    )
            else:
                self._tagged_union_choices[discriminator_value] = choice
