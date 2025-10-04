import json
import os
from datetime import datetime
from typing import Any, Dict, Optional

import streamlit as st
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.e2b import E2BTools
from agno.tools.firecrawl import FirecrawlTools

st.set_page_config(
    page_title="Life Insurance Coverage Advisor",
    page_icon="🛡️",
    layout="centered",
)

st.title("🛡️ Life Insurance Coverage Advisor")
st.caption(
    "Prototype Streamlit app powered by Agno Agents, OpenAI GPT-5, E2B sandboxed code execution, and Firecrawl search."
)

# -----------------------------------------------------------------------------
# Sidebar configuration for API keys
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("API Keys")
    st.write("All keys stay local in your browser session.")
    openai_api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        key="openai_api_key",
        help="Create one at https://platform.openai.com/api-keys",
    )
    firecrawl_api_key = st.text_input(
        "Firecrawl API Key",
        type="password",
        key="firecrawl_api_key",
        help="Create one at https://www.firecrawl.dev/app/api-keys",
    )
    e2b_api_key = st.text_input(
        "E2B API Key",
        type="password",
        key="e2b_api_key",
        help="Create one at https://e2b.dev",
    )
    st.markdown("---")
    st.caption(
        "The agent uses E2B for deterministic coverage math and Firecrawl for fresh term-life product research."
    )

# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------

def safe_number(value: Any) -> float:
    """Best-effort conversion to float for agent outputs."""
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        if isinstance(value, str):
            stripped = value
            for token in [",", "$", "€", "£", "₹", "C$", "A$"]:
                stripped = stripped.replace(token, "")
            stripped = stripped.strip()
            try:
                return float(stripped)
            except ValueError:
                return 0.0
        return 0.0


def format_currency(amount: float, currency_code: str) -> str:
    symbol_map = {
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
        "CAD": "C$",
        "AUD": "A$",
        "INR": "₹",
    }
    code = (currency_code or "USD").upper()
    symbol = symbol_map.get(code, "")
    formatted = f"{amount:,.0f}"
    return f"{symbol}{formatted}" if symbol else f"{formatted} {code}"


def extract_json(payload: str) -> Optional[Dict[str, Any]]:
    if not payload:
        return None

    content = payload.strip()
    if content.startswith("```"):
        lines = content.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        content = "\n".join(lines).strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return None


def parse_percentage(value: Any, fallback: float = 0.02) -> float:
    """Convert percentage-like values to decimal form (e.g., "2%" -> 0.02)."""
    if value is None:
        return fallback
    if isinstance(value, (int, float)):
        # assume already decimal if less than 1, otherwise treat as percentage value
        return float(value) if value < 1 else float(value) / 100
    if isinstance(value, str):
        cleaned = value.strip().replace("%", "")
        try:
            numeric = float(cleaned)
            return numeric if numeric < 1 else numeric / 100
        except ValueError:
            return fallback
    return fallback


def compute_local_breakdown(profile: Dict[str, Any], real_rate: float) -> Dict[str, float]:
    """Replicate the coverage math locally so we can show it to the user."""
    income = safe_number(profile.get("annual_income"))
    years = max(0, int(profile.get("income_replacement_years", 0) or 0))
    total_debt = safe_number(profile.get("total_debt"))
    savings = safe_number(profile.get("available_savings"))
    existing_cover = safe_number(profile.get("existing_life_insurance"))

    if real_rate <= 0:
        discounted_income = income * years
        annuity_factor = years
    else:
        annuity_factor = (1 - (1 + real_rate) ** (-years)) / real_rate if years else 0
        discounted_income = income * annuity_factor

    assets_offset = savings + existing_cover
    recommended = max(0.0, discounted_income + total_debt - assets_offset)

    return {
        "income": income,
        "years": years,
        "real_rate": real_rate,
        "annuity_factor": annuity_factor,
        "discounted_income": discounted_income,
        "debt": total_debt,
        "assets_offset": -assets_offset,
        "recommended": recommended,
    }


