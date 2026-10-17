"""LangGraph travel-planning workflow.

The model writes the itinerary. A deterministic tool calculates the total
budget, so the displayed total does not depend on parsing prose with a regex.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date
from typing import Annotated, Any, Literal, TypedDict

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field


@tool("get_current_date")
def get_current_date() -> str:
    """Return the current local date and weekday.

    Call this tool before planning so the itinerary uses the real current date
    instead of relying on the model's memory.
    """

    today = date.today()
    weekdays = ("星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日")
    return json.dumps(
        {
            "date": today.isoformat(),
            "weekday": weekdays[today.weekday()],
        },
        ensure_ascii=False,
    )


class BudgetInput(BaseModel):
    """Input used by the deterministic trip-budget tool."""

    days: int = Field(ge=1, le=30, description="Total number of travel days")
    nights: int = Field(ge=0, le=30, description="Number of hotel nights")
    hotel_per_night: float = Field(ge=0, description="Hotel cost per night in CNY")
    food_per_day: float = Field(ge=0, description="Food cost per day in CNY")
    transport_per_day: float = Field(
        ge=0,
        description="Local transport cost per day in CNY",
    )
    tickets_total: float = Field(ge=0, description="Total attraction tickets in CNY")


@tool("calculate_trip_budget", args_schema=BudgetInput)
def calculate_trip_budget(
    days: int,
    nights: int,
    hotel_per_night: float,
    food_per_day: float,
    transport_per_day: float,
    tickets_total: float,
) -> str:
    """Calculate a trip budget after estimating each cost component.

    Use this tool exactly once after estimating the user's trip costs. The
    returned total is authoritative and must be included in the final plan.
    """

    hotel = nights * hotel_per_night
    food = days * food_per_day
    transport = days * transport_per_day
    total = hotel + food + transport + tickets_total
    return json.dumps(
        {
            "total": round(total, 2),
            "breakdown": {
                "hotel": round(hotel, 2),
                "food": round(food, 2),
                "transport": round(transport, 2),
                "tickets": round(tickets_total, 2),
            },
            "currency": "CNY",
        },
        ensure_ascii=False,
    )


TOOLS = [get_current_date, calculate_trip_budget]


class TravelState(TypedDict):
    """Shared state passed between LangGraph nodes."""

    messages: Annotated[list[BaseMessage], add_messages]
    destination: str
    num_days: int
    error: str


@dataclass
class TravelResult:
    """Result returned to the UI layer."""

    itinerary: str = ""
    planning_date: str = ""
    total_budget: float | None = None
    budget_breakdown: dict[str, float] = field(default_factory=dict)
    error: str = ""


SYSTEM_PROMPT = """你是一位资深旅行规划师。

工作流程：
1. 必须先调用 get_current_date 工具一次，取得真实规划日期。
2. 根据用户提供的目的地和天数，估算住宿、餐饮、交通和门票费用。
3. 必须调用 calculate_trip_budget 工具一次，由代码计算总预算。
4. 拿到工具结果后，再输出完整行程。不要把工具返回的总价自行改动。

最终输出格式（严格照做）：
**规划日期**：工具返回的日期（星期X）

## 第X天：主题
**🌅 上午**：活动安排

**🍚 中午**：午餐建议

**☀️ 下午**：活动安排

**🌙 晚上**：活动安排

**🏨 住宿**：住宿区域与价格假设

**当日预算**：约¥XXX

