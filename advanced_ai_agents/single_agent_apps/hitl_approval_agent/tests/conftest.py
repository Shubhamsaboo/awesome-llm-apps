"""Shared test utilities: a scripted fake LLM so the agent runs end-to-end offline."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from typing import AsyncGenerator

import pytest
from google.adk.models import BaseLlm, LlmRequest, LlmResponse
from google.adk.runners import InMemoryRunner
from google.genai import types

ROOT = Path(__file__).resolve().parents[1]
_TMP = Path(tempfile.mkdtemp(prefix="hitl-approval-agent-tests-"))
os.environ.setdefault("P06_AUDIT_LOG", str(_TMP / "audit.jsonl"))
sys.path.insert(0, str(ROOT.parent))


def text(t: str) -> LlmResponse:
    return LlmResponse(content=types.Content(role="model", parts=[types.Part(text=t)]))


def call(name: str, **args) -> LlmResponse:
    return LlmResponse(content=types.Content(role="model", parts=[
        types.Part(function_call=types.FunctionCall(name=name, args=args))]))


class ScriptedLlm(BaseLlm):
    """Returns queued responses in order; records every request it received."""

    model: str = "scripted"
    script: list = []
    requests: list = []

    async def generate_content_async(self, llm_request: LlmRequest, stream: bool = False
                                     ) -> AsyncGenerator[LlmResponse, None]:
        self.requests.append(llm_request)
        if not self.script:
            yield text("(script exhausted)")
            return
        nxt = self.script.pop(0)
        yield nxt(llm_request) if callable(nxt) else nxt


def set_model(agent, llm) -> None:
    """Recursively point every LlmAgent in a tree at the fake model."""
    if hasattr(agent, "model") and getattr(agent, "instruction", None) is not None:
        agent.model = llm
    for sub in getattr(agent, "sub_agents", []) or []:
        set_model(sub, llm)


@pytest.fixture
def scripted():
    def make(*responses):
        return ScriptedLlm(script=list(responses), requests=[])
    return make
