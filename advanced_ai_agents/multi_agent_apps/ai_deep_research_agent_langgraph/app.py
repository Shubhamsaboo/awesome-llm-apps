# DeepResearch Agent - LangGraph multi-agent research assistant with a Streamlit UI
#
# Graph flow:
#   START -> query_validator -> planner -> approval (HITL interrupt)
#        -> [Send() fan-out] -> researcher xN -> aggregator -> END
#
# Run with: streamlit run app.py
# The graph itself is importable without Streamlit via build_research_graph().

import base64
import concurrent.futures
import io
import json
import logging
import operator
import os
import random
import re
import time
import uuid
import warnings
from typing import Annotated, List, Literal, Optional, TypedDict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, Send, interrupt
from pydantic import BaseModel, Field
from tavily import TavilyClient

logger = logging.getLogger(__name__)

load_dotenv()


#############################
# LLM configuration
#############################


class _LLMProvider:
    """Lazy LLM chat models. Keys/models can be updated at runtime via reset()."""

    def __init__(self):
        self._cache = {}

    def _create(self, model: str):
        api_key = (
            os.getenv("LLM_API_KEY")
            or os.getenv("DEEPSEEK_API_KEY")
            or os.getenv("OPENAI_API_KEY")
        )
        if not api_key:
            raise RuntimeError(
                "LLM API Key is not set. Set it in the .env file or in the app sidebar."
            )
        base_url = (
            os.getenv("LLM_BASE_URL")
            or os.getenv("DEEPSEEK_BASE_URL")
            or "https://api.deepseek.com"
        )
        return ChatOpenAI(
            model=model,
            openai_api_key=api_key,
            openai_api_base=base_url,
        )

    def flash(self):
        if "flash" not in self._cache:
            model = os.getenv("MODEL_FAST") or "deepseek-v4-flash"
            self._cache["flash"] = self._create(model)
        return self._cache["flash"]

    def pro(self):
        if "pro" not in self._cache:
            model = os.getenv("MODEL_PRO") or "deepseek-v4-pro"
            self._cache["pro"] = self._create(model)
        return self._cache["pro"]

    def reset(self):
        self._cache = {}


llm = _LLMProvider()

# Tavily client is created lazily so importing this module never requires keys.
_tavily = None


def _get_tavily() -> TavilyClient:
    global _tavily
    if _tavily is None:
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise RuntimeError(
                "TAVILY_API_KEY is not set. Set it in the .env file or in the app sidebar."
            )
        _tavily = TavilyClient(api_key=api_key)
    return _tavily


def reset_clients():
    """Re-read environment variables and rebuild LLM/Tavily clients."""
    llm.reset()
    global _tavily
    _tavily = None


#############################
# Graph state
#############################


class ResearchState(TypedDict):
    query: str
    ps: str
    plan: List[str]
    plan_approved: bool
    user_feedback: Optional[str]
    status: Literal[
        "planning", "awaiting_approval", "researching", "reviewing", "completed", "error"
    ]
    results: Annotated[List[str], operator.add]
    final_answer: Optional[str]
    citations: Annotated[List[str], operator.add]
    error: Optional[str]
    search_topic: List[Literal["all", "news", "academic", "finance", "patent"]]


#############################
# Tools
#############################


@tool
def search_web(
    query: str,
    search_topic: Optional[List[str]] = None,
    time_range: Optional[Literal["day", "month", "week", "year"]] = None,
) -> str:
    """Use Tavily search to search the web for the given query."""
    if search_topic:
        query += f" Use sources: {', '.join(search_topic)}"
    try:
        response = _get_tavily().search(
            time_range=time_range,
            query=query,
            max_results=4,
            include_images=False,
            include_raw_content=False,
            search_depth="advanced",
        )
        return str(response)
    except Exception as e:
        return f"Error using Tavily search: {str(e)}"


class _NoShowPyplot:
    """Delegate to pyplot, but neutralize plt.show() for headless rendering."""

    def __getattr__(self, name):
        return getattr(plt, name)

    def show(self, *args, **kwargs):
        return None


CHART_CODE_TIMEOUT = 30  # seconds allowed for LLM-generated chart code


