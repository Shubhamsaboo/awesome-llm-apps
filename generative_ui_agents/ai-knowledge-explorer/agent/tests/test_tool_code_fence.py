import pytest

from src.tools import _strip_code_fence


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("```", ""),
        ("```json", ""),
        ('```json\n{"a": 1}\n```', '{"a": 1}'),
        ('{"a": 1}', '{"a": 1}'),
    ],
)
def test_strip_code_fence(raw, expected):
    assert _strip_code_fence(raw) == expected