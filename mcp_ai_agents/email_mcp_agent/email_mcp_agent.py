import asyncio
import os

import streamlit as st
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.mcp import MCPTools
from mcp import StdioServerParameters

st.set_page_config(page_title="📧 Email MCP Agent", page_icon="📧", layout="wide")

st.markdown("# 📧 Email MCP Agent")
st.markdown(
    "Give your AI agent its own email address. This app is built for **real use cases**: "
    "support inbox triage and reply-drafting, task coordination via email threads, or "
    "stakeholder updates. Use natural language with [NornWeave](https://github.com/DataCovey/nornweave) "
    "and the Model Context Protocol."
)

# --- Sidebar: credentials and scenario walkthrough ---
with st.sidebar:
    st.header("🔑 Configuration")

    openai_key = st.text_input(
        "OpenAI API Key",
        type="password",
        help="Required for the AI agent. Get one at platform.openai.com/api-keys",
    )
    if openai_key:
        os.environ["OPENAI_API_KEY"] = openai_key

    api_url = st.text_input(
        "NornWeave API URL",
        value="http://localhost:8000",
        help="URL of your running NornWeave server",
    )

    api_key = st.text_input(
        "NornWeave API Key",
        type="password",
        help="Optional API key if your NornWeave server requires auth",
    )

    st.markdown("---")
    st.markdown("### Support inbox walkthrough")
    st.markdown("Copy these prompts in order to follow the tutorial from the README.")

    st.markdown("**1. Create inbox**")
    st.code(
        'Create an inbox named "Support Bot" with username "support". '
        "Tell me the inbox id and email address.",
        language=None,
    )

    st.markdown("**2. Seed test tickets**")
    st.code(
        "Send three emails to support@[domain]:\n"
        '1. From alice@example.com, subject "Can\'t log in"\n'
        '2. From bob@example.com, subject "Billing question"\n'
        '3. From carol@example.com, subject "Bug: dashboard blank"',
        language=None,
    )

    st.markdown("**3. Triage & draft**")
    st.code(
        "In inbox [id], list recent messages. Pick the login thread,\n"
        "show the conversation, and draft a professional reply.\n"
        "Don't send — just show the draft.",
        language=None,
    )

    st.markdown("**4. Search by topic**")
    st.code(
        'Search inbox [id] for "billing". Give me a one-line\n'
        "summary and thread id for each match.",
        language=None,
    )

    st.markdown("**5. Attachments**")
    st.code(
        "List attachments in thread [id]. Download the first\n" "and tell me what it contains.",
        language=None,
    )

    st.markdown("**6. Escalate**")
    st.code(
        "List the 10 most recent threads in inbox [id].\n"
        'Classify each as "auto-reply" or "needs human".',
        language=None,
    )

    st.markdown("**7. Batch-process**")
    st.code(
        "Find all threads where the last message is from the\n"
        "customer. Draft a reply for each; show me all drafts.",
        language=None,
    )

    st.markdown("**8. Wait for reply**")
    st.code(
        "Send a follow-up in thread [id] asking if they need\n"
        "anything else, then wait up to 2 min for a reply.",
        language=None,
    )

# --- Main area ---
query = st.text_area(
    "What would you like to do?",
    placeholder=(
        "e.g., Create an inbox named 'Support Bot' with username 'support' "
        "and tell me the inbox id"
    ),
)

# Agent instructions: support/triage style but general enough for other scenarios
AGENT_INSTRUCTIONS = """\
You are an email assistant powered by NornWeave. You help with real-world email workflows:

**Support inbox (primary scenario):**
- Create inboxes for support agents
- List and search messages to triage by topic
- Draft replies for human approval — always show the draft first, never send unless asked
- Handle attachments (list, download, summarize, send)
- Classify threads as "can auto-reply" vs "needs human review" when asked to escalate
- Batch-process multiple threads at once
- Wait for customer replies in a synchronous flow

**Other workflows:**
- Task coordination: parse emails into tasks, reply with summaries
- Stakeholder updates: digest messages and compose summary emails

Always confirm what you did after each action. Use markdown formatting for readability.\
"""


async def run_email_agent(message: str) -> str:
    """Connect to NornWeave MCP server and run the agent."""
    env = {**os.environ, "NORNWEAVE_API_URL": api_url}
    if api_key:
        env["NORNWEAVE_API_KEY"] = api_key

    server_params = StdioServerParameters(
        command="nornweave",
        args=["mcp"],
        env=env,
    )

    async with MCPTools(server_params=server_params) as mcp_tools:
        agent = Agent(
            model=OpenAIChat(id="gpt-4o"),
            tools=[mcp_tools],
            instructions=AGENT_INSTRUCTIONS,
            markdown=True,
        )

        response = await asyncio.wait_for(agent.arun(message), timeout=120.0)
        return response.content


if st.button("🚀 Run", type="primary", use_container_width=True):
    if not openai_key:
        st.error("Please enter your OpenAI API key in the sidebar.")
    elif not query:
        st.error("Please enter a query.")
    else:
        with st.spinner("Working on it..."):
            try:
                result = asyncio.run(run_email_agent(query))
                st.markdown("### Result")
                st.markdown(result)
            except asyncio.TimeoutError:
                st.error("Request timed out after 120 seconds.")
            except Exception as e:
                st.error(f"Error: {e}")

# --- How it works (shown when idle) ---
if "result" not in dir():
    st.markdown(
        """
---

### Quick start

1. **Run NornWeave** — `pip install nornweave[mcp]`, create a `.env` with `EMAIL_DOMAIN=mail.yourdomain.com`, then `nornweave api`.
2. **Follow the sidebar** — The prompts walk you through a full support-agent loop: create inbox → seed tickets → triage → search → attachments → escalate → batch-process → wait for reply.
3. **See the README** for the complete step-by-step tutorial with explanations.
"""
    )
