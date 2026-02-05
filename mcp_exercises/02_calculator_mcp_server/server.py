"""
Calculator MCP Server
=====================
A scientific calculator MCP server with computation history.
Demonstrates: tools with multiple operations, resources for state,
prompts for math help, and in-memory state management.
"""

import json
import math
from datetime import datetime

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Calculator MCP Server")

# ──────────────────────────────────────────────
# In-memory State
# ──────────────────────────────────────────────

calculation_history: list[dict] = []


def record_calculation(operation: str, inputs: dict, result: float | str) -> None:
    """Record a calculation in history."""
    calculation_history.append(
        {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "inputs": inputs,
            "result": result,
        }
    )


# ──────────────────────────────────────────────
# Basic Arithmetic Tools
# ──────────────────────────────────────────────


@mcp.tool()
def add(a: float, b: float) -> str:
    """Add two numbers together.

    Args:
        a: First number
        b: Second number
    """
    result = a + b
    record_calculation("add", {"a": a, "b": b}, result)
    return json.dumps({"operation": f"{a} + {b}", "result": result})


@mcp.tool()
def subtract(a: float, b: float) -> str:
    """Subtract the second number from the first.

    Args:
        a: First number
        b: Second number (subtracted from a)
    """
    result = a - b
    record_calculation("subtract", {"a": a, "b": b}, result)
    return json.dumps({"operation": f"{a} - {b}", "result": result})


@mcp.tool()
def multiply(a: float, b: float) -> str:
    """Multiply two numbers.

    Args:
        a: First number
        b: Second number
    """
    result = a * b
    record_calculation("multiply", {"a": a, "b": b}, result)
    return json.dumps({"operation": f"{a} * {b}", "result": result})


@mcp.tool()
def divide(a: float, b: float) -> str:
    """Divide the first number by the second.

    Args:
        a: Numerator
        b: Denominator (must not be zero)
    """
    if b == 0:
        return json.dumps({"error": "Division by zero is not allowed."})
    result = a / b
    record_calculation("divide", {"a": a, "b": b}, result)
    return json.dumps({"operation": f"{a} / {b}", "result": result})


# ──────────────────────────────────────────────
# Scientific Tools
# ──────────────────────────────────────────────


@mcp.tool()
def power(base: float, exponent: float) -> str:
    """Raise a number to a power.

    Args:
        base: The base number
        exponent: The exponent to raise the base to
    """
    result = math.pow(base, exponent)
    record_calculation("power", {"base": base, "exponent": exponent}, result)
    return json.dumps({"operation": f"{base} ^ {exponent}", "result": result})


@mcp.tool()
def square_root(number: float) -> str:
    """Calculate the square root of a number.

    Args:
        number: The number to calculate the square root of (must be non-negative)
    """
    if number < 0:
        return json.dumps({"error": "Cannot calculate square root of a negative number."})
    result = math.sqrt(number)
    record_calculation("square_root", {"number": number}, result)
    return json.dumps({"operation": f"sqrt({number})", "result": result})


@mcp.tool()
def logarithm(number: float, base: float = 10.0) -> str:
    """Calculate the logarithm of a number.

    Args:
        number: The number to calculate the log of (must be positive)
        base: The logarithm base (default: 10). Use 2.718281828 for natural log.
    """
    if number <= 0:
        return json.dumps({"error": "Logarithm requires a positive number."})
    if base <= 0 or base == 1:
        return json.dumps({"error": "Base must be positive and not equal to 1."})
    result = math.log(number) / math.log(base)
    record_calculation("logarithm", {"number": number, "base": base}, result)
    return json.dumps({"operation": f"log_{base}({number})", "result": result})


@mcp.tool()
def trigonometry(function: str, angle_degrees: float) -> str:
    """Calculate trigonometric functions.

    Args:
        function: The trig function - "sin", "cos", or "tan"
        angle_degrees: The angle in degrees
    """
    radians = math.radians(angle_degrees)
    trig_functions = {
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
    }
    func = trig_functions.get(function.lower())
    if not func:
        return json.dumps({"error": f"Unknown function '{function}'. Use sin, cos, or tan."})
    result = func(radians)
    record_calculation("trigonometry", {"function": function, "angle_degrees": angle_degrees}, result)
    return json.dumps(
        {"operation": f"{function}({angle_degrees}deg)", "result": round(result, 10)}
    )


@mcp.tool()
def factorial(n: int) -> str:
    """Calculate the factorial of a non-negative integer.

    Args:
        n: A non-negative integer (max 170 to avoid overflow)
    """
    if n < 0:
        return json.dumps({"error": "Factorial requires a non-negative integer."})
    if n > 170:
        return json.dumps({"error": "Input too large. Maximum is 170."})
    result = math.factorial(n)
    record_calculation("factorial", {"n": n}, result)
    return json.dumps({"operation": f"{n}!", "result": result})


@mcp.tool()
def percentage(value: float, total: float) -> str:
    """Calculate what percentage a value is of a total.

    Args:
        value: The part value
        total: The total value (must not be zero)
    """
    if total == 0:
        return json.dumps({"error": "Total must not be zero."})
    result = (value / total) * 100
    record_calculation("percentage", {"value": value, "total": total}, result)
    return json.dumps({"operation": f"({value} / {total}) * 100", "result": round(result, 4), "formatted": f"{round(result, 2)}%"})


# ──────────────────────────────────────────────
# History Tools
# ──────────────────────────────────────────────


@mcp.tool()
def clear_history() -> str:
    """Clear the entire calculation history."""
    calculation_history.clear()
    return json.dumps({"message": "Calculation history cleared."})


# ──────────────────────────────────────────────
# Resources
# ──────────────────────────────────────────────


@mcp.resource("calculator://history")
def get_history() -> str:
    """Get the full calculation history."""
    return json.dumps(
        {
            "total_calculations": len(calculation_history),
            "history": calculation_history[-20:],  # Last 20
        },
        indent=2,
    )


@mcp.resource("calculator://last-result")
def get_last_result() -> str:
    """Get the most recent calculation result."""
    if not calculation_history:
        return json.dumps({"message": "No calculations performed yet."})
    return json.dumps(calculation_history[-1], indent=2)


@mcp.resource("calculator://constants")
def math_constants() -> str:
    """Get common mathematical constants."""
    return json.dumps(
        {
            "pi": math.pi,
            "e": math.e,
            "tau": math.tau,
            "inf": "Infinity",
            "golden_ratio": (1 + math.sqrt(5)) / 2,
            "sqrt2": math.sqrt(2),
        },
        indent=2,
    )


# ──────────────────────────────────────────────
# Prompts
# ──────────────────────────────────────────────


@mcp.prompt()
def solve_equation(equation: str) -> str:
    """Generate a prompt to solve a math equation step by step."""
    return f"""Please solve the following equation step by step using the calculator tools:

{equation}

Show each calculation step clearly and explain your reasoning."""


@mcp.prompt()
def unit_conversion(value: str, from_unit: str, to_unit: str) -> str:
    """Generate a prompt for unit conversion."""
    return f"""Please convert {value} from {from_unit} to {to_unit}.
Use the calculator tools to perform the conversion and show the formula used."""


# ──────────────────────────────────────────────
# Entry Point
# ──────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run(transport="stdio")
