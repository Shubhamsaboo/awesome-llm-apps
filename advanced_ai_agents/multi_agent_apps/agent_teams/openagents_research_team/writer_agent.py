#!/usr/bin/env python3
"""
Writer Agent (stable workspace API)
- Listens:  #pitch-room
- Sends:    #discussion
Writes final Markdown reports and saves them to disk.
"""

import asyncio
import os
from pathlib import Path
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


class WriterAgent(WorkerAgent):
    default_agent_id = "writer"

    def __init__(self, **kwargs):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.force_mock = _safe_bool_env("OPENAGENTS_MOCK", default=False)
        self.mock_mode = self.force_mock or (not bool(self.api_key))
        self._dedupe = _Dedupe(max_items=512)

        agent_config = AgentConfig(
            instruction=(
                "You are the Writer agent.\n"
                "Given QUESTION/PLAN/NOTES/CRITIQUE, write a final Markdown report.\n"
                "Use clear headings and concise explanations.\n"
                "Return ONLY the Markdown report."
            ),
            model_name=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            provider=os.getenv("OPENAI_PROVIDER", "openai"),
            api_key=self.api_key,
        )
        super().__init__(agent_config=agent_config, **kwargs)

    async def on_startup(self):
        print(f"✅ WriterAgent online | listens: #pitch-room → sends: #discussion | Mock: {self.mock_mode}")

    def _mock_report(self) -> str:
        return (
            "# Multi-Agent Systems vs Single-Agent LLM Pipelines\n\n"
            "## Overview\n"
            "Single-agent pipelines are typically linear prompt/tool chains, while multi-agent systems split work across roles that communicate via messages.\n\n"
            "## Key Differences\n"
            "- **Control flow**: linear chain vs role-based coordination\n"
            "- **Specialization**: one generalist vs multiple specialists\n"
            "- **Quality control**: limited vs critique/refinement loops\n\n"
            "## Benefits\n"
            "- Better task decomposition and parallelism\n"
            "- More robust outputs via review cycles\n\n"
            "## Limitations & Failure Modes\n"
            "- Higher latency and cost\n"
            "- Coordination issues (loops, conflicts)\n"
            "- Harder observability/debugging\n\n"
            "## When to Use Which\n"
            "- Single-agent: small, well-scoped tasks\n"
            "- Multi-agent: complex tasks needing planning + review + structured output\n\n"
            "## Conclusion\n"
            "Multi-agent designs trade simplicity for controllability and output quality on complex workflows.\n"
        )

    async def _run_llm_report(self, context: ChannelMessageContext, text: str) -> str:
        if self.mock_mode:
            return self._mock_report()

        try:
            trajectory = await self.run_agent(
                context=context,
                instruction=(
                    "IMPORTANT: Do NOT call any tools. Do NOT use tool/function calls. "
                    "Return plain text only.\n\n"
                    "Write a final Markdown report based on the input.\n"
                    "Include sections: Overview, Key Differences, Benefits, Limitations & Failure Modes, When to Use Which, Conclusion.\n"
                    "Return ONLY the Markdown.\n\n"
                    f"Input:\n{text}"
                ),
            )
            return _extract_llm_response(trajectory) or "# Report\n\n(No report generated)"
        except Exception as e:
            print(f"⚠️ Writer LLM error: {e}, using fallback")
            return self._mock_report()

    async def on_channel_post(self, context: ChannelMessageContext):
        if context.channel != "pitch-room":
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
        print(f"✍️ Writer processing (run_id={run_id})")

        report = await self._run_llm_report(context, incoming)

        # Output location (default: current working directory)
        out_dir = os.getenv("OPENAGENTS_OUTPUT_DIR", "").strip()
        base = Path(out_dir) if out_dir else Path.cwd()
        base.mkdir(parents=True, exist_ok=True)

        out_path = base / f"report_{run_id}.md"
        out_path.write_text(report, encoding="utf-8")

        ws = self.workspace()
        await ws.channel("discussion").post(
            "✅ "
            f"RUN_ID: {run_id}\n"
            f"✅ Report written to: {out_path}\n\n"
            f"(Preview)\n{report[:900]}\n\n"
            "Tip: open the full file for the complete report."
        )

        print(f"✅ Writer → #discussion (saved {out_path})")


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Writer Agent (workspace API stable)")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=8700, help="HTTP port for connection (default: 8700)")
    parser.add_argument("--url", default=None, help="Direct connection URL (recommended: grpc://localhost:8600)")
    args = parser.parse_args()

    agent = WriterAgent()
    try:
        if args.url:
            print(f"🚀 Starting Writer with URL: {args.url}")
            await agent.async_start(url=args.url)
        else:
            print(f"🚀 Starting Writer on http://{args.host}:{args.port}")
            await agent.async_start(network_host=args.host, network_port=args.port)

        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\n👋 Writer shutting down...")
    finally:
        await agent.async_stop()


if __name__ == "__main__":
    asyncio.run(main())