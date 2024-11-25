import sys
from typing import Any, Callable, Dict

from .version import version_short

MOVED_IN_V2 = {
    'pydantic.utils:version_info': 'pydantic.version:version_info',
    'pydantic.error_wrappers:ValidationError': 'pydantic:ValidationError',
    'pydantic.utils:to_camel': 'pydantic.alias_generators:to_pascal',
    'pydantic.utils:to_lower_camel': 'pydantic.alias_generators:to_camel',
    'pydantic:PyObject': 'pydantic.types:ImportString',
    'pydantic.types:PyObject': 'pydantic.types:ImportString',
    'pydantic.generics:GenericModel': 'pydantic.BaseModel',
}

DEPRECATED_MOVED_IN_V2 = {
    'pydantic.tools:schema_of': 'pydantic.deprecated.tools:schema_of',
    'pydantic.tools:parse_obj_as': 'pydantic.deprecated.tools:parse_obj_as',
    'pydantic.tools:schema_json_of': 'pydantic.deprecated.tools:schema_json_of',
    'pydantic.json:pydantic_encoder': 'pydantic.deprecated.json:pydantic_encoder',
    'pydantic:validate_arguments': 'pydantic.deprecated.decorator:validate_arguments',
    'pydantic.json:custom_pydantic_encoder': 'pydantic.deprecated.json:custom_pydantic_encoder',
    'pydantic.json:timedelta_isoformat': 'pydantic.deprecated.json:timedelta_isoformat',
    'pydantic.decorator:validate_arguments': 'pydantic.deprecated.decorator:validate_arguments',
    'pydantic.class_validators:validator': 'pydantic.deprecated.class_validators:validator',
    'pydantic.class_validators:root_validator': 'pydantic.deprecated.class_validators:root_validator',
    'pydantic.config:BaseConfig': 'pydantic.deprecated.config:BaseConfig',
    'pydantic.config:Extra': 'pydantic.deprecated.config:Extra',
}

REDIRECT_TO_V1 = {
    f'pydantic.utils:{obj}': f'pydantic.v1.utils:{obj}'
    for obj in (
        'deep_update',
        'GetterDict',
        'lenient_issubclass',
        'lenient_isinstance',
        'is_valid_field',
        'update_not_none',
        'import_string',
        'Representation',
        'ROOT_KEY',
        'smart_deepcopy',
        'sequence_like',
    )
}