@st.cache_resource(show_spinner=False)
def get_agent(openai_key: str, firecrawl_key: str, e2b_key: str) -> Optional[Agent]:
    if not (openai_key and firecrawl_key and e2b_key):
        return None

    os.environ["OPENAI_API_KEY"] = openai_key
    os.environ["FIRECRAWL_API_KEY"] = firecrawl_key
    os.environ["E2B_API_KEY"] = e2b_key

    return Agent(
        name="Life Insurance Advisor",
        model=OpenAIChat(
            id="gpt-5-mini-2025-08-07",
            api_key=openai_key,
        ),
        tools=[
            E2BTools(timeout=180),
            FirecrawlTools(
                api_key=firecrawl_key,
                enable_search=True,
                enable_crawl=True,
                enable_scrape=False,
                search_params={"limit": 5, "lang": "en"},
            ),
        ],
        instructions=[
            "You provide conservative life insurance guidance. Your workflow is strictly:",
            "1. ALWAYS call `run_python_code` from the E2B tools to compute the coverage recommendation using the provided client JSON.",
            "   - Treat missing numeric values as 0.",
            "   - Use a default real discount rate of 2% when discounting income replacement cash flows.",
            "   - Compute: discounted_income = annual_income * ((1 - (1 + r)**(-income_replacement_years)) / r).",
            "   - Recommended coverage = max(0, discounted_income + total_debt - savings - existing_life_insurance).",
            "   - Print a JSON with keys: coverage_amount, coverage_currency, breakdown, assumptions.",
            "2. Use Firecrawl `search` followed by optional `scrape_website` calls to gather up-to-date term life insurance options for the client's region.",
            "3. Respond ONLY with JSON containing the following top-level keys: coverage_amount, coverage_currency, breakdown, assumptions, recommendations, research_notes, timestamp.",
            "   - `coverage_amount`: integer of total recommended coverage.",
            "   - `coverage_currency`: 3-letter currency code.",
            "   - `breakdown`: include income_replacement, debt_obligations, assets_offset, methodology.",
            "   - `assumptions`: include income_replacement_years, real_discount_rate, additional_notes.",
            "   - `recommendations`: list of up to three objects (name, summary, link, source).",
            "   - `research_notes`: brief disclaimer + recency of sources.",
            "   - `timestamp`: ISO 8601 date-time string.",
            "Do not include markdown, commentary, or tool call traces in the final JSON output.",
        ],
        markdown=False,
    )


# -----------------------------------------------------------------------------
# User input form
# -----------------------------------------------------------------------------
st.subheader("Tell us about yourself")

with st.form("coverage_form"):
    col1, col2 = st.columns(2)
    with col1:
        age = st.number_input("Age", min_value=18, max_value=85, value=35)
        annual_income = st.number_input(
            "Annual Income",
            min_value=0.0,
            value=85000.0,
            step=1000.0,
        )
        dependents = st.number_input(
            "Dependents",
            min_value=0,
            max_value=10,
            value=2,
            step=1,
        )
        location = st.text_input(
            "Country / State",
            value="United States",
            help="Used to localize recommended insurers.",
        )
    with col2:
        total_debt = st.number_input(
            "Total Outstanding Debt (incl. mortgage)",
            min_value=0.0,
            value=200000.0,
            step=5000.0,
        )
        savings = st.number_input(
            "Savings & Investments available to dependents",
            min_value=0.0,
            value=50000.0,
            step=5000.0,
        )
        existing_cover = st.number_input(
            "Existing Life Insurance",
            min_value=0.0,
            value=100000.0,
            step=5000.0,
        )
        currency = st.selectbox(
            "Currency",
            options=["USD", "CAD", "EUR", "GBP", "AUD", "INR"],
            index=0,
        )

    income_replacement_years = st.selectbox(
        "Income Replacement Horizon",
        options=[5, 10, 15],
        index=1,
        help="Number of years your income should be replaced for dependents.",
    )

    submitted = st.form_submit_button("Generate Coverage & Options")


def build_client_profile() -> Dict[str, Any]:
    return {
        "age": age,
        "annual_income": annual_income,
        "dependents": dependents,
        "location": location,
        "total_debt": total_debt,
        "available_savings": savings,
        "existing_life_insurance": existing_cover,
        "income_replacement_years": income_replacement_years,
        "currency": currency,
        "request_timestamp": datetime.utcnow().isoformat(),
    }


