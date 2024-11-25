from __future__ import annotations

import math
import typing
import uuid

T = typing.TypeVar("T")


class Convertor(typing.Generic[T]):
    regex: typing.ClassVar[str] = ""

    def convert(self, value: str) -> T:
        raise NotImplementedError()  # pragma: no cover

    def to_string(self, value: T) -> str:
        raise NotImplementedError()  # pragma: no cover


class StringConvertor(Convertor[str]):
    regex = "[^/]+"

    def convert(self, value: str) -> str:
        return value

    def to_string(self, value: str) -> str:
        value = str(value)
        assert "/" not in value, "May not contain path separators"
        assert value, "Must not be empty"
        return value


class PathConvertor(Convertor[str]):
    regex = ".*"

    def convert(self, value: str) -> str:
        return str(value)

    def to_string(self, value: str) -> str:
        return str(value)


class IntegerConvertor(Convertor[int]):
    regex = "[0-9]+"

    def convert(self, value: str) -> int:
        return int(value)

    def to_string(self, value: int) -> str:
        value = int(value)
        assert value >= 0, "Negative integers are not supported"
        return str(value)


class FloatConvertor(Convertor[float]):
    regex = r"[0-9]+(\.[0-9]+)?"

    def convert(self, value: str) -> float:
        return float(value)

    def to_string(self, value: float) -> str:
        value = float(value)
        assert value >= 0.0, "Negative floats are not supported"
        assert not math.isnan(value), "NaN values are not supported"
        assert not math.isinf(value), "Infinite values are not supported"
        return ("%0.20f" % value).rstrip("0").rstrip(".")


class UUIDConvertor(Convertor[uuid.UUID]):
    regex = "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"

    def convert(self, value: str) -> uuid.UUID:
        return uuid.UUID(value)

    def to_string(self, value: uuid.UUID) -> str:
        return str(value)


CONVERTOR_TYPES: dict[str, Convertor[typing.Any]] = {
    "str": StringConvertor(),
    "path": PathConvertor(),
    "int": IntegerConvertor(),
    "float": FloatConvertor(),
    "uuid": UUIDConvertor(),
}


def register_url_convertor(key: str, convertor: Convertor[typing.Any]) -> None:
    CONVERTOR_TYPES[key] = convertor
