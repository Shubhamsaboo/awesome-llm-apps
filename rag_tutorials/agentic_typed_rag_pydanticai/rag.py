"""Document ingestion and a small in-memory vector store."""

from __future__ import annotations

import hashlib
import io
import ipaddress
import math
import os
import re
import socket
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Protocol, Sequence
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

import numpy as np


DEFAULT_CHUNK_SIZE = 180
DEFAULT_CHUNK_OVERLAP = 30
DEFAULT_EMBEDDING_MODEL = "openai:text-embedding-3-small"
MAX_URL_BYTES = 2_000_000

_STOP_WORDS = {
    "a",
    "about",
    "after",
    "all",
    "also",
    "am",
    "an",
    "and",
    "any",
    "are",
    "as",
    "at",
    "be",
    "because",
    "been",
    "before",
    "being",
    "but",
    "by",
    "can",
    "do",
    "does",
    "for",
    "from",
    "had",
    "has",
    "have",
    "how",
    "i",
    "if",
    "in",
    "into",
    "is",
    "it",
    "its",
    "me",
    "more",
    "most",
    "my",
    "no",
    "not",
    "of",
    "on",
    "or",
    "our",
    "so",
    "than",
    "that",
    "the",
    "their",
    "then",
    "there",
    "these",
    "they",
    "this",
    "to",
    "up",
    "was",
    "we",
    "were",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "will",
    "with",
    "would",
    "you",
    "your",
}


@dataclass(frozen=True)
class DocumentChunk:
    """A source span stored in the vector index."""

    source: str
    chunk_id: str
    text: str


@dataclass(frozen=True)
class SearchResult:
    """A chunk paired with its cosine similarity."""

    chunk: DocumentChunk
    score: float


class EmbeddingBackend(Protocol):
    """Interface shared by hosted and local embedding backends."""

    name: str

    async def embed_documents(self, texts: Sequence[str]) -> Sequence[Sequence[float]]:
        """Embed document chunks."""

    async def embed_query(self, text: str) -> Sequence[float]:
        """Embed a search query."""


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    """Split text into word windows with deterministic overlap."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be non-negative and smaller than chunk_size")

    words = text.split()
    if not words:
        return []

    chunks = []
    step = chunk_size - overlap
    for start in range(0, len(words), step):
        window = words[start : start + chunk_size]
        if not window:
            break
        chunks.append(" ".join(window))
        if start + chunk_size >= len(words):
            break
    return chunks


def _document_chunks(
    source: str,
    text: str,
    *,
    locator: str | None,
    chunk_size: int,
    overlap: int,
) -> list[DocumentChunk]:
    texts = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
    prefix = f"{source}:{locator}" if locator else source
    return [
        DocumentChunk(source=source, chunk_id=f"{prefix}:c{index}", text=value)
        for index, value in enumerate(texts, start=1)
    ]


def _stem(token: str) -> str:
    for suffix in ("ingly", "edly", "ing", "ed", "es", "s"):
        if token.endswith(suffix) and len(token) > len(suffix) + 3:
            return token[: -len(suffix)]
    return token


def _terms(text: str) -> list[str]:
    tokens = [
        _stem(token)
        for token in re.findall(r"[a-z0-9]+", text.casefold())
        if token not in _STOP_WORDS
    ]
    bigrams = [f"{left}:{right}" for left, right in zip(tokens, tokens[1:])]
    return tokens + bigrams


class HashingEmbeddingBackend:
    """Offline fallback that maps normalized terms into a fixed vector."""

    def __init__(self, dimensions: int = 768):
        if dimensions < 64:
            raise ValueError("dimensions must be at least 64")
        self.dimensions = dimensions
        self.name = f"local-hashing-{dimensions}"

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for term in _terms(text):
            digest = hashlib.blake2b(term.encode("utf-8"), digest_size=8).digest()
            position = int.from_bytes(digest, "big") % self.dimensions
            sign = 1.0 if digest[0] & 1 else -1.0
            vector[position] += sign

        norm = math.sqrt(sum(value * value for value in vector))
        if norm:
            vector = [value / norm for value in vector]
        return vector

    async def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    async def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


class OpenAIEmbeddingBackend:
    """OpenAI embeddings through Pydantic AI's typed Embedder client."""

    def __init__(self, model: str = DEFAULT_EMBEDDING_MODEL):
        self.name = model

    def _embedder(self):
        from pydantic_ai import Embedder

        return Embedder(self.name)

    async def embed_documents(self, texts: Sequence[str]) -> Sequence[Sequence[float]]:
        result = await self._embedder().embed_documents(list(texts))
        return result.embeddings

    async def embed_query(self, text: str) -> Sequence[float]:
        result = await self._embedder().embed_query(text)
        return result.embeddings[0]


def default_embedding_backend() -> EmbeddingBackend:
    """Use hosted embeddings when possible, otherwise stay fully local."""
    if os.getenv("OPENAI_API_KEY"):
        return OpenAIEmbeddingBackend()
    return HashingEmbeddingBackend()