其他要求：
- 每天单独成段，覆盖用户要求的全部天数。
- 金额使用人民币，注明这是估算值，不伪造实时价格。
- 最后输出一行：**全程预算**：约¥工具计算出的总预算。
- 直接从第1天开始，不要写客套开场白。
"""


def validate_request(state: TravelState) -> dict[str, str]:
    """Validate form values before the model is called."""

    destination = str(state.get("destination", "")).strip()
    num_days = int(state.get("num_days", 0))
    if not destination:
        return {"error": "请填写旅行目的地。"}
    if not 1 <= num_days <= 30:
        return {"error": "旅行天数必须在 1 到 30 天之间。"}
    return {"error": ""}


def route_after_validation(state: TravelState) -> Literal["assistant", "__end__"]:
    """Route invalid requests straight to a friendly error."""

    return END if state.get("error") else "assistant"


def _assistant_node(llm_with_tools: Any):
    def assistant(state: TravelState) -> dict[str, list[AIMessage]]:
        response = llm_with_tools.invoke(
            [SystemMessage(content=SYSTEM_PROMPT), *state["messages"]]
        )
        return {"messages": [response]}

    return assistant


def should_call_tools(state: TravelState) -> Literal["tools", "__end__"]:
    """Continue to tools while the model requests them, with a loop limit."""

    last_message = state["messages"][-1]
    tool_calls = getattr(last_message, "tool_calls", [])
    completed_tool_rounds = sum(
        isinstance(message, ToolMessage) for message in state["messages"]
    )
    if tool_calls and completed_tool_rounds < 4:
        return "tools"
    return END


def build_travel_graph(api_key: str) -> Any:
    """Build the LangGraph workflow used by both the UI and tests."""

    llm = ChatOpenAI(
        model="deepseek-chat",
        api_key=api_key,
        base_url="https://api.deepseek.com/v1",
        temperature=0.4,
    )
    llm_with_tools = llm.bind_tools(TOOLS)

    workflow = StateGraph(TravelState)
    workflow.add_node("validate_request", validate_request)
    workflow.add_node("assistant", _assistant_node(llm_with_tools))
    workflow.add_node("tools", ToolNode(TOOLS))

    workflow.add_edge(START, "validate_request")
    workflow.add_conditional_edges(
        "validate_request",
        route_after_validation,
        {"assistant": "assistant", END: END},
    )
    workflow.add_conditional_edges(
        "assistant",
        should_call_tools,
        {"tools": "tools", END: END},
    )
    workflow.add_edge("tools", "assistant")
    return workflow.compile()


def content_to_text(content: Any) -> str:
    """Normalize text content returned by different chat-model providers."""

    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return str(content)

    parts: list[str] = []
    for item in content:
        if isinstance(item, str):
            parts.append(item)
        elif isinstance(item, dict) and item.get("type") == "text":
            parts.append(str(item.get("text", "")))
    return "\n".join(part for part in parts if part)


def extract_budget_result(messages: list[BaseMessage]) -> tuple[float | None, dict[str, float]]:
    """Read the latest budget-tool observation from the graph messages."""

    for message in reversed(messages):
        if not isinstance(message, ToolMessage):
            continue
        if getattr(message, "name", "") != "calculate_trip_budget":
            continue
        try:
            payload = json.loads(content_to_text(message.content))
            return (
                float(payload["total"]),
                {key: float(value) for key, value in payload["breakdown"].items()},
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            break
    return None, {}


def extract_planning_date(messages: list[BaseMessage]) -> str:
    """Read the date-tool observation from the graph messages."""

    for message in reversed(messages):
        if not isinstance(message, ToolMessage):
            continue
        if getattr(message, "name", "") != "get_current_date":
            continue
        try:
            payload = json.loads(content_to_text(message.content))
            return f"{payload['date']}（{payload['weekday']}）"
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            break
    return ""


def extract_itinerary(messages: list[BaseMessage]) -> str:
    """Return the final assistant text, excluding tool-call messages."""

    for message in reversed(messages):
        if not isinstance(message, AIMessage) or getattr(message, "tool_calls", []):
            continue
        text = content_to_text(message.content).strip()
        if text:
            return text
    return ""


def split_days(plan_text: str) -> list[str]:
    """Split the output into day blocks for the Streamlit renderer."""

    parts = re.split(r"(?=##\s*第\s*\d+\s*天)", plan_text)
    return [
        part.strip()
        for part in parts
        if part.strip() and re.match(r"^##?\s*第\s*\d+\s*天", part.strip())
    ]


def run_travel_agent(api_key: str, destination: str, num_days: int) -> TravelResult:
    """Run one request through the LangGraph workflow."""

    initial_state: TravelState = {
        "messages": [
            HumanMessage(
                content=(
                    f"请规划一次去 {destination.strip()} 的 {num_days} 天旅行。"
                    "请先估算费用并调用预算工具，再输出完整行程。"
                )
            )
        ],
        "destination": destination,
        "num_days": num_days,
        "error": "",
    }
    graph = build_travel_graph(api_key)
    final_state = graph.invoke(initial_state)

    if final_state.get("error"):
        return TravelResult(error=final_state["error"])

    messages = final_state["messages"]
    itinerary = extract_itinerary(messages)
    planning_date = extract_planning_date(messages)
    total_budget, breakdown = extract_budget_result(messages)
    if not itinerary:
        return TravelResult(
            planning_date=planning_date,
            total_budget=total_budget,
            budget_breakdown=breakdown,
            error="模型没有返回可用行程，请稍后重试。",
        )
    return TravelResult(
        itinerary=itinerary,
        planning_date=planning_date,
        total_budget=total_budget,
        budget_breakdown=breakdown,
    )