REMOVED_IN_V2 = {
    'pydantic:ConstrainedBytes',
    'pydantic:ConstrainedDate',
    'pydantic:ConstrainedDecimal',
    'pydantic:ConstrainedFloat',
    'pydantic:ConstrainedFrozenSet',
    'pydantic:ConstrainedInt',
    'pydantic:ConstrainedList',
    'pydantic:ConstrainedSet',
    'pydantic:ConstrainedStr',
    'pydantic:JsonWrapper',
    'pydantic:NoneBytes',
    'pydantic:NoneStr',
    'pydantic:NoneStrBytes',
    'pydantic:Protocol',
    'pydantic:Required',
    'pydantic:StrBytes',
    'pydantic:compiled',
    'pydantic.config:get_config',
    'pydantic.config:inherit_config',
    'pydantic.config:prepare_config',
    'pydantic:create_model_from_namedtuple',
    'pydantic:create_model_from_typeddict',
    'pydantic.dataclasses:create_pydantic_model_from_dataclass',
    'pydantic.dataclasses:make_dataclass_validator',
    'pydantic.dataclasses:set_validation',
    'pydantic.datetime_parse:parse_date',
    'pydantic.datetime_parse:parse_time',
    'pydantic.datetime_parse:parse_datetime',
    'pydantic.datetime_parse:parse_duration',
    'pydantic.error_wrappers:ErrorWrapper',
    'pydantic.errors:AnyStrMaxLengthError',
    'pydantic.errors:AnyStrMinLengthError',
    'pydantic.errors:ArbitraryTypeError',
    'pydantic.errors:BoolError',
    'pydantic.errors:BytesError',
    'pydantic.errors:CallableError',
    'pydantic.errors:ClassError',
    'pydantic.errors:ColorError',
    'pydantic.errors:ConfigError',
    'pydantic.errors:DataclassTypeError',
    'pydantic.errors:DateError',
    'pydantic.errors:DateNotInTheFutureError',
    'pydantic.errors:DateNotInThePastError',
    'pydantic.errors:DateTimeError',
    'pydantic.errors:DecimalError',
    'pydantic.errors:DecimalIsNotFiniteError',
    'pydantic.errors:DecimalMaxDigitsError',
    'pydantic.errors:DecimalMaxPlacesError',
    'pydantic.errors:DecimalWholeDigitsError',
    'pydantic.errors:DictError',
    'pydantic.errors:DurationError',
    'pydantic.errors:EmailError',
    'pydantic.errors:EnumError',
    'pydantic.errors:EnumMemberError',
    'pydantic.errors:ExtraError',
    'pydantic.errors:FloatError',
    'pydantic.errors:FrozenSetError',
    'pydantic.errors:FrozenSetMaxLengthError',
    'pydantic.errors:FrozenSetMinLengthError',
    'pydantic.errors:HashableError',
    'pydantic.errors:IPv4AddressError',
    'pydantic.errors:IPv4InterfaceError',
    'pydantic.errors:IPv4NetworkError',
    'pydantic.errors:IPv6AddressError',
    'pydantic.errors:IPv6InterfaceError',
    'pydantic.errors:IPv6NetworkError',
    'pydantic.errors:IPvAnyAddressError',
    'pydantic.errors:IPvAnyInterfaceError',
    'pydantic.errors:IPvAnyNetworkError',
    'pydantic.errors:IntEnumError',
    'pydantic.errors:IntegerError',
    'pydantic.errors:InvalidByteSize',
    'pydantic.errors:InvalidByteSizeUnit',
    'pydantic.errors:InvalidDiscriminator',
    'pydantic.errors:InvalidLengthForBrand',
    'pydantic.errors:JsonError',
    'pydantic.errors:JsonTypeError',
    'pydantic.errors:ListError',
    'pydantic.errors:ListMaxLengthError',
    'pydantic.errors:ListMinLengthError',
    'pydantic.errors:ListUniqueItemsError',
    'pydantic.errors:LuhnValidationError',
    'pydantic.errors:MissingDiscriminator',
    'pydantic.errors:MissingError',
    'pydantic.errors:NoneIsAllowedError',
    'pydantic.errors:NoneIsNotAllowedError',
    'pydantic.errors:NotDigitError',
    'pydantic.errors:NotNoneError',
    'pydantic.errors:NumberNotGeError',
    'pydantic.errors:NumberNotGtError',
    'pydantic.errors:NumberNotLeError',
    'pydantic.errors:NumberNotLtError',
    'pydantic.errors:NumberNotMultipleError',
    'pydantic.errors:PathError',
    'pydantic.errors:PathNotADirectoryError',
    'pydantic.errors:PathNotAFileError',
    'pydantic.errors:PathNotExistsError',
    'pydantic.errors:PatternError',
    'pydantic.errors:PyObjectError',
    'pydantic.errors:PydanticTypeError',
    'pydantic.errors:PydanticValueError',
    'pydantic.errors:SequenceError',
    'pydantic.errors:SetError',
    'pydantic.errors:SetMaxLengthError',
    'pydantic.errors:SetMinLengthError',
    'pydantic.errors:StrError',
    'pydantic.errors:StrRegexError',
    'pydantic.errors:StrictBoolError',
    'pydantic.errors:SubclassError',
    'pydantic.errors:TimeError',
    'pydantic.errors:TupleError',
    'pydantic.errors:TupleLengthError',
    'pydantic.errors:UUIDError',
    'pydantic.errors:UUIDVersionError',
    'pydantic.errors:UrlError',
    'pydantic.errors:UrlExtraError',
    'pydantic.errors:UrlHostError',
    'pydantic.errors:UrlHostTldError',
    'pydantic.errors:UrlPortError',
    'pydantic.errors:UrlSchemeError',
    'pydantic.errors:UrlSchemePermittedError',
    'pydantic.errors:UrlUserInfoError',
    'pydantic.errors:WrongConstantError',
    'pydantic.main:validate_model',
    'pydantic.networks:stricturl',
    'pydantic:parse_file_as',
    'pydantic:parse_raw_as',
    'pydantic:stricturl',
    'pydantic.tools:parse_file_as',
    'pydantic.tools:parse_raw_as',
    'pydantic.types:ConstrainedBytes',
    'pydantic.types:ConstrainedDate',
    'pydantic.types:ConstrainedDecimal',
    'pydantic.types:ConstrainedFloat',
    'pydantic.types:ConstrainedFrozenSet',
    'pydantic.types:ConstrainedInt',
    'pydantic.types:ConstrainedList',
    'pydantic.types:ConstrainedSet',
    'pydantic.types:ConstrainedStr',
    'pydantic.types:JsonWrapper',
    'pydantic.types:NoneBytes',
    'pydantic.types:NoneStr',
    'pydantic.types:NoneStrBytes',
    'pydantic.types:StrBytes',
    'pydantic.typing:evaluate_forwardref',
    'pydantic.typing:AbstractSetIntStr',
    'pydantic.typing:AnyCallable',
    'pydantic.typing:AnyClassMethod',
    'pydantic.typing:CallableGenerator',
    'pydantic.typing:DictAny',
    'pydantic.typing:DictIntStrAny',
    'pydantic.typing:DictStrAny',
    'pydantic.typing:IntStr',
    'pydantic.typing:ListStr',
    'pydantic.typing:MappingIntStrAny',
    'pydantic.typing:NoArgAnyCallable',
    'pydantic.typing:NoneType',
    'pydantic.typing:ReprArgs',
    'pydantic.typing:SetStr',
    'pydantic.typing:StrPath',
    'pydantic.typing:TupleGenerator',
    'pydantic.typing:WithArgsTypes',
    'pydantic.typing:all_literal_values',
    'pydantic.typing:display_as_type',
    'pydantic.typing:get_all_type_hints',
    'pydantic.typing:get_args',
    'pydantic.typing:get_origin',
    'pydantic.typing:get_sub_types',
    'pydantic.typing:is_callable_type',
    'pydantic.typing:is_classvar',
    'pydantic.typing:is_finalvar',
    'pydantic.typing:is_literal_type',
    'pydantic.typing:is_namedtuple',
    'pydantic.typing:is_new_type',
    'pydantic.typing:is_none_type',
    'pydantic.typing:is_typeddict',
    'pydantic.typing:is_typeddict_special',
    'pydantic.typing:is_union',
    'pydantic.typing:new_type_supertype',
    'pydantic.typing:resolve_annotations',
    'pydantic.typing:typing_base',
    'pydantic.typing:update_field_forward_refs',
    'pydantic.typing:update_model_forward_refs',
    'pydantic.utils:ClassAttribute',
    'pydantic.utils:DUNDER_ATTRIBUTES',
    'pydantic.utils:PyObjectStr',
    'pydantic.utils:ValueItems',
    'pydantic.utils:almost_equal_floats',
    'pydantic.utils:get_discriminator_alias_and_values',
    'pydantic.utils:get_model',
    'pydantic.utils:get_unique_discriminator_alias',
    'pydantic.utils:in_ipython',
    'pydantic.utils:is_valid_identifier',
    'pydantic.utils:path_type',
    'pydantic.utils:validate_field_name',
    'pydantic:validate_model',
}


