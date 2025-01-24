from openai import OpenAI
from phi.agent import Agent
from phi.model.deepseek import DeepSeekChat
from phi.model.anthropic import Claude

# Initialize Deepseek client
deepseek_client = OpenAI(
    api_key="sk-",
    base_url="https://api.deepseek.com"
)

# Get user query
query = input("Enter your query: ")
system_prompt = """You are a Pygame and Python Expert that specializes in making games and visualisation through pygame and python programming. 
During your reasoning and thinking, include clear, concise, and well-formatted Python code in your reasoning. 
Always include explanations for the code you provide."""
# Get reasoning from Deepseek
deepseek_response = deepseek_client.chat.completions.create(
    model="deepseek-reasoner",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query}],
    max_tokens=1  # Increased from 1 to get meaningful reasoning
)

reasoning_content = deepseek_response.choices[0].message.reasoning_content
print("\nDeepseek Reasoning:\n", reasoning_content)

# Initialize Claude agent
claude_agent = Agent(
    model=Claude(id="claude-3-5-sonnet-20240620", api_key="sk-anA"),
    markdown=True
)

# Create extraction prompt
extraction_prompt = f"""Extract ONLY the Python code from the following content which is reasoning of a particular query to make a pygame script. 
Return nothing but the raw code without any explanations, or markdown backticks:

{reasoning_content}"""

# Get and print code extraction
code_response = claude_agent.run(extraction_prompt)
extracted_code = code_response.content

print("\nExtracted Python Code:\n")
print(extracted_code)