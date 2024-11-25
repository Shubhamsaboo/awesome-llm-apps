"""Type adapter specification."""

from __future__ import annotations as _annotations

import sys
from dataclasses import is_dataclass
from types import FrameType
from typing import (
    Any,
    Generic,
    Iterable,
    Literal,
    TypeVar,
    cast,
    final,
    overload,
)

from pydantic_core import CoreSchema, SchemaSerializer, SchemaValidator, Some
from typing_extensions import ParamSpec, is_typeddict

from pydantic.errors import PydanticUserError
from pydantic.main import BaseModel, IncEx

from ._internal import _config, _generate_schema, _mock_val_ser, _namespace_utils, _repr, _typing_extra, _utils
from .config import ConfigDict
from .errors import PydanticUndefinedAnnotation
from .json_schema import (
    DEFAULT_REF_TEMPLATE,
    GenerateJsonSchema,
    JsonSchemaKeyT,
    JsonSchemaMode,
    JsonSchemaValue,
)
from .plugin._schema_validator import PluggableSchemaValidator, create_schema_validator

T = TypeVar('T')
R = TypeVar('R')
P = ParamSpec('P')
TypeAdapterT = TypeVar('TypeAdapterT', bound='TypeAdapter')


def _getattr_no_parents(obj: Any, attribute: str) -> Any:
    """Returns the attribute value without attempting to look up attributes from parent types."""
    if hasattr(obj, '__dict__'):
        try:
            return obj.__dict__[attribute]
        except KeyError:
            pass

    slots = getattr(obj, '__slots__', None)
    if slots is not None and attribute in slots:
        return getattr(obj, attribute)
    else:
        raise AttributeError(attribute)


def _type_has_config(type_: Any) -> bool:
    """Returns whether the type has config."""
    type_ = _typing_extra.annotated_type(type_) or type_
    try:
        return issubclass(type_, BaseModel) or is_dataclass(type_) or is_typeddict(type_)
    except TypeError:
        # type is not a class
        return False


