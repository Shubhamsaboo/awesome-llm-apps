import math
from typing import Dict, Union, List

def calculate_basic_math(expression: str) -> Dict[str, Union[float, str]]:
    """
    Calculate basic mathematical expressions safely.
    
    Use this function when users ask for basic arithmetic calculations
    like addition, subtraction, multiplication, division, or expressions
    with parentheses.
    
    Args:
        expression: A mathematical expression as a string (e.g., "2 + 3 * 4")
    
    Returns:
        Dictionary containing the result and operation details
    """
    try:
        # Remove any potentially dangerous characters and keep only safe ones
        allowed_chars = "0123456789+-*/.() "
        safe_expression = ''.join(c for c in expression if c in allowed_chars)
        
        if not safe_expression.strip():
            return {
                "error": "Empty or invalid expression",
                "status": "error"
            }
        
        # Evaluate the expression
        result = eval(safe_expression)
        
        return {
            "result": float(result),
            "expression": expression,
            "safe_expression": safe_expression,
            "status": "success"
        }
    except ZeroDivisionError:
        return {
            "error": "Division by zero",
            "expression": expression,
            "status": "error"
        }
    except Exception as e:
        return {
            "error": f"Error calculating expression: {str(e)}",
            "expression": expression,
            "status": "error"
        }

def convert_temperature(temperature: float, from_unit: str, to_unit: str) -> Dict[str, Union[float, str, Dict]]:
    """
    Convert temperature between Celsius, Fahrenheit, and Kelvin.
    
    Use this function when users ask to convert temperatures between
    different units (C, F, K).
    
    Args:
        temperature: Temperature value to convert
        from_unit: Source unit ('C', 'F', 'K')
        to_unit: Target unit ('C', 'F', 'K')
    
    Returns:
        Dictionary with conversion results
    """
    try:
        # Normalize unit inputs
        from_unit = from_unit.upper()
        to_unit = to_unit.upper()
        
        # Validate units
        valid_units = ['C', 'F', 'K']
        if from_unit not in valid_units or to_unit not in valid_units:
            return {
                "error": f"Invalid units. Use C, F, or K. Got: {from_unit} to {to_unit}",
                "status": "error"
            }
        
        # Convert to Celsius first
        if from_unit == 'F':
            celsius = (temperature - 32) * 5/9
        elif from_unit == 'K':
            celsius = temperature - 273.15
        else:
            celsius = temperature
        
        # Convert from Celsius to target unit
        if to_unit == 'F':
            result = celsius * 9/5 + 32
        elif to_unit == 'K':
            result = celsius + 273.15
        else:
            result = celsius
        
        return {
            "result": round(result, 2),
            "conversion": {
                "from": {"value": temperature, "unit": from_unit},
                "to": {"value": round(result, 2), "unit": to_unit}
            },
            "status": "success"
        }
    except Exception as e:
        return {
            "error": f"Error converting temperature: {str(e)}",
            "status": "error"
        }

def calculate_compound_interest(principal: float, rate: float, years: int, compound_frequency: int = 1) -> Dict[str, Union[float, str, Dict]]:
    """
    Calculate compound interest for an investment.
    
    Use this function when users ask about investment growth,
    compound interest calculations, or future value of investments.
    
    Args:
        principal: Initial investment amount
        rate: Annual interest rate (as decimal, e.g., 0.05 for 5%)
        years: Number of years to compound
        compound_frequency: How many times per year to compound (default: 1)
    
    Returns:
        Dictionary with calculation results and breakdown
    """
    try:
        if principal <= 0:
            return {"error": "Principal must be positive", "status": "error"}
        if rate < 0:
            return {"error": "Interest rate cannot be negative", "status": "error"}
        if years <= 0:
            return {"error": "Years must be positive", "status": "error"}
        if compound_frequency <= 0:
            return {"error": "Compound frequency must be positive", "status": "error"}
        
        # Calculate compound interest: A = P(1 + r/n)^(nt)
        final_amount = principal * (1 + rate/compound_frequency) ** (compound_frequency * years)
        total_interest = final_amount - principal
        
        return {
            "final_amount": round(final_amount, 2),
            "total_interest": round(total_interest, 2),
            "calculation_details": {
                "principal": principal,
                "annual_rate": rate,
                "rate_percentage": f"{rate * 100}%",
                "years": years,
                "compound_frequency": compound_frequency,
                "formula": "A = P(1 + r/n)^(nt)"
            },
            "status": "success"
        }
    except Exception as e:
        return {
            "error": f"Error calculating compound interest: {str(e)}",
            "status": "error"
        }

