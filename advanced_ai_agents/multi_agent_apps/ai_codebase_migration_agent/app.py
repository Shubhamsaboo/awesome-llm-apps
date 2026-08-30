# Codebase Migration & Refactor Planner - LangGraph multi-agent application with Streamlit UI
#
# Graph flow:
#   START -> query_validator -> planner -> approval (HITL interrupt)
#        -> [Send() fan-out] -> refactor_worker xN -> aggregator -> END
#
# Run with: streamlit run app.py
# The graph itself is importable without Streamlit via build_migration_graph().

import base64
import io
import json
import logging
import math
import operator
import os
import random
import re
import time
import uuid
from typing import Annotated, List, Literal, Optional, TypedDict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, Send, interrupt
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

load_dotenv()


#############################
# LLM configuration
#############################

# Defaults target the OpenAI API. Any OpenAI-compatible endpoint works by setting
# LLM_BASE_URL plus MODEL_FAST / MODEL_PRO (e.g. DeepSeek, Groq, Together, Ollama).
DEFAULT_MODEL_FAST = "gpt-5-mini"  # validation, planning, per-file refactor workers
DEFAULT_MODEL_PRO = "gpt-5.5"  # final report synthesis + chart generation
LLM_TIMEOUT = 300  # seconds for each provider request


class _LLMProvider:
    """Lazy LLM chat models. Keys/models can be updated at runtime via reset()."""

    def __init__(self):
        self._cache = {}

    def _create(self, model: str):
        api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("LLM_BASE_URL")

        if not api_key:
            raise RuntimeError(
                "LLM API Key is not set. Set it in the .env file or in the app sidebar."
            )

        # Passing base_url=None lets the OpenAI client use its own default endpoint.
        return ChatOpenAI(
            model=model,
            openai_api_key=api_key,
            openai_api_base=base_url or None,
            timeout=LLM_TIMEOUT,
        )

    def flash(self):
        if "flash" not in self._cache:
            model = os.getenv("MODEL_FAST") or DEFAULT_MODEL_FAST
            self._cache["flash"] = self._create(model)
        return self._cache["flash"]

    def pro(self):
        if "pro" not in self._cache:
            model = os.getenv("MODEL_PRO") or DEFAULT_MODEL_PRO
            self._cache["pro"] = self._create(model)
        return self._cache["pro"]

    def reset(self):
        self._cache = {}


llm = _LLMProvider()


def reset_clients():
    """Re-read environment variables and rebuild LLM client cache."""
    llm.reset()


#############################
# Graph state
#############################


class MigrationTask(BaseModel):
    file_path: str = Field(
        description="Relative path of the target file to migrate (e.g. 'models/user.py', 'src/api.js')"
    )
    action: str = Field(
        description="Specific migration action (e.g., 'Update Pydantic v1 BaseModel & @validator to v2 Field & @field_validator')"
    )
    risk_level: Literal["Low", "Medium", "High", "Critical"] = Field(
        description="Estimated risk level of refactoring this file"
    )
    risk_reasoning: str = Field(
        description="Detailed explanation of why this risk level was assigned"
    )
    code_context: Optional[str] = Field(
        default=None,
        description="Optional existing code snippet or context for the file",
    )


class MigrationState(TypedDict):
    repo_target: str
    migration_goal: str
    strategy: str
    plan: List[dict]
    plan_approved: bool
    user_feedback: Optional[str]
    status: Literal[
        "planning", "awaiting_approval", "refactoring", "completed", "error"
    ]
    results: Annotated[List[str], operator.add]
    final_answer: Optional[str]
    error: Optional[str]


#############################
# Visualization Tool
#############################


MAX_CHART_POINTS = 50


