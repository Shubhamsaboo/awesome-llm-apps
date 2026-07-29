import asyncio
import os

import streamlit as st
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from mem0 import Memory

APP_NAME = "adk_customer_support"
MODEL = "gemini-2.5-flash"

# Mem0 config: Gemini for both the LLM (fact extraction) and the embedder,
# plus an on-disk Qdrant collection — no Docker/Qdrant server, no OpenAI
# key. Both "llm" and "embedder" read GOOGLE_API_KEY from the environment
# once it's set below. Gemini's embedding model outputs 768-dim vectors, so
# embedder.embedding_dims and vector_store.embedding_model_dims must match.
MEM0_CONFIG = {
    "llm": {
        "provider": "gemini",
        "config": {"model": MODEL, "temperature": 0.2},
    },
    "embedder": {
        "provider": "gemini",
        "config": {"model": "models/gemini-embedding-001", "embedding_dims": 768},
    },
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "collection_name": "adk_customer_support",
            "path": "./qdrant_storage",
            "embedding_model_dims": 768,
            "on_disk": True,
        },
    },
}

# --- Mock backend data the tools read from. Swap for real API/DB calls. ---
MOCK_INVOICES = {
    "INV-1001": {"amount": "$49.00", "status": "Paid", "date": "2026-06-01"},
    "INV-1002": {"amount": "$49.00", "status": "Overdue", "date": "2026-07-01"},
}

MOCK_ACCOUNTS = {
    "demo@example.com": {"plan": "Pro", "renewal_date": "2026-09-15"},
}


def look_up_invoice(invoice_id: str) -> dict:
    """Looks up the amount, status and date for a specific invoice ID (e.g. INV-1001)."""
    invoice = MOCK_INVOICES.get(invoice_id.upper())
    if invoice:
        return {"status": "success", "invoice": invoice}
    return {"status": "error", "message": f"No invoice found with ID {invoice_id}."}


def reset_password(account_email: str) -> dict:
    """Triggers a password reset email for the given account email."""
    return {"status": "success", "message": f"Password reset link sent to {account_email}."}


def check_subscription_status(account_email: str) -> dict:
    """Checks the current subscription plan and renewal date for an account email."""
    account = MOCK_ACCOUNTS.get(account_email.lower())
    if account:
        return {"status": "success", "account": account}
    return {"status": "error", "message": f"No account found for {account_email}."}


def build_triage_agent() -> LlmAgent:
    """Root agent + 3 specialists. ADK routes to a sub-agent based on its description."""
    billing_agent = LlmAgent(
        name="billing_agent",
        model=MODEL,
        description="Handles billing questions, invoice lookups, and payment disputes.",
        instruction=(
            "You help customers with billing issues. Use the look_up_invoice tool "
            "when the customer references an invoice ID (e.g. INV-1001). Be concise "
            "and empathetic, and clearly state the resolution once you have one."
        ),
        tools=[look_up_invoice],
    )

    technical_agent = LlmAgent(
        name="technical_agent",
        model=MODEL,
        description="Handles technical issues such as login failures and password resets.",
        instruction=(
            "You help customers with technical issues. Use the reset_password tool "
            "when the customer needs help logging in or resetting a password. Use the "
            "'Customer account email' given in the message context as the account_email "
            "argument -- do not ask the customer to repeat an email you already have."
        ),
        tools=[reset_password],
    )

    account_agent = LlmAgent(
        name="account_agent",
        model=MODEL,
        description="Handles questions about subscription plans, renewal dates, and account status.",
        instruction=(
            "You help customers understand their subscription and account status. "
            "Use the check_subscription_status tool to look up plan details, passing "
            "the 'Customer account email' given in the message context as account_email "
            "-- do not ask the customer to repeat an email you already have."
        ),
        tools=[check_subscription_status],
    )

    triage_agent = LlmAgent(
        name="triage_agent",
        model=MODEL,
        description="Routes customer support requests to the right specialist.",
        instruction=(
            "You are the first point of contact for customer support. Read the "
            "customer's message, including any 'Relevant past information' block "
            "included with it, and decide whether this is a billing, technical, or "
            "account question. Delegate to the matching sub-agent. If it's unclear, "
            "ask a clarifying question yourself instead of guessing."
        ),
        sub_agents=[billing_agent, technical_agent, account_agent],
    )
    return triage_agent


