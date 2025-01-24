from openai import OpenAI
from phi.agent import Agent
from phi.model.deepseek import DeepSeekChat
from phi.model.anthropic import Claude
from langchain import hub
from langchain_openai import ChatOpenAI
from composio_langchain import ComposioToolSet, Action, App

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


composio_toolset = ComposioToolSet(api_key="")
tools = composio_toolset.get_tools(actions=['CODEINTERPRETER_EXECUTE_CODE'])

# Initialize Claude agent
claude_agent = Agent(
    model=Claude(id="claude-3-5-sonnet-20240620", api_key="sk-ant-aA", tools=tools),
    markdown=True
)

# Create extraction prompt
extraction_prompt = f"""Extract ONLY the Python code from the following content which is reasoning of a particular query to make a pygame script. 
Return nothing but the raw code without any explanations, or markdown backticks:

{reasoning_content} ; Take that python code and run it in the code interpreter through the composio tool - displaying a visualisation of the pygame script. """

# Get and print code extraction
code_response = claude_agent.run(extraction_prompt)
extracted_code = code_response.content

print("\nExtracted Python Code:\n")
print(extracted_code)