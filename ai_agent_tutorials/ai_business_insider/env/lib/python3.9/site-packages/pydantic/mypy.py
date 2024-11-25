"""This module includes classes and functions designed specifically for use with the mypy plugin."""

from __future__ import annotations

import sys
from configparser import ConfigParser
from typing import Any, Callable, Iterator

from mypy.errorcodes import ErrorCode
from mypy.expandtype import expand_type, expand_type_by_instance
from mypy.nodes import (
    ARG_NAMED,
    ARG_NAMED_OPT,
    ARG_OPT,
    ARG_POS,
    ARG_STAR2,
    INVARIANT,
    MDEF,
    Argument,
    AssignmentStmt,
    Block,
    CallExpr,
    ClassDef,
    Context,
    Decorator,
    DictExpr,
    EllipsisExpr,
    Expression,
    FuncDef,
    IfStmt,
    JsonDict,
    MemberExpr,
    NameExpr,
    PassStmt,
    PlaceholderNode,
    RefExpr,
    Statement,
    StrExpr,
    SymbolTableNode,
    TempNode,
    TypeAlias,
    TypeInfo,
    Var,
)
from mypy.options import Options
from mypy.plugin import (
    CheckerPluginInterface,
    ClassDefContext,
    MethodContext,
    Plugin,
    ReportConfigContext,
    SemanticAnalyzerPluginInterface,
)
from mypy.plugins.common import (
    deserialize_and_fixup_type,
)
from mypy.semanal import set_callable_name
from mypy.server.trigger import make_wildcard_trigger
from mypy.state import state
from mypy.typeops import map_type_from_supertype
from mypy.types import (
    AnyType,
    CallableType,
    Instance,
    NoneType,
    Type,
    TypeOfAny,
    TypeType,
    TypeVarType,
    UnionType,
    get_proper_type,
)
from mypy.typevars import fill_typevars
from mypy.util import get_unique_redefinition_name
from mypy.version import __version__ as mypy_version

from pydantic._internal import _fields
from pydantic.version import parse_mypy_version

CONFIGFILE_KEY = 'pydantic-mypy'
METADATA_KEY = 'pydantic-mypy-metadata'
BASEMODEL_FULLNAME = 'pydantic.main.BaseModel'
BASESETTINGS_FULLNAME = 'pydantic_settings.main.BaseSettings'
ROOT_MODEL_FULLNAME = 'pydantic.root_model.RootModel'
MODEL_METACLASS_FULLNAME = 'pydantic._internal._model_construction.ModelMetaclass'
FIELD_FULLNAME = 'pydantic.fields.Field'
DATACLASS_FULLNAME = 'pydantic.dataclasses.dataclass'
MODEL_VALIDATOR_FULLNAME = 'pydantic.functional_validators.model_validator'
DECORATOR_FULLNAMES = {
    'pydantic.functional_validators.field_validator',
    'pydantic.functional_validators.model_validator',
    'pydantic.functional_serializers.serializer',
    'pydantic.functional_serializers.model_serializer',
    'pydantic.deprecated.class_validators.validator',
    'pydantic.deprecated.class_validators.root_validator',
}


MYPY_VERSION_TUPLE = parse_mypy_version(mypy_version)
BUILTINS_NAME = 'builtins'

# Increment version if plugin changes and mypy caches should be invalidated
__version__ = 2


def plugin(version: str) -> type[Plugin]:
    """`version` is the mypy version string.

    We might want to use this to print a warning if the mypy version being used is
    newer, or especially older, than we expect (or need).

    Args:
        version: The mypy version string.

    Return:
        The Pydantic mypy plugin type.
    """
    return PydanticPlugin


class PydanticPlugin(Plugin):
    """The Pydantic mypy plugin."""

    def __init__(self, options: Options) -> None:
        self.plugin_config = PydanticPluginConfig(options)
        self._plugin_data = self.plugin_config.to_data()
        super().__init__(options)

    def get_base_class_hook(self, fullname: str) -> Callable[[ClassDefContext], None] | None:
        """Update Pydantic model class."""
        sym = self.lookup_fully_qualified(fullname)
        if sym and isinstance(sym.node, TypeInfo):  # pragma: no branch
            # No branching may occur if the mypy cache has not been cleared
            if any(base.fullname == BASEMODEL_FULLNAME for base in sym.node.mro):
                return self._pydantic_model_class_maker_callback
        return None

    def get_metaclass_hook(self, fullname: str) -> Callable[[ClassDefContext], None] | None:
        """Update Pydantic `ModelMetaclass` definition."""
        if fullname == MODEL_METACLASS_FULLNAME:
            return self._pydantic_model_metaclass_marker_callback
        return None

    def get_method_hook(self, fullname: str) -> Callable[[MethodContext], Type] | None:
        """Adjust return type of `from_orm` method call."""
        if fullname.endswith('.from_orm'):
            return from_attributes_callback
        return None

    def report_config_data(self, ctx: ReportConfigContext) -> dict[str, Any]:
        """Return all plugin config data.

        Used by mypy to determine if cache needs to be discarded.
        """
        return self._plugin_data

    def _pydantic_model_class_maker_callback(self, ctx: ClassDefContext) -> None:
        transformer = PydanticModelTransformer(ctx.cls, ctx.reason, ctx.api, self.plugin_config)
        transformer.transform()

    def _pydantic_model_metaclass_marker_callback(self, ctx: ClassDefContext) -> None:
        """Reset dataclass_transform_spec attribute of ModelMetaclass.

        Let the plugin handle it. This behavior can be disabled
        if 'debug_dataclass_transform' is set to True', for testing purposes.
        """
        if self.plugin_config.debug_dataclass_transform:
            return
        info_metaclass = ctx.cls.info.declared_metaclass
        assert info_metaclass, "callback not passed from 'get_metaclass_hook'"
        if getattr(info_metaclass.type, 'dataclass_transform_spec', None):
            info_metaclass.type.dataclass_transform_spec = None


