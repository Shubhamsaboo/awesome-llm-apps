import math
import os
import re
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types


EMBED_MODEL = "gemini-embedding-2"
DEFAULT_DIMENSIONS = 768
CHUNK_WORDS = 170
CHUNK_OVERLAP = 35
INLINE_MEDIA_LIMIT_BYTES = 18 * 1024 * 1024
FILE_API_POLL_SECONDS = 2
FILE_API_MAX_WAIT_SECONDS = 90


MODALITY_COLORS = {
    "text": "#9fc9a2",
    "url": "#9fbbe0",
    "pdf": "#c08532",
    "image": "#c0a8dd",
    "audio": "#dfa88f",
    "video": "#e6e5e0",
    "query": "#f54e00",
}


@dataclass
class RackChunk:
    id: str
    source_id: str
    title: str
    modality: str
    text: str
    vector: list[float]
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)


@dataclass
class RackSource:
    id: str
    title: str
    modality: str
    summary: str
    chunks: int
    created_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if not norm_a or not norm_b:
        return 0.0
    return dot / (norm_a * norm_b)


def _clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text


def _chunk_text(text: str) -> list[str]:
    words = _clean_text(text).split()
    if not words:
        return []
    if len(words) <= CHUNK_WORDS:
        return [" ".join(words)]

    chunks: list[str] = []
    step = max(1, CHUNK_WORDS - CHUNK_OVERLAP)
    for start in range(0, len(words), step):
        chunk = words[start : start + CHUNK_WORDS]
        if len(chunk) >= 25:
            chunks.append(" ".join(chunk))
    return chunks


def _blend_vectors(primary: list[float], secondary: list[float], secondary_weight: float = 0.32) -> list[float]:
    primary_weight = 1.0 - secondary_weight
    blended = [
        (left * primary_weight) + (right * secondary_weight)
        for left, right in zip(primary, secondary)
    ]
    norm = math.sqrt(sum(value * value for value in blended)) or 1.0
    return [value / norm for value in blended]


