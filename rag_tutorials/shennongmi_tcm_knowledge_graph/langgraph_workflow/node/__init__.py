"""
LangGraph workflow nodes for the TCM Knowledge Graph RAG pipeline.

Nodes (in execution order):
  ── TCM Q&A pipeline ──
  1. zhongyi_intent_node                  — RoBERTa+LoRA TCM intent classification
  2. extract_entity_from_user_input_node  — LLM entity extraction (symptoms, herbs, formulas, etc.)
  3. match_entity_from_neo4j_node         — FAISS vector similarity entity matching
  4. generate_neo4j_cypher_node           — LLM Cypher query generation with schema context
  5. check_cypher_node                    — Cypher syntax validation
  6. run_cypher_node                      — Neo4j query execution
  7. neo4j_answer_generate_node           — LLM natural-language answer from query results

  ── Fallback ──
  8. llm_direct_out_node                  — Direct LLM answer for non-TCM queries
"""
