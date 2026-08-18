"""
Workflow state definition for the TCM Knowledge Graph RAG pipeline.

Defines the AgentState TypedDict that flows through all LangGraph nodes,
carrying user input, extracted entities, matched KG entities, generated
Cypher queries, Neo4j results, and the final natural-language answer.
"""

from typing import TypedDict, List, Dict


class AgentState(TypedDict):
    """State dictionary shared by all nodes in the TCM Q&A workflow.

    Fields by category:

    ── I/O ──
    - input:             Raw user input text
    - messages:          Conversation history [{"role": "...", "content": "..."}]
    - output:            Final output text (written by terminal nodes)

    ── Intent ──
    - is_zhongyi_intent: Whether the user query is TCM-related

    ── Entity extraction (LLM from user input) ──
    - user_input_effects/diseases/symptoms/formulas/herbs/sources

    ── Entity matching (FAISS vector search → KG entities) ──
    - matched_effects/diseases/symptoms/formulas/herbs/sources

    ── Cypher ──
    - cypher_query:              Generated Cypher queries
    - is_all_validate_cypher:    All queries passed syntax validation
    - cypher_validation_feedback: Error details for LLM self-correction loop
    - cypher_retry_count:        Retry counter (max: MAX_CYPHER_RETRIES)

    ── Neo4j results ──
    - cypher_results:  Results from executed Cypher queries
    - neo4j_answer:    Natural-language answer from query results

    ── Fallback ──
    - direct_out:  LLM direct answer for non-TCM queries

    ── Runtime ──
    - _stream_tokens:  Streaming token buffer (internal, prefixed with _)
    """

    # ── I/O ──
    input: str
    messages: List[Dict[str, str]]
    output: str

    # ── Intent ──
    is_zhongyi_intent: bool

    # ── Entity extraction (LLM) ──
    user_input_effects: List[str]
    user_input_diseases: List[str]
    user_input_symptoms: List[str]
    user_input_formulas: List[str]
    user_input_herbs: List[str]
    user_input_sources: List[str]

    # ── Entity matching (FAISS) ──
    matched_effects: List[str]
    matched_diseases: List[str]
    matched_symptoms: List[str]
    matched_formulas: List[str]
    matched_herbs: List[str]
    matched_sources: List[str]

    # ── Cypher ──
    cypher_query: List[str]
    is_all_validate_cypher: bool
    cypher_validation_feedback: str
    cypher_retry_count: int

    # ── Neo4j results ──
    cypher_results: List[dict]
    neo4j_answer: str

    # ── Fallback ──
    direct_out: str

    # ── Runtime ──
    _stream_tokens: List[str]


def make_initial_state(
    user_input: str = "",
    messages: List[Dict[str, str]] = None,
) -> AgentState:
    """Create a new AgentState with safe defaults.

    All strings default to "", lists to [], bools to False, counters to 0.
    """
    return AgentState(
        input=user_input,
        messages=messages or [],
        output="",
        is_zhongyi_intent=False,
        user_input_effects=[],
        user_input_diseases=[],
        user_input_symptoms=[],
        user_input_formulas=[],
        user_input_herbs=[],
        user_input_sources=[],
        matched_effects=[],
        matched_diseases=[],
        matched_symptoms=[],
        matched_formulas=[],
        matched_herbs=[],
        matched_sources=[],
        cypher_query=[],
        is_all_validate_cypher=False,
        cypher_validation_feedback="",
        cypher_retry_count=0,
        cypher_results=[],
        neo4j_answer="",
        direct_out="",
        _stream_tokens=[],
    )
