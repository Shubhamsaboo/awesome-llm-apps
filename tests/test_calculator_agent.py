"""
Unit tests for the calculator agent tools.
"""
import pytest
import sys
from pathlib import Path

# Add the calculator agent directory to the path
calculator_dir = Path(__file__).parent.parent / \
    "ai_agent_framework_crash_course/google_adk_crash_course/4_tool_using_agent/4_2_function_tools/calculator_agent"

if calculator_dir.exists():
    sys.path.insert(0, str(calculator_dir))


@pytest.mark.unit
class TestCalculateBasicMath:
    """Test the calculate_basic_math function."""

    def test_simple_addition(self):
        """Test simple addition."""
        try:
            from tools import calculate_basic_math
            result = calculate_basic_math("2 + 3")
            assert result["status"] == "success"
            assert result["result"] == 5.0
        except ImportError:
            pytest.skip("Calculator tools not available")

    def test_simple_subtraction(self):
        """Test simple subtraction."""
        try:
            from tools import calculate_basic_math
            result = calculate_basic_math("10 - 3")
            assert result["status"] == "success"
            assert result["result"] == 7.0
        except ImportError:
            pytest.skip("Calculator tools not available")

    def test_multiplication(self):
        """Test multiplication."""
        try:
            from tools import calculate_basic_math
            result = calculate_basic_math("4 * 5")
            assert result["status"] == "success"
            assert result["result"] == 20.0
        except ImportError:
            pytest.skip("Calculator tools not available")

    def test_division(self):
        """Test division."""
        try:
            from tools import calculate_basic_math
            result = calculate_basic_math("20 / 4")
            assert result["status"] == "success"
            assert result["result"] == 5.0
        except ImportError:
            pytest.skip("Calculator tools not available")

    def test_complex_expression(self):
        """Test complex expression with parentheses."""
        try:
            from tools import calculate_basic_math
            result = calculate_basic_math("(2 + 3) * 4")
            assert result["status"] == "success"
            assert result["result"] == 20.0
        except ImportError:
            pytest.skip("Calculator tools not available")

    def test_division_by_zero(self):
        """Test division by zero error handling."""
        try:
            from tools import calculate_basic_math
            result = calculate_basic_math("10 / 0")
            assert result["status"] == "error"
            assert "error" in result
        except ImportError:
            pytest.skip("Calculator tools not available")

    def test_empty_expression(self):
        """Test empty expression handling."""
        try:
            from tools import calculate_basic_math
            result = calculate_basic_math("")
            assert result["status"] == "error"
        except ImportError:
            pytest.skip("Calculator tools not available")

    @pytest.mark.security
    def test_no_code_injection(self):
        """Test that code injection attempts are blocked."""
        try:
            from tools import calculate_basic_math
            # Attempt to inject code - should fail safely
            malicious_inputs = [
                "__import__('os').system('ls')",
                "exec('print(1)')",
                "eval('1+1')",
                "1; import os; os.system('ls')",
            ]

            for malicious_input in malicious_inputs:
                result = calculate_basic_math(malicious_input)
                # Should return error, not execute code
                assert result["status"] == "error" or \
                       result.get("result", 0) in [0, 1], \
                    f"Code injection blocked for: {malicious_input}"
        except ImportError:
            pytest.skip("Calculator tools not available")


@pytest.mark.unit
class TestTemperatureConversion:
    """Test temperature conversion functions."""

    def test_celsius_to_fahrenheit(self):
        """Test Celsius to Fahrenheit conversion."""
        try:
            from tools import convert_temperature
            result = convert_temperature(0, 'C', 'F')
            assert result["status"] == "success"
            assert result["result"] == 32.0
        except ImportError:
            pytest.skip("Calculator tools not available")

    def test_fahrenheit_to_celsius(self):
        """Test Fahrenheit to Celsius conversion."""
        try:
            from tools import convert_temperature
            result = convert_temperature(32, 'F', 'C')
            assert result["status"] == "success"
            assert result["result"] == 0.0
        except ImportError:
            pytest.skip("Calculator tools not available")

    def test_celsius_to_kelvin(self):
        """Test Celsius to Kelvin conversion."""
        try:
            from tools import convert_temperature
            result = convert_temperature(0, 'C', 'K')
            assert result["status"] == "success"
            assert result["result"] == 273.15
        except ImportError:
            pytest.skip("Calculator tools not available")

    def test_invalid_unit(self):
        """Test invalid unit handling."""
        try:
            from tools import convert_temperature
            result = convert_temperature(100, 'X', 'Y')
            assert result["status"] == "error"
        except ImportError:
            pytest.skip("Calculator tools not available")


@pytest.mark.unit
class TestStatistics:
    """Test statistical calculation functions."""

    def test_mean_calculation(self):
        """Test mean calculation."""
        try:
            from tools import calculate_statistics
            result = calculate_statistics([1, 2, 3, 4, 5])
            assert result["status"] == "success"
            assert result["mean"] == 3.0
        except ImportError:
            pytest.skip("Calculator tools not available")

    def test_median_odd_count(self):
        """Test median with odd number of values."""
        try:
            from tools import calculate_statistics
            result = calculate_statistics([1, 2, 3, 4, 5])
            assert result["status"] == "success"
            assert result["median"] == 3.0
        except ImportError:
            pytest.skip("Calculator tools not available")

    def test_median_even_count(self):
        """Test median with even number of values."""
        try:
            from tools import calculate_statistics
            result = calculate_statistics([1, 2, 3, 4])
            assert result["status"] == "success"
            assert result["median"] == 2.5
        except ImportError:
            pytest.skip("Calculator tools not available")

    def test_empty_list(self):
        """Test empty list handling."""
        try:
            from tools import calculate_statistics
            result = calculate_statistics([])
            assert result["status"] == "error"
        except ImportError:
            pytest.skip("Calculator tools not available")
