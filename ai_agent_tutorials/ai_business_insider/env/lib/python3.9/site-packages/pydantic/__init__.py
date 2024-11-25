import typing
from importlib import import_module
from warnings import warn

from ._migration import getattr_migration
from .version import VERSION

if typing.TYPE_CHECKING:
    # import of virtually everything is supported via `__getattr__` below,
    # but we need them here for type checking and IDE support
    import pydantic_core
    from pydantic_core.core_schema import (
        FieldSerializationInfo,
        SerializationInfo,
        SerializerFunctionWrapHandler,
        ValidationInfo,
        ValidatorFunctionWrapHandler,
    )

    from . import dataclasses
    from .aliases import AliasChoices, AliasGenerator, AliasPath
    from .annotated_handlers import GetCoreSchemaHandler, GetJsonSchemaHandler
    from .config import ConfigDict, with_config
    from .errors import *
    from .fields import Field, PrivateAttr, computed_field
    from .functional_serializers import (
        PlainSerializer,
        SerializeAsAny,
        WrapSerializer,
        field_serializer,
        model_serializer,
    )
    from .functional_validators import (
        AfterValidator,
        BeforeValidator,
        InstanceOf,
        PlainValidator,
        SkipValidation,
        WrapValidator,
        field_validator,
        model_validator,
    )
    from .json_schema import WithJsonSchema
    from .main import *
    from .networks import *
    from .type_adapter import TypeAdapter
    from .types import *
    from .validate_call_decorator import validate_call
    from .warnings import (
        PydanticDeprecatedSince20,
        PydanticDeprecatedSince26,
        PydanticDeprecatedSince29,
        PydanticDeprecationWarning,
        PydanticExperimentalWarning,
    )

    # this encourages pycharm to import `ValidationError` from here, not pydantic_core
    ValidationError = pydantic_core.ValidationError
    from .deprecated.class_validators import root_validator, validator
    from .deprecated.config import BaseConfig, Extra
    from .deprecated.tools import *
    from .root_model import RootModel

__version__ = VERSION
__all__ = (
    # dataclasses
    'dataclasses',
    # functional validators
    'field_validator',
    'model_validator',
    'AfterValidator',
    'BeforeValidator',
    'PlainValidator',
    'WrapValidator',
    'SkipValidation',
    'InstanceOf',
    # JSON Schema
    'WithJsonSchema',
    # deprecated V1 functional validators, these are imported via `__getattr__` below
    'root_validator',
    'validator',
    # functional serializers
    'field_serializer',
    'model_serializer',
    'PlainSerializer',
    'SerializeAsAny',
    'WrapSerializer',
    # config
    'ConfigDict',
    'with_config',
    # deprecated V1 config, these are imported via `__getattr__` below
    'BaseConfig',
    'Extra',
    # validate_call
    'validate_call',
    # errors
    'PydanticErrorCodes',
    'PydanticUserError',
    'PydanticSchemaGenerationError',
    'PydanticImportError',
    'PydanticUndefinedAnnotation',
    'PydanticInvalidForJsonSchema',
    # fields
    'Field',
    'computed_field',
    'PrivateAttr',
    # alias
    'AliasChoices',
    'AliasGenerator',
    'AliasPath',
    # main
    'BaseModel',
    'create_model',
    # network
    'AnyUrl',
    'AnyHttpUrl',
    'FileUrl',
    'HttpUrl',
    'FtpUrl',
    'WebsocketUrl',
    'AnyWebsocketUrl',
    'UrlConstraints',
    'EmailStr',
    'NameEmail',
    'IPvAnyAddress',
    'IPvAnyInterface',
    'IPvAnyNetwork',
    'PostgresDsn',
    'CockroachDsn',
    'AmqpDsn',
    'RedisDsn',
    'MongoDsn',
    'KafkaDsn',
    'NatsDsn',
    'MySQLDsn',
    'MariaDBDsn',
    'ClickHouseDsn',
    'SnowflakeDsn',
    'validate_email',
    # root_model
    'RootModel',
    # deprecated tools, these are imported via `__getattr__` below
    'parse_obj_as',
    'schema_of',
    'schema_json_of',
    # types
    'Strict',
    'StrictStr',
    'conbytes',
    'conlist',
    'conset',
    'confrozenset',
    'constr',
    'StringConstraints',
    'ImportString',
    'conint',
    'PositiveInt',
    'NegativeInt',
    'NonNegativeInt',
    'NonPositiveInt',
    'confloat',
    'PositiveFloat',
    'NegativeFloat',
    'NonNegativeFloat',
    'NonPositiveFloat',
    'FiniteFloat',
    'condecimal',
    'condate',
    'UUID1',
    'UUID3',
    'UUID4',
    'UUID5',
    'FilePath',
    'DirectoryPath',
    'NewPath',
    'Json',
    'Secret',
    'SecretStr',
    'SecretBytes',
    'SocketPath',
    'StrictBool',
    'StrictBytes',
    'StrictInt',
    'StrictFloat',
    'PaymentCardNumber',
    'ByteSize',
    'PastDate',
    'FutureDate',
    'PastDatetime',
    'FutureDatetime',
    'AwareDatetime',
    'NaiveDatetime',
    'AllowInfNan',
    'EncoderProtocol',
    'EncodedBytes',
    'EncodedStr',
    'Base64Encoder',
    'Base64Bytes',
    'Base64Str',
    'Base64UrlBytes',
    'Base64UrlStr',
    'GetPydanticSchema',
    'Tag',
    'Discriminator',
    'JsonValue',
    'FailFast',
    # type_adapter
    'TypeAdapter',
    # version
    '__version__',
    'VERSION',
    # warnings
    'PydanticDeprecatedSince20',
    'PydanticDeprecatedSince26',
    'PydanticDeprecatedSince29',
    'PydanticDeprecationWarning',
    'PydanticExperimentalWarning',
    # annotated handlers
    'GetCoreSchemaHandler',
    'GetJsonSchemaHandler',
    # pydantic_core
    'ValidationError',
    'ValidationInfo',
    'SerializationInfo',
    'ValidatorFunctionWrapHandler',
    'FieldSerializationInfo',
    'SerializerFunctionWrapHandler',
    'OnErrorOmit',
)