def _render_chart_png(python_code: str) -> str:
    """Execute LLM-written chart code and return the base64 PNG payload."""
    exec_globals = {
        "plt": _NoShowPyplot(),
        "matplotlib": matplotlib,
        "__builtins__": __builtins__,
    }
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        exec(python_code, exec_globals, {})

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", dpi=150)
    plt.close("all")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("ascii")


@tool
def generate_matplotlib_chart(python_code: str) -> str:
    """Execute Python code containing matplotlib instructions to generate a chart.
    The code should plot data using standard matplotlib.pyplot (plt) functions.
    Do NOT call plt.show() - the execution wrapper will automatically save the figure.
    Always define clean labels, title, and grid/legend where appropriate.
    Returns:
        A markdown image link containing an embedded base64 PNG data URI of the chart
        (e.g. ![Generated Chart](data:image/png;base64,...)) which you MUST insert
        into the appropriate section in the final markdown report.
    """
    plt.clf()
    plt.close("all")
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(_render_chart_png, python_code)
            b64 = future.result(timeout=CHART_CODE_TIMEOUT)
        return f"![Generated Chart](data:image/png;base64,{b64})"
    except concurrent.futures.TimeoutError:
        plt.clf()
        plt.close("all")
        logger.error(f"Chart code timed out after {CHART_CODE_TIMEOUT}s")
        return f"Error executing matplotlib code: timed out after {CHART_CODE_TIMEOUT}s"
    except Exception as e:
        plt.clf()
        plt.close("all")
        return f"Error executing matplotlib code: {str(e)}"


#############################
# Agents
#############################


# --- Query Validator ---

VALIDATOR_SYSTEM_PROMPT = """You are an input validation assistant for a specialized Research Bot.
Your task is to analyze the user's input query and determine if it is a valid, substantive, and safe research topic.

Criteria for a VALID research query:
- It asks to research, explain, analyze, or gather info on a specific topic (e.g., "Recent breakthroughs in Quantum Computing in 2026", "Impact of microplastics on marine life").
- Even if it starts with polite greetings or conversational filler (e.g., "Hello, can you please research...", "Hi, tell me about..."), it is VALID as long as it contains a specific subject of research.

Criteria for an INVALID query:
- It is just conversational greeting/filler (e.g., "hello", "hi there", "greetings").
- It is a general query about you or the bot (e.g., "who are you", "what is your name", "what can you do").
- It is a generic command without any topic (e.g., "do some research for me", "search something", "please start").
- It is empty, gibberish, or completely lacks any researchable subject.
- It contains inappropriate, harmful, unsafe, illegal, sensitive, or restricted content (e.g., self-harm, weapon creation, illegal drugs, cyberattacks, hate speech, explicit content). In this case, mark is_valid as false and set error_message to "Query contains inappropriate or restricted content."

You MUST respond in JSON matching this schema:
{{
  "is_valid": true or false,
  "error_message": "your error message here, or null if is_valid is true"
}}
"""


class QueryValidation(BaseModel):
    is_valid: bool = Field(
        description="True if the input query contains a specific research topic and is safe/appropriate to process. False if it is a greeting, chatbot meta-question, generic conversational filler, or inappropriate/unsafe/restricted content."
    )
    error_message: Optional[str] = Field(
        default=None,
        description="If is_valid is False, provide a friendly error message explaining why (e.g. 'Query contains inappropriate or restricted content.' for unsafe queries) and ask the user to provide a specific research topic. Otherwise, leave empty.",
    )


def query_validator(state: ResearchState) -> dict:
    query = state.get("query", "").strip()
    logger.info(f"Validating query: '{query}'")

    if not query:
        logger.warning("Query validation failed: Empty query.")
        return {"status": "error", "error": "Please provide a specific research topic."}

    words = query.split()
    if len(words) < 4:
        logger.warning(f"Query validation failed: Query too short ({len(words)} words).")
        return {
            "status": "error",
            "error": "Not a valid research query. Please provide a specific research topic.",
        }

    try:
        validator_llm = llm.flash().with_structured_output(
            QueryValidation, method="json_mode"
        )
        prompt = ChatPromptTemplate(
            [
                ("system", VALIDATOR_SYSTEM_PROMPT),
                ("user", f"Input Query: {query}"),
            ]
        )
        messages = prompt.format_messages()
        validation = validator_llm.invoke(messages)

        if not validation.is_valid:
            error_msg = validation.error_message or "Not a valid research query. Please provide a specific research topic."
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
        words = query.split()
        if len(words) < 5:
            logger.warning(
                f"Query validation failed (Fallback check): Query under 5 words ({len(words)} words)."
            )
            return {
                "status": "error",
                "error": "Not a valid research query. Please provide a specific research topic.",
            }

    logger.info("Query validation successful.")
    return {}