class PydanticPluginConfig:
    """A Pydantic mypy plugin config holder.

    Attributes:
        init_forbid_extra: Whether to add a `**kwargs` at the end of the generated `__init__` signature.
        init_typed: Whether to annotate fields in the generated `__init__`.
        warn_required_dynamic_aliases: Whether to raise required dynamic aliases error.
        debug_dataclass_transform: Whether to not reset `dataclass_transform_spec` attribute
            of `ModelMetaclass` for testing purposes.
    """

    __slots__ = (
        'init_forbid_extra',
        'init_typed',
        'warn_required_dynamic_aliases',
        'debug_dataclass_transform',
    )
    init_forbid_extra: bool
    init_typed: bool
    warn_required_dynamic_aliases: bool
    debug_dataclass_transform: bool  # undocumented

    def __init__(self, options: Options) -> None:
        if options.config_file is None:  # pragma: no cover
            return

        toml_config = parse_toml(options.config_file)
        if toml_config is not None:
            config = toml_config.get('tool', {}).get('pydantic-mypy', {})
            for key in self.__slots__:
                setting = config.get(key, False)
                if not isinstance(setting, bool):
                    raise ValueError(f'Configuration value must be a boolean for key: {key}')
                setattr(self, key, setting)
        else:
            plugin_config = ConfigParser()
            plugin_config.read(options.config_file)
            for key in self.__slots__:
                setting = plugin_config.getboolean(CONFIGFILE_KEY, key, fallback=False)
                setattr(self, key, setting)

    def to_data(self) -> dict[str, Any]:
        """Returns a dict of config names to their values."""
        return {key: getattr(self, key) for key in self.__slots__}


def from_attributes_callback(ctx: MethodContext) -> Type:
    """Raise an error if from_attributes is not enabled."""
    model_type: Instance
    ctx_type = ctx.type
    if isinstance(ctx_type, TypeType):
        ctx_type = ctx_type.item
    if isinstance(ctx_type, CallableType) and isinstance(ctx_type.ret_type, Instance):
        model_type = ctx_type.ret_type  # called on the class
    elif isinstance(ctx_type, Instance):
        model_type = ctx_type  # called on an instance (unusual, but still valid)
    else:  # pragma: no cover
        detail = f'ctx.type: {ctx_type} (of type {ctx_type.__class__.__name__})'
        error_unexpected_behavior(detail, ctx.api, ctx.context)
        return ctx.default_return_type
    pydantic_metadata = model_type.type.metadata.get(METADATA_KEY)
    if pydantic_metadata is None:
        return ctx.default_return_type
    if not any(base.fullname == BASEMODEL_FULLNAME for base in model_type.type.mro):
        # not a Pydantic v2 model
        return ctx.default_return_type
    from_attributes = pydantic_metadata.get('config', {}).get('from_attributes')
    if from_attributes is not True:
        error_from_attributes(model_type.type.name, ctx.api, ctx.context)
    return ctx.default_return_type


class PydanticModelField:
    """Based on mypy.plugins.dataclasses.DataclassAttribute."""

    def __init__(
        self,
        name: str,
        alias: str | None,
        is_frozen: bool,
        has_dynamic_alias: bool,
        has_default: bool,
        strict: bool | None,
        line: int,
        column: int,
        type: Type | None,
        info: TypeInfo,
    ):
        self.name = name
        self.alias = alias
        self.is_frozen = is_frozen
        self.has_dynamic_alias = has_dynamic_alias
        self.has_default = has_default
        self.strict = strict
        self.line = line
        self.column = column
        self.type = type
        self.info = info

    def to_argument(
        self,
        current_info: TypeInfo,
        typed: bool,
        model_strict: bool,
        force_optional: bool,
        use_alias: bool,
        api: SemanticAnalyzerPluginInterface,
        force_typevars_invariant: bool,
        is_root_model_root: bool,
    ) -> Argument:
        """Based on mypy.plugins.dataclasses.DataclassAttribute.to_argument."""
        variable = self.to_var(current_info, api, use_alias, force_typevars_invariant)

        strict = model_strict if self.strict is None else self.strict
        if typed or strict:
            type_annotation = self.expand_type(current_info, api)
        else:
            type_annotation = AnyType(TypeOfAny.explicit)

        return Argument(
            variable=variable,
            type_annotation=type_annotation,
            initializer=None,
            kind=ARG_OPT
            if is_root_model_root
            else (ARG_NAMED_OPT if force_optional or self.has_default else ARG_NAMED),
        )

    def expand_type(
        self, current_info: TypeInfo, api: SemanticAnalyzerPluginInterface, force_typevars_invariant: bool = False
    ) -> Type | None:
        """Based on mypy.plugins.dataclasses.DataclassAttribute.expand_type."""
        if force_typevars_invariant:
            # In some cases, mypy will emit an error "Cannot use a covariant type variable as a parameter"
            # To prevent that, we add an option to replace typevars with invariant ones while building certain
            # method signatures (in particular, `__init__`). There may be a better way to do this, if this causes
            # us problems in the future, we should look into why the dataclasses plugin doesn't have this issue.
            if isinstance(self.type, TypeVarType):
                modified_type = self.type.copy_modified()
                modified_type.variance = INVARIANT
                self.type = modified_type

        if self.type is not None and self.info.self_type is not None:
            # In general, it is not safe to call `expand_type()` during semantic analysis,
            # however this plugin is called very late, so all types should be fully ready.
            # Also, it is tricky to avoid eager expansion of Self types here (e.g. because
            # we serialize attributes).
            with state.strict_optional_set(api.options.strict_optional):
                filled_with_typevars = fill_typevars(current_info)
                # Cannot be TupleType as current_info represents a Pydantic model:
                assert isinstance(filled_with_typevars, Instance)
                if force_typevars_invariant:
                    for arg in filled_with_typevars.args:
                        if isinstance(arg, TypeVarType):
                            arg.variance = INVARIANT
                return expand_type(self.type, {self.info.self_type.id: filled_with_typevars})
        return self.type

    def to_var(
        self,
        current_info: TypeInfo,
        api: SemanticAnalyzerPluginInterface,
        use_alias: bool,
        force_typevars_invariant: bool = False,
    ) -> Var:
        """Based on mypy.plugins.dataclasses.DataclassAttribute.to_var."""
        if use_alias and self.alias is not None:
            name = self.alias
        else:
            name = self.name

        return Var(name, self.expand_type(current_info, api, force_typevars_invariant))

    def serialize(self) -> JsonDict:
        """Based on mypy.plugins.dataclasses.DataclassAttribute.serialize."""
        assert self.type
        return {
            'name': self.name,
            'alias': self.alias,
            'is_frozen': self.is_frozen,
            'has_dynamic_alias': self.has_dynamic_alias,
            'has_default': self.has_default,
            'strict': self.strict,
            'line': self.line,
            'column': self.column,
            'type': self.type.serialize(),
        }

    @classmethod
    def deserialize(cls, info: TypeInfo, data: JsonDict, api: SemanticAnalyzerPluginInterface) -> PydanticModelField:
        """Based on mypy.plugins.dataclasses.DataclassAttribute.deserialize."""
        data = data.copy()
        typ = deserialize_and_fixup_type(data.pop('type'), api)
        return cls(type=typ, info=info, **data)

    def expand_typevar_from_subtype(self, sub_type: TypeInfo, api: SemanticAnalyzerPluginInterface) -> None:
        """Expands type vars in the context of a subtype when an attribute is inherited
        from a generic super type.
        """
        if self.type is not None:
            with state.strict_optional_set(api.options.strict_optional):
                self.type = map_type_from_supertype(self.type, sub_type, self.info)


