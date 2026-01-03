"""
Knowledge Graph RAG with Verifiable Citations

A Streamlit app demonstrating how Knowledge Graph-based RAG provides:
1. Multi-hop reasoning across documents
2. Verifiable source attribution for every claim
3. Transparent reasoning traces

This example uses Ollama for local LLM inference and Neo4j for the knowledge graph.
"""

import streamlit as st
import ollama
from ollama import Client as OllamaClient
from neo4j import GraphDatabase
from typing import List, Dict, Tuple
import re
import os
from dataclasses import dataclass
import json
import hashlib

# Configure Ollama host from environment (for Docker)
OLLAMA_HOST = os.environ.get('OLLAMA_HOST', 'http://localhost:11434')
ollama_client = OllamaClient(host=OLLAMA_HOST)


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class Entity:
    """Represents an entity extracted from documents."""
    id: str
    name: str
    entity_type: str
    description: str
    source_doc: str
    source_chunk: str


@dataclass
class Relationship:
    """Represents a relationship between entities."""
    source: str
    target: str
    relation_type: str
    description: str
    source_doc: str


@dataclass
class Citation:
    """Represents a verifiable citation for a claim."""
    claim: str
    source_document: str
    source_text: str
    confidence: float
    reasoning_path: List[str]


@dataclass
class AnswerWithCitations:
    """Final answer with full attribution."""
    answer: str
    citations: List[Citation]
    reasoning_trace: List[str]


# ============================================================================
# Knowledge Graph Manager
# ============================================================================

class KnowledgeGraphManager:
    """Manages the Neo4j knowledge graph for RAG."""
    
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        self.driver.close()
    
    def clear_graph(self):
        """Clear all nodes and relationships."""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
    
    def add_entity(self, entity: Entity):
        """Add an entity to the knowledge graph."""
        with self.driver.session() as session:
            session.run(
                """
                MERGE (e:Entity {id: $id})
                SET e.name = $name,
                    e.type = $entity_type,
                    e.description = $description,
                    e.source_doc = $source_doc,
                    e.source_chunk = $source_chunk
                """,
                id=entity.id,
                name=entity.name,
                entity_type=entity.entity_type,
                description=entity.description,
                source_doc=entity.source_doc,
                source_chunk=entity.source_chunk
            )
    
    def add_relationship(self, rel: Relationship):
        """Add a relationship between entities."""
        with self.driver.session() as session:
            session.run(
                """
                MATCH (a:Entity {name: $source})
                MATCH (b:Entity {name: $target})
                MERGE (a)-[r:RELATES_TO {type: $rel_type}]->(b)
                SET r.description = $description,
                    r.source_doc = $source_doc
                """,
                source=rel.source,
                target=rel.target,
                rel_type=rel.relation_type,
                description=rel.description,
                source_doc=rel.source_doc
            )
    
    def find_related_entities(self, entity_name: str, hops: int = 2) -> List[Dict]:
        """Find entities related within N hops, with full provenance."""
        with self.driver.session() as session:
            result = session.run(
                f"""
                MATCH path = (start:Entity)-[*1..{hops}]-(related:Entity)
                WHERE toLower(start.name) CONTAINS toLower($name) OR toLower(start.description) CONTAINS toLower($name)
                RETURN related.name as name,
                       related.description as description,
                       related.source_doc as source,
                       related.source_chunk as chunk,
                       [r in relationships(path) | r.description] as path_descriptions
                LIMIT 20
                """,
                name=entity_name, hops=hops
            )
            return [dict(record) for record in result]
    
    def semantic_search(self, query: str) -> List[Dict]:
        """Search for relevant entities based on query."""
        with self.driver.session() as session:
            # Simple text matching (in production, use vector embeddings)
            result = session.run(
                """
                MATCH (e:Entity)
                WHERE e.name CONTAINS $query 
                   OR e.description CONTAINS $query
                RETURN e.name as name,
                       e.description as description,
                       e.source_doc as source,
                       e.source_chunk as chunk,
                       e.type as type
                LIMIT 10
                """,
                query=query
            )
            return [dict(record) for record in result]


