"""OpenAI-compatible progressive PDF navigation & verification agent.

Connects a standard OpenAI function-calling loop to four local read-only tools:
- ``get_outline``: inspect document structure first (no body text loaded).
- ``search_pages``: BM25 search with bounded snippets.
- ``read_pages``: read specific 1-based pages under a strict character budget.
- ``verify_claim``: deterministic quote, number, or AST formula verification.

Works with OpenAI, OpenRouter, Ollama, DeepSeek, or any OpenAI-compatible endpoint.
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass, field
from typing import Any

from claim_verifier import verify_formula, verify_number, verify_quote
from pdf_navigator import PDFDocumentIndex, build_sample_financial_pdf

SYSTEM_PROMPT = """You are a meticulous document analyst operating over a long PDF without a vector database.

Follow this progressive workflow strictly:
1. Start with `get_outline` to see the document's structure and page count.
2. Use `search_pages` to find relevant pages before reading body text.
3. Call `read_pages` only for the specific pages you need (keep context lean).
4. Before writing your final answer, call `verify_claim` to deterministically verify:
   - any direct quote you cite (`kind="quote"`),
   - any standalone source figure (`kind="number"`), and
   - any derived metric or calculation (`kind="formula"` with page-cited `operands`).
5. Never fabricate quotes or numbers. If evidence is missing or fails verification, state that clearly and cite exact page numbers."""

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_outline",
            "description": "Return the PDF's page count and hierarchical outline (section titles and page ranges).",
            "parameters": {
                "type": "object",
                "properties": {
                    "max_nodes": {
                        "type": "integer",
                        "description": "Maximum outline sections to return (default 80).",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_pages",
            "description": "Run BM25 lexical search over the PDF and return ranked pages with short snippets.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search keywords or phrases."},
                    "top_k": {"type": "integer", "description": "Number of pages to return (1-10, default 5)."},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_pages",
            "description": "Read exact 1-based PDF pages with a strict character budget (max 6 pages per call).",
            "parameters": {
                "type": "object",
                "properties": {
                    "pages": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "List of 1-based page numbers to read.",
                    }
                },
                "required": ["pages"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "verify_claim",
            "description": (
                "Deterministically verify a quote, number, or arithmetic formula against the source PDF. "
                "Always run this before asserting quotes or computed metrics."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "kind": {
                        "type": "string",
                        "enum": ["quote", "number", "formula"],
                        "description": "Type of deterministic check to run.",
                    },
                    "page": {
                        "type": "integer",
                        "description": "1-based cited page (required for 'quote' and 'number').",
                    },
                    "quote": {
                        "type": "string",
                        "description": "Exact quote text to check on `page` (for kind='quote').",
                    },
                    "value": {
                        "type": "number",
                        "description": "Numeric value to check on `page` (for kind='number').",
                    },
                    "formula": {
                        "type": "string",
                        "description": "Arithmetic expression using operand names, e.g. '(revenue - cogs) / revenue * 100'.",
                    },
                    "operands": {
                        "type": "object",
                        "description": "Map of variable name -> {value: number, page: integer} for kind='formula'.",
                        "additionalProperties": {
                            "type": "object",
                            "properties": {
                                "value": {"type": "number"},
                                "page": {"type": "integer"},
                            },
                            "required": ["value", "page"],
                        },
                    },
                    "claimed_result": {
                        "type": "number",
                        "description": "Expected numeric result of `formula` (for kind='formula').",
                    },
                },
                "required": ["kind"],
            },
        },
    },
]


@dataclass
class ToolTraceStep:
    step: int
    tool: str
    arguments: dict[str, Any]
    result: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AgentRunResult:
    answer: str
    steps_used: int
    pages_read: list[int] = field(default_factory=list)
    verifications: list[dict[str, Any]] = field(default_factory=list)
    trace: list[ToolTraceStep] = field(default_factory=list)
    stopped_reason: str = "completed"


def dispatch_tool(index: PDFDocumentIndex, name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Execute one local navigation/verification tool with strict input validation."""
    if not isinstance(args, dict):
        return {"error": "Tool arguments must be a JSON object."}

    if name == "get_outline":
        max_nodes = args.get("max_nodes", 80)
        try:
            max_nodes = max(1, min(int(max_nodes), 200))
        except (TypeError, ValueError):
            max_nodes = 80
        return index.get_outline(max_nodes=max_nodes)

    if name == "search_pages":
        query = str(args.get("query") or "").strip()
        if not query:
            return {"error": "Missing required parameter 'query'."}
        try:
            top_k = max(1, min(int(args.get("top_k", 5)), 10))
        except (TypeError, ValueError):
            top_k = 5
        return index.search_pages(query=query, top_k=top_k)

    if name == "read_pages":
        pages = args.get("pages")
        if not isinstance(pages, list) or not pages:
            return {"error": "Parameter 'pages' must be a non-empty list of integers."}
        return index.read_pages(pages=pages)

    if name == "verify_claim":
        kind = str(args.get("kind") or "").strip().lower()
        if kind == "quote":
            if "page" not in args or not args.get("quote"):
                return {"error": "kind='quote' requires 'quote' and 'page'."}
            try:
                page = int(args["page"])
            except (TypeError, ValueError):
                return {"error": "Parameter 'page' must be an integer."}
            return verify_quote(index, str(args["quote"]), page).to_dict()

        if kind == "number":
            if "page" not in args or "value" not in args:
                return {"error": "kind='number' requires 'value' and 'page'."}
            try:
                page = int(args["page"])
                val = float(args["value"])
            except (TypeError, ValueError):
                return {"error": "Parameters 'value' and 'page' must be numeric."}
            return verify_number(index, val, page).to_dict()

        if kind == "formula":
            formula = str(args.get("formula") or "").strip()
            operands = args.get("operands")
            if not formula or not isinstance(operands, dict) or "claimed_result" not in args:
                return {"error": "kind='formula' requires 'formula', 'operands', and 'claimed_result'."}
            try:
                claimed = float(args["claimed_result"])
            except (TypeError, ValueError):
                return {"error": "Parameter 'claimed_result' must be numeric."}
            return verify_formula(index, formula, operands, claimed).to_dict()

        return {"error": f"Unknown verification kind: {kind!r}. Expected 'quote', 'number', or 'formula'."}

    return {"error": f"Unknown tool: {name!r}."}