class PydanticModelClassVar:
    """Based on mypy.plugins.dataclasses.DataclassAttribute.

    ClassVars are ignored by subclasses.

    Attributes:
        name: the ClassVar name
    """

    def __init__(self, name):
        self.name = name

    @classmethod
    def deserialize(cls, data: JsonDict) -> PydanticModelClassVar:
        """Based on mypy.plugins.dataclasses.DataclassAttribute.deserialize."""
        data = data.copy()
        return cls(**data)

    def serialize(self) -> JsonDict:
        """Based on mypy.plugins.dataclasses.DataclassAttribute.serialize."""
        return {
            'name': self.name,
        }


class PydanticModelTransformer:
    """Transform the BaseModel subclass according to the plugin settings.

    Attributes:
        tracked_config_fields: A set of field configs that the plugin has to track their value.
    """

    tracked_config_fields: set[str] = {
        'extra',
        'frozen',
        'from_attributes',
        'populate_by_name',
        'alias_generator',
        'strict',
    }

    def __init__(
        self,
        cls: ClassDef,
        reason: Expression | Statement,
        api: SemanticAnalyzerPluginInterface,
        plugin_config: PydanticPluginConfig,
    ) -> None:
        self._cls = cls
        self._reason = reason
        self._api = api

        self.plugin_config = plugin_config

    def transform(self) -> bool:
        """Configures the BaseModel subclass according to the plugin settings.

        In particular:

        * determines the model config and fields,
        * adds a fields-aware signature for the initializer and construct methods
        * freezes the class if frozen = True
        * stores the fields, config, and if the class is settings in the mypy metadata for access by subclasses
        """
        info = self._cls.info
        is_root_model = any(ROOT_MODEL_FULLNAME in base.fullname for base in info.mro[:-1])
        config = self.collect_config()
        fields, class_vars = self.collect_fields_and_class_vars(config, is_root_model)
        if fields is None or class_vars is None:
            # Some definitions are not ready. We need another pass.
            return False
        for field in fields:
            if field.type is None:
                return False

        is_settings = any(base.fullname == BASESETTINGS_FULLNAME for base in info.mro[:-1])
        self.add_initializer(fields, config, is_settings, is_root_model)
        self.add_model_construct_method(fields, config, is_settings, is_root_model)
        self.set_frozen(fields, self._api, frozen=config.frozen is True)

        self.adjust_decorator_signatures()

        info.metadata[METADATA_KEY] = {
            'fields': {field.name: field.serialize() for field in fields},
            'class_vars': {class_var.name: class_var.serialize() for class_var in class_vars},
            'config': config.get_values_dict(),
        }

        return True

    def adjust_decorator_signatures(self) -> None:
        """When we decorate a function `f` with `pydantic.validator(...)`, `pydantic.field_validator`
        or `pydantic.serializer(...)`, mypy sees `f` as a regular method taking a `self` instance,
        even though pydantic internally wraps `f` with `classmethod` if necessary.

        Teach mypy this by marking any function whose outermost decorator is a `validator()`,
        `field_validator()` or `serializer()` call as a `classmethod`.
        """
        for sym in self._cls.info.names.values():
            if isinstance(sym.node, Decorator):
                first_dec = sym.node.original_decorators[0]
                if (
                    isinstance(first_dec, CallExpr)
                    and isinstance(first_dec.callee, NameExpr)
                    and first_dec.callee.fullname in DECORATOR_FULLNAMES
                    # @model_validator(mode="after") is an exception, it expects a regular method
                    and not (
                        first_dec.callee.fullname == MODEL_VALIDATOR_FULLNAME
                        and any(
                            first_dec.arg_names[i] == 'mode' and isinstance(arg, StrExpr) and arg.value == 'after'
                            for i, arg in enumerate(first_dec.args)
                        )
                    )
                ):
                    # TODO: Only do this if the first argument of the decorated function is `cls`
                    sym.node.func.is_class = True

    def collect_config(self) -> ModelConfigData:  # noqa: C901 (ignore complexity)
        """Collects the values of the config attributes that are used by the plugin, accounting for parent classes."""
        cls = self._cls
        config = ModelConfigData()

        has_config_kwargs = False
        has_config_from_namespace = False

        # Handle `class MyModel(BaseModel, <name>=<expr>, ...):`
        for name, expr in cls.keywords.items():
            config_data = self.get_config_update(name, expr)
            if config_data:
                has_config_kwargs = True
                config.update(config_data)

        # Handle `model_config`
        stmt: Statement | None = None
        for stmt in cls.defs.body:
            if not isinstance(stmt, (AssignmentStmt, ClassDef)):
                continue

            if isinstance(stmt, AssignmentStmt):
                lhs = stmt.lvalues[0]
                if not isinstance(lhs, NameExpr) or lhs.name != 'model_config':
                    continue

                if isinstance(stmt.rvalue, CallExpr):  # calls to `dict` or `ConfigDict`
                    for arg_name, arg in zip(stmt.rvalue.arg_names, stmt.rvalue.args):
                        if arg_name is None:
                            continue
                        config.update(self.get_config_update(arg_name, arg, lax_extra=True))
                elif isinstance(stmt.rvalue, DictExpr):  # dict literals
                    for key_expr, value_expr in stmt.rvalue.items:
                        if not isinstance(key_expr, StrExpr):
                            continue
                        config.update(self.get_config_update(key_expr.value, value_expr))

            elif isinstance(stmt, ClassDef):
                if stmt.name != 'Config':  # 'deprecated' Config-class
                    continue
                for substmt in stmt.defs.body:
                    if not isinstance(substmt, AssignmentStmt):
                        continue
                    lhs = substmt.lvalues[0]
                    if not isinstance(lhs, NameExpr):
                        continue
                    config.update(self.get_config_update(lhs.name, substmt.rvalue))

            if has_config_kwargs:
                self._api.fail(
                    'Specifying config in two places is ambiguous, use either Config attribute or class kwargs',
                    cls,
                )
                break

            has_config_from_namespace = True

        if has_config_kwargs or has_config_from_namespace:
            if (
                stmt
                and config.has_alias_generator
                and not config.populate_by_name
                and self.plugin_config.warn_required_dynamic_aliases
            ):
                error_required_dynamic_aliases(self._api, stmt)

        for info in cls.info.mro[1:]:  # 0 is the current class
            if METADATA_KEY not in info.metadata:
                continue

            # Each class depends on the set of fields in its ancestors
            self._api.add_plugin_dependency(make_wildcard_trigger(info.fullname))
            for name, value in info.metadata[METADATA_KEY]['config'].items():
                config.setdefault(name, value)
        return config

    def collect_fields_and_class_vars(
        self, model_config: ModelConfigData, is_root_model: bool
    ) -> tuple[list[PydanticModelField] | None, list[PydanticModelClassVar] | None]:
        """Collects the fields for the model, accounting for parent classes."""
        cls = self._cls

        # First, collect fields and ClassVars belonging to any class in the MRO, ignoring duplicates.
        #
        # We iterate through the MRO in reverse because attrs defined in the parent must appear
        # earlier in the attributes list than attrs defined in the child. See:
        # https://docs.python.org/3/library/dataclasses.html#inheritance
        #
        # However, we also want fields defined in the subtype to override ones defined
        # in the parent. We can implement this via a dict without disrupting the attr order
        # because dicts preserve insertion order in Python 3.7+.
        found_fields: dict[str, PydanticModelField] = {}
        found_class_vars: dict[str, PydanticModelClassVar] = {}
        for info in reversed(cls.info.mro[1:-1]):  # 0 is the current class, -2 is BaseModel, -1 is object
            # if BASEMODEL_METADATA_TAG_KEY in info.metadata and BASEMODEL_METADATA_KEY not in info.metadata:
            #     # We haven't processed the base class yet. Need another pass.
            #     return None, None
            if METADATA_KEY not in info.metadata:
                continue

            # Each class depends on the set of attributes in its dataclass ancestors.
            self._api.add_plugin_dependency(make_wildcard_trigger(info.fullname))

            for name, data in info.metadata[METADATA_KEY]['fields'].items():
                field = PydanticModelField.deserialize(info, data, self._api)
                # (The following comment comes directly from the dataclasses plugin)
                # TODO: We shouldn't be performing type operations during the main
                #       semantic analysis pass, since some TypeInfo attributes might
                #       still be in flux. This should be performed in a later phase.
                field.expand_typevar_from_subtype(cls.info, self._api)
                found_fields[name] = field

                sym_node = cls.info.names.get(name)
                if sym_node and sym_node.node and not isinstance(sym_node.node, Var):
                    self._api.fail(
                        'BaseModel field may only be overridden by another field',
                        sym_node.node,
                    )
            # Collect ClassVars
            for name, data in info.metadata[METADATA_KEY]['class_vars'].items():
                found_class_vars[name] = PydanticModelClassVar.deserialize(data)

        # Second, collect fields and ClassVars belonging to the current class.
        current_field_names: set[str] = set()
        current_class_vars_names: set[str] = set()
        for stmt in self._get_assignment_statements_from_block(cls.defs):
            maybe_field = self.collect_field_or_class_var_from_stmt(stmt, model_config, found_class_vars)
            if maybe_field is None:
                continue

            lhs = stmt.lvalues[0]
            assert isinstance(lhs, NameExpr)  # collect_field_or_class_var_from_stmt guarantees this
            if isinstance(maybe_field, PydanticModelField):
                if is_root_model and lhs.name != 'root':
                    error_extra_fields_on_root_model(self._api, stmt)
                else:
                    current_field_names.add(lhs.name)
                    found_fields[lhs.name] = maybe_field
            elif isinstance(maybe_field, PydanticModelClassVar):
                current_class_vars_names.add(lhs.name)
                found_class_vars[lhs.name] = maybe_field

        return list(found_fields.values()), list(found_class_vars.values())

    def _get_assignment_statements_from_if_statement(self, stmt: IfStmt) -> Iterator[AssignmentStmt]:
        for body in stmt.body:
            if not body.is_unreachable:
                yield from self._get_assignment_statements_from_block(body)
        if stmt.else_body is not None and not stmt.else_body.is_unreachable:
            yield from self._get_assignment_statements_from_block(stmt.else_body)

    def _get_assignment_statements_from_block(self, block: Block) -> Iterator[AssignmentStmt]:
        for stmt in block.body:
            if isinstance(stmt, AssignmentStmt):
                yield stmt
            elif isinstance(stmt, IfStmt):
                yield from self._get_assignment_statements_from_if_statement(stmt)

    def collect_field_or_class_var_from_stmt(  # noqa C901
        self, stmt: AssignmentStmt, model_config: ModelConfigData, class_vars: dict[str, PydanticModelClassVar]
    ) -> PydanticModelField | PydanticModelClassVar | None:
        """Get pydantic model field from statement.

        Args:
            stmt: The statement.
            model_config: Configuration settings for the model.
            class_vars: ClassVars already known to be defined on the model.

        Returns:
            A pydantic model field if it could find the field in statement. Otherwise, `None`.
        """
        cls = self._cls

        lhs = stmt.lvalues[0]
        if not isinstance(lhs, NameExpr) or not _fields.is_valid_field_name(lhs.name) or lhs.name == 'model_config':
            return None

        if not stmt.new_syntax:
            if (
                isinstance(stmt.rvalue, CallExpr)
                and isinstance(stmt.rvalue.callee, CallExpr)
                and isinstance(stmt.rvalue.callee.callee, NameExpr)
                and stmt.rvalue.callee.callee.fullname in DECORATOR_FULLNAMES
            ):
                # This is a (possibly-reused) validator or serializer, not a field
                # In particular, it looks something like: my_validator = validator('my_field')(f)
                # Eventually, we may want to attempt to respect model_config['ignored_types']
                return None

            if lhs.name in class_vars:
                # Class vars are not fields and are not required to be annotated
                return None

            # The assignment does not have an annotation, and it's not anything else we recognize
            error_untyped_fields(self._api, stmt)
            return None

        lhs = stmt.lvalues[0]
        if not isinstance(lhs, NameExpr):
            return None

        if not _fields.is_valid_field_name(lhs.name) or lhs.name == 'model_config':
            return None

        sym = cls.info.names.get(lhs.name)
        if sym is None:  # pragma: no cover
            # This is likely due to a star import (see the dataclasses plugin for a more detailed explanation)
            # This is the same logic used in the dataclasses plugin
            return None

        node = sym.node
        if isinstance(node, PlaceholderNode):  # pragma: no cover
            # See the PlaceholderNode docstring for more detail about how this can occur
            # Basically, it is an edge case when dealing with complex import logic

            # The dataclasses plugin now asserts this cannot happen, but I'd rather not error if it does..
            return None

        if isinstance(node, TypeAlias):
            self._api.fail(
                'Type aliases inside BaseModel definitions are not supported at runtime',
                node,
            )
            # Skip processing this node. This doesn't match the runtime behaviour,
            # but the only alternative would be to modify the SymbolTable,
            # and it's a little hairy to do that in a plugin.
            return None

        if not isinstance(node, Var):  # pragma: no cover
            # Don't know if this edge case still happens with the `is_valid_field` check above
            # but better safe than sorry

            # The dataclasses plugin now asserts this cannot happen, but I'd rather not error if it does..
            return None

        # x: ClassVar[int] is not a field
        if node.is_classvar:
            return PydanticModelClassVar(lhs.name)

        # x: InitVar[int] is not supported in BaseModel
        node_type = get_proper_type(node.type)
        if isinstance(node_type, Instance) and node_type.type.fullname == 'dataclasses.InitVar':
            self._api.fail(
                'InitVar is not supported in BaseModel',
                node,
            )

        has_default = self.get_has_default(stmt)
        strict = self.get_strict(stmt)

        if sym.type is None and node.is_final and node.is_inferred:
            # This follows the logic from the dataclasses plugin. The following comment is taken verbatim:
            #
            # This is a special case, assignment like x: Final = 42 is classified
            # annotated above, but mypy strips the `Final` turning it into x = 42.
            # We do not support inferred types in dataclasses, so we can try inferring
            # type for simple literals, and otherwise require an explicit type
            # argument for Final[...].
            typ = self._api.analyze_simple_literal_type(stmt.rvalue, is_final=True)
            if typ:
                node.type = typ
            else:
                self._api.fail(
                    'Need type argument for Final[...] with non-literal default in BaseModel',
                    stmt,
                )
                node.type = AnyType(TypeOfAny.from_error)

        alias, has_dynamic_alias = self.get_alias_info(stmt)
        if has_dynamic_alias and not model_config.populate_by_name and self.plugin_config.warn_required_dynamic_aliases:
            error_required_dynamic_aliases(self._api, stmt)
        is_frozen = self.is_field_frozen(stmt)

        init_type = self._infer_dataclass_attr_init_type(sym, lhs.name, stmt)
        return PydanticModelField(
            name=lhs.name,
            has_dynamic_alias=has_dynamic_alias,
            has_default=has_default,
            strict=strict,
            alias=alias,
            is_frozen=is_frozen,
            line=stmt.line,
            column=stmt.column,
            type=init_type,
            info=cls.info,
        )

    def _infer_dataclass_attr_init_type(self, sym: SymbolTableNode, name: str, context: Context) -> Type | None:
        """Infer __init__ argument type for an attribute.

        In particular, possibly use the signature of __set__.
        """
        default = sym.type
        if sym.implicit:
            return default
        t = get_proper_type(sym.type)

        # Perform a simple-minded inference from the signature of __set__, if present.
        # We can't use mypy.checkmember here, since this plugin runs before type checking.
        # We only support some basic scanerios here, which is hopefully sufficient for
        # the vast majority of use cases.
        if not isinstance(t, Instance):
            return default
        setter = t.type.get('__set__')
        if setter:
            if isinstance(setter.node, FuncDef):
                super_info = t.type.get_containing_type_info('__set__')
                assert super_info
                if setter.type:
                    setter_type = get_proper_type(map_type_from_supertype(setter.type, t.type, super_info))
                else:
                    return AnyType(TypeOfAny.unannotated)
                if isinstance(setter_type, CallableType) and setter_type.arg_kinds == [
                    ARG_POS,
                    ARG_POS,
                    ARG_POS,
                ]:
                    return expand_type_by_instance(setter_type.arg_types[2], t)
                else:
                    self._api.fail(f'Unsupported signature for "__set__" in "{t.type.name}"', context)
            else:
                self._api.fail(f'Unsupported "__set__" in "{t.type.name}"', context)

        return default

    def add_initializer(
        self, fields: list[PydanticModelField], config: ModelConfigData, is_settings: bool, is_root_model: bool
    ) -> None:
        """Adds a fields-aware `__init__` method to the class.

        The added `__init__` will be annotated with types vs. all `Any` depending on the plugin settings.
        """
        if '__init__' in self._cls.info.names and not self._cls.info.names['__init__'].plugin_generated:
            return  # Don't generate an __init__ if one already exists

        typed = self.plugin_config.init_typed
        model_strict = bool(config.strict)
        use_alias = config.populate_by_name is not True
        requires_dynamic_aliases = bool(config.has_alias_generator and not config.populate_by_name)
        args = self.get_field_arguments(
            fields,
            typed=typed,
            model_strict=model_strict,
            requires_dynamic_aliases=requires_dynamic_aliases,
            use_alias=use_alias,
            is_settings=is_settings,
            is_root_model=is_root_model,
            force_typevars_invariant=True,
        )

        if is_settings:
            base_settings_node = self._api.lookup_fully_qualified(BASESETTINGS_FULLNAME).node
            assert isinstance(base_settings_node, TypeInfo)
            if '__init__' in base_settings_node.names:
                base_settings_init_node = base_settings_node.names['__init__'].node
                assert isinstance(base_settings_init_node, FuncDef)
                if base_settings_init_node is not None and base_settings_init_node.type is not None:
                    func_type = base_settings_init_node.type
                    assert isinstance(func_type, CallableType)
                    for arg_idx, arg_name in enumerate(func_type.arg_names):
                        if arg_name is None or arg_name.startswith('__') or not arg_name.startswith('_'):
                            continue
                        analyzed_variable_type = self._api.anal_type(func_type.arg_types[arg_idx])
                        variable = Var(arg_name, analyzed_variable_type)
                        args.append(Argument(variable, analyzed_variable_type, None, ARG_OPT))

        if not self.should_init_forbid_extra(fields, config):
            var = Var('kwargs')
            args.append(Argument(var, AnyType(TypeOfAny.explicit), None, ARG_STAR2))

        add_method(self._api, self._cls, '__init__', args=args, return_type=NoneType())

    def add_model_construct_method(
        self,
        fields: list[PydanticModelField],
        config: ModelConfigData,
        is_settings: bool,
        is_root_model: bool,
    ) -> None:
        """Adds a fully typed `model_construct` classmethod to the class.

        Similar to the fields-aware __init__ method, but always uses the field names (not aliases),
        and does not treat settings fields as optional.
        """
        set_str = self._api.named_type(f'{BUILTINS_NAME}.set', [self._api.named_type(f'{BUILTINS_NAME}.str')])
        optional_set_str = UnionType([set_str, NoneType()])
        fields_set_argument = Argument(Var('_fields_set', optional_set_str), optional_set_str, None, ARG_OPT)
        with state.strict_optional_set(self._api.options.strict_optional):
            args = self.get_field_arguments(
                fields,
                typed=True,
                model_strict=bool(config.strict),
                requires_dynamic_aliases=False,
                use_alias=False,
                is_settings=is_settings,
                is_root_model=is_root_model,
            )
        if not self.should_init_forbid_extra(fields, config):
            var = Var('kwargs')
            args.append(Argument(var, AnyType(TypeOfAny.explicit), None, ARG_STAR2))

        args = args + [fields_set_argument] if is_root_model else [fields_set_argument] + args

        add_method(
            self._api,
            self._cls,
            'model_construct',
            args=args,
            return_type=fill_typevars(self._cls.info),
            is_classmethod=True,
        )

    def set_frozen(self, fields: list[PydanticModelField], api: SemanticAnalyzerPluginInterface, frozen: bool) -> None:
        """Marks all fields as properties so that attempts to set them trigger mypy errors.

        This is the same approach used by the attrs and dataclasses plugins.
        """
        info = self._cls.info
        for field in fields:
            sym_node = info.names.get(field.name)
            if sym_node is not None:
                var = sym_node.node
                if isinstance(var, Var):
                    var.is_property = frozen or field.is_frozen
                elif isinstance(var, PlaceholderNode) and not self._api.final_iteration:
                    # See https://github.com/pydantic/pydantic/issues/5191 to hit this branch for test coverage
                    self._api.defer()
                else:  # pragma: no cover
                    # I don't know whether it's possible to hit this branch, but I've added it for safety
                    try:
                        var_str = str(var)
                    except TypeError:
                        # This happens for PlaceholderNode; perhaps it will happen for other types in the future..
                        var_str = repr(var)
                    detail = f'sym_node.node: {var_str} (of type {var.__class__})'
                    error_unexpected_behavior(detail, self._api, self._cls)
            else:
                var = field.to_var(info, api, use_alias=False)
                var.info = info
                var.is_property = frozen
                var._fullname = info.fullname + '.' + var.name
                info.names[var.name] = SymbolTableNode(MDEF, var)

    def get_config_update(self, name: str, arg: Expression, lax_extra: bool = False) -> ModelConfigData | None:
        """Determines the config update due to a single kwarg in the ConfigDict definition.

        Warns if a tracked config attribute is set to a value the plugin doesn't know how to interpret (e.g., an int)
        """
        if name not in self.tracked_config_fields:
            return None
        if name == 'extra':
            if isinstance(arg, StrExpr):
                forbid_extra = arg.value == 'forbid'
            elif isinstance(arg, MemberExpr):
                forbid_extra = arg.name == 'forbid'
            else:
                if not lax_extra:
                    # Only emit an error for other types of `arg` (e.g., `NameExpr`, `ConditionalExpr`, etc.) when
                    # reading from a config class, etc. If a ConfigDict is used, then we don't want to emit an error
                    # because you'll get type checking from the ConfigDict itself.
                    #
                    # It would be nice if we could introspect the types better otherwise, but I don't know what the API
                    # is to evaluate an expr into its type and then check if that type is compatible with the expected
                    # type. Note that you can still get proper type checking via: `model_config = ConfigDict(...)`, just
                    # if you don't use an explicit string, the plugin won't be able to infer whether extra is forbidden.
                    error_invalid_config_value(name, self._api, arg)
                return None
            return ModelConfigData(forbid_extra=forbid_extra)
        if name == 'alias_generator':
            has_alias_generator = True
            if isinstance(arg, NameExpr) and arg.fullname == 'builtins.None':
                has_alias_generator = False
            return ModelConfigData(has_alias_generator=has_alias_generator)
        if isinstance(arg, NameExpr) and arg.fullname in ('builtins.True', 'builtins.False'):
            return ModelConfigData(**{name: arg.fullname == 'builtins.True'})
        error_invalid_config_value(name, self._api, arg)
        return None

    @staticmethod
    def get_has_default(stmt: AssignmentStmt) -> bool:
        """Returns a boolean indicating whether the field defined in `stmt` is a required field."""
        expr = stmt.rvalue
        if isinstance(expr, TempNode):
            # TempNode means annotation-only, so has no default
            return False
        if isinstance(expr, CallExpr) and isinstance(expr.callee, RefExpr) and expr.callee.fullname == FIELD_FULLNAME:
            # The "default value" is a call to `Field`; at this point, the field has a default if and only if:
            # * there is a positional argument that is not `...`
            # * there is a keyword argument named "default" that is not `...`
            # * there is a "default_factory" that is not `None`
            for arg, name in zip(expr.args, expr.arg_names):
                # If name is None, then this arg is the default because it is the only positional argument.
                if name is None or name == 'default':
                    return arg.__class__ is not EllipsisExpr
                if name == 'default_factory':
                    return not (isinstance(arg, NameExpr) and arg.fullname == 'builtins.None')
            return False
        # Has no default if the "default value" is Ellipsis (i.e., `field_name: Annotation = ...`)
        return not isinstance(expr, EllipsisExpr)

    @staticmethod
    def get_strict(stmt: AssignmentStmt) -> bool | None:
        """Returns a the `strict` value of a field if defined, otherwise `None`."""
        expr = stmt.rvalue
        if isinstance(expr, CallExpr) and isinstance(expr.callee, RefExpr) and expr.callee.fullname == FIELD_FULLNAME:
            for arg, name in zip(expr.args, expr.arg_names):
                if name != 'strict':
                    continue
                if isinstance(arg, NameExpr):
                    if arg.fullname == 'builtins.True':
                        return True
                    elif arg.fullname == 'builtins.False':
                        return False
                return None
        return None

    @staticmethod
    def get_alias_info(stmt: AssignmentStmt) -> tuple[str | None, bool]:
        """Returns a pair (alias, has_dynamic_alias), extracted from the declaration of the field defined in `stmt`.

        `has_dynamic_alias` is True if and only if an alias is provided, but not as a string literal.
        If `has_dynamic_alias` is True, `alias` will be None.
        """
        expr = stmt.rvalue
        if isinstance(expr, TempNode):
            # TempNode means annotation-only
            return None, False

        if not (
            isinstance(expr, CallExpr) and isinstance(expr.callee, RefExpr) and expr.callee.fullname == FIELD_FULLNAME
        ):
            # Assigned value is not a call to pydantic.fields.Field
            return None, False

        for i, arg_name in enumerate(expr.arg_names):
            if arg_name != 'alias':
                continue
            arg = expr.args[i]
            if isinstance(arg, StrExpr):
                return arg.value, False
            else:
                return None, True
        return None, False

    @staticmethod
    def is_field_frozen(stmt: AssignmentStmt) -> bool:
        """Returns whether the field is frozen, extracted from the declaration of the field defined in `stmt`.

        Note that this is only whether the field was declared to be frozen in a `<field_name> = Field(frozen=True)`
        sense; this does not determine whether the field is frozen because the entire model is frozen; that is
        handled separately.
        """
        expr = stmt.rvalue
        if isinstance(expr, TempNode):
            # TempNode means annotation-only
            return False

        if not (
            isinstance(expr, CallExpr) and isinstance(expr.callee, RefExpr) and expr.callee.fullname == FIELD_FULLNAME
        ):
            # Assigned value is not a call to pydantic.fields.Field
            return False

        for i, arg_name in enumerate(expr.arg_names):
            if arg_name == 'frozen':
                arg = expr.args[i]
                return isinstance(arg, NameExpr) and arg.fullname == 'builtins.True'
        return False

    def get_field_arguments(
        self,
        fields: list[PydanticModelField],
        typed: bool,
        model_strict: bool,
        use_alias: bool,
        requires_dynamic_aliases: bool,
        is_settings: bool,
        is_root_model: bool,
        force_typevars_invariant: bool = False,
    ) -> list[Argument]:
        """Helper function used during the construction of the `__init__` and `model_construct` method signatures.

        Returns a list of mypy Argument instances for use in the generated signatures.
        """
        info = self._cls.info
        arguments = [
            field.to_argument(
                info,
                typed=typed,
                model_strict=model_strict,
                force_optional=requires_dynamic_aliases or is_settings,
                use_alias=use_alias,
                api=self._api,
                force_typevars_invariant=force_typevars_invariant,
                is_root_model_root=is_root_model and field.name == 'root',
            )
            for field in fields
            if not (use_alias and field.has_dynamic_alias)
        ]
        return arguments

    def should_init_forbid_extra(self, fields: list[PydanticModelField], config: ModelConfigData) -> bool:
        """Indicates whether the generated `__init__` should get a `**kwargs` at the end of its signature.

        We disallow arbitrary kwargs if the extra config setting is "forbid", or if the plugin config says to,
        *unless* a required dynamic alias is present (since then we can't determine a valid signature).
        """
        if not config.populate_by_name:
            if self.is_dynamic_alias_present(fields, bool(config.has_alias_generator)):
                return False
        if config.forbid_extra:
            return True
        return self.plugin_config.init_forbid_extra

    @staticmethod
    def is_dynamic_alias_present(fields: list[PydanticModelField], has_alias_generator: bool) -> bool:
        """Returns whether any fields on the model have a "dynamic alias", i.e., an alias that cannot be
        determined during static analysis.
        """
        for field in fields:
            if field.has_dynamic_alias:
                return True
        if has_alias_generator:
            for field in fields:
                if field.alias is None:
                    return True
        return False


