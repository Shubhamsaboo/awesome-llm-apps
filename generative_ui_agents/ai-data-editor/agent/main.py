import os
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from copilotkit import CopilotKitMiddleware, StateStreamingMiddleware, StateItem

from src.state import AgentState
from src.tools import query_database, propose_mutation, execute_mutation
from src.db import get_schema_context
from src.seed import seed_if_needed

load_dotenv()
seed_if_needed()

model = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-4o"),
    model_kwargs={"parallel_tool_calls": False},
)

schema_context = get_schema_context()

SYSTEM_PROMPT = f"""You are a data editor agent. You help users query and edit data in a SaaS accounts database.

## Database Schema
{schema_context}

## Your Capabilities

### Reading Data
When the user asks to see data, generate a SQL SELECT statement and call query_database.
- Use the schema above to write correct SQL
- Add appropriate WHERE, ORDER BY, GROUP BY clauses based on the request
- For aggregates (counts, sums, averages), use aggregate functions
- Results are automatically rendered in the canvas as the state updates

### Editing Data
When the user asks to change data:
1. First, call propose_mutation with the UPDATE statement, target table, row ID, and changes
2. Then IMMEDIATELY call confirm_mutation (a frontend tool) with the mutation_id and description — this shows the user an approve/reject dialog
3. If the user approves, call execute_mutation with the mutation_id
4. If the user rejects, acknowledge and do NOT execute
5. After execution, query the updated data to show the result

IMPORTANT: Always call confirm_mutation after propose_mutation. This is how the user approves writes. Do NOT ask them to type "confirm" — the confirm_mutation tool renders buttons they can click.

### Rules
- NEVER execute a write without user confirmation
- NEVER generate DELETE, DROP, ALTER, or TRUNCATE statements
- UPDATE statements MUST include a WHERE clause with a primary key
- Use parameterized queries (? placeholders) for all values
- If you're unsure about the schema or data, query first before proposing changes
"""

agent = create_agent(
    model=model,
    tools=[query_database, propose_mutation, execute_mutation],
    middleware=[
        CopilotKitMiddleware(),
        StateStreamingMiddleware(
            StateItem(state_key="query_result", tool="query_database", tool_argument="query_result"),
            StateItem(state_key="pending_mutation", tool="propose_mutation", tool_argument="pending_mutation"),
        ),
    ],
    state_schema=AgentState,
    system_prompt=SYSTEM_PROMPT,
)

graph = agent
