"""AI Financial Coach — coach agent + tools (Budget / Savings / Debt)."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint
from dotenv import load_dotenv
from fastapi import FastAPI
from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.tools import AgentTool, ToolContext
from google.genai import types
from pydantic import BaseModel, Field

load_dotenv()


# ---------- Output schemas (sub-agent results) ----------


class SpendingCategory(BaseModel):
    category: str = Field(..., description="Expense category name")
    amount: float = Field(..., description="Amount spent in this category")
    percentage: Optional[float] = Field(None, description="Percentage of total spending")


class SpendingRecommendation(BaseModel):
    category: str = Field(..., description="Category for recommendation")
    recommendation: str = Field(..., description="Recommendation details")
    potential_savings: Optional[float] = Field(None, description="Estimated monthly savings")


class BudgetAnalysis(BaseModel):
    total_expenses: float = Field(..., description="Total monthly expenses")
    monthly_income: Optional[float] = Field(None, description="Monthly income")
    spending_categories: List[SpendingCategory] = Field(..., description="Breakdown of spending by category")
    recommendations: List[SpendingRecommendation] = Field(..., description="Spending recommendations")


class EmergencyFund(BaseModel):
    recommended_amount: float = Field(..., description="Recommended emergency fund size")
    current_amount: Optional[float] = Field(None, description="Current emergency fund (if any)")
    current_status: str = Field(..., description="Status assessment of emergency fund")


class SavingsRecommendation(BaseModel):
    category: str = Field(..., description="Savings category")
    amount: float = Field(..., description="Recommended monthly amount")
    rationale: Optional[str] = Field(None, description="Explanation for this recommendation")


class AutomationTechnique(BaseModel):
    name: str = Field(..., description="Name of automation technique")
    description: str = Field(..., description="Details of how to implement")


class SavingsStrategy(BaseModel):
    emergency_fund: EmergencyFund = Field(..., description="Emergency fund recommendation")
    recommendations: List[SavingsRecommendation] = Field(..., description="Savings allocation recommendations")
    automation_techniques: Optional[List[AutomationTechnique]] = Field(
        None, description="Automation techniques to help save"
    )


class Debt(BaseModel):
    name: str = Field(..., description="Name of debt")
    amount: float = Field(..., description="Current balance")
    interest_rate: float = Field(..., description="Annual interest rate (%)")
    min_payment: Optional[float] = Field(None, description="Minimum monthly payment")


class PayoffPlan(BaseModel):
    total_interest: float = Field(..., description="Total interest paid")
    months_to_payoff: int = Field(..., description="Months until debt-free")
    monthly_payment: Optional[float] = Field(None, description="Recommended monthly payment")


class PayoffPlans(BaseModel):
    avalanche: PayoffPlan = Field(..., description="Highest interest first method")
    snowball: PayoffPlan = Field(..., description="Smallest balance first method")


class DebtRecommendation(BaseModel):
    title: str = Field(..., description="Title of recommendation")
    description: str = Field(..., description="Details of recommendation")
    impact: Optional[str] = Field(None, description="Expected impact of this action")


class DebtReduction(BaseModel):
    total_debt: float = Field(..., description="Total debt amount")
    debts: List[Debt] = Field(..., description="List of all debts")
    payoff_plans: PayoffPlans = Field(..., description="Debt payoff strategies")
    recommendations: Optional[List[DebtRecommendation]] = Field(
        None, description="Recommendations for debt reduction"
    )


# ---------- Shared state plumbing ----------


DEFAULT_FINANCIAL_DATA: Dict[str, Any] = {
    "monthly_income": 0,
    "dependants": 0,
    "manual_expenses": {},
    "debts": [],
}


def on_before_agent(callback_context: CallbackContext):
    """Initialize financial_data in shared state if missing."""
    if "financial_data" not in callback_context.state:
        callback_context.state["financial_data"] = dict(DEFAULT_FINANCIAL_DATA)
    return None


def _safe_dumps(value: Any) -> str:
    try:
        return json.dumps(value, indent=2, default=str)
    except Exception:
        return str(value)


def _state_context(state, include_keys: List[str]) -> str:
    """Render selected state slices as a readable context block."""
    blocks: List[str] = []
    fd = state.get("financial_data") or DEFAULT_FINANCIAL_DATA
    blocks.append(f"FINANCIAL DATA:\n{_safe_dumps(fd)}")
    for key in include_keys:
        value = state.get(key)
        if value:
            blocks.append(f"{key.upper()}:\n{_safe_dumps(value)}")
    return "\n\n".join(blocks)


def _make_state_injector(prior_keys: List[str]):
    """Build a before_model_callback that prepends financial state to system instruction."""

    def modifier(callback_context: CallbackContext, llm_request: LlmRequest):
        context = _state_context(callback_context.state, prior_keys)
        prefix = (
            "The user's financial information and prior agent outputs are below. "
            "Use them to produce your structured response.\n\n"
            f"{context}\n\n---\n"
        )

        original = llm_request.config.system_instruction or types.Content(
            role="system", parts=[]
        )
        if not isinstance(original, types.Content):
            original = types.Content(
                role="system", parts=[types.Part(text=str(original))]
            )
        if not original.parts:
            original.parts = [types.Part(text="")]
        original.parts[0].text = prefix + (original.parts[0].text or "")
        llm_request.config.system_instruction = original
        return None

    return modifier


# ---------- Specialist agents ----------


budget_agent = LlmAgent(
    name="BudgetAnalysisAgent",
    model="gemini-3.5-flash",
    description="Analyzes financial data to categorize spending patterns and recommend budget improvements.",
    instruction="""You are a Budget Analysis Agent. Read FINANCIAL DATA above.

