#!/usr/bin/env python3
"""
Planner Agent (stable workspace API)
- Listens:  #general
- Sends:    #ideas
Creates a structured plan from user questions.
"""

import asyncio
import os
import uuid
from collections import deque
from typing import Optional

from openagents.agents.worker_agent import WorkerAgent, EventContext, ChannelMessageContext
from openagents.models.agent_config import AgentConfig


def _safe_bool_env(name: str, default: bool = False) -> bool:
    v = os.getenv(name, "")
    if not v:
        return default
    return v.strip().lower() in ("1", "true", "yes", "y", "on")


class _Dedupe:
    """Simple in-memory dedupe (OpenAgents can deliver at-least-once)."""
    def __init__(self, max_items: int = 512):
        self.max_items = max_items
        self._q = deque()
        self._s = set()

    def seen(self, key: str) -> bool:
        if key in self._s:
            return True
        self._s.add(key)
        self._q.append(key)
        while len(self._q) > self.max_items:
            old = self._q.popleft()
            self._s.discard(old)
        return False


def _get_text_from_channel_event(context: ChannelMessageContext) -> str:
    payload = getattr(context.incoming_event, "payload", None) or {}
    if isinstance(payload, dict):
        content = payload.get("content")
        if isinstance(content, dict) and isinstance(content.get("text"), str):
            return content["text"]
        if isinstance(payload.get("text"), str):
            return payload["text"]
    return ""


def _event_id_or_hash(context: EventContext, text: str) -> str:
    ev = getattr(context, "incoming_event", None)
    ev_id = getattr(ev, "id", None) or getattr(ev, "event_id", None)
    if ev_id:
        return str(ev_id)
    return f"hash:{hash(text)}"


def _extract_llm_response(trajectory) -> Optional[str]:
    """Be defensive about payload shapes across versions/providers."""
    for action in getattr(trajectory, "actions", []) or []:
        payload = getattr(action, "payload", None) or {}
        if not isinstance(payload, dict):
            continue
        for k in ("response", "text", "content", "output"):
            v = payload.get(k)
            if isinstance(v, str) and v.strip():
                return v
            if isinstance(v, dict) and isinstance(v.get("text"), str) and v.get("text").strip():
                return v["text"]
    return None


class PlannerAgent(WorkerAgent):
    default_agent_id = "planner"

    def __init__(self, **kwargs):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.force_mock = _safe_bool_env("OPENAGENTS_MOCK", default=False)
        self.mock_mode = self.force_mock or (not bool(self.api_key))
        self._dedupe = _Dedupe(max_items=512)

        agent_config = AgentConfig(
            instruction=(
                "You are the Planner agent in a multi-agent research pipeline.\n"
                "When you receive a user question, produce a short, structured plan.\n"
                "Output MUST be concise and actionable."
            ),
            model_name=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            provider=os.getenv("OPENAI_PROVIDER", "openai"),
            api_key=self.api_key,
        )
        super().__init__(agent_config=agent_config, **kwargs)

    async def on_startup(self):
        print(f"✅ PlannerAgent online | listens: #general → sends: #ideas | Mock: {self.mock_mode}")
        # Optional hello
        # ws = self.workspace()
        # await ws.channel("general").post("Planner online ✅")

    async def on_channel_post(self, context: ChannelMessageContext):
        # Only handle #general
        if context.channel != "general":
            return

        # Ignore own messages
        if getattr(context, "source_id", None) == self.agent_id:
            return

        question = _get_text_from_channel_event(context).strip()
        if not question:
            return

        # Deduplicate
        key = f"{context.channel}:{_event_id_or_hash(context, question)}"
        if self._dedupe.seen(key):
            return

        run_id = uuid.uuid4().hex[:8]
        print(f"📋 Planner processing (run_id={run_id}): {question[:80]}")

        if self.mock_mode:
            plan = (
                "- Define key terms and scope\n"
                "- Identify 3–5 core points to cover\n"
                "- Gather examples / evidence\n"
                "- Draft structure with headings\n"
                "- Review & refine for clarity"
            )
        else:
            try:
                trajectory = await self.run_agent(
                    context=context,
                    instruction=(
                        "Create a step-by-step plan for researching and writing a report.\n"
                        "Return ONLY the plan as bullet points.\n\n"
                        f"User question: {question}"
                    ),
                )
                plan = _extract_llm_response(trajectory) or "- (No plan generated)"
            except Exception as e:
                print(f"⚠️ Planner LLM error: {e}")
                plan = "- (Error generating plan, using fallback)"

        msg = f"RUN_ID: {run_id}\nQUESTION:\n{question}\n\nPLAN:\n{plan}"

        ws = self.workspace()
        await ws.channel("ideas").post(msg)
        print(f"✅ Planner → #ideas (run_id={run_id})")


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Planner Agent (workspace API stable)")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=8700, help="HTTP port for connection (default: 8700)")
    parser.add_argument("--url", default=None, help="Direct connection URL (recommended: grpc://localhost:8600)")
    args = parser.parse_args()

    agent = PlannerAgent()
    try:
        if args.url:
            print(f"🚀 Starting Planner with URL: {args.url}")
            await agent.async_start(url=args.url)
        else:
            print(f"🚀 Starting Planner on http://{args.host}:{args.port}")
            await agent.async_start(network_host=args.host, network_port=args.port)

        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\n👋 Planner shutting down...")
    finally:
        await agent.async_stop()


if __name__ == "__main__":
    asyncio.run(main())