def getattr_migration(module: str) -> Callable[[str], Any]:
    """Implement PEP 562 for objects that were either moved or removed on the migration
    to V2.

    Args:
        module: The module name.

    Returns:
        A callable that will raise an error if the object is not found.
    """
    # This avoids circular import with errors.py.
    from .errors import PydanticImportError

    def wrapper(name: str) -> object:
        """Raise an error if the object is not found, or warn if it was moved.

        In case it was moved, it still returns the object.

        Args:
            name: The object name.

        Returns:
            The object.
        """
        if name == '__path__':
            raise AttributeError(f'module {module!r} has no attribute {name!r}')

        import warnings

        from ._internal._validators import import_string

        import_path = f'{module}:{name}'
        if import_path in MOVED_IN_V2.keys():
            new_location = MOVED_IN_V2[import_path]
            warnings.warn(f'`{import_path}` has been moved to `{new_location}`.')
            return import_string(MOVED_IN_V2[import_path])
        if import_path in DEPRECATED_MOVED_IN_V2:
            # skip the warning here because a deprecation warning will be raised elsewhere
            return import_string(DEPRECATED_MOVED_IN_V2[import_path])
        if import_path in REDIRECT_TO_V1:
            new_location = REDIRECT_TO_V1[import_path]
            warnings.warn(
                f'`{import_path}` has been removed. We are importing from `{new_location}` instead.'
                'See the migration guide for more details: https://docs.pydantic.dev/latest/migration/'
            )
            return import_string(REDIRECT_TO_V1[import_path])
        if import_path == 'pydantic:BaseSettings':
            raise PydanticImportError(
                '`BaseSettings` has been moved to the `pydantic-settings` package. '
                f'See https://docs.pydantic.dev/{version_short()}/migration/#basesettings-has-moved-to-pydantic-settings '
                'for more details.'
            )
        if import_path in REMOVED_IN_V2:
            raise PydanticImportError(f'`{import_path}` has been removed in V2.')
        globals: Dict[str, Any] = sys.modules[module].__dict__
        if name in globals:
            return globals[name]
        raise AttributeError(f'module {module!r} has no attribute {name!r}')

    return wrapper