def render_recommendations(result: Dict[str, Any], profile: Dict[str, Any]) -> None:
    coverage_currency = result.get("coverage_currency", currency)
    coverage_amount = safe_number(result.get("coverage_amount", 0))

    st.subheader("Recommended Coverage")
    st.metric(
        label="Total Coverage Needed",
        value=format_currency(coverage_amount, coverage_currency),
    )

    assumptions = result.get("assumptions", {})
    real_rate = parse_percentage(assumptions.get("real_discount_rate", "2%"))
    local_breakdown = compute_local_breakdown(profile, real_rate)

    st.subheader("Calculation Inputs")
    st.table(
        {
            "Input": [
                "Annual income",
                "Income replacement horizon",
                "Total debt",
                "Liquid assets",
                "Existing life cover",
                "Real discount rate",
            ],
            "Value": [
                format_currency(local_breakdown["income"], coverage_currency),
                f"{local_breakdown['years']} years",
                format_currency(local_breakdown["debt"], coverage_currency),
                format_currency(safe_number(profile.get("available_savings")), coverage_currency),
                format_currency(safe_number(profile.get("existing_life_insurance")), coverage_currency),
                f"{real_rate * 100:.2f}%",
            ],
        }
    )

    st.subheader("Step-by-step Coverage Math")
    step_rows = [
        ("Annuity factor", f"{local_breakdown['annuity_factor']:.3f}"),
        ("Discounted income replacement", format_currency(local_breakdown["discounted_income"], coverage_currency)),
        ("+ Outstanding debt", format_currency(local_breakdown["debt"], coverage_currency)),
        ("- Assets & existing cover", format_currency(local_breakdown["assets_offset"], coverage_currency)),
        ("= Formula estimate", format_currency(local_breakdown["recommended"], coverage_currency)),
    ]
    step_rows.append(("= Agent recommendation", format_currency(coverage_amount, coverage_currency)))

    st.table({"Step": [s for s, _ in step_rows], "Amount": [a for _, a in step_rows]})

    breakdown = result.get("breakdown", {})
    with st.expander("How this number was calculated", expanded=True):
        st.markdown(
            f"- Income replacement value: {format_currency(safe_number(breakdown.get('income_replacement')), coverage_currency)}"
        )
        st.markdown(
            f"- Debt obligations: {format_currency(safe_number(breakdown.get('debt_obligations')), coverage_currency)}"
        )
        assets_offset = safe_number(breakdown.get("assets_offset"))
        st.markdown(
            f"- Assets & existing cover offset: {format_currency(assets_offset, coverage_currency)}"
        )
        methodology = breakdown.get("methodology")
        if methodology:
            st.caption(methodology)

    recommendations = result.get("recommendations", [])
    if recommendations:
        st.subheader("Top Term Life Options")
        for idx, option in enumerate(recommendations, start=1):
            with st.container():
                name = option.get("name", "Unnamed Product")
                summary = option.get("summary", "No summary provided.")
                st.markdown(f"**{idx}. {name}** — {summary}")
                link = option.get("link")
                if link:
                    st.markdown(f"[View details]({link})")
                source = option.get("source")
                if source:
                    st.caption(f"Source: {source}")
                st.markdown("---")

    with st.expander("Model assumptions"):
        st.write(
            {
                "Income replacement years": assumptions.get(
                    "income_replacement_years", income_replacement_years
                ),
                "Real discount rate": assumptions.get("real_discount_rate", "2%"),
                "Notes": assumptions.get("additional_notes", ""),
            }
        )

    if result.get("research_notes"):
        st.caption(result["research_notes"])
    if result.get("timestamp"):
        st.caption(f"Generated: {result['timestamp']}")

    with st.expander("Agent response JSON"):
        st.json(result)


if submitted:
    if not all([openai_api_key, firecrawl_api_key, e2b_api_key]):
        st.error("Please configure OpenAI, Firecrawl, and E2B API keys in the sidebar.")
        st.stop()

    advisor_agent = get_agent(openai_api_key, firecrawl_api_key, e2b_api_key)
    if not advisor_agent:
        st.error("Unable to initialize the advisor. Double-check API keys.")
        st.stop()

    client_profile = build_client_profile()
    user_prompt = (
        "You will receive a JSON object describing the client's profile. Follow your workflow instructions to calculate coverage and surface suitable products.\n"
        f"Client profile JSON: {json.dumps(client_profile)}"
    )

    with st.spinner("Consulting advisor agent..."):
        response = advisor_agent.run(user_prompt, stream=False)

    parsed = extract_json(response.content if response else "")
    if not parsed:
        st.error("The agent returned an unexpected response. Enable debug below to inspect raw output.")
        with st.expander("Raw agent output"):
            st.write(response.content if response else "<empty>")
    else:
        render_recommendations(parsed, client_profile)
        with st.expander("Agent debug"):
            st.write(response.content)

st.divider()
st.caption(
    "This prototype is for educational use only and does not provide licensed financial advice. "
    "Verify all recommendations with a qualified professional and the insurers listed."
)
