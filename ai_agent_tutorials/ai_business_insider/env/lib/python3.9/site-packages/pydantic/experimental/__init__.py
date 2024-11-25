"""The "experimental" module of pydantic contains potential new features that are subject to change."""

import warnings

from pydantic.warnings import PydanticExperimentalWarning

warnings.warn(
    'This module is experimental, its contents are subject to change and deprecation.',
    category=PydanticExperimentalWarning,
)
