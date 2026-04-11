"""
FERPA-Compliant RAG Pipeline Demo

Demonstrates identity-scoped pre-filtering for higher-education AI systems.
Documents belonging to a different student or institution are excluded before
they reach the LLM context window — not after.

Requirements:
    pip install enterprise-rag-patterns

Run:
    python app.py
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from enterprise_rag_patterns.compliance import (
    AuditRecord,
    FERPAContextPolicy,
    StudentIdentityScope,
    make_enrollment_advisor_policy,
)


# ---------------------------------------------------------------------------
# Mock vector store
# ---------------------------------------------------------------------------
# In production, replace this with a call to your actual vector store
# (Pinecone, Weaviate, Qdrant, pgvector, Chroma, etc.) that returns
# document dicts with metadata fields.

MOCK_DOCUMENTS: list[dict[str, Any]] = [
    {
        "doc_id": "doc-001",
        "student_id": "student-alice",
        "institution_id": "univ-east",
        "category": "academic_record",
        "content": "Alice enrolled full-time, GPA 3.7, 15 credit hours this term.",
    },
    {
        "doc_id": "doc-002",
        "student_id": "student-alice",
        "institution_id": "univ-east",
        "category": "financial_record",
        "content": "Alice: tuition balance $0. Financial aid disbursed 2026-01-15.",
    },
    {
        "doc_id": "doc-003",
        "student_id": "student-alice",
        "institution_id": "univ-east",
        "category": "counseling_notes",
        "content": "Session notes: career planning discussion, 2026-02-10.",
    },
    {
        "doc_id": "doc-004",
        "student_id": "student-bob",
        "institution_id": "univ-east",
        "category": "academic_record",
        "content": "Bob: enrolled part-time, 6 credit hours.",  # different student
    },
    {
        "doc_id": "doc-005",
        "student_id": "student-carol",
        "institution_id": "univ-west",
        "category": "academic_record",
        "content": "Carol: enrolled at West University, 12 credit hours.",  # different institution
    },
    {
        "doc_id": "doc-006",
        "student_id": "shared",
        "institution_id": "univ-east",
        "category": "policy_document",
        "content": "Enrollment policy: students must register by the add/drop deadline.",
    },
]


def mock_vector_search(
    query: str,
    student_id: str,
    institution_id: str,
) -> list[dict[str, Any]]:
    """
    Simulates a vector store metadata pre-filter query.

    In a real implementation, this is a single query to your vector store with
    a metadata filter expression such as:
        {"$and": [{"student_id": student_id}, {"institution_id": institution_id}]}
    or the equivalent for your vector store's filter syntax.

    The key point: the filter is applied AT QUERY TIME, before semantic ranking.
    Unauthorized documents are never retrieved — they are excluded from the
    candidate set, not filtered out afterward.
    """
    print(f"\n[vector store] query='{query}'")
    print(f"[vector store] metadata filter: student_id='{student_id}' OR shared, institution_id='{institution_id}'")

    results = [
        doc for doc in MOCK_DOCUMENTS
        if doc["institution_id"] == institution_id
        and (doc["student_id"] == student_id or doc["student_id"] == "shared")
    ]
    print(f"[vector store] {len(results)} documents match the pre-filter")
    return results


# ---------------------------------------------------------------------------
# Audit sink
# ---------------------------------------------------------------------------

audit_log: list[AuditRecord] = []


def audit_sink(record: AuditRecord) -> None:
    """Collects audit records. In production: write to your compliance database."""
    audit_log.append(record)


# ---------------------------------------------------------------------------
# Scenario 1: Compliant retrieval — authorized student
# ---------------------------------------------------------------------------

def scenario_authorized_retrieval() -> None:
    print("\n" + "=" * 60)
    print("SCENARIO 1: Authorized student retrieval")
    print("=" * 60)

    scope = StudentIdentityScope(
        student_id="student-alice",
        institution_id="univ-east",
        allowed_categories={"academic_record", "financial_record", "policy_document"},
    )

    policy = FERPAContextPolicy(scope=scope)

    # Step 1: Vector store pre-filter (returns only Alice's + shared docs at univ-east)
    raw_docs = mock_vector_search(
        query="What is my current enrollment status and balance?",
        student_id=scope.student_id,
        institution_id=scope.institution_id,
    )

    # Step 2: Category authorization pass (second layer)
    authorized_docs = policy.filter_retrieved_documents(raw_docs)

    print(f"\n[policy] {len(authorized_docs)} documents authorized for context window:")
    for doc in authorized_docs:
        print(f"  - [{doc['category']}] {doc['doc_id']}: {doc['content'][:60]}...")

    # Step 3: Audit log
    policy.record_access(
        documents_retrieved=len(raw_docs),
        documents_filtered=len(authorized_docs),
        audit_sink=audit_sink,
        requester_context={"session_id": "sess-001", "channel": "web"},
    )
    print(f"\n[audit] AuditRecord recorded. record_id={audit_log[-1].record_id}")


# ---------------------------------------------------------------------------
# Scenario 2: Cross-institution block
# ---------------------------------------------------------------------------

def scenario_cross_institution_block() -> None:
    print("\n" + "=" * 60)
    print("SCENARIO 2: Cross-institution block")
    print("Student from univ-west querying the univ-east system")
    print("=" * 60)

    scope = StudentIdentityScope(
        student_id="student-carol",
        institution_id="univ-west",
        allowed_categories={"academic_record"},
    )

    policy = FERPAContextPolicy(scope=scope)

    # Vector store pre-filter: carol + univ-west — no documents match univ-east corpus
    raw_docs = mock_vector_search(
        query="Show me my enrollment record",
        student_id=scope.student_id,
        institution_id=scope.institution_id,
    )

    authorized_docs = policy.filter_retrieved_documents(raw_docs)
    print(f"\n[policy] {len(authorized_docs)} documents authorized (expected 0 — cross-institution)")

    policy.record_access(
        documents_retrieved=len(raw_docs),
        documents_filtered=len(authorized_docs),
        audit_sink=audit_sink,
        requester_context={"session_id": "sess-002", "channel": "voice"},
    )
    print(f"[audit] Cross-institution access attempt logged. record_id={audit_log[-1].record_id}")


# ---------------------------------------------------------------------------
# Scenario 3: Category authorization — counseling notes restricted
# ---------------------------------------------------------------------------

def scenario_category_restriction() -> None:
    print("\n" + "=" * 60)
    print("SCENARIO 3: Category restriction — counseling notes excluded")
    print("Alice's scope does NOT include counseling_notes")
    print("=" * 60)

    scope = StudentIdentityScope(
        student_id="student-alice",
        institution_id="univ-east",
        allowed_categories={"academic_record", "policy_document"},
        # Note: financial_record and counseling_notes not included
    )

    policy = FERPAContextPolicy(scope=scope)

    # Pre-filter returns Alice's docs at univ-east (including counseling_notes)
    raw_docs = mock_vector_search(
        query="Tell me about my academic standing",
        student_id=scope.student_id,
        institution_id=scope.institution_id,
    )

    authorized_docs = policy.filter_retrieved_documents(raw_docs)

    print(f"\n[policy] {len(raw_docs)} docs from pre-filter → {len(authorized_docs)} after category auth:")
    for doc in authorized_docs:
        print(f"  - [{doc['category']}] {doc['doc_id']}")

    excluded = set(d["doc_id"] for d in raw_docs) - set(d["doc_id"] for d in authorized_docs)
    print(f"[policy] Excluded by category restriction: {excluded}")

    policy.record_access(
        documents_retrieved=len(raw_docs),
        documents_filtered=len(authorized_docs),
        audit_sink=audit_sink,
        requester_context={"session_id": "sess-003", "channel": "dashboard"},
    )


# ---------------------------------------------------------------------------
# Scenario 4: Factory method for common enrollment advisor use case
# ---------------------------------------------------------------------------

def scenario_enrollment_advisor() -> None:
    print("\n" + "=" * 60)
    print("SCENARIO 4: Enrollment advisor policy (factory method)")
    print("=" * 60)

    policy = make_enrollment_advisor_policy(
        student_id="student-alice",
        institution_id="univ-east",
    )

    raw_docs = mock_vector_search(
        query="What courses am I eligible for next term?",
        student_id="student-alice",
        institution_id="univ-east",
    )

    authorized_docs = policy.filter_retrieved_documents(raw_docs)

    print(f"\n[policy] Enrollment advisor scope: {policy.scope.allowed_categories}")
    print(f"[policy] {len(authorized_docs)} documents authorized")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("FERPA-Compliant RAG Pipeline Demo")
    print("enterprise-rag-patterns — https://github.com/ashutoshrana/enterprise-rag-patterns")

    scenario_authorized_retrieval()
    scenario_cross_institution_block()
    scenario_category_restriction()
    scenario_enrollment_advisor()

    print("\n" + "=" * 60)
    print(f"AUDIT LOG: {len(audit_log)} records captured")
    print("=" * 60)
    for record in audit_log:
        entry = record.to_log_entry()
        print(
            f"  record_id={entry['record_id'][:8]}... "
            f"student={entry['student_id']} "
            f"retrieved={entry['documents_retrieved']} "
            f"authorized={entry['documents_filtered']} "
            f"ts={entry['timestamp'][:19]}"
        )

    print("\nKey takeaways:")
    print("  1. Pre-filter at the vector store: unauthorized docs never enter the pipeline")
    print("  2. Category authorization: second layer blocks restricted document types")
    print("  3. Every retrieval event is logged with a typed AuditRecord (34 CFR § 99.32)")
    print("  4. Platform-agnostic: swap mock_vector_search() for any vector store provider")


if __name__ == "__main__":
    main()
