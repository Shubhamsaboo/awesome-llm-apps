from __future__ import annotations

import asyncio
import inspect
import os
import uuid

from google.genai import types


APP_NAME = "earnings_call_analyst_agent"
USER_ID = "local_demo_user"


async def run_adk_agent_text_async(agent: object, prompt: str, state: dict | None = None) -> str:
    """Run an ADK agent once and return the final text it emits."""
    message = types.Content(role="user", parts=[types.Part(text=prompt)])
    return await run_adk_agent_content_async(agent, message, state=state)


async def run_adk_agent_content_async(
    agent: object, message: types.Content, state: dict | None = None
) -> str:
    """Run an ADK agent once with a prepared Content payload."""
    _ensure_google_api_key_alias()
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService

    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=uuid.uuid4().hex,
        state=state or {},
    )
    runner = Runner(
        app_name=APP_NAME,
        agent=agent,
        session_service=session_service,
    )
    final_text = ""
    try:
        async for event in runner.run_async(
            user_id=session.user_id,
            session_id=session.id,
            new_message=message,
        ):
            if not event.content or not event.content.parts:
                continue
            text = "".join(part.text or "" for part in event.content.parts)
            if text:
                final_text = text
            if event.is_final_response() and text:
                final_text = text
    finally:
        close = getattr(runner, "close", None)
        if close:
            result = close()
            if inspect.isawaitable(result):
                await result
    return final_text


def run_adk_agent_text(agent: object, prompt: str, state: dict | None = None) -> str:
    return asyncio.run(run_adk_agent_text_async(agent, prompt, state=state))


def run_adk_agent_content(
    agent: object, message: types.Content, state: dict | None = None
) -> str:
    return asyncio.run(run_adk_agent_content_async(agent, message, state=state))


def _ensure_google_api_key_alias() -> None:
    if os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
        os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]
