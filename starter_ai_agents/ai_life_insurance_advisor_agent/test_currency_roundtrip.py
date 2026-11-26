import ast
from pathlib import Path
from typing import Any
import unittest


source = Path(__file__).with_name("life_insurance_advisor_agent.py")
tree = ast.parse(source.read_text(encoding="utf-8"))
functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)
             and node.name in {"safe_number", "format_currency"}]
namespace = {"Any": Any}
exec(compile(ast.Module(body=functions, type_ignores=[]), str(source), "exec"), namespace)
safe_number = namespace["safe_number"]
format_currency = namespace["format_currency"]


class CurrencyRoundtripTests(unittest.TestCase):
    def test_all_supported_symbols_roundtrip_without_zeroing_amounts(self):
        for currency in ("USD", "CAD", "AUD", "GBP", "EUR", "INR"):
            with self.subTest(currency=currency):
                self.assertEqual(safe_number(format_currency(125000, currency)), 125000)

    def test_prefixed_amounts_preserve_decimal_and_negative_values(self):
        self.assertEqual(safe_number("C$1,250.50"), 1250.5)
        self.assertEqual(safe_number("A$-250.75"), -250.75)
        self.assertEqual(safe_number(None), 0)
        self.assertEqual(safe_number("unavailable"), 0)


if __name__ == "__main__":
    unittest.main()