@tool
def generate_matplotlib_chart(
    chart_type: Literal["bar", "line"],
    labels: list[str],
    values: list[float],
    title: str = "Migration Risk Distribution",
    y_label: str = "Files",
) -> str:
    """Render a chart from validated data selected by the model.

    This tool accepts data only. It never executes model-generated Python,
    imports, or callables, so model output cannot access the host filesystem.
    """
    if chart_type not in {"bar", "line"}:
        return "Error rendering chart: chart_type must be 'bar' or 'line'."
    if not labels or len(labels) > MAX_CHART_POINTS:
        return f"Error rendering chart: provide 1-{MAX_CHART_POINTS} labels."
    if len(labels) != len(values):
        return "Error rendering chart: labels and values must have the same length."
    if any(
        not isinstance(label, str) or not label.strip() or len(label) > 120
        for label in labels
    ):
        return "Error rendering chart: labels must be non-empty strings of at most 120 characters."
    if any(
        not isinstance(value, (int, float)) or not math.isfinite(value)
        for value in values
    ):
        return "Error rendering chart: values must be finite numbers."
    if not isinstance(title, str) or not title.strip() or len(title) > 120:
        return "Error rendering chart: title must be a non-empty string of at most 120 characters."
    if not isinstance(y_label, str) or not y_label.strip() or len(y_label) > 80:
        return "Error rendering chart: y_label must be a non-empty string of at most 80 characters."

    try:
        fig, axis = plt.subplots(figsize=(10, 6))
        if chart_type == "bar":
            axis.bar(labels, values)
        else:
            axis.plot(labels, values, marker="o")
        axis.set_title(title)
        axis.set_ylabel(y_label)
        axis.grid(axis="y", alpha=0.3)
        fig.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", dpi=150)
        plt.close(fig)
        buf.seek(0)
        b64 = base64.b64encode(buf.read()).decode("ascii")
        return f"![Generated Chart](data:image/png;base64,{b64})"
    except Exception as exc:
        plt.close("all")
        return f"Error rendering chart: {exc}"


#############################
# Agents & Nodes
#############################


# --- Query Validator ---

VALIDATOR_SYSTEM_PROMPT = """You are an input validation assistant for a Codebase Migration & Refactor Planner.
Your task is to analyze the user's input repository target and migration goal to ensure they provide a valid, safe, and substantive migration request.

Criteria for a VALID migration query:
- A repository path or URL is provided (e.g. "github.com/my-org/my-project", "./src/my_app", "https://github.com/fastapi/fastapi").
- A clear migration goal is specified (e.g. "Migrate Pydantic v1 to v2", "Upgrade Flask 2 to 3", "Convert JavaScript files to TypeScript", "Refactor synchronous database calls to async SQLAlchemy 2.0").

Criteria for an INVALID query:
- Missing repository target or missing migration goal.
- Conversational filler or greeting without any migration details (e.g., "hi", "help me code").
- Empty, gibberish, or generic commands (e.g., "fix my repo", "do code").
- Malicious, destructive, unsafe, or illegal requests (e.g., "write malware", "delete root files", "bypass authentication security checks"). Mark is_valid as false and set error_message to "Query contains inappropriate or unsafe content."

You MUST respond in JSON matching this schema:
{
  "is_valid": true or false,
  "error_message": "your error message here, or null if is_valid is true"
}
"""


class QueryValidation(BaseModel):
    is_valid: bool = Field(
        description="True if both repo target and migration goal are provided and safe. False otherwise."
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Friendly explanation if is_valid is False.",
    )


def query_validator(state: MigrationState) -> dict:
    repo = state.get("repo_target", "").strip()
    goal = state.get("migration_goal", "").strip()
    logger.info(f"Validating migration request - Repo: '{repo}', Goal: '{goal}'")

    if not repo or not goal:
        logger.warning("Query validation failed: Missing repo or migration goal.")
        return {
            "status": "error",
            "error": "Please provide both a target repository URL/path AND a clear migration goal.",
        }

    try:
        validator_llm = llm.flash().with_structured_output(
            QueryValidation, method="json_mode"
        )
        messages = [
            SystemMessage(content=VALIDATOR_SYSTEM_PROMPT),
            HumanMessage(content=f"Repository Target: {repo}\nMigration Goal: {goal}"),
        ]
        validation = validator_llm.invoke(messages)

        if not validation.is_valid:
            error_msg = (
                validation.error_message
                or "Invalid migration request. Please provide a valid repo target and clear migration goal."
            )
            logger.warning(f"Query validation failed (LLM): {error_msg}")
            return {"status": "error", "error": error_msg}

    except Exception as e:
        error_msg = str(e).lower()
        logger.error(f"Error during query validation LLM call: {e}")
        if any(
            kw in error_msg
            for kw in [
                "api key",
                "authentication",
                "unauthorized",
                "401",
                "403",
                "invalid key",
                "missing credentials",
                "not set",
            ]
        ):
            return {
                "status": "error",
                "error": "API key is missing or invalid. Open the sidebar to configure your API keys.",
            }

    logger.info("Query validation successful.")
    return {}