async def ensure_session(session_service, user_id, session_id):
    await session_service.create_session(app_name=APP_NAME, user_id=user_id, session_id=session_id)


async def call_agent(runner, user_id, session_id, message_text) -> str:
    content = types.Content(role="user", parts=[types.Part(text=message_text)])
    final_text = ""
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        if event.is_final_response() and event.content and event.content.parts:
            final_text = event.content.parts[0].text
    return final_text


def run_agent_sync(runner, user_id, session_id, message_text) -> str:
    return asyncio.run(call_agent(runner, user_id, session_id, message_text))


@st.cache_resource
def get_memory() -> Memory:
    # Embedded/on-disk Qdrant only allows one open client per storage path
    # per process (it takes a file lock) -- cache_resource makes this a
    # single instance shared by every browser session on this server,
    # instead of one per session, which would crash the 2nd concurrent
    # user with "Storage folder ... already accessed by another instance".
    return Memory.from_config(MEM0_CONFIG)


@st.cache_resource
def get_runner():
    triage_agent = build_triage_agent()
    session_service = InMemorySessionService()
    runner = Runner(agent=triage_agent, app_name=APP_NAME, session_service=session_service)
    return runner, session_service


def format_memories(memories: dict) -> str:
    results = (memories or {}).get("results") or []
    if not results:
        return ""
    lines = "\n".join(f"- {m['memory']}" for m in results if "memory" in m)
    return f"Relevant past information:\n{lines}\n" if lines else ""


# --- Streamlit app ---
st.title("🎧 ADK Multi-Agent Customer Support (with Memory)")
st.caption(
    "A triage agent delegates to billing / technical / account specialists "
    "(Google ADK), while Mem0 + Qdrant remember each customer across sessions."
)

google_api_key = st.text_input(
    "Enter Google API Key (for Gemini)",
    type="password",
    value=os.getenv("GOOGLE_API_KEY", ""),
)

if google_api_key:
    os.environ["GOOGLE_API_KEY"] = google_api_key

    memory = get_memory()
    runner, session_service = get_runner()

    st.sidebar.title("Customer")
    previous_user_id = st.session_state.get("previous_user_id")
    user_id = st.sidebar.text_input("Customer email", value="demo@example.com")

    if user_id != previous_user_id:
        st.session_state.messages = []
        st.session_state.previous_user_id = user_id
        st.session_state.pop("session_ready", None)

    if st.sidebar.button("View customer memory"):
        memories = memory.get_all(filters={"user_id": user_id})
        results = (memories or {}).get("results") or []
        if results:
            for mem in results:
                st.sidebar.write(f"- {mem['memory']}")
        else:
            st.sidebar.info("No memory on file for this customer yet.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("How can we help you today?")

    if prompt and user_id:
        session_id = f"session-{user_id}"
        if not st.session_state.get("session_ready"):
            asyncio.run(ensure_session(session_service, user_id, session_id))
            st.session_state.session_ready = True

        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Long-term memory: pull what Mem0 knows about this customer before routing.
        relevant_memories = memory.search(query=prompt, filters={"user_id": user_id}, top_k=5)
        context = format_memories(relevant_memories)
        full_message = f"Customer account email: {user_id}\n{context}\nCustomer says: {prompt}"

        with st.chat_message("assistant"):
            with st.spinner("Routing to the right specialist..."):
                answer = run_agent_sync(runner, user_id, session_id, full_message)
            st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})

        # Write this exchange back to long-term memory for future sessions.
        memory.add(prompt, user_id=user_id, metadata={"role": "user"})
        memory.add(answer, user_id=user_id, metadata={"role": "assistant"})
    elif not user_id:
        st.error("Please enter a customer email to start the chat.")
else:
    st.warning("Please enter your Google API key to continue.")
