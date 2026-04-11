# FERPA-Compliant RAG Pipeline

A complete, runnable reference implementation of a retrieval-augmented generation
pipeline that enforces FERPA (Family Educational Rights and Privacy Act) identity
boundaries before documents reach the LLM context window.

Designed for higher education AI systems where student records must not cross
institutional or identity boundaries during retrieval.

## What this demonstrates

- **Pre-filter identity enforcement:** student records are filtered *before*
  semantic ranking — unauthorized documents never enter the retrieval pipeline
- **Two-layer access control:** Layer 1 = identity scope (student_id + institution_id);
  Layer 2 = category authorization (transcript, financial, counseling, etc.)
- **Structured audit logging:** every retrieval event produces a typed `AuditRecord`
  compliant with 34 CFR § 99.32 disclosure record requirements
- **Cross-institution blocking:** documents belonging to a different institution
  are excluded even if semantically relevant to the query
- **Platform-agnostic design:** works with any vector store that supports metadata
  filtering (Pinecone, Weaviate, Qdrant, pgvector, Chroma, and others)

## Architecture

```
Query
  │
  ▼
Identity Scope Construction
(student_id + institution_id + allowed_categories)
  │
  ▼
Vector Store Pre-filter
(metadata constraint: student_id match + institution_id match)
  │
  ▼
Semantic Ranking
(only authorized documents scored)
  │
  ▼
Category Authorization
(second pass: filter by allowed document types)
  │
  ▼
Context Assembly
  │
  ▼
LLM Call
  │
  ▼
Audit Log (34 CFR § 99.32)
```

## Requirements

```
pip install enterprise-rag-patterns
```

Or to run with this demo:

```
pip install -r requirements.txt
```

## Usage

```python
python app.py
```

The script demonstrates:
1. A compliant retrieval for an authorized student
2. Cross-institution blocking (different institution_id = no results)
3. Category authorization (counseling_notes not in allowed_categories = filtered)
4. Audit record output for each retrieval event

## Technologies

- **Compliance framework:** [enterprise-rag-patterns](https://github.com/ashutoshrana/enterprise-rag-patterns)
- **Pattern:** Identity-scoped pre-filter + category authorization
- **Regulation:** FERPA (20 U.S.C. § 1232g; 34 CFR Part 99)
- **Vector store integration:** Platform-agnostic (mock store in demo; swap for any provider)
- **Python version:** 3.10+

## Extending this example

- **Replace the mock vector store** with your actual provider — the
  `FERPAContextPolicy.filter_retrieved_documents()` call is provider-agnostic
- **Wire a real audit sink** — replace `audit_log.append` with a write to
  your compliance database or structured log stream
- **Apply to HIPAA or GLBA** — the same two-layer enforcement pattern applies
  to any regulation requiring identity-scoped record access

## Source

Full documentation and additional modules: [enterprise-rag-patterns](https://github.com/ashutoshrana/enterprise-rag-patterns)