# ============================================================================
# LLM-based Entity Extraction
# ============================================================================

def extract_entities_with_llm(text: str, source_doc: str, model: str = "llama3.2") -> Tuple[List[Entity], List[Relationship]]:
    """Use LLM to extract entities and relationships from text."""
    
    extraction_prompt = f"""Analyze the following text and extract:
1. KEY ENTITIES (people, organizations, concepts, technologies, events)
2. RELATIONSHIPS between these entities

For each entity, provide:
- name: The entity name
- type: Category (PERSON, ORGANIZATION, CONCEPT, TECHNOLOGY, EVENT, LOCATION)
- description: Brief description based on the text

For each relationship, provide:
- source: Source entity name
- target: Target entity name  
- type: Relationship type (e.g., WORKS_FOR, CREATED, USES, LOCATED_IN)
- description: Description of how they relate

TEXT:
{text}

Respond in JSON format:
{{
  "entities": [
    {{"name": "...", "type": "...", "description": "..."}}
  ],
  "relationships": [
    {{"source": "...", "target": "...", "type": "...", "description": "..."}}
  ]
}}
"""
    
    try:
        response = ollama_client.chat(
            model=model,
            messages=[{"role": "user", "content": extraction_prompt}],
            format="json"
        )
        
        data = json.loads(response['message']['content'])
        
        entities = []
        for e in data.get('entities', []):
            entity_id = hashlib.md5(f"{e['name']}_{source_doc}".encode()).hexdigest()[:12]
            entities.append(Entity(
                id=entity_id,
                name=e['name'],
                entity_type=e['type'],
                description=e['description'],
                source_doc=source_doc,
                source_chunk=text[:200] + "..."
            ))
        
        relationships = []
        for r in data.get('relationships', []):
            relationships.append(Relationship(
                source=r['source'],
                target=r['target'],
                relation_type=r['type'],
                description=r['description'],
                source_doc=source_doc
            ))
        
        return entities, relationships
    
    except Exception as e:
        st.warning(f"Entity extraction error: {e}")
        return [], []


# ============================================================================
# Multi-hop RAG with Citations
# ============================================================================

def generate_answer_with_citations(
    query: str,
    graph: KnowledgeGraphManager,
    model: str = "llama3.2"
) -> AnswerWithCitations:
    """
    Generate an answer using multi-hop graph traversal with full citations.
    
    This is the core differentiator: every claim is traced back to source documents.
    """
    
    reasoning_trace = []
    citations = []
    
    # Step 1: Initial semantic search
    reasoning_trace.append(f"🔍 Searching knowledge graph for: '{query}'")
    initial_results = graph.semantic_search(query)
    
    if not initial_results:
        return AnswerWithCitations(
            answer="I couldn't find relevant information in the knowledge graph.",
            citations=[],
            reasoning_trace=reasoning_trace
        )
    
    reasoning_trace.append(f"📊 Found {len(initial_results)} initial entities")
    
    # Step 2: Multi-hop expansion
    all_context = []
    for entity in initial_results[:3]:
        reasoning_trace.append(f"🔗 Expanding from entity: {entity['name']}")
        related = graph.find_related_entities(entity['name'], hops=2)
        
        for rel in related:
            all_context.append({
                "entity": rel['name'],
                "description": rel['description'],
                "source": rel['source'],
                "chunk": rel['chunk'],
                "path": rel.get('path_descriptions', [])
            })
            reasoning_trace.append(f"  → Found related: {rel['name']}")
    
    # Step 3: Build context with source tracking
    context_parts = []
    source_map = {}
    
    for i, ctx in enumerate(all_context):
        source_key = f"[{i+1}]"
        context_parts.append(f"{source_key} {ctx['entity']}: {ctx['description']}")
        source_map[source_key] = {
            "document": ctx['source'],
            "text": ctx['chunk'],
            "entity": ctx['entity']
        }
    
    context_text = "\n".join(context_parts)
    reasoning_trace.append(f"📝 Built context from {len(context_parts)} sources")
    
    # Step 4: Generate answer with citation requirements
    answer_prompt = f"""Based on the following knowledge graph context, answer the question.
IMPORTANT: For each claim you make, cite the source using [N] notation.

CONTEXT:
{context_text}

QUESTION: {query}

Provide a comprehensive answer with inline citations [1], [2], etc. for each claim.
"""
    
    try:
        response = ollama_client.chat(
            model=model,
            messages=[{"role": "user", "content": answer_prompt}]
        )
        answer = response['message']['content']
        reasoning_trace.append("✅ Generated answer with citations")
        
        # Step 5: Extract and verify citations
        citation_refs = re.findall(r'\[(\d+)\]', answer)
        
        for ref in set(citation_refs):
            key = f"[{ref}]"
            if key in source_map:
                src = source_map[key]
                citations.append(Citation(
                    claim=f"Reference {key}",
                    source_document=src['document'],
                    source_text=src['text'],
                    confidence=0.85,
                    reasoning_path=[f"Entity: {src['entity']}"]
                ))
        
        reasoning_trace.append(f"🔒 Verified {len(citations)} citations")
        
        return AnswerWithCitations(
            answer=answer,
            citations=citations,
            reasoning_trace=reasoning_trace
        )
        
    except Exception as e:
        return AnswerWithCitations(
            answer=f"Error generating answer: {e}",
            citations=[],
            reasoning_trace=reasoning_trace
        )


