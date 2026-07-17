#!/usr/bin/env python3
"""Deterministic tests for the typed agentic RAG example."""

import asyncio
import os
import unittest
from unittest.mock import patch

from rag import (
    HashingEmbeddingBackend,
    InMemoryVectorStore,
    chunk_text,
    html_to_text,
    ingest_pdf,
    validate_public_url,
)
from agent import (
    Answer,
    Citation,
    RagDependencies,
    answer_question,
    rag_agent,
    resolve_model_name,
    retrieve_evidence,
)


class TypedRagTests(unittest.TestCase):
    def run_async(self, awaitable):
        return asyncio.run(awaitable)

    def make_store(self):
        return InMemoryVectorStore(HashingEmbeddingBackend(dimensions=512))

    def make_pdf(self, text):
        escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        content = f"BT /F1 12 Tf 72 100 Td ({escaped}) Tj ET".encode("ascii")
        objects = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            (
                b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 200] "
                b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>"
            ),
            b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        ]
        payload = b"%PDF-1.4\n"
        offsets = [0]
        for number, value in enumerate(objects, start=1):
            offsets.append(len(payload))
            payload += b"%d 0 obj\n" % number + value + b"\nendobj\n"
        xref_offset = len(payload)
        payload += b"xref\n0 6\n0000000000 65535 f \n"
        payload += b"".join(b"%010d 00000 n \n" % offset for offset in offsets[1:])
        payload += b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n"
        return payload + str(xref_offset).encode("ascii") + b"\n%%EOF\n"

    def test_chunk_text_uses_stable_overlap(self):
        text = " ".join(f"word{number}" for number in range(24))
        chunks = chunk_text(text, chunk_size=10, overlap=2)

        self.assertEqual(3, len(chunks))
        self.assertEqual(chunks[0].split()[-2:], chunks[1].split()[:2])
        self.assertEqual(chunks[1].split()[-2:], chunks[2].split()[:2])

    def test_local_store_ranks_relevant_evidence(self):
        store = self.make_store()
        self.run_async(
            store.add_document(
                "handbook.pdf",
                "Employees receive twelve weeks of paid parental leave after six months of service.",
            )
        )
        self.run_async(
            store.add_document(
                "astronomy.pdf",
                "Europa is an icy moon of Jupiter with a subsurface ocean.",
            )
        )

        relevant = self.run_async(
            store.search("How much parental leave do employees receive?")
        )
        unrelated = self.run_async(
            store.search("What is the production database password?")
        )

        self.assertEqual("handbook.pdf", relevant[0].chunk.source)
        self.assertGreater(relevant[0].score, 0.2)
        self.assertLess(unrelated[0].score, 0.2)

    def test_retrieve_evidence_reports_threshold_decision(self):
        store = self.make_store()
        self.run_async(
            store.add_document(
                "policy.pdf",
                "Expense reports must be submitted within thirty days of travel.",
            )
        )
        deps = RagDependencies(store=store, min_relevance=0.2, top_k=3)

        grounded = self.run_async(
            retrieve_evidence(deps, "When are expense reports due?")
        )
        missing = self.run_async(retrieve_evidence(deps, "Who won the 1978 World Cup?"))

        self.assertTrue(grounded.enough_evidence)
        self.assertFalse(missing.enough_evidence)
        self.assertEqual("policy.pdf", grounded.chunks[0].source)

    def test_pdf_text_is_extracted_and_indexed(self):
        store = self.make_store()
        added = self.run_async(
            ingest_pdf(
                store,
                "policy.pdf",
                self.make_pdf("Travel receipts are required within thirty days."),
            )
        )
        results = self.run_async(store.search("When are travel receipts required?"))

        self.assertEqual(1, added)
        self.assertEqual("policy.pdf:p1:c1", results[0].chunk.chunk_id)
        self.assertGreater(results[0].score, 0.2)

    def test_answer_model_requires_citations_when_answered(self):
        from pydantic import ValidationError

        with self.assertRaises(ValidationError):
            Answer(text="Unsupported", citations=[], confidence=0.8, answered=True)

        with self.assertRaises(ValidationError):
            Answer(
                text="Too confident",
                citations=[Citation(source="x", chunk_id="x:c1", quoted_span="quote")],
                confidence=1.2,
                answered=True,
            )

    def test_out_of_corpus_question_refuses_without_model_request(self):
        from pydantic_ai import models

        store = self.make_store()
        self.run_async(
            store.add_document(
                "benefits.pdf",
                "Dental coverage begins on the first day of employment.",
            )
        )
        deps = RagDependencies(store=store, min_relevance=0.2, top_k=3)
        previous = models.ALLOW_MODEL_REQUESTS
        models.ALLOW_MODEL_REQUESTS = False
        try:
            answer = self.run_async(
                answer_question("How do I configure a Kubernetes ingress?", deps)
            )
        finally:
            models.ALLOW_MODEL_REQUESTS = previous

        self.assertFalse(answer.answered)
        self.assertEqual([], answer.citations)
        self.assertIn("enough evidence", answer.text.lower())

    def test_agent_calls_retrieve_and_returns_typed_cited_answer(self):
        from pydantic_ai import capture_run_messages, models
        from pydantic_ai.models.test import TestModel

        store = self.make_store()
        self.run_async(
            store.add_document(
                "atlas-handbook.pdf",
                "The Atlas handbook grants twelve weeks of paid parental leave.",
            )
        )
        chunk = store.chunks[0]
        deps = RagDependencies(store=store, min_relevance=0.2, top_k=3)
        model = TestModel(
            call_tools=["retrieve"],
            custom_output_args={
                "text": "Atlas grants twelve weeks of paid parental leave.",
                "citations": [
                    {
                        "source": chunk.source,
                        "chunk_id": chunk.chunk_id,
                        "quoted_span": "twelve weeks of paid parental leave",
                    }
                ],
                "confidence": 0.91,
                "answered": True,
            },
        )
        previous = models.ALLOW_MODEL_REQUESTS
        models.ALLOW_MODEL_REQUESTS = False
        try:
            with capture_run_messages() as messages:
                with rag_agent.override(model=model):
                    answer = self.run_async(
                        answer_question(
                            "How much parental leave does Atlas grant?", deps
                        )
                    )
        finally:
            models.ALLOW_MODEL_REQUESTS = previous

        tool_names = [
            getattr(part, "tool_name", "")
            for message in messages
            for part in message.parts
        ]
        self.assertIsInstance(answer, Answer)
        self.assertTrue(answer.answered)
        self.assertEqual("atlas-handbook.pdf", answer.citations[0].source)
        self.assertIn("retrieve", tool_names)

    def test_forged_citation_forces_refusal(self):
        from pydantic_ai import models
        from pydantic_ai.models.test import TestModel

        store = self.make_store()
        self.run_async(
            store.add_document(
                "travel.pdf",
                "The meal allowance is seventy dollars per day.",
            )
        )
        chunk = store.chunks[0]
        deps = RagDependencies(store=store, min_relevance=0.2, top_k=3)
        model = TestModel(
            call_tools=["retrieve"],
            custom_output_args={
                "text": "The allowance is one hundred dollars.",
                "citations": [
                    {
                        "source": chunk.source,
                        "chunk_id": chunk.chunk_id,
                        "quoted_span": "one hundred dollars per day",
                    }
                ],
                "confidence": 0.95,
                "answered": True,
            },
        )
        previous = models.ALLOW_MODEL_REQUESTS
        models.ALLOW_MODEL_REQUESTS = False
        try:
            with rag_agent.override(model=model):
                answer = self.run_async(
                    answer_question("What is the daily meal allowance?", deps)
                )
        finally:
            models.ALLOW_MODEL_REQUESTS = previous

        self.assertFalse(answer.answered)
        self.assertEqual([], answer.citations)

    def test_model_resolution_supports_both_providers(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "key"}, clear=True):
            self.assertEqual("openai:gpt-5.2", resolve_model_name())
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "key"}, clear=True):
            self.assertEqual("anthropic:claude-sonnet-4-6", resolve_model_name())
        with patch.dict(os.environ, {"RAG_MODEL": "anthropic:custom"}, clear=True):
            self.assertEqual("anthropic:custom", resolve_model_name())

    def test_html_to_text_ignores_scripts_and_styles(self):
        html = """
        <html><head><style>.hidden { display: none; }</style></head>
        <body><h1>Policy</h1><p>Travel receipts are required.</p>
        <script>window.secret = 'ignore';</script></body></html>
        """
        text = html_to_text(html)

        self.assertIn("Policy", text)
        self.assertIn("Travel receipts are required.", text)
        self.assertNotIn("window.secret", text)
        self.assertNotIn("display: none", text)

    def test_private_docs_urls_are_rejected(self):
        private_urls = (
            "http://localhost/docs",
            "http://127.0.0.1/admin",
            "http://[::1]/admin",
            "http://169.254.169.254/latest/meta-data",
            "http://10.0.0.4/internal",
        )
        for url in private_urls:
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    validate_public_url(url)


if __name__ == "__main__":
    unittest.main(verbosity=2)