# --- Planner Node ---

PLANNER_SYSTEM_PROMPT = """You are a Lead Software Architect and Code Refactoring Planner.

Given a target repository and a migration goal, construct a file-by-file migration plan.

Output requirements:
1. Strategy (strategy)
- Executive summary of the architectural strategy (1-3 concise sentences).
- Explain the key migration pattern, safety approach, and breaking change risks.

2. Tasks (tasks)
Generate between 3 and 6 file migration tasks.

For each task:
- file_path: clean relative file path (e.g. `src/models/user.py`, `api/routes.py`, `config/settings.py`).
- action: specific refactoring instruction (e.g., `Migrate Pydantic v1 BaseModel & validator to v2 Field & field_validator`).
- risk_level: assign one of ["Low", "Medium", "High", "Critical"].
- risk_reasoning: 1-2 sentence explanation of why this risk rating was assigned (e.g., dependency on core database models, external API contract changes, stateful state logic).

Revision rules:
- If user feedback is provided, adjust the strategy or file task list accordingly (e.g. add/remove files, change risk ratings).
- Preserve unaffected tasks accurately.

Return ONLY valid JSON matching this schema:
{
  "strategy": "string",
  "tasks": [
    {
      "file_path": "string",
      "action": "string",
      "risk_level": "Low" | "Medium" | "High" | "Critical",
      "risk_reasoning": "string"
    }
  ]
}
"""


class MigrationPlanResponse(BaseModel):
    strategy: str = Field(description="High-level migration strategy summary")
    tasks: List[MigrationTask] = Field(
        description="List of file migration tasks with risk assessments",
        min_length=1,
        max_length=8,
    )


def planner_node(state: MigrationState) -> dict:
    planner_llm = llm.flash().with_structured_output(
        MigrationPlanResponse, method="json_mode"
    )

    user_content = (
        f"Repository: {state['repo_target']}\n"
        f"Migration Goal: {state['migration_goal']}\n"
    )
    if state.get("user_feedback"):
        user_content += (
            f"\nUser feedback on previous plan: {state['user_feedback']}\n"
            f"Previous Strategy: {state.get('strategy', '')}\n"
            f"Previous Plan: {json.dumps(state.get('plan', []), indent=2)}"
        )

    messages = [
        SystemMessage(content=PLANNER_SYSTEM_PROMPT),
        HumanMessage(content=user_content),
    ]

    try:
        result = planner_llm.invoke(messages)
        tasks_as_dicts = [task.model_dump() for task in result.tasks]
        logger.info(
            f"Planner generated {len(tasks_as_dicts)} file tasks for migration goal: {state['migration_goal']}"
        )
        return {
            "strategy": result.strategy,
            "plan": tasks_as_dicts,
            "status": "awaiting_approval",
        }
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error generating migration plan: {e}", exc_info=True)
        return {
            "status": "error",
            "error": f"Failed to generate migration plan: {error_msg}",
        }


# --- Plan Approval Node (HITL Interrupt) ---

APPROVAL_SYSTEM_PROMPT = """You are a migration plan approval classifier.
Analyze the user's feedback to determine if they approved the codebase migration plan, or if they are requesting modifications.

Classification Rules:
- If the user explicitly approves (e.g. "looks good", "approve", "proceed", "go ahead", "run", "yes", "execute", "ok"), set 'plan_approved' to true.
- If the user requests changes, additions, deletions, risk level updates, or revisions (e.g. "remove file X", "increase risk on Y", "add step Z"), set 'plan_approved' to false.
- Respond strictly in JSON format matching the schema."""