class InMemoryVectorStore:
    """A NumPy cosine index intended for small, session-scoped corpora."""

    def __init__(self, embedding_backend: EmbeddingBackend):
        self.embedding_backend = embedding_backend
        self._chunks: list[DocumentChunk] = []
        self._vectors: np.ndarray | None = None

    @property
    def chunks(self) -> tuple[DocumentChunk, ...]:
        return tuple(self._chunks)

    @property
    def count(self) -> int:
        return len(self._chunks)

    @property
    def sources(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(chunk.source for chunk in self._chunks))

    def clear(self) -> None:
        self._chunks.clear()
        self._vectors = None

    async def add_document(
        self,
        source: str,
        text: str,
        *,
        locator: str | None = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        overlap: int = DEFAULT_CHUNK_OVERLAP,
    ) -> int:
        """Chunk, embed, and append one document to the index."""
        source = source.strip()
        if not source:
            raise ValueError("source must not be empty")

        chunks = _document_chunks(
            source,
            text,
            locator=locator,
            chunk_size=chunk_size,
            overlap=overlap,
        )
        return await self.add_chunks(chunks)

    async def add_chunks(self, chunks: Sequence[DocumentChunk]) -> int:
        """Embed and append prepared chunks in one provider request."""
        if not chunks:
            return 0

        texts = [chunk.text for chunk in chunks]
        vectors = np.asarray(
            await self.embedding_backend.embed_documents(texts), dtype=np.float32
        )
        if vectors.ndim != 2 or vectors.shape[0] != len(chunks):
            raise ValueError("embedding backend returned an unexpected shape")
        vectors = _normalize_rows(vectors)

        if self._vectors is not None and self._vectors.shape[1] != vectors.shape[1]:
            raise ValueError("embedding dimensions changed within one index")

        self._chunks.extend(chunks)
        self._vectors = (
            vectors if self._vectors is None else np.vstack((self._vectors, vectors))
        )
        return len(chunks)

    async def search(self, query: str, limit: int = 4) -> list[SearchResult]:
        """Return the nearest chunks ordered by cosine similarity."""
        if not query.strip() or limit <= 0 or self._vectors is None:
            return []

        query_vector = np.asarray(
            await self.embedding_backend.embed_query(query), dtype=np.float32
        )
        if query_vector.ndim != 1 or query_vector.shape[0] != self._vectors.shape[1]:
            raise ValueError("query embedding dimensions do not match the index")

        norm = float(np.linalg.norm(query_vector))
        if not norm:
            scores = np.zeros(len(self._chunks), dtype=np.float32)
        else:
            scores = self._vectors @ (query_vector / norm)
        order = np.argsort(scores)[::-1][:limit]
        return [
            SearchResult(
                chunk=self._chunks[int(index)],
                score=round(float(np.clip(scores[index], 0.0, 1.0)), 4),
            )
            for index in order
        ]

    def find_chunk(self, source: str, chunk_id: str) -> DocumentChunk | None:
        for chunk in self._chunks:
            if chunk.source == source and chunk.chunk_id == chunk_id:
                return chunk
        return None


def _normalize_rows(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return np.divide(vectors, norms, out=np.zeros_like(vectors), where=norms != 0)


def extract_pdf_pages(data: bytes) -> list[str]:
    """Extract text page by page from a PDF byte string."""
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return [(page.extract_text() or "").strip() for page in reader.pages]


async def ingest_pdf(store: InMemoryVectorStore, source: str, data: bytes) -> int:
    """Extract and index all text-bearing pages from a PDF."""
    pages = extract_pdf_pages(data)
    chunks = []
    for page_number, text in enumerate(pages, start=1):
        if text:
            chunks.extend(
                _document_chunks(
                    source,
                    text,
                    locator=f"p{page_number}",
                    chunk_size=DEFAULT_CHUNK_SIZE,
                    overlap=DEFAULT_CHUNK_OVERLAP,
                )
            )
    if not chunks:
        raise ValueError(f"No extractable text found in {source}")
    return await store.add_chunks(chunks)


class _ReadableHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in {"script", "style", "noscript"}:
            self._ignored_depth += 1
        elif tag in {"br", "p", "div", "article", "section", "li", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self._ignored_depth:
            self._ignored_depth -= 1
        elif tag in {"p", "div", "article", "section", "li", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._ignored_depth:
            self.parts.append(data)


def html_to_text(html: str) -> str:
    """Reduce HTML to readable text without third-party parsers."""
    parser = _ReadableHTMLParser()
    parser.feed(html)
    lines = [" ".join(line.split()) for line in "".join(parser.parts).splitlines()]
    return "\n".join(line for line in lines if line)


def validate_public_url(url: str) -> None:
    """Reject malformed URLs and hosts that resolve outside the public internet."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("URL must use http or https")
    if parsed.username or parsed.password:
        raise ValueError("URL credentials are not supported")

    hostname = parsed.hostname.rstrip(".").casefold()
    if hostname == "localhost":
        raise ValueError("Private or local URLs are not supported")

    try:
        addresses = {ipaddress.ip_address(hostname)}
    except ValueError:
        try:
            answers = socket.getaddrinfo(hostname, parsed.port, type=socket.SOCK_STREAM)
        except socket.gaierror as exc:
            raise ValueError(f"Could not resolve URL host: {hostname}") from exc
        addresses = {
            ipaddress.ip_address(answer[4][0].split("%", 1)[0]) for answer in answers
        }

    if not addresses or any(not address.is_global for address in addresses):
        raise ValueError("Private or local URLs are not supported")


class _PublicRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_public_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_url_text(url: str) -> str:
    """Fetch a bounded HTTP document and return readable text."""
    validate_public_url(url)
    request = Request(url, headers={"User-Agent": "typed-rag-demo/1.0"})
    opener = build_opener(_PublicRedirectHandler())
    with opener.open(request, timeout=15) as response:
        content_type = response.headers.get_content_type()
        if content_type not in {"text/html", "text/plain"}:
            raise ValueError(f"Unsupported URL content type: {content_type}")
        body = response.read(MAX_URL_BYTES + 1)
        if len(body) > MAX_URL_BYTES:
            raise ValueError("URL content is larger than 2 MB")
        charset = response.headers.get_content_charset() or "utf-8"

    decoded = body.decode(charset, errors="replace")
    text = html_to_text(decoded) if content_type == "text/html" else decoded.strip()
    if not text:
        raise ValueError("No readable text found at URL")
    return text