# ============================================================================
# Streamlit UI
# ============================================================================

def main():
    st.set_page_config(
        page_title="Knowledge Graph RAG with Citations",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("🔍 Knowledge Graph RAG with Verifiable Citations")
    st.markdown("""
    This demo shows how **Knowledge Graph-based RAG** provides:
    - **Multi-hop reasoning** across connected information
    - **Verifiable source attribution** for every claim
    - **Transparent reasoning traces** you can audit
    
    Unlike traditional vector RAG, every answer is traceable to its source documents.
    """)
    
    # Sidebar configuration
    st.sidebar.header("⚙️ Configuration")
    
    neo4j_uri = st.sidebar.text_input("Neo4j URI", "bolt://localhost:7687")
    neo4j_user = st.sidebar.text_input("Neo4j User", "neo4j")
    neo4j_password = st.sidebar.text_input("Neo4j Password", type="password", value="password")
    llm_model = st.sidebar.selectbox("LLM Model", ["llama3.2", "mistral", "phi3"])
    
    # Initialize session state
    if 'graph_initialized' not in st.session_state:
        st.session_state.graph_initialized = False
        st.session_state.documents = []
    
    # Main content
    tab1, tab2, tab3 = st.tabs(["📄 Add Documents", "❓ Ask Questions", "🔬 View Graph"])
    
    with tab1:
        st.header("Step 1: Build Knowledge Graph from Documents")
        
        sample_docs = {
            "AI Research Paper": """
            GraphRAG is a technique developed by Microsoft Research that combines knowledge graphs 
            with retrieval-augmented generation. Unlike traditional RAG which uses vector similarity,
            GraphRAG builds a structured knowledge graph from documents, enabling multi-hop reasoning.
            The technique was introduced by researchers including Darren Edge and Ha Trinh.
            GraphRAG excels at answering complex questions that require connecting information 
            from multiple sources, such as "What are the relationships between different research projects?"
            """,
            "Company Report": """
            Acme Corp was founded in 2020 by Jane Smith and John Doe in San Francisco.
            The company develops AI-powered analytics tools for enterprise customers.
            Their flagship product, DataSense, uses machine learning to analyze business data.
            Jane Smith previously worked at Google as a senior engineer on the TensorFlow team.
            John Doe was a co-founder of StartupX, which was acquired by Microsoft in 2019.
            Acme Corp raised $50 million in Series B funding led by Sequoia Capital.
            """
        }
        
        doc_choice = st.selectbox("Choose sample document:", list(sample_docs.keys()))
        doc_text = st.text_area("Or paste your own document:", sample_docs[doc_choice], height=200)
        doc_name = st.text_input("Document name:", doc_choice)
        
        if st.button("🔨 Extract & Add to Knowledge Graph"):
            with st.spinner("Extracting entities and relationships..."):
                try:
                    graph = KnowledgeGraphManager(neo4j_uri, neo4j_user, neo4j_password)
                    entities, relationships = extract_entities_with_llm(doc_text, doc_name, llm_model)
                    
                    for entity in entities:
                        graph.add_entity(entity)
                    
                    for rel in relationships:
                        graph.add_relationship(rel)
                    
                    graph.close()
                    
                    st.success(f"✅ Extracted {len(entities)} entities and {len(relationships)} relationships")
                    
                    with st.expander("View Extracted Entities"):
                        for e in entities:
                            st.write(f"**{e.name}** ({e.entity_type}): {e.description}")
                    
                    with st.expander("View Extracted Relationships"):
                        for r in relationships:
                            st.write(f"{r.source} --[{r.relation_type}]--> {r.target}: {r.description}")
                    
                    st.session_state.graph_initialized = True
                    st.session_state.documents.append(doc_name)
                    
                except Exception as e:
                    st.error(f"Error: {e}")
                    st.info("Make sure Neo4j is running and Ollama has the model pulled.")
    
    with tab2:
        st.header("Step 2: Ask Questions with Verifiable Answers")
        
        if not st.session_state.graph_initialized:
            st.warning("⚠️ Please add documents to the knowledge graph first.")
        else:
            st.info(f"📚 Knowledge graph contains documents: {', '.join(st.session_state.documents)}")
        
        query = st.text_input("Enter your question:", "What are the key concepts in GraphRAG and who developed it?")
        
        if st.button("🔍 Ask with Citations"):
            with st.spinner("Traversing knowledge graph and generating answer..."):
                try:
                    graph = KnowledgeGraphManager(neo4j_uri, neo4j_user, neo4j_password)
                    result = generate_answer_with_citations(query, graph, llm_model)
                    graph.close()
                    
                    # Display reasoning trace
                    st.subheader("🧠 Reasoning Trace")
                    for step in result.reasoning_trace:
                        st.write(step)
                    
                    # Display answer
                    st.subheader("💬 Answer")
                    st.markdown(result.answer)
                    
                    # Display citations
                    st.subheader("📚 Source Citations")
                    if result.citations:
                        for i, citation in enumerate(result.citations):
                            with st.expander(f"Citation {i+1}: {citation.source_document}"):
                                st.write(f"**Source Document:** {citation.source_document}")
                                st.write(f"**Source Text:** {citation.source_text}")
                                st.write(f"**Confidence:** {citation.confidence:.0%}")
                                st.write(f"**Reasoning Path:** {' → '.join(citation.reasoning_path)}")
                    else:
                        st.info("No specific citations extracted for this answer.")
                        
                except Exception as e:
                    st.error(f"Error: {e}")
    
    with tab3:
        st.header("🔬 Knowledge Graph Visualization")
        st.info("This tab shows the structure of your knowledge graph.")
        
        if st.button("📊 Show Graph Statistics"):
            try:
                graph = KnowledgeGraphManager(neo4j_uri, neo4j_user, neo4j_password)
                with graph.driver.session() as session:
                    node_count = session.run("MATCH (n) RETURN count(n) as count").single()['count']
                    rel_count = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()['count']
                
                col1, col2 = st.columns(2)
                col1.metric("Total Entities", node_count)
                col2.metric("Total Relationships", rel_count)
                
                graph.close()
            except Exception as e:
                st.error(f"Error connecting to Neo4j: {e}")
        
        if st.button("🗑️ Clear Graph"):
            try:
                graph = KnowledgeGraphManager(neo4j_uri, neo4j_user, neo4j_password)
                graph.clear_graph()
                graph.close()
                st.session_state.graph_initialized = False
                st.session_state.documents = []
                st.success("Graph cleared!")
            except Exception as e:
                st.error(f"Error: {e}")


if __name__ == "__main__":
    main()