def calculate_percentage(value: float, total: float) -> Dict[str, Union[float, str]]:
    """
    Calculate what percentage one value is of another.
    
    Use this function when users ask to calculate percentages,
    such as "what percentage is 25 of 100?"
    
    Args:
        value: The value to calculate percentage for
        total: The total value (100% reference)
    
    Returns:
        Dictionary with percentage calculation results
    """
    try:
        if total == 0:
            return {
                "error": "Cannot calculate percentage when total is zero",
                "status": "error"
            }
        
        percentage = (value / total) * 100
        
        return {
            "percentage": round(percentage, 2),
            "calculation": {
                "value": value,
                "total": total,
                "formula": f"({value} / {total}) * 100"
            },
            "formatted": f"{round(percentage, 2)}%",
            "status": "success"
        }
    except Exception as e:
        return {
            "error": f"Error calculating percentage: {str(e)}",
            "status": "error"
        }

def calculate_statistics(numbers: List[float]) -> Dict[str, Union[float, str, int]]:
    """
    Calculate basic statistics for a list of numbers.
    
    Use this function when users ask for statistical analysis
    of a set of numbers (mean, median, mode, etc.).
    
    Args:
        numbers: List of numbers to analyze
    
    Returns:
        Dictionary with statistical results
    """
    try:
        if not numbers:
            return {"error": "Cannot calculate statistics for empty list", "status": "error"}
        
        # Convert to floats and validate
        try:
            nums = [float(x) for x in numbers]
        except (ValueError, TypeError):
            return {"error": "All values must be numbers", "status": "error"}
        
        # Calculate statistics
        mean = sum(nums) / len(nums)
        sorted_nums = sorted(nums)
        
        # Median
        n = len(sorted_nums)
        if n % 2 == 0:
            median = (sorted_nums[n//2 - 1] + sorted_nums[n//2]) / 2
        else:
            median = sorted_nums[n//2]
        
        # Mode (most frequent value)
        from collections import Counter
        counts = Counter(nums)
        mode_count = max(counts.values())
        modes = [k for k, v in counts.items() if v == mode_count]
        
        # Standard deviation
        variance = sum((x - mean) ** 2 for x in nums) / len(nums)
        std_dev = math.sqrt(variance)
        
        return {
            "count": len(nums),
            "mean": round(mean, 2),
            "median": round(median, 2),
            "mode": modes[0] if len(modes) == 1 else modes,
            "min": min(nums),
            "max": max(nums),
            "range": max(nums) - min(nums),
            "standard_deviation": round(std_dev, 2),
            "sum": sum(nums),
            "status": "success"
        }
    except Exception as e:
        return {
            "error": f"Error calculating statistics: {str(e)}",
            "status": "error"
        }

def round_number(number: float, decimal_places: int = 2) -> Dict[str, Union[float, str]]:
    """
    Round a number to specified decimal places.
    
    Use this function when users ask to round numbers to specific
    decimal places or need cleaner number formatting.
    
    Args:
        number: Number to round
        decimal_places: Number of decimal places (default: 2)
    
    Returns:
        Dictionary with rounded number and details
    """
    try:
        if decimal_places < 0:
            return {"error": "Decimal places cannot be negative", "status": "error"}
        
        rounded_number = round(number, decimal_places)
        
        return {
            "rounded_number": rounded_number,
            "original_number": number,
            "decimal_places": decimal_places,
            "status": "success"
        }
    except Exception as e:
        return {
            "error": f"Error rounding number: {str(e)}",
            "status": "error"
        } 