# --- Planner ---

PLANNER_SYSTEM_PROMPT = """You are a strategic research planner.

Given a research query, create a structured research plan.

Output:
1. Problem Statement (ps)
- Explain the core research gap, uncertainty, limitation, or challenge.
- Describe the difference between current understanding and desired understanding.
- Do not propose solutions.
- Keep it specific and research-focused.
- Length: 1 to 3 sentences.
- Do not use em dashes.

2. Sub-tasks (sub_tasks)
Generate at most 5 independent research areas.

Rules:
- Each sub-task must investigate one distinct aspect of the query.
- Each sub-task must be understandable without reading other tasks.
- Each sub-task must represent a concrete research objective.
- Keep each sub-task under 20 words.
- Avoid vague tasks.
- Do not create meta-tasks like:
  "summarize findings"
  "compile information"
  "review literature"
  "analyze all research"

Example:

Query:
"room temperature superconductivity 2026"

Good ps:
"Despite progress in superconductivity research, achieving superconductivity at practical temperatures and pressures remains unresolved. This research examines current evidence, competing theories, and barriers preventing reliable room-temperature superconductors."

Good sub_tasks:
[
"Investigate LK-99 replication studies and experimental outcomes from 2024-2026",
"Examine hydrogen-rich compounds as high-temperature superconductor candidates",
"Analyze theoretical mechanisms proposed for room-temperature superconductivity",
"Evaluate experimental challenges preventing practical superconducting materials",
"Study recent superconductivity measurement and verification methods"
]

Revision rules:
- If the user requests a ps change, modify only ps.
- If the user requests sub-task changes, modify only sub_tasks.
- Preserve unchanged sections exactly when not requested.
- Do not rewrite the entire plan unnecessarily.

Return ONLY valid JSON:
{{
  "ps": "string",
  "sub_tasks": ["string"]
}}
"""


class ResearchPlan(BaseModel):
    ps: Optional[str] = Field(
        default=None,
        description="Detailed Problem Statement of the research plan. Omit if not revising.",
    )
    sub_tasks: Optional[List[str]] = Field(
        default=None,
        description="Ordered list of independent research sub-tasks. Omit if not revising.",
        min_length=1,
        max_length=5,
    )