class ModelConfigData:
    """Pydantic mypy plugin model config class."""

    def __init__(
        self,
        forbid_extra: bool | None = None,
        frozen: bool | None = None,
        from_attributes: bool | None = None,
        populate_by_name: bool | None = None,
        has_alias_generator: bool | None = None,
        strict: bool | None = None,
    ):
        self.forbid_extra = forbid_extra
        self.frozen = frozen
        self.from_attributes = from_attributes
        self.populate_by_name = populate_by_name
        self.has_alias_generator = has_alias_generator
        self.strict = strict

    def get_values_dict(self) -> dict[str, Any]:
        """Returns a dict of Pydantic model config names to their values.

        It includes the config if config value is not `None`.
        """
        return {k: v for k, v in self.__dict__.items() if v is not None}

    def update(self, config: ModelConfigData | None) -> None:
        """Update Pydantic model config values."""
        if config is None:
            return
        for k, v in config.get_values_dict().items():
            setattr(self, k, v)

    def setdefault(self, key: str, value: Any) -> None:
        """Set default value for Pydantic model config if config value is `None`."""
        if getattr(self, key) is None:
            setattr(self, key, value)


ERROR_ORM = ErrorCode('pydantic-orm', 'Invalid from_attributes call', 'Pydantic')
ERROR_CONFIG = ErrorCode('pydantic-config', 'Invalid config value', 'Pydantic')
ERROR_ALIAS = ErrorCode('pydantic-alias', 'Dynamic alias disallowed', 'Pydantic')
ERROR_UNEXPECTED = ErrorCode('pydantic-unexpected', 'Unexpected behavior', 'Pydantic')
ERROR_UNTYPED = ErrorCode('pydantic-field', 'Untyped field disallowed', 'Pydantic')
ERROR_FIELD_DEFAULTS = ErrorCode('pydantic-field', 'Invalid Field defaults', 'Pydantic')
ERROR_EXTRA_FIELD_ROOT_MODEL = ErrorCode('pydantic-field', 'Extra field on RootModel subclass', 'Pydantic')


