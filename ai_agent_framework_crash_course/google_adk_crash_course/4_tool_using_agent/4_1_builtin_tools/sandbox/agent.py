import os
from google.adk.agents import Agent
from google.genai import types
from e2b_code_interpreter import Sandbox
from dotenv import load_dotenv

# Load API keys from .env file
load_dotenv()


#GOOGLE_APY_KEY=os.getenv("GOOGLE_APY_KEY")
E2B_API_KEY=os.getenv("E2B_API_KEY")

# 1. Define the tool the AI can use
def execute_python_code(code: str) -> dict:
    """
    Executes Python code safely inside an isolated cloud sandbox and returns the logs.
    Use this whenever you need to compute math, parse data, or verify logic.
    """
    print(f"\n[E2B Sandbox] Executing AI-generated code...")
    
    # Spin up a fresh microVM sandbox
    try:
        # Create a fresh E2B sandbox
        with Sandbox.create(api_key=E2B_API_KEY) as sandbox:
            execution = sandbox.run_code(code)
            return {
                "stdout": execution.logs.stdout,
                "stderr": execution.logs.stderr,
                "error": execution.error.message if execution.error else None
            }
    except Exception as e:
        return {
            "stdout": "",
            "stderr": "",
            "error": str(e)
       }

# 2. Define the Google ADK agent
root_agent = Agent(
    name="python_execution_agent",
    model="gemini-3.5-flash",

    description=(
        "An AI agent that can execute Python code "
        "inside an isolated E2B cloud sandbox."
    ),

    instruction="""
    You are a helpful AI assistant with access to a Python execution tool.

    Your responsibilities:
    1. Understand the user's request.
    2. Use execute_python_code whenever calculations,
       data processing, or code execution are needed.
    3. Write correct and efficient Python code.
    4. Execute the code using the E2B sandbox.
    5. Inspect stdout, stderr, and errors.
    6. Explain the results clearly to the user.

    Never claim that code executed successfully unless
    the tool confirms successful execution.
    """,

    tools=[execute_python_code],

    generate_content_config={
        "temperature": 0.1
    }
)
# --- Run the Agent ---
# if __name__ == "__main__":
#     # Test with a prompt that inherently forces code generation and execution
#     run_agent("Calculate the 45th Fibonacci number using an efficient iterative approach.")