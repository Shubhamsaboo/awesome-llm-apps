import ast
from pathlib import Path
from typing import Any
import unittest


source = Path(__file__).with_name("life_insurance_advisor_agent.py")
tree = ast.parse(source.read_text(encoding="utf-8"))
function = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                and node.name == "parse_percentage")
namespace = {"Any": Any}
exec(compile(ast.Module(body=[function], type_ignores=[]), str(source), "exec"), namespace)
parse_percentage = namespace["parse_percentage"]


class PercentageUnitTests(unittest.TestCase):
    def test_explicit_percent_sign_controls_units_below_one(self):
        self.assertAlmostEqual(parse_percentage("0.5%"), 0.005)
        self.assertAlmostEqual(parse_percentage(" 0.25 % "), 0.0025)
        self.assertAlmostEqual(parse_percentage("-0.5%"), -0.005)

    def test_existing_decimal_and_whole_percent_inputs_are_preserved(self):
        self.assertEqual(parse_percentage(0.02), 0.02)
        self.assertEqual(parse_percentage("0.02"), 0.02)
        self.assertEqual(parse_percentage("2%"), 0.02)
        self.assertEqual(parse_percentage(2), 0.02)
        self.assertEqual(parse_percentage("invalid", fallback=0.03), 0.03)


if __name__ == "__main__":
    unittest.main()