def planner_node(state: ResearchState) -> dict:
    planner_llm = llm.flash().with_structured_output(ResearchPlan, method="json_mode")

    user_content = (
        f"Create a Problem statement (ps) and a research plan for: {state['query']}"
    )
    if state.get("user_feedback"):
        user_content += (
            f"\n\nUser feedback on previous ps and plan : {state['user_feedback']}"
            f"\nPrevious ps: {state.get('ps', '')}"
            f"\nPrevious plan: {state.get('plan', [])}"
        )

    prompt = ChatPromptTemplate([("system", PLANNER_SYSTEM_PROMPT), ("user", user_content)])
    messages = prompt.format_messages()

    try:
        result = planner_llm.invoke(messages)
        new_ps = result.ps if result.ps is not None else state.get("ps", "")
        new_plan = (
            result.sub_tasks if result.sub_tasks is not None else state.get("plan", [])
        )
        logger.info(
            f"Planner generated {len(new_plan)} sub-tasks for query: {state['query']}"
        )
        return {"ps": new_ps, "plan": new_plan, "status": "awaiting_approval"}
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error generating research plan: {e}", exc_info=True)

        error_lower = error_msg.lower()
        if any(
            kw in error_lower
            for kw in ["violates safety", "safety", "inappropriate", "restricted"]
        ):
            friendly_error = "Query contains inappropriate or restricted content."
        elif any(
            kw in error_lower
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
            friendly_error = "API key is missing or invalid. Open the sidebar to configure your API keys."
        else:
            friendly_error = f"Failed to generate research plan: {error_msg}"

        return {"status": "error", "error": friendly_error}


# --- Plan Approval (HITL) ---

APPROVAL_SYSTEM_PROMPT = """You are a plan approval classifier.
Analyze the user's feedback to determine if they approved the current plan, or if they are requesting revisions or changes.

Classification Rules:
- If the user explicitly approves the plan (e.g., "looks good", "approve", "proceed", "go ahead", "run", "yes", "perfect", "ok"), set 'plan_approved' to true.
- If the user requests any change, addition, deletion, modification, or feedback (e.g., "add trend analysis step", "remove step 2", "change X", "focus on Y"), set 'plan_approved' to false.
- Be conservative: if they ask questions, provide suggestions, or demand adjustments, set 'plan_approved' to false.
- Respond in JSON format matching the schema."""


class PlanState(BaseModel):
    plan_approved: bool = Field(description="Whether the plan is approved or not")


def plan_approval(state: ResearchState) -> dict:
    user_response = interrupt("Waiting for plan approval/feedback")

    feedback = (
        user_response.get("message", "")
        if isinstance(user_response, dict)
        else str(user_response)
    )

    approval_llm = llm.flash().with_structured_output(PlanState, method="json_mode")

    user_content = (
        f"User feedback: {feedback}\n"
        f"Previous ps: {state.get('ps', '')}\n"
        f"Previous plan: {state.get('plan', [])}"
    )

    prompt = ChatPromptTemplate([("system", APPROVAL_SYSTEM_PROMPT), ("user", user_content)])
    messages = prompt.format_messages()
    result = approval_llm.invoke(messages)

    logger.info(f"Plan approval result: {result.plan_approved}")
    logger.info(f"User feedback: {feedback}")

    status = "researching" if result.plan_approved else "planning"
    return {"plan_approved": result.plan_approved, "user_feedback": feedback, "status": status}


# --- Supervisor: fan-out workers via Send() ---

def dispatch_researchers(state: ResearchState) -> List[Send]:
    """Spawn one researcher per sub-task; each runs as an independent parallel branch."""
    return [Send("researcher", {**state, "query": task}) for task in state["plan"][:5]]


# --- Researcher (worker) ---

LLM_TIMEOUT = 90


def _invoke_with_timeout(agent_or_llm, messages, timeout=LLM_TIMEOUT):
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        fut = pool.submit(agent_or_llm.invoke, messages)
        try:
            return fut.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            logger.error(f"LLM invoke timed out after {timeout}s")
            raise TimeoutError(f"LLM call timed out after {timeout}s")


RESEARCHER_SYSTEM_PROMPT = """You are an elite, highly-analytical research analyst with access to real-time web search.
Your objective is to thoroughly investigate the assigned research task by formulating precise search queries and critically evaluating the results.

### Your Search Workflow
1. **Analyze the Task**: Determine the core concepts, temporal constraints (e.g., specific years or recent dates), and information gaps.
2. **Formulate Queries**:
   - Construct queries using dense, information-rich keywords (avoid natural language sentences where keywords are more effective).
   - If the task mentions a specific timeframe, include relevant years or dates in your queries.
3. **Execute and Refine**:
   - Call the `search_web` tool.
   - Use the `time_range` parameter ONLY if the task specifies a recent timeframe (e.g., "today", "this week", "recently"):
     * `"day"` for news within the last 24 hours.
     * `"week"` for updates from the last 7 days.
     * `"month"` for events in the last 30 days.
     * `"year"` for events in the last 12 months.
     * Do not specify `time_range` (leave as None) for historical or general queries.
   - Limit yourself to a maximum of 3 search iterations.
4. **Evaluate Critically**:
   - Assess search results for credibility, relevance, and completeness.
   - If results are insufficient or ambiguous, refine your search terms and query again.
5. **Conclude**: Once you have gathered sufficient high-quality facts to fully address the task, stop calling tools.

### Constraints & Rigor
- **Factual Grounding**: Every fact, number, and claim you output must be strictly backed by the retrieved search results. Do not speculate or make assumptions.
- **Conciseness**: Keep summaries structured, dense, and under 500 - 700 tokens.
- **Citations**: Track all source URLs from search results so they can be cited in your final response.
"""

SYNTHESIS_PROMPT = """Using all search results gathered above, write your final research report.

You MUST respond in valid JSON with this exact schema:
{{
  "result": "<comprehensive research summary based only on search results>",
  "citations": ["<url1>", "<url2>", ...]
}}

Only include URLs that appeared in the search results."""


class ResearchResult(BaseModel):
    result: str = Field(description="Comprehensive research summary based on search results")
    citations: List[str] = Field(description="List of source URLs from search results")


def researcher_node(state: ResearchState) -> dict:
    query = state["query"]
    logger.info(f"Researcher starting for query: {query}")

    # Stagger execution of concurrent researcher nodes to reduce API rate limit spikes
    stagger_time = random.uniform(0.5, 3.0)
    logger.info(f"Staggering researcher start by {stagger_time:.2f}s for: {query}")
    time.sleep(stagger_time)

    try:
        agent = llm.flash().bind_tools([search_web])

        messages = [
            SystemMessage(content=RESEARCHER_SYSTEM_PROMPT),
            HumanMessage(content=f"Research Task: {query}"),
        ]

        max_steps = 10
        search_count = 0

        for step in range(max_steps):
            response = _invoke_with_timeout(agent, messages)
            messages.append(response)

            if not response.tool_calls:
                logger.info(
                    f"Researcher completed search in {step + 1} steps with {search_count} searches"
                )
                break

            for tool_call in response.tool_calls:
                if tool_call["name"] == "search_web":
                    args = tool_call["args"]

                    # Inject search_topic from the active graph state if not already set by the LLM
                    if "search_topic" not in args and "search_topic" in state:
                        args["search_topic"] = state["search_topic"]

                    logger.info(
                        f"Executing search: query='{args.get('query')}', "
                        f"search_topic={args.get('search_topic')}, time_range={args.get('time_range')}"
                    )

                    try:
                        tool_output = search_web.invoke(args)
                        search_count += 1
                    except Exception as e:
                        tool_output = f"Search failed: {str(e)}"
                        logger.warning(f"Search failed: {e}")

                    messages.append(
                        ToolMessage(
                            content=str(tool_output),
                            tool_call_id=tool_call["id"],
                            name=tool_call["name"],
                        )
                    )
                else:
                    logger.warning(f"Unknown tool call: {tool_call['name']}")
                    messages.append(
                        ToolMessage(
                            content=f"Unknown tool {tool_call['name']}",
                            tool_call_id=tool_call["id"],
                        )
                    )

        # Synthesis step: plain LLM (no tools) to structure the gathered results
        messages.append(HumanMessage(content=SYNTHESIS_PROMPT))
        final_response = _invoke_with_timeout(llm.flash(), messages)

        try:
            raw = final_response.content.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            data = json.loads(raw)
            final_result = ResearchResult(**data)
        except Exception as e:
            logger.error(f"Structured output parsing failed: {e}")
            return {"results": [final_response.content], "citations": []}

        logger.info(f"Researcher completed. Citations: {len(final_result.citations)}")
        return {
            "results": [final_result.result],
            "citations": final_result.citations,
        }
    except Exception as e:
        logger.error(f"Error in researcher node for task '{query}': {e}", exc_info=True)
        return {
            "results": [f"Research failed for this task due to an error: {str(e)}"],
            "citations": [],
        }


# --- Aggregator ---

AGGREGATOR_SYSTEM_PROMPT = """You are a Principal Research Analyst and Writer.

Your task is to synthesize the provided raw research findings into a cohesive, publication-ready research report in markdown format.

Structure requirements:
- Use a single, clean markdown title for the report.
- Provide a clear Executive Summary / Overview at the beginning.
- Organically group the findings into logical sections based on the research content.
- Incorporate the Problem Statement naturally into the intro/executive summary section.
- List all the provided source URLs cleanly under a 'Sources & References' section at the end.

Matplotlib Chart Tool instructions:
- You have access to a matplotlib chart generation tool (`generate_matplotlib_chart`).
- Analyze the research sections. If there are numerical data, comparisons, statistics, or historical trends, you MUST call this tool to generate charts.
- Generate between 1 and 3 charts (e.g., bar chart, line plot, pie chart, scatter plot).
- Each successful call returns a marker like <!--CHART_1--> (the chart image is attached automatically afterwards). Embed the EXACT marker text at the location where the chart belongs in your report.
- Never invent image links, URLs, or markers that were not returned by the tool.

Guidelines:
- Keep the tone formal, objective, and analytical.
- Present data in well-formatted markdown tables or bullet points where appropriate.
- Strictly stick to the facts provided. Do not extrapolate, invent metrics, or fabricate URLs."""


MAX_AGGREGATOR_ROUNDS = 8  # cap on LLM tool-calling rounds in the aggregator
AGGREGATOR_TIMEOUT = 180  # seconds per aggregator LLM call (pro model is slower)


def aggregator_node(state: ResearchState) -> dict:
    combined = "\n\n".join(
        f"Research Section {i + 1}:\n{result}"
        for i, result in enumerate(state["results"])
    )

    citations = list(dict.fromkeys(state.get("citations", [])))

    messages = [
        SystemMessage(content=AGGREGATOR_SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"User Query: {state['query']}\n"
                f"Problem Statement (ps): {state.get('ps', '')}\n\n"
                f"Research Sections:\n{combined}\n\n"
                f"Citations:\n"
                + "\n".join(f"- {url}" for url in citations)
                + "\n\n"
                "Write the final synthesized markdown report. Call "
                "`generate_matplotlib_chart` to generate between 1 and 3 charts "
                "based on the research findings data, and embed the returned "
                "<!--CHART_N--> markers where the charts belong."
            )
        ),
    ]

    try:
        llm_with_tools = llm.pro().bind_tools([generate_matplotlib_chart])

        messages_history = list(messages)
        chart_links = []

        for round_num in range(1, MAX_AGGREGATOR_ROUNDS + 1):
            try:
                response = _invoke_with_timeout(
                    llm_with_tools, messages_history, timeout=AGGREGATOR_TIMEOUT
                )
            except TimeoutError:
                logger.error(
                    f"Aggregator LLM call timed out after {AGGREGATOR_TIMEOUT}s "
                    f"(round {round_num})"
                )
                break

            messages_history.append(response)

            if not response.tool_calls or round_num == MAX_AGGREGATOR_ROUNDS:
                break

            for tool_call in response.tool_calls:
                if tool_call["name"] == "generate_matplotlib_chart":
                    result = generate_matplotlib_chart.invoke(tool_call["args"])
                    if result.startswith("Error executing matplotlib code"):
                        # Keep the error in context (truncated) so the LLM can retry
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
                        # The LLM only needs the marker, not the base64 payload
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

        # Reconstruct the final report from all assistant turns
        final_content = "".join(
            msg.content for msg in messages_history if isinstance(msg, AIMessage)
        )

        # Substitute the real embedded chart images for the markers
        for i, link in enumerate(chart_links, start=1):
            final_content = final_content.replace(f"<!--CHART_{i}-->", link)

    except Exception as e:
        error_msg = str(e).lower()
        logger.error(f"Error in aggregator: {e}", exc_info=True)
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
        return {"status": "error", "error": f"Synthesis failed: {str(e)}"}

    return {"final_answer": final_content, "status": "completed"}


