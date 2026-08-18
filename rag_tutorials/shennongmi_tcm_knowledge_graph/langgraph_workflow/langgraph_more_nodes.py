"""
LangGraph-based TCM Knowledge Graph RAG workflow.

A single pipeline that receives a user query, determines whether it is
TCM-related, and if so extracts entities, matches them against a Neo4j
knowledge graph via FAISS, generates and validates Cypher queries, executes
them, and returns a natural-language answer.

Architecture
============

    START
      │
      ▼
    [zhongyi_intent_node]   ← RoBERTa+LoRA TCM intent classifier
      ├── TCM ──────────────────────────────────────────┐
      │   [extract_entity_from_user_input_node]         │  LLM entity extraction
      │   [match_entity_from_neo4j_node]                │  FAISS vector matching
      │   [generate_neo4j_cypher_node]                  │  LLM Cypher generation
      │   [check_cypher_node]                           │  Syntax validation
      │     ├── valid ── [run_cypher_node] ──┐          │
      │     ├── retry ── back to generate ────┤          │
      │     └── exhausted ──────────────────▶[neo4j_answer_generate_node] → END
      │
      └── Non-TCM ── [llm_direct_out_node] → END

Key design points
-----------------
1. FAISS index preloaded at module import time (must import match_entity
   first to avoid OpenMP conflicts with langchain_openai/httpcore).
2. Cypher self-correction loop: check_cypher → generate_neo4j_cypher,
   with a max retry counter (MAX_CYPHER_RETRIES = 3).
3. RoBERTa+LoRA local model for TCM intent (fast, no API cost).
4. SSE streaming support via the _stream_tokens runtime field.
"""

from typing import Literal
import sys

from langgraph.graph import StateGraph, START, END

from langgraph_workflow.agent_state import AgentState, make_initial_state

# ⚠️  IMPORTANT: match_entity must be imported FIRST.
# It initialises FAISS + PyTorch MPS embeddings at load time.
# Importing langchain_openai (via common.llm) before it causes
# httpcore/anyio OpenMP conflicts → segmentation fault on macOS.
from langgraph_workflow.node.match_entity_from_neo4j_node import (
    match_entity_from_neo4j_node,
)
from langgraph_workflow.node.zhongyi_intent_node import (
    zhongyi_intent_node,
)
from langgraph_workflow.node.llm_direct_out_node import (
    llm_direct_out_node,
)
from langgraph_workflow.node.extract_entity_from_user_input_node import (
    extract_entity_from_user_input_node,
)
from langgraph_workflow.node.generate_neo4j_cypher_node import (
    generate_neo4j_cypher_node,
)
from langgraph_workflow.node.check_cypher_node import (
    check_cypher_node,
)
from langgraph_workflow.node.run_cypher_node import (
    run_cypher_node,
)
from langgraph_workflow.node.neo4j_answer_generate_node import (
    neo4j_answer_generate_node,
)


# ── Constants ────────────────────────────────────────────────────────
MAX_CYPHER_RETRIES = 3  # max self-correction attempts after initial generation


# ── Conditional routing ──────────────────────────────────────────────

def route_after_intent(state: AgentState) -> Literal["extract_entity_from_user_input_node", "llm_direct_out_node"]:
    """Route based on TCM intent classification."""
    if state.get("is_zhongyi_intent"):
        return "extract_entity_from_user_input_node"
    return "llm_direct_out_node"


def route_after_cypher_check(state: AgentState) -> Literal["run_cypher_node", "generate_neo4j_cypher_node", "neo4j_answer_generate_node"]:
    """Route after Cypher validation, with self-correction retry loop.

    Three branches:
      - All valid + non-empty → execute
      - Empty cypher_query → straight to fallback answer
      - Invalid but retries left → loop back to generator with feedback
      - Invalid + retries exhausted → fallback answer
    """
    if state.get("is_all_validate_cypher") and state.get("cypher_query"):
        return "run_cypher_node"

    if not state.get("cypher_query"):
        return "neo4j_answer_generate_node"

    retry = state.get("cypher_retry_count", 0)
    if retry < MAX_CYPHER_RETRIES:
        return "generate_neo4j_cypher_node"
    return "neo4j_answer_generate_node"


# ── Build workflow ───────────────────────────────────────────────────

def build_workflow() -> StateGraph:
    """Build the TCM knowledge-graph RAG workflow graph (uncompiled)."""
    wf = StateGraph(AgentState)

    # Register nodes
    wf.add_node("zhongyi_intent_node", zhongyi_intent_node)
    wf.add_node("extract_entity_from_user_input_node", extract_entity_from_user_input_node)
    wf.add_node("match_entity_from_neo4j_node", match_entity_from_neo4j_node)
    wf.add_node("generate_neo4j_cypher_node", generate_neo4j_cypher_node)
    wf.add_node("check_cypher_node", check_cypher_node)
    wf.add_node("run_cypher_node", run_cypher_node)
    wf.add_node("neo4j_answer_generate_node", neo4j_answer_generate_node)
    wf.add_node("llm_direct_out_node", llm_direct_out_node)

    # Edges
    wf.add_edge(START, "zhongyi_intent_node")
    wf.add_conditional_edges("zhongyi_intent_node", route_after_intent, {
        "extract_entity_from_user_input_node": "extract_entity_from_user_input_node",
        "llm_direct_out_node": "llm_direct_out_node",
    })
    wf.add_edge("extract_entity_from_user_input_node", "match_entity_from_neo4j_node")
    wf.add_edge("match_entity_from_neo4j_node", "generate_neo4j_cypher_node")
    wf.add_edge("generate_neo4j_cypher_node", "check_cypher_node")
    wf.add_conditional_edges("check_cypher_node", route_after_cypher_check, {
        "run_cypher_node": "run_cypher_node",
        "generate_neo4j_cypher_node": "generate_neo4j_cypher_node",
        "neo4j_answer_generate_node": "neo4j_answer_generate_node",
    })
    wf.add_edge("run_cypher_node", "neo4j_answer_generate_node")
    wf.add_edge("neo4j_answer_generate_node", END)
    wf.add_edge("llm_direct_out_node", END)

    return wf