Your tasks:
1. Categorize ALL expenses from the user's financial data into logical groups, with percentages summing to 100%.
2. Identify spending patterns and trends across categories.
3. Provide 3-5 specific, actionable recommendations with quantified potential monthly savings.

Consider:
- Number of dependants when evaluating household expenses.
- Typical spending ratios for the income level (housing ~30%, food ~15%).
- Essential vs discretionary spending separation.

Respond strictly using the BudgetAnalysis schema.""",
    output_schema=BudgetAnalysis,
    output_key="budget_analysis",
    before_model_callback=_make_state_injector([]),
)


savings_agent = LlmAgent(
    name="SavingsStrategyAgent",
    model="gemini-3.5-flash",
    description="Recommends savings strategies based on income, expenses, and prior budget analysis.",
    instruction="""You are a Savings Strategy Agent. Read FINANCIAL DATA and BUDGET_ANALYSIS above when available.

Your tasks:
1. Recommend an emergency fund size based on monthly expenses and dependants (typically 3-6 months of expenses).
2. Suggest savings allocations across categories (emergency, retirement, specific goals).
3. Recommend practical automation techniques.

Consider:
- Risk factors based on dependants and stability.
- Balancing immediate needs with long-term financial health.
- Areas of potential savings identified in the budget analysis.

Respond strictly using the SavingsStrategy schema.""",
    output_schema=SavingsStrategy,
    output_key="savings_strategy",
    before_model_callback=_make_state_injector(["budget_analysis"]),
)


debt_agent = LlmAgent(
    name="DebtReductionAgent",
    model="gemini-3.5-flash",
    description="Creates optimized debt payoff plans (avalanche & snowball).",
    instruction="""You are a Debt Reduction Agent. Read FINANCIAL DATA, BUDGET_ANALYSIS, and SAVINGS_STRATEGY above when available.

Your tasks:
1. Compute total debt and list each debt by name, amount, interest rate, min payment.
2. Build BOTH avalanche (highest interest first) and snowball (smallest balance first) payoff plans, including:
   - total_interest paid
   - months_to_payoff
   - monthly_payment recommended
3. Provide 2-4 actionable recommendations to accelerate payoff (consolidation, refinancing, etc.).

Consider:
- Cash-flow constraints from the budget analysis.
- Emergency-fund and savings goals from the savings strategy.
- Psychological factors (quick wins vs mathematical optimization).

If the user has no debts, return total_debt=0, empty debts list, and zeroed payoff plans.

