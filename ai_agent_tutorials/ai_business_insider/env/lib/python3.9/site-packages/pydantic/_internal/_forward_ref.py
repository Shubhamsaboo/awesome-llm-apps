from __future__ import annotations as _annotations

from dataclasses import dataclass
from typing import Union


@dataclass
class PydanticRecursiveRef:
    type_ref: str

    __name__ = 'PydanticRecursiveRef'
    __hash__ = object.__hash__

    def __call__(self) -> None:
        """Defining __call__ is necessary for the `typing` module to let you use an instance of
        this class as the result of resolving a standard ForwardRef.
        """

    def __or__(self, other):
        return Union[self, other]  # type: ignore

    def __ror__(self, other):
        return Union[other, self]  # type: ignore