# ── Module-level compiled graph ──────────────────────────────────────
graph = build_workflow().compile()


# ── Public API ───────────────────────────────────────────────────────

def run_workflow(user_input: str, messages: list = None) -> AgentState:
    """Synchronous entry point for scripts and tests."""
    return graph.invoke(make_initial_state(user_input, messages))


async def zhongyi_response(user_input: str, messages: list = None) -> str:
    """Async entry point for FastAPI. Returns the final answer string."""
    result = await graph.ainvoke(make_initial_state(user_input, messages))
    return result["output"]


# ── Integration test ─────────────────────────────────────────────────
# Run with: python langgraph_workflow/langgraph_more_nodes.py

if __name__ == "__main__":
    import json
    import os
    from unittest.mock import patch, MagicMock

    def _llm(content: str):
        m = MagicMock()
        m.content = content
        r = MagicMock()
        r.content = m.content
        return r

    print("\n" + "=" * 70)
    print("🧪 TCM Knowledge Graph RAG — Integration Test")
    print("=" * 70)

    user_input = "我最近拉肚子、恶心想吐，有什么中药方剂可以缓解症状？"
    print(f"📝 Input: {user_input}")

    # Chain of LLM responses (in call order)
    llm_chain = [
        _llm(json.dumps({"symptoms": ["腹泻", "恶心", "呕吐"], "diseases": [],
                         "formulas": ["藿香正气散"], "herbs": ["藿香", "陈皮", "白术"],
                         "effects": ["止泻", "止呕", "化湿"], "sources": []}, ensure_ascii=False)),
        _llm(json.dumps({"cypher_queries": [
            "MATCH (f:Formula {name: '藿香正气散'})-[:HAS_INGREDIENT]->(h:Herb) RETURN f.name, h.name",
            "MATCH (f:Formula {name: '藿香正气散'})-[:HAS_EFFECT]->(e:Effect) RETURN e.name",
            "MATCH (h:Herb)-[:HAS_EFFECT]->(e:Effect) WHERE e.name IN ['止泻', '止呕', '化湿'] RETURN h.name, e.name",
        ], "reasoning": "Query formula composition, effects, and herbs with matching effects"}, ensure_ascii=False)),
        _llm("根据中医知识图谱查询结果，藿香正气散是治疗您所述腹泻、恶心、呕吐症状的常用方剂。主要由藿香、陈皮、白术等组成，具有化湿止泻、理气和中的功效。建议在中医师指导下使用。"),
    ]

    def mock_faiss(queries, top_k=3, threshold=0.85):
        mapping = {"腹泻": [("腹泻", 0.99)], "恶心": [("恶心", 0.98)], "呕吐": [("呕吐", 0.97)],
                   "藿香正气散": [("藿香正气散", 0.99)], "藿香": [("藿香", 0.96)],
                   "陈皮": [("陈皮", 0.97)], "白术": [("白术", 0.98)],
                   "止泻": [("止泻", 0.95)], "止呕": [("止呕", 0.94)], "化湿": [("化湿", 0.93)]}
        return [mapping.get(q, []) for q in queries]

    mock_results = [
        {"query": "...", "result": [{"f.name": "藿香正气散", "h.name": "藿香"}, {"f.name": "藿香正气散", "h.name": "陈皮"}, {"f.name": "藿香正气散", "h.name": "白术"}]},
        {"query": "...", "result": [{"e.name": "化湿"}, {"e.name": "止泻"}, {"e.name": "止呕"}]},
        {"query": "...", "result": [{"h.name": "藿香", "e.name": "止呕"}, {"h.name": "白术", "e.name": "止泻"}, {"h.name": "陈皮", "e.name": "化湿"}]},
    ]

    with (
        patch("langchain_openai.ChatOpenAI.invoke", side_effect=llm_chain),
        patch("langgraph_workflow.node.zhongyi_intent_node.predict_tcm_intent", return_value=True),
        patch("langgraph_workflow.node.match_entity_from_neo4j_node.batch_search_similar_entities", side_effect=mock_faiss),
        patch("common.neo4j_manager.neo4j_client.valid_cypher", return_value=(True, "")),
        patch("common.neo4j_manager.neo4j_client.run_cypher", side_effect=[r["result"] for r in mock_results]),
    ):
        result = run_workflow(user_input)

    print(f"  TCM intent:   {'✅ Yes' if result.get('is_zhongyi_intent') else '❌ No'}")
    print(f"  Symptoms:     {result.get('user_input_symptoms', [])}")
    print(f"  Formulas:     {result.get('user_input_formulas', [])}")
    print(f"  Matched:      {result.get('matched_formulas', [])}")
    print(f"  Cypher count: {len(result.get('cypher_query', []))}")
    print(f"  Valid:        {'✅' if result.get('is_all_validate_cypher') else '❌'}")
    print(f"  Answer:       {result.get('output', '')[:120]}...")
    print("-" * 50)

    assert result.get("is_zhongyi_intent") is True
    assert len(result.get("user_input_symptoms", [])) > 0
    assert len(result.get("matched_formulas", [])) > 0
    assert len(result.get("cypher_query", [])) > 0
    assert result.get("is_all_validate_cypher") is True
    assert len(result.get("output", "")) > 0

    print("✅ All assertions passed — TCM Knowledge Graph RAG pipeline works end-to-end")
    print("=" * 70)