class PlanApprovalState(BaseModel):
    plan_approved: bool = Field(
        description="True if user approved the migration plan, False if modifications requested."
    )


def plan_approval(state: MigrationState) -> dict:
    user_response = interrupt("Waiting for migration plan approval/feedback")

    feedback = (
        user_response.get("message", "")
        if isinstance(user_response, dict)
        else str(user_response)
    )

    approval_llm = llm.flash().with_structured_output(
        PlanApprovalState, method="json_mode"
    )

    user_content = (
        f"User feedback: {feedback}\n"
        f"Proposed Strategy: {state.get('strategy', '')}\n"
        f"Proposed Plan: {json.dumps(state.get('plan', []), indent=2)}"
    )

    messages = [
        SystemMessage(content=APPROVAL_SYSTEM_PROMPT),
        HumanMessage(content=user_content),
    ]
    result = approval_llm.invoke(messages)

    logger.info(f"Plan approval status: {result.plan_approved}, Feedback: '{feedback}'")

    status = "refactoring" if result.plan_approved else "planning"
    return {
        "plan_approved": result.plan_approved,
        "user_feedback": feedback,
        "status": status,
    }


# --- Supervisor: Fan-out Workers via Send() ---


def dispatch_workers(state: MigrationState) -> List[Send]:
    """Fan-out to one refactor worker per file in the approved migration plan."""
    return [
        Send("refactor_worker", {**state, "file_task": task})
        for task in state["plan"][:8]
    ]


# --- Refactor Worker Node ---

REFACTOR_WORKER_PROMPT = """You are a Senior Staff Refactoring Engineer specializing in automated, production-grade code migrations.

Your task is to refactor a single file based on the migration goal and assigned action.

File Task Details:
- File Path: {file_path}
- Migration Action: {action}
- Risk Level: {risk_level}
- Risk Reasoning: {risk_reasoning}
- Migration Goal: {migration_goal}

Instructions:
1. Provide a clear Markdown output section for this file.
2. Include a **Refactoring Breakdown** detailing specific line changes, imports updated, and API contract modifications.
3. Produce a clean **Unified Diff or Before/After Code Block** illustrating the exact refactored code for `{file_path}`.
4. Highlight **Breaking Changes & Risk Mitigation** steps to ensure safety.
5. Provide **Recommended Unit Tests** to verify the migration.

Keep the formatting clean, professional, and directly actionable."""


def refactor_worker_node(state: MigrationState) -> dict:
    file_task = state.get("file_task", {})
    file_path = file_task.get("file_path", "unknown_file")
    logger.info(f"Refactor worker starting for file: {file_path}")

    # Stagger worker execution to avoid API rate limit spikes
    stagger_time = random.uniform(0.3, 1.5)
    time.sleep(stagger_time)

    prompt_text = REFACTOR_WORKER_PROMPT.format(
        file_path=file_path,
        action=file_task.get("action", ""),
        risk_level=file_task.get("risk_level", "Medium"),
        risk_reasoning=file_task.get("risk_reasoning", ""),
        migration_goal=state.get("migration_goal", ""),
    )

    messages = [
        SystemMessage(
            content="You are an expert code refactoring worker producing clean diffs and migration code."
        ),
        HumanMessage(content=prompt_text),
    ]

    try:
        response = llm.flash().invoke(messages)
        diff_output = (
            f"### 📄 File: `{file_path}`\n"
            f"**Risk Level:** `{file_task.get('risk_level', 'Medium')}` | **Action:** {file_task.get('action', '')}\n\n"
            f"{response.content.strip()}\n\n"
            f"---"
        )
        logger.info(f"Refactor worker finished for {file_path}")
        return {"results": [diff_output]}
    except Exception as e:
        logger.error(
            f"Error in refactor worker node for {file_path}: {e}", exc_info=True
        )
        return {
            "results": [
                f"### 📄 File: `{file_path}`\n"
                f"❌ **Refactoring Failed**: {str(e)}\n\n---"
            ]
        }