def _dot(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def _normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm < 1e-12:
        return [0.0] * len(vector)
    return [value / norm for value in vector]


def _orthogonalize(vector: list[float], components: list[list[float]]) -> list[float]:
    adjusted = vector[:]
    for component in components:
        projection = _dot(adjusted, component)
        adjusted = [value - projection * component[index] for index, value in enumerate(adjusted)]
    return adjusted


class MultimodalRagStore:
    def __init__(self, dimensions: int = DEFAULT_DIMENSIONS):
        self.dimensions = dimensions
        self.api_key = os.getenv("GOOGLE_API_KEY", "")
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None
        self.sources: list[RackSource] = []
        self.chunks: list[RackChunk] = []
        self.events: list[dict[str, Any]] = []
        self._lock = threading.RLock()
        self.embedding_provider = "gemini-embedding-2"

    def _require_client(self) -> genai.Client:
        if not self.client:
            raise RuntimeError("GOOGLE_API_KEY is required for Gemini Embedding 2.")
        return self.client

    def _emit(self, event_type: str, payload: dict[str, Any]) -> None:
        self.events.append({"type": event_type, "at": time.time(), **payload})
        self.events = self.events[-80:]

    def _embed_text(self, text: str, task_prefix: str) -> list[float]:
        content = f"{task_prefix}: {text}"
        client = self._require_client()

        result = client.models.embed_content(
            model=EMBED_MODEL,
            contents=[content],
            config=types.EmbedContentConfig(output_dimensionality=self.dimensions),
        )
        return result.embeddings[0].values

    def _embed_uploaded_file(self, data: bytes, mime_type: str, title: str) -> list[float]:
        client = self._require_client()
        suffix = Path(title).suffix or self._suffix_from_mime(mime_type)
        uploaded = None
        try:
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=True) as temp_file:
                temp_file.write(data)
                temp_file.flush()
                uploaded = client.files.upload(
                    file=temp_file.name,
                    config=types.UploadFileConfig(mime_type=mime_type, display_name=title),
                )

            waited = 0
            while getattr(getattr(uploaded, "state", None), "name", "") == "PROCESSING":
                if waited >= FILE_API_MAX_WAIT_SECONDS:
                    raise ValueError("Gemini is still processing this media file. Try a shorter clip or upload it again in a moment.")
                time.sleep(FILE_API_POLL_SECONDS)
                waited += FILE_API_POLL_SECONDS
                uploaded = client.files.get(name=uploaded.name)

            state_name = getattr(getattr(uploaded, "state", None), "name", "")
            if state_name and state_name not in {"ACTIVE", "SUCCEEDED"}:
                raise ValueError(f"Gemini could not process this media file. File state: {state_name}.")

            part = types.Part.from_uri(file_uri=uploaded.uri, mime_type=mime_type)
            result = client.models.embed_content(
                model=EMBED_MODEL,
                contents=[part],
                config=types.EmbedContentConfig(output_dimensionality=self.dimensions),
            )
            return result.embeddings[0].values
        finally:
            uploaded_name = getattr(uploaded, "name", None)
            if uploaded_name:
                try:
                    client.files.delete(name=uploaded_name)
                except Exception as exc:
                    self._emit("file_cleanup_failed", {"name": uploaded_name, "error": str(exc)})

    def _embed_file(self, data: bytes, mime_type: str, title: str, notes: str) -> tuple[list[float], str]:
        client = self._require_client()

        use_file_api = (
            len(data) > INLINE_MEDIA_LIMIT_BYTES
            or mime_type.startswith("video/")
            or mime_type.startswith("audio/")
        )
        if use_file_api:
            return self._embed_uploaded_file(data, mime_type, title), "gemini-file-api"

        part = types.Part.from_bytes(data=data, mime_type=mime_type)
        try:
            result = client.models.embed_content(
                model=EMBED_MODEL,
                contents=[part],
                config=types.EmbedContentConfig(output_dimensionality=self.dimensions),
            )
            return result.embeddings[0].values, "gemini-inline"
        except Exception:
            if mime_type.startswith(("video/", "audio/")) or mime_type == "application/pdf":
                return self._embed_uploaded_file(data, mime_type, title), "gemini-file-api"
            raise

    def _pca_projection(self, vectors: dict[str, list[float]]) -> dict[str, dict[str, float]]:
        if not vectors:
            return {}

        ids = list(vectors)
        rows = [vectors[item_id][: self.dimensions] for item_id in ids]
        if len(rows) == 1:
            return {ids[0]: {"x": 0.0, "y": 0.0, "z": 0.0}}

        means = [sum(row[index] for row in rows) / len(rows) for index in range(self.dimensions)]
        centered = [[row[index] - means[index] for index in range(self.dimensions)] for row in rows]
        components: list[list[float]] = []

        for component_index in range(3):
            candidate = [
                math.sin((index + 1) * (component_index + 1) * 0.017)
                + math.cos((index + 1) * (component_index + 2) * 0.013)
                for index in range(self.dimensions)
            ]
            candidate = _normalize(_orthogonalize(candidate, components))

            for _ in range(24):
                scores = [_dot(row, candidate) for row in centered]
                next_candidate = [0.0] * self.dimensions
                for score, row in zip(scores, centered):
                    for index, value in enumerate(row):
                        next_candidate[index] += score * value
                next_candidate = _normalize(_orthogonalize(next_candidate, components))
                if not any(next_candidate):
                    break
                candidate = next_candidate

            if not any(candidate):
                candidate = [0.0] * self.dimensions
                candidate[min(component_index, self.dimensions - 1)] = 1.0
            components.append(candidate)

        raw = {
            item_id: [_dot(row, component) for component in components]
            for item_id, row in zip(ids, centered)
        }
        max_radius = max(
            math.sqrt(values[0] * values[0] + values[1] * values[1] + values[2] * values[2])
            for values in raw.values()
        ) or 1.0
        scale = 2.65 / max_radius
        return {
            item_id: {
                "x": round(values[0] * scale, 4),
                "y": round(values[1] * scale, 4),
                "z": round(values[2] * scale, 4),
            }
            for item_id, values in raw.items()
        }

    def _chunks_for_source(self, source_id: str) -> list[RackChunk]:
        return [chunk for chunk in self.chunks if chunk.source_id == source_id]

    def _source_vector(self, source_id: str) -> list[float]:
        chunks = self._chunks_for_source(source_id)
        if not chunks:
            return [0.0] * self.dimensions

        vector = [0.0] * self.dimensions
        for chunk in chunks:
            for index, value in enumerate(chunk.vector[: self.dimensions]):
                vector[index] += value
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    def _source_vectors(self) -> dict[str, list[float]]:
        return {source.id: self._source_vector(source.id) for source in self.sources}

    def _source_point(self, source: RackSource, projection: dict[str, float]) -> dict[str, Any]:
        return {
            "id": source.id,
            "source_id": source.id,
            "title": source.title,
            "modality": source.modality,
            "projection": projection,
            "color": MODALITY_COLORS.get(source.modality, "#94a3b8"),
            "preview": source.summary,
        }

    def add_text_source(self, title: str, text: str, modality: str = "text", seed: bool = False) -> RackSource:
        with self._lock:
            source_id = uuid.uuid4().hex[:10]
            chunks = _chunk_text(text)
            if not chunks:
                raise ValueError("Source text is empty.")

            source = RackSource(
                id=source_id,
                title=title.strip() or f"{modality.title()} source",
                modality=modality,
                summary=_clean_text(text)[:220],
                chunks=len(chunks),
            )
            pending_chunks = []
            for index, chunk_text in enumerate(chunks):
                vector = self._embed_text(chunk_text, "task: retrieval document")
                chunk = RackChunk(
                    id=f"{source_id}-{index + 1}",
                    source_id=source_id,
                    title=source.title,
                    modality=modality,
                    text=chunk_text,
                    vector=vector,
                    metadata={"chunk_index": index + 1},
                )
                pending_chunks.append(chunk)

            # Publish the source only after every embedding succeeded. A failed
            # request must not leave partial evidence that appears in retrieval.
            self.sources.append(source)
            self.chunks.extend(pending_chunks)

            if not seed:
                self._emit("source_added", {"source_id": source_id, "title": source.title, "chunks": len(chunks)})
            return source

    def add_file_source(self, title: str, data: bytes, mime_type: str, notes: str = "") -> RackSource:
        with self._lock:
            modality = self._modality_from_mime(mime_type)
            source_id = uuid.uuid4().hex[:10]
            display_text = _clean_text(notes) or f"{title} ({mime_type}) embedded natively in Gemini Embedding 2."
            media_vector, embedding_path = self._embed_file(data, mime_type, title, display_text)
            annotation_text = _clean_text(f"{title}. {display_text}")
            annotation_vector = self._embed_text(annotation_text, "task: retrieval document")
            vector = _blend_vectors(media_vector, annotation_vector)
            source = RackSource(
                id=source_id,
                title=title.strip() or "Uploaded source",
                modality=modality,
                summary=display_text[:220],
                chunks=1,
                metadata={
                    "mime_type": mime_type,
                    "bytes": len(data),
                    "embedding_path": embedding_path,
                    "annotation_blended": True,
                },
            )
            chunk = RackChunk(
                id=f"{source_id}-1",
                source_id=source_id,
                title=source.title,
                modality=modality,
                text=display_text,
                vector=vector,
                metadata={
                    "mime_type": mime_type,
                    "bytes": len(data),
                    "native_multimodal": bool(self.client),
                    "embedding_path": embedding_path,
                    "annotation_blended": True,
                },
            )
            self.sources.append(source)
            self.chunks.append(chunk)
            self._emit("source_added", {"source_id": source_id, "title": source.title, "chunks": 1})
            return source

    def remove_source(self, source_id: str) -> bool:
        with self._lock:
            source = next((item for item in self.sources if item.id == source_id), None)
            if not source:
                return False

            self.sources = [item for item in self.sources if item.id != source_id]
            self.chunks = [chunk for chunk in self.chunks if chunk.source_id != source_id]
            self._emit("source_removed", {"source_id": source_id, "title": source.title})
            return True

    def search(self, query: str, top_k: int = 6) -> dict[str, Any]:
        with self._lock:
            query_vector = self._embed_text(query, "task: question answering | query")
            query_id = f"query-{uuid.uuid4().hex[:8]}"
            source_vectors = self._source_vectors()
            projections = self._pca_projection({**source_vectors, query_id: query_vector})
            query_point = {
                "id": query_id,
                "source_id": "query",
                "title": query,
                "modality": "query",
                "projection": projections.get(query_id, {"x": 0.0, "y": 0.0, "z": 0.0}),
                "color": MODALITY_COLORS["query"],
                "score": 1,
                "preview": "Query embedding projected with the active source set.",
            }
            source_by_id = {source.id: source for source in self.sources}
            source_matches: dict[str, dict[str, Any]] = {}
            for chunk in self.chunks:
                score = round(_cosine(query_vector, chunk.vector), 4)
                current = source_matches.get(chunk.source_id)
                if not current or score > current["score"]:
                    source = source_by_id.get(chunk.source_id)
                    if not source:
                        continue
                    source_matches[chunk.source_id] = {
                        "id": source.id,
                        "source_id": source.id,
                        "title": source.title,
                        "modality": source.modality,
                        "text": chunk.text,
                        "score": score,
                        "projection": projections.get(source.id, {"x": 0.0, "y": 0.0, "z": 0.0}),
                        "metadata": {"best_chunk": chunk.id, **chunk.metadata},
                    }

            matches = sorted(source_matches.values(), key=lambda item: item["score"], reverse=True)[:top_k]
            self._emit("query_embedded", {"query": query, "matches": [m["id"] for m in matches]})
            return {
                "query_point": query_point,
                "matches": matches,
                "space": self.snapshot(projections=projections),
            }

    def snapshot(self, projections: dict[str, dict[str, float]] | None = None) -> dict[str, Any]:
        with self._lock:
            source_vectors = self._source_vectors()
            projection_map = projections or self._pca_projection(source_vectors)
            points = [
                self._source_point(source, projection_map.get(source.id, {"x": 0.0, "y": 0.0, "z": 0.0}))
                for source in self.sources
            ]
            return {
                "sources": [source.__dict__ for source in self.sources],
                "points": points,
                "events": self.events,
                "provider": self.embedding_provider,
                "dimensions": self.dimensions,
                "model": EMBED_MODEL,
                "projection": {
                    "method": "pca_3d",
                    "basis": "current source vectors plus active query when present",
                },
            }

    def retrieval_tool(self, query: str, top_k: int = 5) -> dict[str, Any]:
        results = self.search(query, top_k=top_k)
        return self.retrieval_payload(results)

    def retrieval_payload(self, results: dict[str, Any]) -> dict[str, Any]:
        return {
            "provider": self.embedding_provider,
            "matches": [
                {
                    "citation": match["id"],
                    "source": match["title"],
                    "modality": match["modality"],
                    "similarity": match["score"],
                    "evidence": match["text"],
                }
                for match in results["matches"]
            ],
        }

    def space_tool(self) -> dict[str, Any]:
        with self._lock:
            source_modalities: dict[str, int] = {}
            chunk_modalities: dict[str, int] = {}
            for source in self.sources:
                source_modalities[source.modality] = source_modalities.get(source.modality, 0) + 1
            for chunk in self.chunks:
                chunk_modalities[chunk.modality] = chunk_modalities.get(chunk.modality, 0) + 1
            return {
                "sources": len(self.sources),
                "chunks": len(self.chunks),
                "dimensions": self.dimensions,
                "provider": self.embedding_provider,
                "modalities": source_modalities,
                "chunk_modalities": chunk_modalities,
                "projection": "pca_3d",
            }

    @staticmethod
    def _modality_from_mime(mime_type: str) -> str:
        if mime_type == "application/pdf":
            return "pdf"
        if mime_type.startswith("image/"):
            return "image"
        if mime_type.startswith("audio/"):
            return "audio"
        if mime_type.startswith("video/"):
            return "video"
        return "text"

    @staticmethod
    def _suffix_from_mime(mime_type: str) -> str:
        if mime_type == "application/pdf":
            return ".pdf"
        if mime_type.startswith("image/"):
            return f".{mime_type.split('/', 1)[1].split(';', 1)[0]}"
        if mime_type.startswith("audio/"):
            return ".mp3"
        if mime_type.startswith("video/"):
            return ".mp4"
        return ".bin"
