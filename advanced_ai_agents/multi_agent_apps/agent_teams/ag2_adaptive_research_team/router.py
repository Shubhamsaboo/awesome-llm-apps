from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from agents import build_agents, run_agent
from tools import Chunk, run_searxng, search_local


def _extract_json(text: str) -> Dict[str, Any]:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return {}
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return {}


def _summarize_chunks(chunks: List[Chunk]) -> str:
    lines = []
    for chunk in chunks:
        snippet = chunk.text[:300].strip()
        lines.append(f"- {chunk.doc_name} [chunk {chunk.chunk_id}]: {snippet}")
    return "\n".join(lines)


def run_pipeline(
    question: str,
    local_chunks: List[Chunk],
    api_key: str,
    model: str,
    web_enabled: bool,
    searxng_base_url: str,
) -> Dict[str, Any]:
    agents = build_agents(api_key=api_key, model=model)

    doc_summary = "No local documents provided."
    if local_chunks:
        doc_names = sorted({chunk.doc_name for chunk in local_chunks})
        doc_summary = f"Local docs: {', '.join(doc_names)} (total chunks: {len(local_chunks)})"

    triage_prompt = f"""
Question: {question}
{doc_summary}

Decide the best route. Output JSON with keys:
- route: "local" or "web"
- confidence: number 0 to 1
- rationale: short string
"""
    triage_raw = run_agent(agents["triage"], triage_prompt)
    triage = _extract_json(triage_raw)

    route = triage.get("route", "local")
    if not local_chunks and web_enabled:
        route = "web"

    evidence: List[Dict[str, Any]] = []
    draft_answer = ""

    if route == "web" and web_enabled:
        search_results = run_searxng(question, base_url=searxng_base_url, max_results=5)
        formatted_results = "\n".join(
            [
                f"- {item.get('title', 'Untitled')} | {item.get('link', '')} | {item.get('snippet', '')}"
                for item in search_results
            ]
        )
        web_prompt = f"""
Question: {question}

Web results:
{formatted_results}

Return JSON with keys:
- evidence: list of {{source, summary}}
- draft_answer: string
"""
        web_raw = run_agent(agents["web"], web_prompt)
        web_json = _extract_json(web_raw)
        evidence = web_json.get("evidence", [])
        draft_answer = web_json.get("draft_answer", "")
    else:
        hits = search_local(question, local_chunks, top_k=5)
        formatted_hits = _summarize_chunks(hits)
        local_prompt = f"""
Question: {question}

Document excerpts:
{formatted_hits}

Return JSON with keys:
- evidence: list of {{source, summary}}
- draft_answer: string
"""
        local_raw = run_agent(agents["local"], local_prompt)
        local_json = _extract_json(local_raw)
        evidence = local_json.get("evidence", [])
        draft_answer = local_json.get("draft_answer", "")

    verifier_prompt = f"""
Question: {question}

Draft answer:
{draft_answer}

Evidence:
{json.dumps(evidence, indent=2)}

Return JSON with keys:
- verdict: "sufficient" or "insufficient"
- gaps: list of short strings
"""
    verifier_raw = run_agent(agents["verifier"], verifier_prompt)
    verifier = _extract_json(verifier_raw)

    synth_prompt = f"""
Question: {question}

Draft answer:
{draft_answer}

Evidence:
{json.dumps(evidence, indent=2)}

Verifier verdict:
{json.dumps(verifier, indent=2)}

Provide the final answer with clear citations to the evidence sources.
"""
    final_answer = run_agent(agents["synthesizer"], synth_prompt)

    return {
        "route": route,
        "triage": triage,
        "evidence": evidence,
        "verifier": verifier,
        "final_answer": final_answer,
    }
