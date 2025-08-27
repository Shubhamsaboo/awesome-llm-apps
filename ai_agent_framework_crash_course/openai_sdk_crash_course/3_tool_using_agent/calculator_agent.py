"""
OpenAI Agents SDK Tutorial 3: Tool Using Agent - Calculator

This module demonstrates how to create custom function tools for mathematical operations.
"""

import os
import math
from dotenv import load_dotenv
from agents import Agent, Runner, function_tool

# Load environment variables
load_dotenv()

@function_tool
def add_numbers(a: float, b: float) -> float:
    """Add two numbers together"""
    return a + b

@function_tool
def subtract_numbers(a: float, b: float) -> float:
    """Subtract second number from first number"""
    return a - b

@function_tool
def multiply_numbers(a: float, b: float) -> float:
    """Multiply two numbers together"""
    return a * b

@function_tool
def divide_numbers(a: float, b: float) -> float:
    """Divide first number by second number"""
    if b == 0:
        return "Error: Cannot divide by zero"
    return a / b

@function_tool
def calculate_compound_interest(principal: float, rate: float, time: int, compounds_per_year: int = 1) -> str:
    """Calculate compound interest using the formula A = P(1 + r/n)^(nt)"""
    if principal <= 0 or rate < 0 or time <= 0 or compounds_per_year <= 0:
        return "Error: All values must be positive"
    
    # Convert percentage to decimal if needed
    if rate > 1:
        rate = rate / 100
    
    amount = principal * (1 + rate/compounds_per_year) ** (compounds_per_year * time)
    interest = amount - principal
    
    return f"Principal: ${principal:,.2f}, Final Amount: ${amount:,.2f}, Interest Earned: ${interest:,.2f}"

@function_tool
def calculate_circle_area(radius: float) -> str:
    """Calculate the area of a circle given its radius"""
    if radius <= 0:
        return "Error: Radius must be positive"
    
    area = math.pi * radius ** 2
    return f"Circle with radius {radius} has area {area:.2f} square units"

@function_tool
def calculate_triangle_area(base: float, height: float) -> str:
    """Calculate the area of a triangle given base and height"""
    if base <= 0 or height <= 0:
        return "Error: Base and height must be positive"
    
    area = 0.5 * base * height
    return f"Triangle with base {base} and height {height} has area {area:.2f} square units"

@function_tool
def convert_temperature(temperature: float, from_unit: str, to_unit: str) -> str:
    """Convert temperature between Celsius, Fahrenheit, and Kelvin"""
    from_unit = from_unit.lower()
    to_unit = to_unit.lower()
    
    # Convert to Celsius first
    if from_unit == "fahrenheit" or from_unit == "f":
        celsius = (temperature - 32) * 5/9
    elif from_unit == "kelvin" or from_unit == "k":
        celsius = temperature - 273.15
    elif from_unit == "celsius" or from_unit == "c":
        celsius = temperature
    else:
        return "Error: Supported units are Celsius, Fahrenheit, and Kelvin"
    
    # Convert from Celsius to target unit
    if to_unit == "fahrenheit" or to_unit == "f":
        result = celsius * 9/5 + 32
        unit_symbol = "°F"
    elif to_unit == "kelvin" or to_unit == "k":
        result = celsius + 273.15
        unit_symbol = "K"
    elif to_unit == "celsius" or to_unit == "c":
        result = celsius
        unit_symbol = "°C"
    else:
        return "Error: Supported units are Celsius, Fahrenheit, and Kelvin"
    
    return f"{temperature}° {from_unit.title()} = {result:.2f}{unit_symbol}"

# Create the calculator agent
calculator_agent = Agent(
    name="Calculator Agent",
    instructions="""
    You are a mathematical calculator assistant with access to various calculation tools.
    
    You can help with:
    - Basic arithmetic (addition, subtraction, multiplication, division)
    - Compound interest calculations
    - Geometric calculations (circle and triangle areas)
    - Temperature conversions between Celsius, Fahrenheit, and Kelvin
    
    When users ask for calculations:
    1. Use the appropriate tool for the calculation
    2. Explain what calculation you're performing
    3. Show the result clearly
    4. Provide additional context if helpful
    
    Always use the provided tools rather than doing calculations yourself.
    Be helpful and explain your calculations step by step.
    """,
    tools=[
        add_numbers,
        subtract_numbers, 
        multiply_numbers,
        divide_numbers,
        calculate_compound_interest,
        calculate_circle_area,
        calculate_triangle_area,
        convert_temperature
    ]
)

def demonstrate_calculator():
    """Demonstrate the calculator agent with various examples"""
    print("🎯 OpenAI Agents SDK - Tutorial 3: Calculator Agent")
    print("=" * 60)
    print()
    
    # Test cases
    test_cases = [
        "Calculate 15 + 27",
        "What's the compound interest on $5000 at 3.5% for 8 years?",
        "Find the area of a circle with radius 12",
        "Convert 100 degrees Fahrenheit to Celsius",
        "What's 144 divided by 12?",
        "Calculate the area of a triangle with base 8 and height 6"
    ]
    
    for i, question in enumerate(test_cases, 1):
        print(f"=== Calculation {i} ===")
        print(f"Question: {question}")
        
        try:
            result = Runner.run_sync(calculator_agent, question)
            print(f"Answer: {result.final_output}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()
        print("-" * 40)
        print()

def interactive_mode():
    """Interactive calculator mode"""
    print("=== Interactive Calculator ===")
    print("Ask me to perform any mathematical calculation!")
    print("Type 'quit' to exit.")
    print()
    
    while True:
        question = input("Math Question: ").strip()
        
        if question.lower() in ['quit', 'exit', 'bye']:
            print("Goodbye!")
            break
        
        if not question:
            continue
        
        try:
            result = Runner.run_sync(calculator_agent, question)
            print(f"📊 Answer: {result.final_output}")
            print()
        except Exception as e:
            print(f"❌ Error: {e}")
            print()

def main():
    """Main function"""
    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not found in environment variables")
        print("Please create a .env file with your OpenAI API key")
        return
    
    try:
        # Run demonstrations
        demonstrate_calculator()
        
        # Interactive mode
        interactive_mode()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