# --- Aggregator Node ---

AGGREGATOR_SYSTEM_PROMPT = """You are a Principal Software Architect and Code Quality Lead.

Your task is to synthesize all individual file refactoring diffs into a comprehensive, publication-ready **Codebase Migration Report & Risk Guide** in markdown format.

Structure requirements:
1. **Title**: Clean markdown title (e.g. `# Codebase Migration Report: <Goal>`).
2. **Executive Migration Strategy**: Overview of the refactoring methodology and architectural impact.
3. **Migration Risk Summary & Impact Matrix**: Markdown table summarizing all files, their risk level (Low/Medium/High/Critical), and primary changes.
4. **Matplotlib Risk Visualization Tool**:
   - You have access to `generate_matplotlib_chart`.
   - Call this tool to generate 1 to 2 visual charts (e.g. Risk Level Distribution bar chart, Migration Progress / Complexity by File).
   - The tool accepts only `chart_type` (`bar` or `line`), string `labels`, numeric `values`, and optional title/y-axis label. Never provide Python source code.
   - Embed the exact return marker (e.g. `<!--CHART_1-->`) in the report where the chart belongs.
5. **Consolidated File Refactoring & Diffs**: Include all individual file diffs and refactored code clearly grouped by module/file.
6. **Post-Migration Verification & Rollback Plan**: Checklist for automated tests, CI validation, and emergency rollback.

Keep the style formal, highly technical, visually clean, and thorough."""


MAX_AGGREGATOR_ROUNDS = 6


def aggregator_node(state: MigrationState) -> dict:
    combined_results = "\n\n".join(state.get("results", []))

    messages = [
        SystemMessage(content=AGGREGATOR_SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"Target Repository: {state['repo_target']}\n"
                f"Migration Goal: {state['migration_goal']}\n"
                f"Overall Strategy: {state.get('strategy', '')}\n\n"
                f"Individual File Diffs & Refactoring Output:\n{combined_results}\n\n"
                "Synthesize the final Codebase Migration Report & Risk Guide in Markdown. "
                "Call `generate_matplotlib_chart` with chart data to render 1-2 charts showing risk distribution or migration effort across files."
            )
        ),
    ]

    try:
        llm_with_tools = llm.pro().bind_tools([generate_matplotlib_chart])
        messages_history = list(messages)
        chart_links = []

        for round_num in range(1, MAX_AGGREGATOR_ROUNDS + 1):
            try:
                response = llm_with_tools.invoke(messages_history)
            except TimeoutError:
                logger.error(f"Aggregator LLM request timed out on round {round_num}")
                break

            messages_history.append(response)

            if not response.tool_calls or round_num == MAX_AGGREGATOR_ROUNDS:
                break

            for tool_call in response.tool_calls:
                if tool_call["name"] == "generate_matplotlib_chart":
                    result = generate_matplotlib_chart.invoke(tool_call["args"])
                    if result.startswith("Error rendering chart"):
                        messages_history.append(
                            ToolMessage(
                                content=result[:300],
                                tool_call_id=tool_call["id"],
                                name=tool_call["name"],
                            )
                        )
                    else:
                        chart_links.append(result)
                        marker = f"<!--CHART_{len(chart_links)}-->"
                        messages_history.append(
                            ToolMessage(
                                content=marker,
                                tool_call_id=tool_call["id"],
                                name=tool_call["name"],
                            )
                        )
                else:
                    messages_history.append(
                        ToolMessage(
                            content=f"Unknown tool {tool_call['name']}",
                            tool_call_id=tool_call["id"],
                        )
                    )

        # The model emits the report as prose across the rounds it is not calling a
        # tool in, so concatenate every assistant turn. Non-str content (tool-call-only
        # turns, or providers that return content blocks) contributes nothing.
        final_content = "".join(
            msg.content
            for msg in messages_history
            if isinstance(msg, AIMessage) and isinstance(msg.content, str)
        )

        for i, link in enumerate(chart_links, start=1):
            final_content = final_content.replace(f"<!--CHART_{i}-->", link)

        # A timeout on the first round leaves no assistant turns at all. Without this
        # the node would report status="completed" with an empty report.
        if not final_content.strip():
            return {
                "status": "error",
                "error": (
                    "The report synthesis step returned no content (the model timed out "
                    "or produced only tool calls). Re-run the approval step to try again."
                ),
            }

    except Exception as e:
        logger.error(f"Error in aggregator node: {e}", exc_info=True)
        return {"status": "error", "error": f"Report synthesis failed: {str(e)}"}

    return {"final_answer": final_content, "status": "completed"}


