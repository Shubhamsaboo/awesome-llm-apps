from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from agno.tools.reasoning import ReasoningTools
from rich.console import Console
import os

api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    api_key = Console().input("[bold yellow]Enter OpenRouter API Key: [/bold yellow]").strip()

# Free model router (live-tested). Routes to a working free model automatically.
# Override with: $env:OPENROUTER_MODEL="google/gemma-4-26b-a4b-it:free"
model_id = os.getenv("OPENROUTER_MODEL", "openrouter/free")

regular_agent = Agent(model=OpenRouter(id=model_id, api_key=api_key), markdown=True)
console = Console()
reasoning_agent = Agent(
    model=OpenRouter(id=model_id, api_key=api_key),
    tools=[ReasoningTools(add_instructions=True)],
    markdown=True,
    structured_outputs=True,
)

task = "How many 'r' are in the word 'supercalifragilisticexpialidocious'?"

console.rule("[bold green]Regular Agent[/bold green]")
regular_agent.print_response(task, stream=False)
console.rule("[bold yellow]Reasoning Agent[/bold yellow]")
reasoning_agent.print_response(task, stream=False, show_full_reasoning=True)