#############################
# Graph builder
#############################


def build_research_graph():
    """Build and compile the research graph (no Streamlit involved)."""
    builder = StateGraph(ResearchState)

    builder.add_node("query_validator", query_validator)
    builder.add_node("planner", planner_node)
    builder.add_node("approval", plan_approval)
    builder.add_node("researcher", researcher_node)
    builder.add_node("aggregator", aggregator_node)

    def route_after_approval(state: ResearchState):
        """Fan out to one researcher per sub-task if approved, else loop to planner."""
        if state.get("plan_approved"):
            return dispatch_researchers(state)
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
        "approval", route_after_approval, ["researcher", "planner"]
    )
    builder.add_edge("researcher", "aggregator")
    builder.add_edge("aggregator", END)

    return builder.compile(checkpointer=MemorySaver())


# The compiled graph is cached per API-key pair so MemorySaver checkpoint state
# persists across Streamlit reruns within the same process.
_graph_key = None
_graph = None


def get_graph():
    global _graph_key, _graph
    llm_key = (
        os.getenv("LLM_API_KEY")
        or os.getenv("DEEPSEEK_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or ""
    )
    base_url = (
        os.getenv("LLM_BASE_URL")
        or os.getenv("DEEPSEEK_BASE_URL")
        or "https://api.deepseek.com"
    )
    model_fast = os.getenv("MODEL_FAST") or "deepseek-v4-flash"
    model_pro = os.getenv("MODEL_PRO") or "deepseek-v4-pro"
    tavily_key = os.getenv("TAVILY_API_KEY") or ""

    key = (llm_key, base_url, model_fast, model_pro, tavily_key)
    if _graph is None or _graph_key != key:
        _graph_key = key
        _graph = build_research_graph()
    return _graph


def apply_api_keys(api_key: str, base_url: str, model_fast: str, model_pro: str, tavily_key: str):
    """Update runtime configuration and rebuild clients."""
    if api_key:
        os.environ["LLM_API_KEY"] = api_key
    if base_url:
        os.environ["LLM_BASE_URL"] = base_url
    if model_fast:
        os.environ["MODEL_FAST"] = model_fast
    if model_pro:
        os.environ["MODEL_PRO"] = model_pro
    if tavily_key:
        os.environ["TAVILY_API_KEY"] = tavily_key
    reset_clients()


#############################
# Streamlit UI
#############################

_CHART_RE = re.compile(
    r"!\[([^\]]*)\]\((data:image/png;base64,[A-Za-z0-9+/=]+)\)"
)


def _render_report_with_charts(report: str):
    """Render a markdown report, displaying embedded base64 charts via st.image."""
    import streamlit as st

    parts = _CHART_RE.split(report)
    for i in range(1, len(parts), 3):
        alt, data_uri = parts[i], parts[i + 1]
        st.markdown(parts[i - 1])
        try:
            img_bytes = base64.b64decode(data_uri.split(",", 1)[1])
            st.image(io.BytesIO(img_bytes), caption=alt or "Generated Chart")
        except Exception:
            st.markdown(f"![{alt}]({data_uri})")
    if parts:
        st.markdown(parts[-1])


def render_ui():
    import streamlit as st

    st.set_page_config(page_title="DeepResearch Agent", page_icon="🔬", layout="wide")

    # ------------------------- session state -------------------------
    for key in (
        "thread_id",
        "ps",
        "plan",
        "status",
        "error",
        "final_answer",
        "citations",
        "researcher_log",
    ):
        st.session_state.setdefault(key, None)

    # ------------------------- sidebar -------------------------
    with st.sidebar:
        st.title("⚙️ Settings")

        st.subheader("LLM Configuration")
        base_url = st.text_input(
            "Base URL",
            value=os.getenv("LLM_BASE_URL") or os.getenv("DEEPSEEK_BASE_URL") or "https://api.deepseek.com",
            help="DeepSeek, OpenAI, or custom API compatible base URL.",
        )
        model_fast = st.text_input(
            "Fast Model",
            value=os.getenv("MODEL_FAST") or "deepseek-v4-flash",
            help="Model for fast steps like validation, planning, and research.",
        )
        model_pro = st.text_input(
            "Pro Model",
            value=os.getenv("MODEL_PRO") or "deepseek-v4-pro",
            help="Model for aggregation and synthesis.",
        )
        api_key = st.text_input(
            "LLM API Key",
            type="password",
            value=os.getenv("LLM_API_KEY") or os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY") or "",
            help="API Key for the provider. Falls back to .env.",
        )

        st.subheader("Search Service")
        tavily_key = st.text_input(
            "Tavily API Key",
            type="password",
            value=os.getenv("TAVILY_API_KEY") or "",
            help="Get one at tavily.com. Falls back to .env.",
        )

        if st.button("Save Settings", type="primary"):
            apply_api_keys(api_key, base_url, model_fast, model_pro, tavily_key)
            st.success("Settings saved.")
            st.rerun()

        st.divider()
        if st.button("🆕 New Research", use_container_width=True):
            for key in (
                "thread_id",
                "ps",
                "plan",
                "status",
                "error",
                "final_answer",
                "citations",
                "researcher_log",
            ):
                st.session_state[key] = None
            st.rerun()

        st.caption(
            "Keys can also be placed in a `.env` file next to `app.py` "
            "(see `.env.example`)."
        )

    # ------------------------- main -------------------------
    st.title("🔬 DeepResearch Agent")
    st.caption(
        "Multi-agent research assistant: plan, human-approve, then fan out parallel "
        "researchers to produce a cited markdown report."
    )

    status = st.session_state.status

    # ----- Step 1: query input -----
    if not status or status in ("error", "awaiting_approval"):
        query = st.text_area(
            "Research Query",
            placeholder="e.g. Recent breakthroughs in Quantum Computing in 2026",
            height=100,
        )
        search_topic = st.multiselect(
            "Search Topic Filters",
            ["all", "news", "academic", "finance", "patent"],
            default=["all"],
        )

        if st.button("🚀 Start Research", type="primary"):
            if not query.strip():
                st.warning("Please enter a research query.")
                return
            graph = get_graph()
            thread_id = str(uuid.uuid4())
            st.session_state.thread_id = thread_id
            config = {"configurable": {"thread_id": thread_id}}
            with st.spinner("Planning the research strategy..."):
                try:
                    for _ in graph.stream(
                        {"query": query.strip(), "search_topic": search_topic},
                        config=config,
                    ):
                        pass
                except Exception as e:
                    st.error(f"Failed to start research: {str(e)}")
                    return

            state = graph.get_state(config)
            st.session_state.ps = state.values.get("ps")
            st.session_state.plan = state.values.get("plan")
            st.session_state.status = state.values.get("status")
            st.session_state.error = state.values.get("error")
            st.rerun()

    # ----- Step 2: plan review (HITL) -----
    if status == "awaiting_approval" and st.session_state.plan:
        st.subheader("📋 Proposed Research Plan")
        if st.session_state.ps:
            st.info(f"**Problem Statement:** {st.session_state.ps}")
        for i, task in enumerate(st.session_state.plan, start=1):
            st.markdown(f"**{i}.** {task}")

        st.divider()
        st.subheader("👤 Review & Approve")
        st.caption(
            "Approve to start research, or request changes in natural language "
            "(e.g. 'add a trend analysis step', 'remove step 2')."
        )
        feedback = st.text_area(
            "Feedback / revision request (optional)",
            placeholder="Approve or describe what to change...",
        )
        col1, col2 = st.columns(2)
        with col1:
            approve_clicked = st.button("✅ Approve & Start Research", type="primary")
        with col2:
            revise_clicked = st.button("🔄 Revise Plan")

        if approve_clicked or revise_clicked:
            message = "Approved. Proceed with the research."
            if revise_clicked:
                if not feedback.strip():
                    st.warning("Please describe what to change before revising.")
                    return
                message = feedback.strip()

            graph = get_graph()
            config = {"configurable": {"thread_id": st.session_state.thread_id}}
            log = []
            with st.status("🔎 Researchers are investigating...", expanded=True) as box:
                try:
                    for event in graph.stream(
                        Command(resume={"message": message}), config=config
                    ):
                        for node_name, payload in event.items():
                            if node_name == "researcher":
                                results = payload.get("results") or []
                                snippet = str(results[0])[:100] if results else "done"
                                log.append(
                                    f"**Researcher** → {snippet}"
                                )
                                box.write(f"✅ Researcher completed: {snippet}")
                            elif node_name == "aggregator":
                                box.write("🧠 Aggregator is synthesizing the final report...")
                except Exception as e:
                    box.write(f"❌ Error: {str(e)}")
                    st.session_state.status = "error"
                    st.session_state.error = str(e)
                    st.rerun()

            state = graph.get_state(config)
            st.session_state.researcher_log = log
            st.session_state.final_answer = state.values.get("final_answer")
            st.session_state.citations = state.values.get("citations") or []
            st.session_state.status = state.values.get("status")
            st.session_state.error = state.values.get("error")
            st.rerun()

    # ----- errors -----
    if st.session_state.status == "error" and st.session_state.error:
        st.error(st.session_state.error)
        st.session_state.status = None  # allow retrying with a new query
        st.rerun()

    # ----- Step 3: final report -----
    if st.session_state.status == "completed" and st.session_state.final_answer:
        st.subheader("📄 Research Report")

        st.download_button(
            "⬇️ Download Report (.md)",
            data=st.session_state.final_answer,
            file_name=f"deep_research_{st.session_state.thread_id}.md",
            mime="text/markdown",
        )

        _render_report_with_charts(st.session_state.final_answer)

        if st.session_state.citations:
            st.subheader("🔗 Sources & References")
            for url in st.session_state.citations:
                st.markdown(f"- [{url}]({url})")

        if st.session_state.researcher_log:
            with st.expander("Research process log"):
                for entry in st.session_state.researcher_log:
                    st.markdown(entry)

    if not status and not st.session_state.thread_id:
        st.info(
            "Enter a research query and click **Start Research**. The app will plan "
            "the research, let you approve or revise the plan, then dispatch parallel "
            "researchers before writing the final report."
        )


if __name__ == "__main__":
    render_ui()