#############################
# Graph builder
#############################


def build_migration_graph():
    """Build and compile the codebase migration graph (pure LangGraph logic)."""
    builder = StateGraph(MigrationState)

    builder.add_node("query_validator", query_validator)
    builder.add_node("planner", planner_node)
    builder.add_node("approval", plan_approval)
    builder.add_node("refactor_worker", refactor_worker_node)
    builder.add_node("aggregator", aggregator_node)

    def route_after_approval(state: MigrationState):
        # An approved-but-empty plan would fan out to zero workers and strand the
        # graph before the aggregator, so send it back to the planner instead.
        if state.get("plan_approved") and state.get("plan"):
            return dispatch_workers(state)
        return "planner"

    builder.add_edge(START, "query_validator")
    builder.add_conditional_edges(
        "query_validator",
        lambda state: END if state.get("error") else "planner",
        ["planner", END],
    )
    builder.add_conditional_edges(
        "planner",
        lambda state: END if state.get("error") else "approval",
        ["approval", END],
    )
    builder.add_conditional_edges(
        "approval", route_after_approval, ["refactor_worker", "planner"]
    )
    builder.add_edge("refactor_worker", "aggregator")
    builder.add_edge("aggregator", END)

    return builder.compile(checkpointer=MemorySaver())


_graph_key = None
_graph = None


def get_graph():
    global _graph_key, _graph
    llm_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or ""
    base_url = os.getenv("LLM_BASE_URL") or ""
    model_fast = os.getenv("MODEL_FAST") or DEFAULT_MODEL_FAST
    model_pro = os.getenv("MODEL_PRO") or DEFAULT_MODEL_PRO

    key = (llm_key, base_url, model_fast, model_pro)
    if _graph is None or _graph_key != key:
        _graph_key = key
        _graph = build_migration_graph()
    return _graph


def apply_api_keys(api_key: str, base_url: str, model_fast: str, model_pro: str):
    """Update runtime configuration and reset client cache."""
    if api_key:
        os.environ["LLM_API_KEY"] = api_key
    if base_url:
        os.environ["LLM_BASE_URL"] = base_url
    if model_fast:
        os.environ["MODEL_FAST"] = model_fast
    if model_pro:
        os.environ["MODEL_PRO"] = model_pro
    reset_clients()


#############################
# Streamlit UI
#############################

_CHART_RE = re.compile(r"!\[([^\]]*)\]\((data:image/png;base64,[A-Za-z0-9+/=]+)\)")


def _render_report_with_charts(report: str):
    """Render markdown report, displaying base64 matplotlib charts via st.image."""
    import streamlit as st

    parts = _CHART_RE.split(report)
    for i in range(1, len(parts), 3):
        alt, data_uri = parts[i], parts[i + 1]
        st.markdown(parts[i - 1])
        try:
            img_bytes = base64.b64decode(data_uri.split(",", 1)[1])
            st.image(io.BytesIO(img_bytes), caption=alt or "Migration Chart")
        except Exception:
            st.markdown(f"![{alt}]({data_uri})")
    if parts:
        st.markdown(parts[-1])


