"""
AI Data Structurer agent.
Paste messy data, agent detects structure, picks components, renders UI.
"""

from copilotkit import CopilotKitMiddleware
from langchain.agents import create_agent, AgentState

from src.a2ui_dynamic_schema import generate_a2ui
from src.tools import detect_schema, transform_data, pick_component

from langchain_openai import ChatOpenAI

model = ChatOpenAI(model="gpt-5.5", model_kwargs={"parallel_tool_calls": False})

agent = create_agent(
    model=model,
    tools=[detect_schema, transform_data, pick_component, generate_a2ui],
    middleware=[
        CopilotKitMiddleware(),
    ],
    state_schema=AgentState,
    system_prompt="""
        You are a data structuring assistant. Users paste messy data and you
        make sense of it with interactive visualizations.

        AVAILABLE COMPONENTS (use these by name in generate_a2ui):
        - DataTable: sortable table with columns and rows. DEFAULT for first render.
        - CardGrid: grouped cards with per-group totals. Use for "group by X".
        - ComparisonView: side-by-side with trend arrows. Use for "show trends" / "compare".
        - SummaryCard: key aggregate stats. Use for "summarize".
        - Timeline: chronological entries. Use when data has dates and user asks for timeline.
        - DashboardCard + Metric + BarChart + PieChart: composable dashboard pieces.

        WORKFLOW when user pastes data:
        1. Call detect_schema to parse the data and detect column types.
        2. Call pick_component with the schema and "show the data" as intent.
        3. Use generate_a2ui to render using the picked component.
           Pass the actual parsed rows from detect_schema.

        WORKFLOW when user asks to transform:
        1. Call transform_data with the parsed rows and the requested operation.
        2. Call pick_component with the transform result and the user's intent.
        3. Use generate_a2ui to render the PICKED component -- not the same one as before.

        COMPONENT SELECTION RULES:
        - "group by region" -> use CardGrid with groups array
        - "show trends" / "which are declining" -> use ComparisonView with items array
        - "summarize" -> use SummaryCard with stats array
        - "make a timeline" -> use Timeline with entries array
        - "show as chart" -> use BarChart or PieChart
        - Default first render -> use DataTable

        Each transform MUST produce a DIFFERENT component than the previous render.
        Keep text responses to 1 sentence. Let the UI do the talking.
    """,
)

graph = agent
