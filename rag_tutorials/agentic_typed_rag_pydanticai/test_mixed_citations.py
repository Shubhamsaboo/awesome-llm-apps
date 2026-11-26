"""A valid quote must not make a mixed, partially fabricated answer pass."""

import ast
import asyncio
from dataclasses import dataclass
from pathlib import Path
import re
import unittest

from pydantic import BaseModel, Field, field_validator, model_validator

from rag import HashingEmbeddingBackend, InMemoryVectorStore


def load_validation():
    # Run the real models/validation functions without constructing a paid agent.
    source = Path(__file__).with_name("agent.py")
    names = {"Citation", "Answer", "RetrievedChunk", "RetrievalEvidence", "RagDependencies",
             "_normalize_quote", "_valid_citations", "validate_grounded_answer"}
    tree = ast.parse(source.read_text())
    nodes = [node for node in tree.body if getattr(node, "name", None) in names]
    namespace = {
        "BaseModel": BaseModel, "Field": Field, "field_validator": field_validator,
        "model_validator": model_validator, "dataclass": dataclass, "re": re,
        "InMemoryVectorStore": InMemoryVectorStore, "DEFAULT_MIN_RELEVANCE": 0.2,
        "REFUSAL_TEXT": "I do not have enough evidence in the indexed sources to answer that question.",
    }
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), "exec"), namespace)
    return namespace


class MixedCitationTests(unittest.TestCase):
    def setUp(self):
        self.code = load_validation()
        store = InMemoryVectorStore(HashingEmbeddingBackend())
        asyncio.run(store.add_document("travel.pdf", "The meal allowance is seventy dollars per day."))
        chunk = store.chunks[0]
        self.good = self.code["Citation"](source=chunk.source, chunk_id=chunk.chunk_id,
                                          quoted_span="seventy dollars per day")
        self.bad = self.code["Citation"](source=chunk.source, chunk_id=chunk.chunk_id,
                                         quoted_span="Taxi reimbursement is unlimited")
        self.deps = self.code["RagDependencies"](store=store)
        self.preflight = self.code["RetrievalEvidence"](
            query="What expenses are covered?", enough_evidence=True, top_score=0.8, chunks=[]
        )

    def validate(self, citations, text="Meals are seventy dollars per day, and taxis are unlimited."):
        answer = self.code["Answer"](
            text=text,
            citations=citations, confidence=0.9, answered=True,
        )
        return self.code["validate_grounded_answer"](
            answer, self.deps, self.preflight, used_retrieve=True
        )

    def test_mixed_valid_and_fabricated_citations_refuse_the_whole_answer(self):
        result = self.validate([self.good, self.bad])
        self.assertFalse(result.answered)
        self.assertEqual(result.citations, [])
        self.assertNotIn("taxis are unlimited", result.text)

    def test_fully_verified_citations_are_preserved(self):
        result = self.validate([self.good], text="Meals are seventy dollars per day.")
        self.assertTrue(result.answered)
        self.assertEqual(result.citations, [self.good])

    def test_all_fabricated_citations_still_refuse(self):
        self.assertFalse(self.validate([self.bad]).answered)


if __name__ == "__main__":
    unittest.main()