def render_ui():
    import streamlit as st

    st.set_page_config(
        page_title="Codebase Migration Planner", page_icon="⚡", layout="wide"
    )

    # Session state initialization
    for key in (
        "thread_id",
        "strategy",
        "plan",
        "status",
        "error",
        "final_answer",
        "refactor_log",
    ):
        st.session_state.setdefault(key, None)

    # ------------------------- Sidebar -------------------------
    with st.sidebar:
        st.title("⚙️ LLM Settings")

        api_key = st.text_input(
            "API Key",
            type="password",
            value=os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or "",
            help="Your OpenAI API key (or the key for whichever compatible endpoint you point at below).",
        )
        model_fast = st.text_input(
            "Fast Model",
            value=os.getenv("MODEL_FAST") or DEFAULT_MODEL_FAST,
            help=f"Validation, planning, and per-file refactor workers (default: {DEFAULT_MODEL_FAST}).",
        )
        model_pro = st.text_input(
            "Pro Model",
            value=os.getenv("MODEL_PRO") or DEFAULT_MODEL_PRO,
            help=f"Final report synthesis and chart generation (default: {DEFAULT_MODEL_PRO}).",
        )
        base_url = st.text_input(
            "Base URL (optional)",
            value=os.getenv("LLM_BASE_URL") or "",
            placeholder="https://api.openai.com/v1",
            help="Leave blank for OpenAI. Set this to use any OpenAI-compatible endpoint.",
        )

        if st.button("Save Settings", type="primary", use_container_width=True):
            apply_api_keys(api_key, base_url, model_fast, model_pro)
            st.success("Settings saved.")
            st.rerun()

        st.divider()
        if st.button("🆕 New Migration Plan", use_container_width=True):
            for key in (
                "thread_id",
                "strategy",
                "plan",
                "status",
                "error",
                "final_answer",
                "refactor_log",
            ):
                st.session_state[key] = None
            st.rerun()

        st.caption(
            "Credentials can also be placed in a `.env` file next to `app.py` "
            "(see `.env.example`)."
        )

    # ------------------------- Main UI -------------------------
    st.title("⚡ Codebase Migration & Refactor Planner")
    st.caption(
        "LangGraph HITL Multi-Agent System: Plan file-by-file migrations, review & approve safety risks, "
        "fan-out parallel refactoring workers, and aggregate complete diffs & risk charts."
    )

    status = st.session_state.status

    # ----- Step 1: Input -----
    if not status or status == "error":
        repo_target = st.text_input(
            "Target Repository Path or URL",
            placeholder="e.g. github.com/my-org/my-project or ./src/my_app",
        )
        migration_goal = st.text_area(
            "Migration Goal & Scope",
            placeholder="e.g. Migrate Pydantic v1 BaseModel to v2 Field & @field_validator across all services",
            height=90,
        )

        if st.button("🚀 Plan Migration", type="primary"):
            if not repo_target.strip() or not migration_goal.strip():
                st.warning("Please enter both a repository target and migration goal.")
                return
            graph = get_graph()
            thread_id = str(uuid.uuid4())
            st.session_state.thread_id = thread_id
            config = {"configurable": {"thread_id": thread_id}}
            with st.spinner("Analyzing repository & planning migration strategy..."):
                try:
                    for _ in graph.stream(
                        {
                            "repo_target": repo_target.strip(),
                            "migration_goal": migration_goal.strip(),
                        },
                        config=config,
                    ):
                        pass
                except Exception as e:
                    st.error(f"Failed to start migration planning: {str(e)}")
                    return

            state = graph.get_state(config)
            st.session_state.strategy = state.values.get("strategy")
            st.session_state.plan = state.values.get("plan")
            st.session_state.status = state.values.get("status")
            st.session_state.error = state.values.get("error")
            st.rerun()

    # ----- Step 2: HITL Plan Review & Approval -----
    if status == "awaiting_approval" and st.session_state.plan:
        st.subheader("📋 Proposed Migration Strategy & File Plan")
        if st.session_state.strategy:
            st.info(f"**Strategy Overview:** {st.session_state.strategy}")

        st.markdown("### File-by-File Migration Tasks & Risk Matrix")
        risk_badges = {
            "Critical": "🔴 **Critical**",
            "High": "🟠 **High**",
            "Medium": "🟡 **Medium**",
            "Low": "🟢 **Low**",
        }

        for i, task in enumerate(st.session_state.plan, start=1):
            file_path = task.get("file_path", "File")
            action = task.get("action", "")
            risk = task.get("risk_level", "Medium")
            reasoning = task.get("risk_reasoning", "")

            badge = risk_badges.get(risk, risk)
            st.markdown(
                f"**{i}. `{file_path}`** — Risk: {badge}\n"
                f"- **Action:** {action}\n"
                f"- **Risk Rationale:** {reasoning}"
            )

        st.divider()
        st.subheader("🛡️ Safety & Approval Gate (HITL)")
        st.caption(
            "Review the file plan carefully. Approve to execute code refactoring workers, "
            "or type revision instructions (e.g. 'mark models/user.py as Critical risk', 'skip config/settings.py')."
        )
        feedback = st.text_area(
            "Revision instructions (optional)",
            placeholder="Approve or describe requested adjustments...",
        )
        col1, col2 = st.columns(2)
        with col1:
            approve_clicked = st.button(
                "✅ Approve & Execute Migration Plan", type="primary"
            )
        with col2:
            revise_clicked = st.button("🔄 Revise Migration Plan")

        if approve_clicked or revise_clicked:
            message = "Approved. Proceed with codebase migration."
            if revise_clicked:
                if not feedback.strip():
                    st.warning("Please enter revision feedback before clicking Revise.")
                    return
                message = feedback.strip()

            graph = get_graph()
            config = {"configurable": {"thread_id": st.session_state.thread_id}}
            log = []
            with st.status(
                "🛠️ Parallel refactoring workers executing...", expanded=True
            ) as box:
                try:
                    for event in graph.stream(
                        Command(resume={"message": message}), config=config
                    ):
                        for node_name, payload in event.items():
                            if node_name == "refactor_worker":
                                results = payload.get("results") or []
                                snippet = str(results[0])[:80] if results else "done"
                                log.append(f"**Refactor Worker** → {snippet}")
                                box.write(f"✅ Refactor worker completed: {snippet}")
                            elif node_name == "aggregator":
                                box.write(
                                    "🧠 Aggregator synthesizing migration report & charts..."
                                )
                except Exception as e:
                    box.write(f"❌ Error: {str(e)}")
                    st.session_state.status = "error"
                    st.session_state.error = str(e)
                    st.rerun()

            state = graph.get_state(config)
            st.session_state.refactor_log = log
            st.session_state.final_answer = state.values.get("final_answer")
            st.session_state.status = state.values.get("status")
            st.session_state.error = state.values.get("error")
            st.rerun()

    # ----- Errors -----
    if st.session_state.status == "error" and st.session_state.error:
        # Render the error and clear it without an immediate rerun; calling
        # st.rerun() here would discard the frame before the user ever sees it.
        st.error(st.session_state.error)
        st.session_state.status = None
        st.session_state.error = None

    # ----- Step 3: Final Report & Diffs -----
    if st.session_state.status == "completed" and st.session_state.final_answer:
        st.subheader("📄 Codebase Migration Report & Refactoring Guide")

        st.download_button(
            "⬇️ Download Migration Report (.md)",
            data=st.session_state.final_answer,
            file_name=f"migration_plan_{st.session_state.thread_id}.md",
            mime="text/markdown",
        )

        _render_report_with_charts(st.session_state.final_answer)

        if st.session_state.refactor_log:
            with st.expander("Worker execution log"):
                for entry in st.session_state.refactor_log:
                    st.markdown(entry)

    if not status and not st.session_state.thread_id:
        st.info(
            "Enter a target repository and migration goal, then click **Plan Migration**. "
            "The multi-agent system will generate a file-by-file strategy with risk levels, "
            "pause for your HITL approval, fan out parallel refactoring workers, and compile full diffs & charts."
        )


if __name__ == "__main__":
    render_ui()
