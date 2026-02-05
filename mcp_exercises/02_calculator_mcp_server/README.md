# Calculator MCP Server

A scientific calculator MCP server with computation history tracking.

## Features

**Tools - Basic Arithmetic:**
- `add` - Add two numbers
- `subtract` - Subtract two numbers
- `multiply` - Multiply two numbers
- `divide` - Divide two numbers (with zero-division protection)

**Tools - Scientific:**
- `power` - Raise a number to a power
- `square_root` - Calculate square root
- `logarithm` - Calculate logarithm with custom base
- `trigonometry` - sin, cos, tan functions
- `factorial` - Compute factorial (up to 170)
- `percentage` - Calculate percentage

**Tools - History:**
- `clear_history` - Clear calculation history

**Resources:**
- `calculator://history` - View last 20 calculations
- `calculator://last-result` - Get the most recent result
- `calculator://constants` - Common math constants (pi, e, golden ratio, etc.)

**Prompts:**
- `solve_equation` - Step-by-step equation solving
- `unit_conversion` - Unit conversion helper

## Concepts Demonstrated

- Multiple tool categories (arithmetic, scientific, history)
- In-memory state management (calculation history)
- Resources exposing dynamic server state
- Input validation and error handling
- Mathematical operations with the `math` module

## Setup

```bash
pip install -r requirements.txt
python server.py
```

## Example Tool Calls

```
add(a=15.5, b=24.3)
power(base=2, exponent=10)
trigonometry(function="sin", angle_degrees=45)
logarithm(number=100, base=10)
```
