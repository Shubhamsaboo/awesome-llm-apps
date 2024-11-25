from functools import lru_cache
from typing import TYPE_CHECKING, Type

if TYPE_CHECKING:
    from pydantic import BaseModel
    from pydantic.fields import FieldInfo


@lru_cache(maxsize=None)
def import_cached_base_model() -> Type['BaseModel']:
    from pydantic import BaseModel

    return BaseModel


@lru_cache(maxsize=None)
def import_cached_field_info() -> Type['FieldInfo']:
    from pydantic.fields import FieldInfo

    return FieldInfo
