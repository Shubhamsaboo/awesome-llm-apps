#!/usr/bin/env python3
"""
Researcher Agent (stable workspace API)
- Listens:  #ideas
- Sends:    #discussion
Produces structured research notes from plans.
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


class ResearcherAgent(WorkerAgent):
    default_agent_id = "researcher"

    def __init__(self, **kwargs):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.force_mock = _safe_bool_env("OPENAGENTS_MOCK", default=False)
        self.mock_mode = self.force_mock or (not bool(self.api_key))
        self._dedupe = _Dedupe(max_items=512)

        agent_config = AgentConfig(
            instruction=(
                "You are the Researcher agent.\n"
                "Given a QUESTION and a PLAN, produce structured research notes.\n"
                "Notes should be factual, organized, and suitable for a final report."
            ),
            model_name=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            provider=os.getenv("OPENAI_PROVIDER", "openai"),
            api_key=self.api_key,
        )
        super().__init__(agent_config=agent_config, **kwargs)

    async def on_startup(self):
        print(f"✅ ResearcherAgent online | listens: #ideas → sends: #discussion | Mock: {self.mock_mode}")

    async def on_channel_post(self, context: ChannelMessageContext):
        if context.channel != "ideas":
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
        print(f"🔍 Researcher processing (run_id={run_id})")

        if self.mock_mode:
            notes = (
                "## Definitions\n"
                "- **Single-agent pipeline**: one LLM call chain (prompt → response), optionally with tools/RAG.\n"
                "- **Multi-agent system**: multiple specialized agents collaborate via messages and roles.\n\n"
                "## Key differences\n"
                "- **Control flow**: linear chain vs role-based message passing.\n"
                "- **Specialization**: one generalist vs multiple specialists.\n"
                "- **Quality control**: limited vs critique/refinement loops.\n\n"
                "## Benefits\n"
                "- Better task decomposition\n"
                "- Higher quality via review and iteration\n\n"
                "## Limitations\n"
                "- More latency/cost\n"
                "- Coordination complexity\n\n"
                "## Practical examples\n"
                "- Research pipeline (planner/researcher/critic/writer)\n"
                "- Code review team (dev/reviewer/tester)\n"
            )
        else:
            try:
                trajectory = await self.run_agent(
                    context=context,
                    instruction=(
                        "From the input, produce research notes with headings:\n"
                        "1) Definitions\n2) Key differences\n3) Benefits\n4) Limitations\n5) Practical examples\n\n"
                        "Return ONLY the notes.\n\n"
                        f"Input:\n{incoming}"
                    ),
                )
                notes = _extract_llm_response(trajectory) or "(No notes generated)"
            except Exception as e:
                print(f"⚠️ Researcher LLM error: {e}")
                notes = "(Error generating notes, using fallback)"

        msg = f"RUN_ID: {run_id}\n{incoming}\n\nNOTES:\n{notes}"

        ws = self.workspace()
        await ws.channel("discussion").post(msg)
        print(f"✅ Researcher → #discussion (run_id={run_id})")


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Researcher Agent (workspace API stable)")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=8700, help="HTTP port for connection (default: 8700)")
    parser.add_argument("--url", default=None, help="Direct connection URL (recommended: grpc://localhost:8600)")
    args = parser.parse_args()

    agent = ResearcherAgent()
    try:
        if args.url:
            print(f"🚀 Starting Researcher with URL: {args.url}")
            await agent.async_start(url=args.url)
        else:
            print(f"🚀 Starting Researcher on http://{args.host}:{args.port}")
            await agent.async_start(network_host=args.host, network_port=args.port)

        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\n👋 Researcher shutting down...")
    finally:
        await agent.async_stop()


if __name__ == "__main__":
    asyncio.run(main())