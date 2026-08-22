"""
langgraph_workflow — TCM Knowledge Graph RAG pipeline.

Two core execution paths built on LangGraph StateGraph:

  1. TCM Knowledge Graph Q&A
     User query → Intent classification (RoBERTa+LoRA) → Entity extraction (LLM)
     → FAISS vector matching → Cypher generation & validation → Neo4j execution
     → Natural-language answer (LLM)

  2. Non-TCM fallback
     User query → LLM direct answer

Package structure:
  - agent_state.py           — AgentState TypedDict + make_initial_state() factory
  - langgraph_more_nodes.py  — build_workflow(), routing functions, integration tests
  - tcm_predictor.py         — RoBERTa+LoRA intent classifier (lazy-loading singleton)
  - node/                    — Individual workflow node implementations

Usage:
  >>> from langgraph_workflow.langgraph_more_nodes import run_workflow, zhongyi_response
  >>> result = run_workflow("枸杞有什么功效？")
  >>> print(result["output"])
"""