class ProgressivePDFAgent:
    """Hardened function-calling loop over an indexed PDF."""

    def __init__(
        self,
        index: PDFDocumentIndex,
        client: Any,
        model: str = "gpt-4o-mini",
        max_steps: int = 8,
        max_tool_chars: int = 12000,
    ) -> None:
        self.index = index
        self.client = client
        self.model = model
        self.max_steps = max(1, min(max_steps, 16))
        self.max_tool_chars = max_tool_chars

    def ask(self, question: str) -> AgentRunResult:
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Document: {self.index.name} ({self.index.num_pages} pages)\n"
                    f"Question: {question}"
                ),
            },
        ]
        trace: list[ToolTraceStep] = []
        verifications: list[dict[str, Any]] = []
        pages_read: set[int] = set()

        for step in range(1, self.max_steps + 1):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=TOOL_SCHEMAS,
                tool_choice="auto",
            )

            choices = getattr(response, "choices", None) or []
            if not choices or getattr(choices[0], "message", None) is None:
                return AgentRunResult(
                    answer="Model returned an empty response.",
                    steps_used=step,
                    pages_read=sorted(pages_read),
                    verifications=verifications,
                    trace=trace,
                    stopped_reason="empty_model_response",
                )

            msg = choices[0].message
            tool_calls = getattr(msg, "tool_calls", None) or []
            content_text = (getattr(msg, "content", None) or "").strip()

            if not tool_calls:
                return AgentRunResult(
                    answer=content_text or "No answer text was returned by the model.",
                    steps_used=step,
                    pages_read=sorted(pages_read),
                    verifications=verifications,
                    trace=trace,
                    stopped_reason="completed",
                )

            assistant_tool_calls = []
            for tc in tool_calls:
                fn = getattr(tc, "function", None)
                assistant_tool_calls.append(
                    {
                        "id": str(getattr(tc, "id", f"call_{step}")),
                        "type": "function",
                        "function": {
                            "name": str(getattr(fn, "name", "")),
                            "arguments": str(getattr(fn, "arguments", "{}")),
                        },
                    }
                )
            messages.append(
                {
                    "role": "assistant",
                    "content": content_text or None,
                    "tool_calls": assistant_tool_calls,
                }
            )

            for tc_dict in assistant_tool_calls:
                tool_name = tc_dict["function"]["name"]
                raw_args = tc_dict["function"]["arguments"]
                try:
                    parsed_args = json.loads(raw_args) if raw_args else {}
                except json.JSONDecodeError as exc:
                    parsed_args = {}
                    result: dict[str, Any] = {"error": f"Malformed JSON arguments: {exc}"}
                else:
                    result = dispatch_tool(self.index, tool_name, parsed_args)

                if tool_name == "read_pages" and isinstance(result.get("pages_read"), list):
                    pages_read.update(int(p) for p in result["pages_read"])
                if tool_name == "verify_claim" and "status" in result:
                    verifications.append(result)

                trace.append(ToolTraceStep(step=step, tool=tool_name, arguments=parsed_args, result=result))
                serialized = json.dumps(result, ensure_ascii=False)
                if len(serialized) > self.max_tool_chars:
                    serialized = serialized[: self.max_tool_chars] + "... [truncated]"
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc_dict["id"],
                        "content": serialized,
                    }
                )

        return AgentRunResult(
            answer="Reached the maximum tool-call step budget before producing a final answer.",
            steps_used=self.max_steps,
            pages_read=sorted(pages_read),
            verifications=verifications,
            trace=trace,
            stopped_reason="max_steps_reached",
        )


