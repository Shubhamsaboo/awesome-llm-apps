from agno.models.google import Gemini
from agno.models.openai import OpenAIChat
from agno.models.openrouter import OpenRouter

# model = Gemini(id="gemini-2.0-flash-001", temperature=0.1)
# model2 = OpenAIChat(id="gpt-4o", temperature=0.1)

model = OpenRouter(id="google/gemini-2.0-flash-001", temperature=0.3, max_tokens=8096)
model2 = OpenRouter(id="openai/gpt-4o", temperature=0.1)
model_zero = OpenRouter(
    id="google/gemini-2.0-flash-001", temperature=0.1, max_tokens=8096
)