Respond strictly using the DebtReduction schema.""",
    output_schema=DebtReduction,
    output_key="debt_reduction",
    before_model_callback=_make_state_injector(["budget_analysis", "savings_strategy"]),
)


full_analysis_pipeline = SequentialAgent(
    name="FullAnalysisPipeline",
    description="Runs Budget Analysis → Savings Strategy → Debt Reduction in sequence.",
    sub_agents=[budget_agent, savings_agent, debt_agent],
)


# ---------- Coach tools ----------


CANONICAL_EXPENSE_CATEGORIES = [
    "Housing",
    "Utilities",
    "Food",
    "Transportation",
    "Healthcare",
    "Entertainment",
    "Personal",
    "Savings",
    "Other",
]

# Lowercase alias → canonical category. Keep this lean and obvious; unknown
# inputs fall through to "Other".
_EXPENSE_ALIASES: Dict[str, str] = {
    "housing": "Housing",
    "rent": "Housing",
    "mortgage": "Housing",
    "home": "Housing",
    "utilities": "Utilities",
    "utility": "Utilities",
    "electric": "Utilities",
    "electricity": "Utilities",
    "internet": "Utilities",
    "phone": "Utilities",
    "water": "Utilities",
    "gas_bill": "Utilities",
    "food": "Food",
    "groceries": "Food",
    "grocery": "Food",
    "dining": "Food",
    "restaurants": "Food",
    "transportation": "Transportation",
    "transport": "Transportation",
    "car": "Transportation",
    "gas": "Transportation",
    "fuel": "Transportation",
    "transit": "Transportation",
    "healthcare": "Healthcare",
    "health": "Healthcare",
    "medical": "Healthcare",
    "insurance": "Healthcare",
    "entertainment": "Entertainment",
    "fun": "Entertainment",
    "subscriptions": "Entertainment",
    "streaming": "Entertainment",
    "personal": "Personal",
    "clothing": "Personal",
    "personal_care": "Personal",
    "savings": "Savings",
    "investing": "Savings",
    "retirement": "Savings",
    "other": "Other",
    "misc": "Other",
    "miscellaneous": "Other",
}


def _normalize_category(key: str) -> str:
    """Map a free-form expense key to a canonical category label."""
    if not key:
        return "Other"
    cleaned = key.strip().replace("-", "_").replace(" ", "_").lower()
    if cleaned in _EXPENSE_ALIASES:
        return _EXPENSE_ALIASES[cleaned]
    # If the user passed an already-canonical label in any case, accept it.
    for canonical in CANONICAL_EXPENSE_CATEGORIES:
        if cleaned == canonical.lower():
            return canonical
    return "Other"


def _ensure_financial_data(tool_context: ToolContext) -> Dict[str, Any]:
    fd = tool_context.state.get("financial_data")
    if not isinstance(fd, dict):
        fd = dict(DEFAULT_FINANCIAL_DATA)
    fd.setdefault("monthly_income", 0)
    fd.setdefault("dependants", 0)
    if not isinstance(fd.get("manual_expenses"), dict):
        fd["manual_expenses"] = {}
    if not isinstance(fd.get("debts"), list):
        fd["debts"] = []
    return fd


def update_financial_data(
    tool_context: ToolContext,
    monthly_income: Optional[float] = None,
    dependants: Optional[int] = None,
    expenses_patch: Optional[Dict[str, float]] = None,
    add_debts: Optional[List[Dict[str, Any]]] = None,
    remove_debt_names: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Patch the user's financial profile in shared state. All arguments are optional and applied with append/merge semantics.

    Args:
        monthly_income: New monthly take-home income in USD. Replaces the existing value.
        dependants: New number of dependants. Replaces the existing value.
        expenses_patch: Partial map of expense category to monthly USD amount. Merges into manual_expenses (existing keys not in the patch are preserved). To zero a category, pass it as 0.
        add_debts: List of debts to APPEND to the existing debts list. Each item must include name, amount, interest_rate, and optionally min_payment.
        remove_debt_names: List of debt names to remove from the debts list (case-insensitive match).

    Returns:
        A summary describing what changed and the updated financial_data.
    """
    fd = _ensure_financial_data(tool_context)
    changes: List[str] = []

    if monthly_income is not None:
        fd["monthly_income"] = float(monthly_income)
        changes.append(f"income → ${float(monthly_income):,.0f}")

    if dependants is not None:
        fd["dependants"] = int(dependants)
        changes.append(f"dependants → {int(dependants)}")

    if expenses_patch:
        merged = dict(fd.get("manual_expenses") or {})
        normalized: Dict[str, float] = {}
        for k, v in expenses_patch.items():
            canonical = _normalize_category(k)
            normalized[canonical] = normalized.get(canonical, 0.0) + float(v)
        for k, v in normalized.items():
            merged[k] = float(v)
        fd["manual_expenses"] = merged
        patch_pretty = ", ".join(f"{k}=${v:,.0f}" for k, v in normalized.items())
        changes.append(f"expenses {{{patch_pretty}}}")

    if add_debts:
        existing = list(fd.get("debts") or [])
        for d in add_debts:
            existing.append(
                {
                    "name": str(d.get("name", "Debt")),
                    "amount": float(d.get("amount", 0) or 0),
                    "interest_rate": float(d.get("interest_rate", 0) or 0),
                    "min_payment": (
                        float(d["min_payment"]) if d.get("min_payment") is not None else None
                    ),
                }
            )
        fd["debts"] = existing
        added_pretty = ", ".join(
            f"{d.get('name', 'Debt')} (${float(d.get('amount', 0) or 0):,.0f} @ {float(d.get('interest_rate', 0) or 0)}%)"
            for d in add_debts
        )
        changes.append(f"+{len(add_debts)} debt(s): {added_pretty}")

    if remove_debt_names:
        targets = {n.strip().lower() for n in remove_debt_names if n}
        before = len(fd.get("debts") or [])
        fd["debts"] = [
            d
            for d in (fd.get("debts") or [])
            if str(d.get("name", "")).strip().lower() not in targets
        ]
        removed = before - len(fd["debts"])
        if removed:
            changes.append(f"-{removed} debt(s) removed: {', '.join(remove_debt_names)}")

    tool_context.state["financial_data"] = fd

    return {
        "status": "updated",
        "changes": changes or ["no-op"],
        "financial_data": fd,
    }