def _run_offline_demo() -> None:
    """Demonstrate indexing, progressive navigation, and verification with zero API key."""
    index = PDFDocumentIndex.from_bytes(build_sample_financial_pdf(), name="acme_fy2025_report.pdf")
    print("=== 1. Outline (Zero LLM, Zero Vector DB) ===")
    print(json.dumps(index.get_outline(), indent=2))

    print("\n=== 2. BM25 Search: 'gross margin COGS' ===")
    print(json.dumps(index.search_pages("gross margin COGS", top_k=2), indent=2))

    print("\n=== 3. Deterministic Formula Verification (Valid) ===")
    ok = verify_formula(
        index,
        formula="(revenue - cogs) / revenue * 100",
        operands={"revenue": {"value": 480.0, "page": 3}, "cogs": {"value": 288.0, "page": 3}},
        claimed_result=40.0,
    )
    print(json.dumps(ok.to_dict(), indent=2))

    print("\n=== 4. Deterministic Formula Verification (Hallucinated Math Trap) ===")
    bad = verify_formula(
        index,
        formula="(revenue - cogs) / revenue * 100",
        operands={"revenue": {"value": 480.0, "page": 3}, "cogs": {"value": 288.0, "page": 3}},
        claimed_result=45.0,
    )
    print(json.dumps(bad.to_dict(), indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Progressive PDF RAG & Deterministic Verifier CLI")
    parser.add_argument("--pdf", help="Path to a local PDF file (omit with --sample to use built-in PDF).")
    parser.add_argument("--sample", action="store_true", help="Use the built-in FY2025 sample PDF.")
    parser.add_argument("--demo-verify", action="store_true", help="Run offline deterministic demo (no API key).")
    parser.add_argument("--question", help="Question to ask the progressive PDF agent (requires API key).")
    parser.add_argument("--model", default=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    parser.add_argument("--base-url", default=os.getenv("OPENAI_BASE_URL") or None)
    args = parser.parse_args()

    if args.demo_verify or (not args.question and not args.pdf):
        _run_offline_demo()
        return

    if args.pdf:
        index = PDFDocumentIndex.from_file(args.pdf)
    else:
        index = PDFDocumentIndex.from_bytes(build_sample_financial_pdf(), name="acme_fy2025_report.pdf")

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is required when using --question (or run with --demo-verify offline).")

    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url=args.base_url)
    agent = ProgressivePDFAgent(index=index, client=client, model=args.model)
    result = agent.ask(args.question)

    print(f"Answer:\n{result.answer}\n")
    print(f"Pages read: {result.pages_read} / {index.num_pages} total pages ({result.steps_used} steps)")
    if result.verifications:
        print("Deterministic verifications:")
        for v in result.verifications:
            print(f"  - [{v['status'].upper()}] ({v['kind']}) {v['detail']}")


if __name__ == "__main__":
    main()