def error_from_attributes(model_name: str, api: CheckerPluginInterface, context: Context) -> None:
    """Emits an error when the model does not have `from_attributes=True`."""
    api.fail(f'"{model_name}" does not have from_attributes=True', context, code=ERROR_ORM)


def error_invalid_config_value(name: str, api: SemanticAnalyzerPluginInterface, context: Context) -> None:
    """Emits an error when the config value is invalid."""
    api.fail(f'Invalid value for "Config.{name}"', context, code=ERROR_CONFIG)


def error_required_dynamic_aliases(api: SemanticAnalyzerPluginInterface, context: Context) -> None:
    """Emits required dynamic aliases error.

    This will be called when `warn_required_dynamic_aliases=True`.
    """
    api.fail('Required dynamic aliases disallowed', context, code=ERROR_ALIAS)


def error_unexpected_behavior(
    detail: str, api: CheckerPluginInterface | SemanticAnalyzerPluginInterface, context: Context
) -> None:  # pragma: no cover
    """Emits unexpected behavior error."""
    # Can't think of a good way to test this, but I confirmed it renders as desired by adding to a non-error path
    link = 'https://github.com/pydantic/pydantic/issues/new/choose'
    full_message = f'The pydantic mypy plugin ran into unexpected behavior: {detail}\n'
    full_message += f'Please consider reporting this bug at {link} so we can try to fix it!'
    api.fail(full_message, context, code=ERROR_UNEXPECTED)


