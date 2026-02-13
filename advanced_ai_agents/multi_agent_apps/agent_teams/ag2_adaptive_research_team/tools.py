from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List

from pypdf import PdfReader
from autogen.tools.experimental import SearxngSearchTool


@dataclass
class Document:
    name: str
    text: str


@dataclass
class Chunk:
    doc_name: str
    chunk_id: int
    text: str


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z0-9]+", text.lower())


def load_documents(uploaded_files: Iterable) -> List[Document]:
    documents: List[Document] = []

    for file in uploaded_files:
        name = file.name
        if name.lower().endswith(".pdf"):
            reader = PdfReader(file)
            pages_text = []
            for page in reader.pages:
                pages_text.append(page.extract_text() or "")
            text = _clean_text("\n".join(pages_text))
        else:
            raw = file.read()
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                text = raw.decode("latin-1")
            text = _clean_text(text)

        if text:
            documents.append(Document(name=name, text=text))

    return documents


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 120) -> List[str]:
    words = text.split()
    if not words:
        return []

    chunks: List[str] = []
    start = 0
    while start < len(words):
        end = min(len(words), start + chunk_size)
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end == len(words):
            break
        start = max(0, end - overlap)

    return chunks


def build_local_index(documents: List[Document]) -> List[Chunk]:
    index: List[Chunk] = []
    for doc in documents:
        chunks = chunk_text(doc.text)
        for idx, chunk in enumerate(chunks, start=1):
            index.append(Chunk(doc_name=doc.name, chunk_id=idx, text=chunk))
    return index


def search_local(query: str, index: List[Chunk], top_k: int = 5) -> List[Chunk]:
    query_tokens = set(_tokenize(query))
    scored = []
    for chunk in index:
        chunk_tokens = set(_tokenize(chunk.text))
        overlap = len(query_tokens & chunk_tokens)
        if overlap == 0:
            continue
        scored.append((overlap, chunk))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [item[1] for item in scored[:top_k]]


def run_searxng(query: str, base_url: str, max_results: int = 5) -> List[dict]:
    tool = SearxngSearchTool(base_url=base_url)
    results = tool(query=query, max_results=max_results)
    if isinstance(results, dict):
        return results.get("results", [])
    if isinstance(results, list):
        return results
    return []