# Wrap each phase as an AgentTool. skip_summarization=True keeps the coach from
# re-narrating the full JSON (which already lands in shared state via output_key
# and renders as a card in the UI).
run_budget_analysis = AgentTool(agent=budget_agent, skip_summarization=True)
run_savings_strategy = AgentTool(agent=savings_agent, skip_summarization=True)
run_debt_reduction = AgentTool(agent=debt_agent, skip_summarization=True)
run_full_analysis = AgentTool(agent=full_analysis_pipeline, skip_summarization=True)


# ---------- Coach (top-level router) ----------


COACH_INSTRUCTION = """You are a friendly, concise AI Financial Coach. You collaborate with the user via chat while their structured financial profile and analysis cards live on a side panel.

You have these tools:
- update_financial_data — patch the user's profile (income, dependants, expenses, debts). Uses APPEND semantics for debts.
- BudgetAnalysisAgent — produce a fresh budget breakdown card.
- SavingsStrategyAgent — produce a fresh savings strategy card.
- DebtReductionAgent — produce a fresh debt-payoff plan card.
- FullAnalysisPipeline — run all three in sequence.

When calling update_financial_data with expenses_patch, ONLY use these canonical category keys (the backend will also normalize aliases like "rent"→"Housing", but prefer canonicals):
Housing, Utilities, Food, Transportation, Healthcare, Entertainment, Personal, Savings, Other.
Map terms intelligently: rent/mortgage → Housing; groceries/dining → Food; gas/car/transit → Transportation; subscriptions/streaming → Entertainment; medical/insurance → Healthcare; clothing/personal_care → Personal; investing/retirement → Savings.

Routing rules — pick the SMALLEST tool that satisfies the request:
1. If the user states a fact about their finances (e.g. "my income is $8k", "my rent is $2400", "I just paid off the car loan", "add a $500 student loan at 5%"), call update_financial_data with only the fields they mentioned. To add a new debt, use add_debts (which appends). To remove a paid-off debt, use remove_debt_names. Never overwrite the entire profile.
2. If the user asks for a specific report ("analyze my budget", "what should I save?", "plan my debt payoff"), call the matching single tool.
3. If the user asks for a full review ("analyze my finances", "give me the full picture", "run a full review"), call FullAnalysisPipeline.
4. If the user asks a general question or chats, just answer in plain text — DO NOT call a tool.
5. Never call multiple tools in the same turn unless explicitly asked. Never call an analysis tool to confirm a profile update.

After a tool call:
- For update_financial_data: reply in 1 short sentence confirming what changed and (if relevant) suggest a next step.
- For analysis tools: the card renders automatically. Reply in 1-2 sentences highlighting the most important takeaway. Do NOT restate the full JSON.

Style: warm, plain language, no jargon, no markdown headers in chat replies."""


coach_agent = LlmAgent(
    name="FinanceCoachAgent",
    model="gemini-3.5-flash",
    description="Routes user requests to profile updates or specialist analysis agents.",
    instruction=COACH_INSTRUCTION,
    tools=[
        update_financial_data,
        run_budget_analysis,
        run_savings_strategy,
        run_debt_reduction,
        run_full_analysis,
    ],
    before_agent_callback=on_before_agent,
)


# ---------- ADK / FastAPI wiring ----------


adk_finance_agent = ADKAgent(
    adk_agent=coach_agent,
    user_id="demo_user",
    session_timeout_seconds=3600,
    use_in_memory_services=True,
)

app = FastAPI(title="AI Financial Coach Agent")
add_adk_fastapi_endpoint(app, adk_finance_agent, path="/")


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import os

    import uvicorn

    if not os.getenv("GOOGLE_API_KEY"):
        print("⚠️  Warning: GOOGLE_API_KEY environment variable not set!")
        print("   Set it with: export GOOGLE_API_KEY='your-key-here'")
        print("   Get a key from: https://makersuite.google.com/app/apikey")
        print()

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