# A mapping of {<member name>: (package, <module name>)} defining dynamic imports
_dynamic_imports: 'dict[str, tuple[str, str]]' = {
    'dataclasses': (__spec__.parent, '__module__'),
    # functional validators
    'field_validator': (__spec__.parent, '.functional_validators'),
    'model_validator': (__spec__.parent, '.functional_validators'),
    'AfterValidator': (__spec__.parent, '.functional_validators'),
    'BeforeValidator': (__spec__.parent, '.functional_validators'),
    'PlainValidator': (__spec__.parent, '.functional_validators'),
    'WrapValidator': (__spec__.parent, '.functional_validators'),
    'SkipValidation': (__spec__.parent, '.functional_validators'),
    'InstanceOf': (__spec__.parent, '.functional_validators'),
    # JSON Schema
    'WithJsonSchema': (__spec__.parent, '.json_schema'),
    # functional serializers
    'field_serializer': (__spec__.parent, '.functional_serializers'),
    'model_serializer': (__spec__.parent, '.functional_serializers'),
    'PlainSerializer': (__spec__.parent, '.functional_serializers'),
    'SerializeAsAny': (__spec__.parent, '.functional_serializers'),
    'WrapSerializer': (__spec__.parent, '.functional_serializers'),
    # config
    'ConfigDict': (__spec__.parent, '.config'),
    'with_config': (__spec__.parent, '.config'),
    # validate call
    'validate_call': (__spec__.parent, '.validate_call_decorator'),
    # errors
    'PydanticErrorCodes': (__spec__.parent, '.errors'),
    'PydanticUserError': (__spec__.parent, '.errors'),
    'PydanticSchemaGenerationError': (__spec__.parent, '.errors'),
    'PydanticImportError': (__spec__.parent, '.errors'),
    'PydanticUndefinedAnnotation': (__spec__.parent, '.errors'),
    'PydanticInvalidForJsonSchema': (__spec__.parent, '.errors'),
    # fields
    'Field': (__spec__.parent, '.fields'),
    'computed_field': (__spec__.parent, '.fields'),
    'PrivateAttr': (__spec__.parent, '.fields'),
    # alias
    'AliasChoices': (__spec__.parent, '.aliases'),
    'AliasGenerator': (__spec__.parent, '.aliases'),
    'AliasPath': (__spec__.parent, '.aliases'),
    # main
    'BaseModel': (__spec__.parent, '.main'),
    'create_model': (__spec__.parent, '.main'),
    # network
    'AnyUrl': (__spec__.parent, '.networks'),
    'AnyHttpUrl': (__spec__.parent, '.networks'),
    'FileUrl': (__spec__.parent, '.networks'),
    'HttpUrl': (__spec__.parent, '.networks'),
    'FtpUrl': (__spec__.parent, '.networks'),
    'WebsocketUrl': (__spec__.parent, '.networks'),
    'AnyWebsocketUrl': (__spec__.parent, '.networks'),
    'UrlConstraints': (__spec__.parent, '.networks'),
    'EmailStr': (__spec__.parent, '.networks'),
    'NameEmail': (__spec__.parent, '.networks'),
    'IPvAnyAddress': (__spec__.parent, '.networks'),
    'IPvAnyInterface': (__spec__.parent, '.networks'),
    'IPvAnyNetwork': (__spec__.parent, '.networks'),
    'PostgresDsn': (__spec__.parent, '.networks'),
    'CockroachDsn': (__spec__.parent, '.networks'),
    'AmqpDsn': (__spec__.parent, '.networks'),
    'RedisDsn': (__spec__.parent, '.networks'),
    'MongoDsn': (__spec__.parent, '.networks'),
    'KafkaDsn': (__spec__.parent, '.networks'),
    'NatsDsn': (__spec__.parent, '.networks'),
    'MySQLDsn': (__spec__.parent, '.networks'),
    'MariaDBDsn': (__spec__.parent, '.networks'),
    'ClickHouseDsn': (__spec__.parent, '.networks'),
    'SnowflakeDsn': (__spec__.parent, '.networks'),
    'validate_email': (__spec__.parent, '.networks'),
    # root_model
    'RootModel': (__spec__.parent, '.root_model'),
    # types
    'Strict': (__spec__.parent, '.types'),
    'StrictStr': (__spec__.parent, '.types'),
    'conbytes': (__spec__.parent, '.types'),
    'conlist': (__spec__.parent, '.types'),
    'conset': (__spec__.parent, '.types'),
    'confrozenset': (__spec__.parent, '.types'),
    'constr': (__spec__.parent, '.types'),
    'StringConstraints': (__spec__.parent, '.types'),
    'ImportString': (__spec__.parent, '.types'),
    'conint': (__spec__.parent, '.types'),
    'PositiveInt': (__spec__.parent, '.types'),
    'NegativeInt': (__spec__.parent, '.types'),
    'NonNegativeInt': (__spec__.parent, '.types'),
    'NonPositiveInt': (__spec__.parent, '.types'),
    'confloat': (__spec__.parent, '.types'),
    'PositiveFloat': (__spec__.parent, '.types'),
    'NegativeFloat': (__spec__.parent, '.types'),
    'NonNegativeFloat': (__spec__.parent, '.types'),
    'NonPositiveFloat': (__spec__.parent, '.types'),
    'FiniteFloat': (__spec__.parent, '.types'),
    'condecimal': (__spec__.parent, '.types'),
    'condate': (__spec__.parent, '.types'),
    'UUID1': (__spec__.parent, '.types'),
    'UUID3': (__spec__.parent, '.types'),
    'UUID4': (__spec__.parent, '.types'),
    'UUID5': (__spec__.parent, '.types'),
    'FilePath': (__spec__.parent, '.types'),
    'DirectoryPath': (__spec__.parent, '.types'),
    'NewPath': (__spec__.parent, '.types'),
    'Json': (__spec__.parent, '.types'),
    'Secret': (__spec__.parent, '.types'),
    'SecretStr': (__spec__.parent, '.types'),
    'SecretBytes': (__spec__.parent, '.types'),
    'StrictBool': (__spec__.parent, '.types'),
    'StrictBytes': (__spec__.parent, '.types'),
    'StrictInt': (__spec__.parent, '.types'),
    'StrictFloat': (__spec__.parent, '.types'),
    'PaymentCardNumber': (__spec__.parent, '.types'),
    'ByteSize': (__spec__.parent, '.types'),
    'PastDate': (__spec__.parent, '.types'),
    'SocketPath': (__spec__.parent, '.types'),
    'FutureDate': (__spec__.parent, '.types'),
    'PastDatetime': (__spec__.parent, '.types'),
    'FutureDatetime': (__spec__.parent, '.types'),
    'AwareDatetime': (__spec__.parent, '.types'),
    'NaiveDatetime': (__spec__.parent, '.types'),
    'AllowInfNan': (__spec__.parent, '.types'),
    'EncoderProtocol': (__spec__.parent, '.types'),
    'EncodedBytes': (__spec__.parent, '.types'),
    'EncodedStr': (__spec__.parent, '.types'),
    'Base64Encoder': (__spec__.parent, '.types'),
    'Base64Bytes': (__spec__.parent, '.types'),
    'Base64Str': (__spec__.parent, '.types'),
    'Base64UrlBytes': (__spec__.parent, '.types'),
    'Base64UrlStr': (__spec__.parent, '.types'),
    'GetPydanticSchema': (__spec__.parent, '.types'),
    'Tag': (__spec__.parent, '.types'),
    'Discriminator': (__spec__.parent, '.types'),
    'JsonValue': (__spec__.parent, '.types'),
    'OnErrorOmit': (__spec__.parent, '.types'),
    'FailFast': (__spec__.parent, '.types'),
    # type_adapter
    'TypeAdapter': (__spec__.parent, '.type_adapter'),
    # warnings
    'PydanticDeprecatedSince20': (__spec__.parent, '.warnings'),
    'PydanticDeprecatedSince26': (__spec__.parent, '.warnings'),
    'PydanticDeprecatedSince29': (__spec__.parent, '.warnings'),
    'PydanticDeprecationWarning': (__spec__.parent, '.warnings'),
    'PydanticExperimentalWarning': (__spec__.parent, '.warnings'),
    # annotated handlers
    'GetCoreSchemaHandler': (__spec__.parent, '.annotated_handlers'),
    'GetJsonSchemaHandler': (__spec__.parent, '.annotated_handlers'),
    # pydantic_core stuff
    'ValidationError': ('pydantic_core', '.'),
    'ValidationInfo': ('pydantic_core', '.core_schema'),
    'SerializationInfo': ('pydantic_core', '.core_schema'),
    'ValidatorFunctionWrapHandler': ('pydantic_core', '.core_schema'),
    'FieldSerializationInfo': ('pydantic_core', '.core_schema'),
    'SerializerFunctionWrapHandler': ('pydantic_core', '.core_schema'),
    # deprecated, mostly not included in __all__
    'root_validator': (__spec__.parent, '.deprecated.class_validators'),
    'validator': (__spec__.parent, '.deprecated.class_validators'),
    'BaseConfig': (__spec__.parent, '.deprecated.config'),
    'Extra': (__spec__.parent, '.deprecated.config'),
    'parse_obj_as': (__spec__.parent, '.deprecated.tools'),
    'schema_of': (__spec__.parent, '.deprecated.tools'),
    'schema_json_of': (__spec__.parent, '.deprecated.tools'),
    # deprecated dynamic imports
    'FieldValidationInfo': ('pydantic_core', '.core_schema'),
    'GenerateSchema': (__spec__.parent, '._internal._generate_schema'),
}
_deprecated_dynamic_imports = {'FieldValidationInfo', 'GenerateSchema'}

_getattr_migration = getattr_migration(__name__)


def __getattr__(attr_name: str) -> object:
    if attr_name in _deprecated_dynamic_imports:
        warn(
            f'Importing {attr_name} from `pydantic` is deprecated. This feature is either no longer supported, or is not public.',
            DeprecationWarning,
            stacklevel=2,
        )

    dynamic_attr = _dynamic_imports.get(attr_name)
    if dynamic_attr is None:
        return _getattr_migration(attr_name)

    package, module_name = dynamic_attr

    if module_name == '__module__':
        result = import_module(f'.{attr_name}', package=package)
        globals()[attr_name] = result
        return result
    else:
        module = import_module(module_name, package=package)
        result = getattr(module, attr_name)
        g = globals()
        for k, (_, v_module_name) in _dynamic_imports.items():
            if v_module_name == module_name and k not in _deprecated_dynamic_imports:
                g[k] = getattr(module, k)
        return result


def __dir__() -> 'list[str]':
    return list(__all__)
