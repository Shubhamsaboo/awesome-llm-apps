"""Pydantic-specific errors."""

from __future__ import annotations as _annotations

import re

from typing_extensions import Literal, Self

from ._migration import getattr_migration
from .version import version_short

__all__ = (
    'PydanticUserError',
    'PydanticUndefinedAnnotation',
    'PydanticImportError',
    'PydanticSchemaGenerationError',
    'PydanticInvalidForJsonSchema',
    'PydanticErrorCodes',
)

# We use this URL to allow for future flexibility about how we host the docs, while allowing for Pydantic
# code in the while with "old" URLs to still work.
# 'u' refers to "user errors" - e.g. errors caused by developers using pydantic, as opposed to validation errors.
DEV_ERROR_DOCS_URL = f'https://errors.pydantic.dev/{version_short()}/u/'
PydanticErrorCodes = Literal[
    'class-not-fully-defined',
    'custom-json-schema',
    'decorator-missing-field',
    'discriminator-no-field',
    'discriminator-alias-type',
    'discriminator-needs-literal',
    'discriminator-alias',
    'discriminator-validator',
    'callable-discriminator-no-tag',
    'typed-dict-version',
    'model-field-overridden',
    'model-field-missing-annotation',
    'config-both',
    'removed-kwargs',
    'circular-reference-schema',
    'invalid-for-json-schema',
    'json-schema-already-used',
    'base-model-instantiated',
    'undefined-annotation',
    'schema-for-unknown-type',
    'import-error',
    'create-model-field-definitions',
    'create-model-config-base',
    'validator-no-fields',
    'validator-invalid-fields',
    'validator-instance-method',
    'validator-input-type',
    'root-validator-pre-skip',
    'model-serializer-instance-method',
    'validator-field-config-info',
    'validator-v1-signature',
    'validator-signature',
    'field-serializer-signature',
    'model-serializer-signature',
    'multiple-field-serializers',
    'invalid-annotated-type',
    'type-adapter-config-unused',
    'root-model-extra',
    'unevaluable-type-annotation',
    'dataclass-init-false-extra-allow',
    'clashing-init-and-init-var',
    'model-config-invalid-field-name',
    'with-config-on-model',
    'dataclass-on-model',
    'validate-call-type',
    'unpack-typed-dict',
    'overlapping-unpack-typed-dict',
    'invalid-self-type',
]


class PydanticErrorMixin:
    """A mixin class for common functionality shared by all Pydantic-specific errors.

    Attributes:
        message: A message describing the error.
        code: An optional error code from PydanticErrorCodes enum.
    """

    def __init__(self, message: str, *, code: PydanticErrorCodes | None) -> None:
        self.message = message
        self.code = code

    def __str__(self) -> str:
        if self.code is None:
            return self.message
        else:
            return f'{self.message}\n\nFor further information visit {DEV_ERROR_DOCS_URL}{self.code}'


class PydanticUserError(PydanticErrorMixin, TypeError):
    """An error raised due to incorrect use of Pydantic."""


class PydanticUndefinedAnnotation(PydanticErrorMixin, NameError):
    """A subclass of `NameError` raised when handling undefined annotations during `CoreSchema` generation.

    Attributes:
        name: Name of the error.
        message: Description of the error.
    """

    def __init__(self, name: str, message: str) -> None:
        self.name = name
        super().__init__(message=message, code='undefined-annotation')

    @classmethod
    def from_name_error(cls, name_error: NameError) -> Self:
        """Convert a `NameError` to a `PydanticUndefinedAnnotation` error.

        Args:
            name_error: `NameError` to be converted.

        Returns:
            Converted `PydanticUndefinedAnnotation` error.
        """
        try:
            name = name_error.name  # type: ignore  # python > 3.10
        except AttributeError:
            name = re.search(r".*'(.+?)'", str(name_error)).group(1)  # type: ignore[union-attr]
        return cls(name=name, message=str(name_error))


class PydanticImportError(PydanticErrorMixin, ImportError):
    """An error raised when an import fails due to module changes between V1 and V2.

    Attributes:
        message: Description of the error.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message, code='import-error')


class PydanticSchemaGenerationError(PydanticUserError):
    """An error raised during failures to generate a `CoreSchema` for some type.

    Attributes:
        message: Description of the error.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message, code='schema-for-unknown-type')


class PydanticInvalidForJsonSchema(PydanticUserError):
    """An error raised during failures to generate a JSON schema for some `CoreSchema`.

    Attributes:
        message: Description of the error.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message, code='invalid-for-json-schema')


__getattr__ = getattr_migration(__name__)
