from agno.agent import Agent
from agno.models.ollama import Ollama
from agno.playground import Playground, serve_playground_app

reasoning_agent = Agent(name="Reasoning Agent", model=Ollama(id="qwq:32b"), markdown=True)

# UI for Reasoning agent
app = Playground(agents=[reasoning_agent]).get_app()

# Run the Playground app
if __name__ == "__main__":
    serve_playground_app("local_ai_reasoning_agent:app", reload=True)