@final
class TypeAdapter(Generic[T]):
    """Usage docs: https://docs.pydantic.dev/2.10/concepts/type_adapter/

    Type adapters provide a flexible way to perform validation and serialization based on a Python type.

    A `TypeAdapter` instance exposes some of the functionality from `BaseModel` instance methods
    for types that do not have such methods (such as dataclasses, primitive types, and more).

    **Note:** `TypeAdapter` instances are not types, and cannot be used as type annotations for fields.

    Args:
        type: The type associated with the `TypeAdapter`.
        config: Configuration for the `TypeAdapter`, should be a dictionary conforming to
            [`ConfigDict`][pydantic.config.ConfigDict].

            !!! note
                You cannot provide a configuration when instantiating a `TypeAdapter` if the type you're using
                has its own config that cannot be overridden (ex: `BaseModel`, `TypedDict`, and `dataclass`). A
                [`type-adapter-config-unused`](../errors/usage_errors.md#type-adapter-config-unused) error will
                be raised in this case.
        _parent_depth: Depth at which to search for the [parent frame][frame-objects]. This frame is used when
            resolving forward annotations during schema building, by looking for the globals and locals of this
            frame. Defaults to 2, which will result in the frame where the `TypeAdapter` was instantiated.

            !!! note
                This parameter is named with an underscore to suggest its private nature and discourage use.
                It may be deprecated in a minor version, so we only recommend using it if you're comfortable
                with potential change in behavior/support. It's default value is 2 because internally,
                the `TypeAdapter` class makes another call to fetch the frame.
        module: The module that passes to plugin if provided.

    Attributes:
        core_schema: The core schema for the type.
        validator: The schema validator for the type.
        serializer: The schema serializer for the type.
        pydantic_complete: Whether the core schema for the type is successfully built.

    ??? tip "Compatibility with `mypy`"
        Depending on the type used, `mypy` might raise an error when instantiating a `TypeAdapter`. As a workaround, you can explicitly
        annotate your variable:

        ```py
        from typing import Union

        from pydantic import TypeAdapter

        ta: TypeAdapter[Union[str, int]] = TypeAdapter(Union[str, int])  # type: ignore[arg-type]
        ```

    ??? info "Namespace management nuances and implementation details"

        Here, we collect some notes on namespace management, and subtle differences from `BaseModel`:

        `BaseModel` uses its own `__module__` to find out where it was defined
        and then looks for symbols to resolve forward references in those globals.
        On the other hand, `TypeAdapter` can be initialized with arbitrary objects,
        which may not be types and thus do not have a `__module__` available.
        So instead we look at the globals in our parent stack frame.

        It is expected that the `ns_resolver` passed to this function will have the correct
        namespace for the type we're adapting. See the source code for `TypeAdapter.__init__`
        and `TypeAdapter.rebuild` for various ways to construct this namespace.

        This works for the case where this function is called in a module that
        has the target of forward references in its scope, but
        does not always work for more complex cases.

        For example, take the following:

        ```python {title="a.py"}
        from typing import Dict, List

        IntList = List[int]
        OuterDict = Dict[str, 'IntList']
        ```

        ```python {test="skip" title="b.py"}
        from a import OuterDict

        from pydantic import TypeAdapter

        IntList = int  # replaces the symbol the forward reference is looking for
        v = TypeAdapter(OuterDict)
        v({'x': 1})  # should fail but doesn't
        ```

        If `OuterDict` were a `BaseModel`, this would work because it would resolve
        the forward reference within the `a.py` namespace.
        But `TypeAdapter(OuterDict)` can't determine what module `OuterDict` came from.

        In other words, the assumption that _all_ forward references exist in the
        module we are being called from is not technically always true.
        Although most of the time it is and it works fine for recursive models and such,
        `BaseModel`'s behavior isn't perfect either and _can_ break in similar ways,
        so there is no right or wrong between the two.

        But at the very least this behavior is _subtly_ different from `BaseModel`'s.
    """

    core_schema: CoreSchema
    validator: SchemaValidator | PluggableSchemaValidator
    serializer: SchemaSerializer
    pydantic_complete: bool

    @overload
    def __init__(
        self,
        type: type[T],
        *,
        config: ConfigDict | None = ...,
        _parent_depth: int = ...,
        module: str | None = ...,
    ) -> None: ...

    # This second overload is for unsupported special forms (such as Annotated, Union, etc.)
    # Currently there is no way to type this correctly
    # See https://github.com/python/typing/pull/1618
    @overload
    def __init__(
        self,
        type: Any,
        *,
        config: ConfigDict | None = ...,
        _parent_depth: int = ...,
        module: str | None = ...,
    ) -> None: ...

    def __init__(
        self,
        type: Any,
        *,
        config: ConfigDict | None = None,
        _parent_depth: int = 2,
        module: str | None = None,
    ) -> None:
        if _type_has_config(type) and config is not None:
            raise PydanticUserError(
                'Cannot use `config` when the type is a BaseModel, dataclass or TypedDict.'
                ' These types can have their own config and setting the config via the `config`'
                ' parameter to TypeAdapter will not override it, thus the `config` you passed to'
                ' TypeAdapter becomes meaningless, which is probably not what you want.',
                code='type-adapter-config-unused',
            )

        self._type = type
        self._config = config
        self._parent_depth = _parent_depth
        self.pydantic_complete = False

        parent_frame = self._fetch_parent_frame()
        if parent_frame is not None:
            globalns = parent_frame.f_globals
            # Do not provide a local ns if the type adapter happens to be instantiated at the module level:
            localns = parent_frame.f_locals if parent_frame.f_locals is not globalns else {}
        else:
            globalns = {}
            localns = {}

        self._module_name = module or cast(str, globalns.get('__name__', ''))
        self._init_core_attrs(
            ns_resolver=_namespace_utils.NsResolver(
                namespaces_tuple=_namespace_utils.NamespacesTuple(locals=localns, globals=globalns),
                parent_namespace=localns,
            ),
            force=False,
        )

    def _fetch_parent_frame(self) -> FrameType | None:
        frame = sys._getframe(self._parent_depth)
        if frame.f_globals.get('__name__') == 'typing':
            # Because `TypeAdapter` is generic, explicitly parametrizing the class results
            # in a `typing._GenericAlias` instance, which proxies instantiation calls to the
            # "real" `TypeAdapter` class and thus adding an extra frame to the call. To avoid
            # pulling anything from the `typing` module, use the correct frame (the one before):
            return frame.f_back

        return frame

    def _init_core_attrs(
        self, ns_resolver: _namespace_utils.NsResolver, force: bool, raise_errors: bool = False
    ) -> bool:
        """Initialize the core schema, validator, and serializer for the type.

        Args:
            ns_resolver: The namespace resolver to use when building the core schema for the adapted type.
            force: Whether to force the construction of the core schema, validator, and serializer.
                If `force` is set to `False` and `_defer_build` is `True`, the core schema, validator, and serializer will be set to mocks.
            raise_errors: Whether to raise errors if initializing any of the core attrs fails.

        Returns:
            `True` if the core schema, validator, and serializer were successfully initialized, otherwise `False`.

        Raises:
            PydanticUndefinedAnnotation: If `PydanticUndefinedAnnotation` occurs in`__get_pydantic_core_schema__`
                and `raise_errors=True`.
        """
        if not force and self._defer_build:
            _mock_val_ser.set_type_adapter_mocks(self, str(self._type))
            self.pydantic_complete = False
            return False

        try:
            self.core_schema = _getattr_no_parents(self._type, '__pydantic_core_schema__')
            self.validator = _getattr_no_parents(self._type, '__pydantic_validator__')
            self.serializer = _getattr_no_parents(self._type, '__pydantic_serializer__')

            # TODO: we don't go through the rebuild logic here directly because we don't want
            # to repeat all of the namespace fetching logic that we've already done
            # so we simply skip to the block below that does the actual schema generation
            if (
                isinstance(self.core_schema, _mock_val_ser.MockCoreSchema)
                or isinstance(self.validator, _mock_val_ser.MockValSer)
                or isinstance(self.serializer, _mock_val_ser.MockValSer)
            ):
                raise AttributeError()
        except AttributeError:
            config_wrapper = _config.ConfigWrapper(self._config)

            schema_generator = _generate_schema.GenerateSchema(config_wrapper, ns_resolver=ns_resolver)

            try:
                core_schema = schema_generator.generate_schema(self._type)
            except PydanticUndefinedAnnotation:
                if raise_errors:
                    raise
                _mock_val_ser.set_type_adapter_mocks(self, str(self._type))
                return False

            try:
                self.core_schema = schema_generator.clean_schema(core_schema)
            except schema_generator.CollectedInvalid:
                _mock_val_ser.set_type_adapter_mocks(self, str(self._type))
                return False

            core_config = config_wrapper.core_config(None)

            self.validator = create_schema_validator(
                schema=self.core_schema,
                schema_type=self._type,
                schema_type_module=self._module_name,
                schema_type_name=str(self._type),
                schema_kind='TypeAdapter',
                config=core_config,
                plugin_settings=config_wrapper.plugin_settings,
            )
            self.serializer = SchemaSerializer(self.core_schema, core_config)

        self.pydantic_complete = True
        return True

    @property
    def _defer_build(self) -> bool:
        config = self._config if self._config is not None else self._model_config
        if config:
            return config.get('defer_build') is True
        return False

    @property
    def _model_config(self) -> ConfigDict | None:
        type_: Any = _typing_extra.annotated_type(self._type) or self._type  # Eg FastAPI heavily uses Annotated
        if _utils.lenient_issubclass(type_, BaseModel):
            return type_.model_config
        return getattr(type_, '__pydantic_config__', None)

    def __repr__(self) -> str:
        return f'TypeAdapter({_repr.display_as_type(self._type)})'

    def rebuild(
        self,
        *,
        force: bool = False,
        raise_errors: bool = True,
        _parent_namespace_depth: int = 2,
        _types_namespace: _namespace_utils.MappingNamespace | None = None,
    ) -> bool | None:
        """Try to rebuild the pydantic-core schema for the adapter's type.

        This may be necessary when one of the annotations is a ForwardRef which could not be resolved during
        the initial attempt to build the schema, and automatic rebuilding fails.

        Args:
            force: Whether to force the rebuilding of the type adapter's schema, defaults to `False`.
            raise_errors: Whether to raise errors, defaults to `True`.
            _parent_namespace_depth: Depth at which to search for the [parent frame][frame-objects]. This
                frame is used when resolving forward annotations during schema rebuilding, by looking for
                the locals of this frame. Defaults to 2, which will result in the frame where the method
                was called.
            _types_namespace: An explicit types namespace to use, instead of using the local namespace
                from the parent frame. Defaults to `None`.

        Returns:
            Returns `None` if the schema is already "complete" and rebuilding was not required.
            If rebuilding _was_ required, returns `True` if rebuilding was successful, otherwise `False`.
        """
        if not force and self.pydantic_complete:
            return None

        if _types_namespace is not None:
            rebuild_ns = _types_namespace
        elif _parent_namespace_depth > 0:
            rebuild_ns = _typing_extra.parent_frame_namespace(parent_depth=_parent_namespace_depth, force=True) or {}
        else:
            rebuild_ns = {}

        # we have to manually fetch globals here because there's no type on the stack of the NsResolver
        # and so we skip the globalns = get_module_ns_of(typ) call that would normally happen
        globalns = sys._getframe(max(_parent_namespace_depth - 1, 1)).f_globals
        ns_resolver = _namespace_utils.NsResolver(
            namespaces_tuple=_namespace_utils.NamespacesTuple(locals=rebuild_ns, globals=globalns),
            parent_namespace=rebuild_ns,
        )
        return self._init_core_attrs(ns_resolver=ns_resolver, force=True, raise_errors=raise_errors)

    def validate_python(
        self,
        object: Any,
        /,
        *,
        strict: bool | None = None,
        from_attributes: bool | None = None,
        context: dict[str, Any] | None = None,
        experimental_allow_partial: bool | Literal['off', 'on', 'trailing-strings'] = False,
    ) -> T:
        """Validate a Python object against the model.

        Args:
            object: The Python object to validate against the model.
            strict: Whether to strictly check types.
            from_attributes: Whether to extract data from object attributes.
            context: Additional context to pass to the validator.
            experimental_allow_partial: **Experimental** whether to enable
                [partial validation](../concepts/experimental.md#partial-validation), e.g. to process streams.
                * False / 'off': Default behavior, no partial validation.
                * True / 'on': Enable partial validation.
                * 'trailing-strings': Enable partial validation and allow trailing strings in the input.

        !!! note
            When using `TypeAdapter` with a Pydantic `dataclass`, the use of the `from_attributes`
            argument is not supported.

        Returns:
            The validated object.
        """
        return self.validator.validate_python(
            object,
            strict=strict,
            from_attributes=from_attributes,
            context=context,
            allow_partial=experimental_allow_partial,
        )

    def validate_json(
        self,
        data: str | bytes | bytearray,
        /,
        *,
        strict: bool | None = None,
        context: dict[str, Any] | None = None,
        experimental_allow_partial: bool | Literal['off', 'on', 'trailing-strings'] = False,
    ) -> T:
        """Usage docs: https://docs.pydantic.dev/2.10/concepts/json/#json-parsing

        Validate a JSON string or bytes against the model.

        Args:
            data: The JSON data to validate against the model.
            strict: Whether to strictly check types.
            context: Additional context to use during validation.
            experimental_allow_partial: **Experimental** whether to enable
                [partial validation](../concepts/experimental.md#partial-validation), e.g. to process streams.
                * False / 'off': Default behavior, no partial validation.
                * True / 'on': Enable partial validation.
                * 'trailing-strings': Enable partial validation and allow trailing strings in the input.

        Returns:
            The validated object.
        """
        return self.validator.validate_json(
            data, strict=strict, context=context, allow_partial=experimental_allow_partial
        )

    def validate_strings(
        self,
        obj: Any,
        /,
        *,
        strict: bool | None = None,
        context: dict[str, Any] | None = None,
        experimental_allow_partial: bool | Literal['off', 'on', 'trailing-strings'] = False,
    ) -> T:
        """Validate object contains string data against the model.

        Args:
            obj: The object contains string data to validate.
            strict: Whether to strictly check types.
            context: Additional context to use during validation.
            experimental_allow_partial: **Experimental** whether to enable
                [partial validation](../concepts/experimental.md#partial-validation), e.g. to process streams.
                * False / 'off': Default behavior, no partial validation.
                * True / 'on': Enable partial validation.
                * 'trailing-strings': Enable partial validation and allow trailing strings in the input.

        Returns:
            The validated object.
        """
        return self.validator.validate_strings(
            obj, strict=strict, context=context, allow_partial=experimental_allow_partial
        )

    def get_default_value(self, *, strict: bool | None = None, context: dict[str, Any] | None = None) -> Some[T] | None:
        """Get the default value for the wrapped type.

        Args:
            strict: Whether to strictly check types.
            context: Additional context to pass to the validator.

        Returns:
            The default value wrapped in a `Some` if there is one or None if not.
        """
        return self.validator.get_default_value(strict=strict, context=context)

    def dump_python(
        self,
        instance: T,
        /,
        *,
        mode: Literal['json', 'python'] = 'python',
        include: IncEx | None = None,
        exclude: IncEx | None = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool | Literal['none', 'warn', 'error'] = True,
        serialize_as_any: bool = False,
        context: dict[str, Any] | None = None,
    ) -> Any:
        """Dump an instance of the adapted type to a Python object.

        Args:
            instance: The Python object to serialize.
            mode: The output format.
            include: Fields to include in the output.
            exclude: Fields to exclude from the output.
            by_alias: Whether to use alias names for field names.
            exclude_unset: Whether to exclude unset fields.
            exclude_defaults: Whether to exclude fields with default values.
            exclude_none: Whether to exclude fields with None values.
            round_trip: Whether to output the serialized data in a way that is compatible with deserialization.
            warnings: How to handle serialization errors. False/"none" ignores them, True/"warn" logs errors,
                "error" raises a [`PydanticSerializationError`][pydantic_core.PydanticSerializationError].
            serialize_as_any: Whether to serialize fields with duck-typing serialization behavior.
            context: Additional context to pass to the serializer.

        Returns:
            The serialized object.
        """
        return self.serializer.to_python(
            instance,
            mode=mode,
            by_alias=by_alias,
            include=include,
            exclude=exclude,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            round_trip=round_trip,
            warnings=warnings,
            serialize_as_any=serialize_as_any,
            context=context,
        )

    def dump_json(
        self,
        instance: T,
        /,
        *,
        indent: int | None = None,
        include: IncEx | None = None,
        exclude: IncEx | None = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool | Literal['none', 'warn', 'error'] = True,
        serialize_as_any: bool = False,
        context: dict[str, Any] | None = None,
    ) -> bytes:
        """Usage docs: https://docs.pydantic.dev/2.10/concepts/json/#json-serialization

        Serialize an instance of the adapted type to JSON.

        Args:
            instance: The instance to be serialized.
            indent: Number of spaces for JSON indentation.
            include: Fields to include.
            exclude: Fields to exclude.
            by_alias: Whether to use alias names for field names.
            exclude_unset: Whether to exclude unset fields.
            exclude_defaults: Whether to exclude fields with default values.
            exclude_none: Whether to exclude fields with a value of `None`.
            round_trip: Whether to serialize and deserialize the instance to ensure round-tripping.
            warnings: How to handle serialization errors. False/"none" ignores them, True/"warn" logs errors,
                "error" raises a [`PydanticSerializationError`][pydantic_core.PydanticSerializationError].
            serialize_as_any: Whether to serialize fields with duck-typing serialization behavior.
            context: Additional context to pass to the serializer.

        Returns:
            The JSON representation of the given instance as bytes.
        """
        return self.serializer.to_json(
            instance,
            indent=indent,
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            round_trip=round_trip,
            warnings=warnings,
            serialize_as_any=serialize_as_any,
            context=context,
        )

    def json_schema(
        self,
        *,
        by_alias: bool = True,
        ref_template: str = DEFAULT_REF_TEMPLATE,
        schema_generator: type[GenerateJsonSchema] = GenerateJsonSchema,
        mode: JsonSchemaMode = 'validation',
    ) -> dict[str, Any]:
        """Generate a JSON schema for the adapted type.

        Args:
            by_alias: Whether to use alias names for field names.
            ref_template: The format string used for generating $ref strings.
            schema_generator: The generator class used for creating the schema.
            mode: The mode to use for schema generation.

        Returns:
            The JSON schema for the model as a dictionary.
        """
        schema_generator_instance = schema_generator(by_alias=by_alias, ref_template=ref_template)
        if isinstance(self.core_schema, _mock_val_ser.MockCoreSchema):
            self.core_schema.rebuild()
            assert not isinstance(self.core_schema, _mock_val_ser.MockCoreSchema), 'this is a bug! please report it'
        return schema_generator_instance.generate(self.core_schema, mode=mode)

    @staticmethod
    def json_schemas(
        inputs: Iterable[tuple[JsonSchemaKeyT, JsonSchemaMode, TypeAdapter[Any]]],
        /,
        *,
        by_alias: bool = True,
        title: str | None = None,
        description: str | None = None,
        ref_template: str = DEFAULT_REF_TEMPLATE,
        schema_generator: type[GenerateJsonSchema] = GenerateJsonSchema,
    ) -> tuple[dict[tuple[JsonSchemaKeyT, JsonSchemaMode], JsonSchemaValue], JsonSchemaValue]:
        """Generate a JSON schema including definitions from multiple type adapters.

        Args:
            inputs: Inputs to schema generation. The first two items will form the keys of the (first)
                output mapping; the type adapters will provide the core schemas that get converted into
                definitions in the output JSON schema.
            by_alias: Whether to use alias names.
            title: The title for the schema.
            description: The description for the schema.
            ref_template: The format string used for generating $ref strings.
            schema_generator: The generator class used for creating the schema.

        Returns:
            A tuple where:

                - The first element is a dictionary whose keys are tuples of JSON schema key type and JSON mode, and
                    whose values are the JSON schema corresponding to that pair of inputs. (These schemas may have
                    JsonRef references to definitions that are defined in the second returned element.)
                - The second element is a JSON schema containing all definitions referenced in the first returned
                    element, along with the optional title and description keys.

        """
        schema_generator_instance = schema_generator(by_alias=by_alias, ref_template=ref_template)

        inputs_ = []
        for key, mode, adapter in inputs:
            # This is the same pattern we follow for model json schemas - we attempt a core schema rebuild if we detect a mock
            if isinstance(adapter.core_schema, _mock_val_ser.MockCoreSchema):
                adapter.core_schema.rebuild()
                assert not isinstance(
                    adapter.core_schema, _mock_val_ser.MockCoreSchema
                ), 'this is a bug! please report it'
            inputs_.append((key, mode, adapter.core_schema))

        json_schemas_map, definitions = schema_generator_instance.generate_definitions(inputs_)

        json_schema: dict[str, Any] = {}
        if definitions:
            json_schema['$defs'] = definitions
        if title:
            json_schema['title'] = title
        if description:
            json_schema['description'] = description

        return json_schemas_map, json_schema
