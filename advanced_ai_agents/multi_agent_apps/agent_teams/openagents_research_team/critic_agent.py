#!/usr/bin/env python3
"""
Critic Agent (stable workspace API)
- Listens:  #discussion
- Sends:    #pitch-room
Reviews research notes and provides constructive critique.
"""

import asyncio
import os
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


def _parse_run_id(text: str) -> Optional[str]:
    first = (text.splitlines() or [""])[0].strip()
    if first.lower().startswith("run_id:"):
        return first.split(":", 1)[1].strip() or None
    return None


class CriticAgent(WorkerAgent):
    default_agent_id = "critic"

    def __init__(self, **kwargs):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.force_mock = _safe_bool_env("OPENAGENTS_MOCK", default=False)
        self.mock_mode = self.force_mock or (not bool(self.api_key))
        self._dedupe = _Dedupe(max_items=512)

        agent_config = AgentConfig(
            instruction=(
                "You are the Critic agent.\n"
                "Given QUESTION/PLAN/NOTES, critique the notes:\n"
                "- identify gaps\n- suggest improvements\n- propose a better outline\n"
                "Be constructive and specific."
            ),
            model_name=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            provider=os.getenv("OPENAI_PROVIDER", "openai"),
            api_key=self.api_key,
        )
        super().__init__(agent_config=agent_config, **kwargs)

    async def on_startup(self):
        print(f"✅ CriticAgent online | listens: #discussion → sends: #pitch-room | Mock: {self.mock_mode}")

    async def on_channel_post(self, context: ChannelMessageContext):
        if context.channel != "discussion":
            return
        if getattr(context, "source_id", None) == self.agent_id:
            return

        incoming = _get_text_from_channel_event(context).strip()
        if not incoming:
            return

        key = f"{context.channel}:{_event_id_or_hash(context, incoming)}"
        if self._dedupe.seen(key):
            return

        run_id = _parse_run_id(incoming) or "unknown"
        print(f"🔎 Critic processing (run_id={run_id})")

        if self.mock_mode:
            critique = (
                "## Gaps / missing points\n"
                "- Add a short section on evaluation/observability (logs, traces, metrics).\n"
                "- Mention coordination failure modes (conflicts, loops).\n"
                "- Clarify when single-agent is sufficient.\n\n"
                "## Suggested improvements\n"
                "- Add a simple workflow diagram / message flow.\n"
                "- Use concrete examples with inputs/outputs.\n\n"
                "## Proposed final outline\n"
                "1) Overview\n"
                "2) Definitions\n"
                "3) Key Differences\n"
                "4) Benefits\n"
                "5) Limitations & Failure Modes\n"
                "6) When to Use Which\n"
                "7) Conclusion\n"
            )
        else:
            try:
                trajectory = await self.run_agent(
                    context=context,
                    instruction=(
                        "Review the input and produce:\n"
                        "1) Gaps / missing points\n"
                        "2) Suggested improvements\n"
                        "3) Proposed final outline\n"
                        "Return ONLY the critique.\n\n"
                        f"Input:\n{incoming}"
                    ),
                )
                critique = _extract_llm_response(trajectory) or "(No critique generated)"
            except Exception as e:
                print(f"⚠️ Critic LLM error: {e}")
                critique = "(Error generating critique, using fallback)"

        msg = f"RUN_ID: {run_id}\n{incoming}\n\nCRITIQUE:\n{critique}"

        ws = self.workspace()
        await ws.channel("pitch-room").post(msg)
        print(f"✅ Critic → #pitch-room (run_id={run_id})")


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Critic Agent (workspace API stable)")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=8700, help="HTTP port for connection (default: 8700)")
    parser.add_argument("--url", default=None, help="Direct connection URL (recommended: grpc://localhost:8600)")
    args = parser.parse_args()

    agent = CriticAgent()
    try:
        if args.url:
            print(f"🚀 Starting Critic with URL: {args.url}")
            await agent.async_start(url=args.url)
        else:
            print(f"🚀 Starting Critic on http://{args.host}:{args.port}")
            await agent.async_start(network_host=args.host, network_port=args.port)

        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\n👋 Critic shutting down...")
    finally:
        await agent.async_stop()


if __name__ == "__main__":
    asyncio.run(main())