def error_untyped_fields(api: SemanticAnalyzerPluginInterface, context: Context) -> None:
    """Emits an error when there is an untyped field in the model."""
    api.fail('Untyped fields disallowed', context, code=ERROR_UNTYPED)


def error_extra_fields_on_root_model(api: CheckerPluginInterface, context: Context) -> None:
    """Emits an error when there is more than just a root field defined for a subclass of RootModel."""
    api.fail('Only `root` is allowed as a field of a `RootModel`', context, code=ERROR_EXTRA_FIELD_ROOT_MODEL)


def add_method(
    api: SemanticAnalyzerPluginInterface | CheckerPluginInterface,
    cls: ClassDef,
    name: str,
    args: list[Argument],
    return_type: Type,
    self_type: Type | None = None,
    tvar_def: TypeVarType | None = None,
    is_classmethod: bool = False,
) -> None:
    """Very closely related to `mypy.plugins.common.add_method_to_class`, with a few pydantic-specific changes."""
    info = cls.info

    # First remove any previously generated methods with the same name
    # to avoid clashes and problems in the semantic analyzer.
    if name in info.names:
        sym = info.names[name]
        if sym.plugin_generated and isinstance(sym.node, FuncDef):
            cls.defs.body.remove(sym.node)  # pragma: no cover

    if isinstance(api, SemanticAnalyzerPluginInterface):
        function_type = api.named_type('builtins.function')
    else:
        function_type = api.named_generic_type('builtins.function', [])

    if is_classmethod:
        self_type = self_type or TypeType(fill_typevars(info))
        first = [Argument(Var('_cls'), self_type, None, ARG_POS, True)]
    else:
        self_type = self_type or fill_typevars(info)
        # `self` is positional *ONLY* here, but this can't be expressed
        # fully in the mypy internal API. ARG_POS is the closest we can get.
        # Using ARG_POS will, however, give mypy errors if a `self` field
        # is present on a model:
        #
        #     Name "self" already defined (possibly by an import)  [no-redef]
        #
        # As a workaround, we give this argument a name that will
        # never conflict. By its positional nature, this name will not
        # be used or exposed to users.
        first = [Argument(Var('__pydantic_self__'), self_type, None, ARG_POS)]
    args = first + args

    arg_types, arg_names, arg_kinds = [], [], []
    for arg in args:
        assert arg.type_annotation, 'All arguments must be fully typed.'
        arg_types.append(arg.type_annotation)
        arg_names.append(arg.variable.name)
        arg_kinds.append(arg.kind)

    signature = CallableType(arg_types, arg_kinds, arg_names, return_type, function_type)
    if tvar_def:
        signature.variables = [tvar_def]

    func = FuncDef(name, args, Block([PassStmt()]))
    func.info = info
    func.type = set_callable_name(signature, func)
    func.is_class = is_classmethod
    func._fullname = info.fullname + '.' + name
    func.line = info.line

    # NOTE: we would like the plugin generated node to dominate, but we still
    # need to keep any existing definitions so they get semantically analyzed.
    if name in info.names:
        # Get a nice unique name instead.
        r_name = get_unique_redefinition_name(name, info.names)
        info.names[r_name] = info.names[name]

    # Add decorator for is_classmethod
    # The dataclasses plugin claims this is unnecessary for classmethods, but not including it results in a
    # signature incompatible with the superclass, which causes mypy errors to occur for every subclass of BaseModel.
    if is_classmethod:
        func.is_decorated = True
        v = Var(name, func.type)
        v.info = info
        v._fullname = func._fullname
        v.is_classmethod = True
        dec = Decorator(func, [NameExpr('classmethod')], v)
        dec.line = info.line
        sym = SymbolTableNode(MDEF, dec)
    else:
        sym = SymbolTableNode(MDEF, func)
    sym.plugin_generated = True
    info.names[name] = sym

    info.defn.defs.body.append(func)


def parse_toml(config_file: str) -> dict[str, Any] | None:
    """Returns a dict of config keys to values.

    It reads configs from toml file and returns `None` if the file is not a toml file.
    """
    if not config_file.endswith('.toml'):
        return None

    if sys.version_info >= (3, 11):
        import tomllib as toml_
    else:
        try:
            import tomli as toml_
        except ImportError:  # pragma: no cover
            import warnings

            warnings.warn('No TOML parser installed, cannot read configuration from `pyproject.toml`.')
            return None

    with open(config_file, 'rb') as rf:
        return toml_.load(rf)
