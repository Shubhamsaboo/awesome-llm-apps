"""Regression tests for the advisor's numeric inputs, without provider calls."""

import unittest

from life_insurance_advisor_agent import (
    compute_local_breakdown,
    format_currency,
    parse_percentage,
    safe_number,
)


class NumericInputTests(unittest.TestCase):
    def test_explicit_percent_sign_controls_fractional_units(self):
        for value, expected in (("0.5%", 0.005), (" 0.25 % ", 0.0025), ("-0.5%", -0.005)):
            with self.subTest(value=value):
                self.assertAlmostEqual(parse_percentage(value), expected)

    def test_existing_percentage_inputs_and_fallbacks_are_preserved(self):
        for value in (0.02, "0.02", "2%", 2):
            with self.subTest(value=value):
                self.assertEqual(parse_percentage(value), 0.02)
        self.assertEqual(parse_percentage("invalid", fallback=0.03), 0.03)
        self.assertEqual(parse_percentage(None, fallback=0.03), 0.03)

    def test_all_supported_currencies_roundtrip(self):
        for currency in ("USD", "CAD", "AUD", "GBP", "EUR", "INR"):
            with self.subTest(currency=currency):
                self.assertEqual(safe_number(format_currency(125000, currency)), 125000)

    def test_prefixed_amounts_preserve_decimals_and_negatives(self):
        self.assertEqual(safe_number("C$1,250.50"), 1250.5)
        self.assertEqual(safe_number("A$-250.75"), -250.75)
        self.assertEqual(safe_number(None), 0)
        self.assertEqual(safe_number("unavailable"), 0)

    def test_breakdown_uses_explicit_rate_and_formatted_amounts(self):
        profile = {
            "annual_income": "C$100,000",
            "income_replacement_years": 1,
            "total_debt": "C$10,000",
            "available_savings": "C$2,000",
            "existing_life_insurance": "C$3,000",
        }
        result = compute_local_breakdown(profile, parse_percentage("0.5%"))
        self.assertAlmostEqual(result["real_rate"], 0.005)
        self.assertAlmostEqual(result["recommended"], 104502.48756219, places=5)


if __name__ == "__main__":
    unittest.main()
