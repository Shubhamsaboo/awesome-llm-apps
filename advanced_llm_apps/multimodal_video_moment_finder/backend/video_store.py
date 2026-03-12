"""
Video Moment Finder — Gemini Embedding 2 + ChromaDB

Extracts frames from video, embeds each frame natively with
Gemini Embedding 2, then finds matching moments via image query.
Zero transcription. Pure visual matching.
"""

import hashlib
import io
import os
import subprocess
import tempfile
import uuid
from pathlib import Path
from PIL import Image

import chromadb
from google import genai
from google.genai import types

MAX_IMAGE_DIMENSION = 1024  # Max width/height for embedding

GEMINI_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
EMBED_MODEL = "gemini-embedding-2-preview"
DESCRIBE_MODEL = "gemini-3-flash-preview"
COLLECTION_NAME = "video_frames"


class VideoStore:
    def __init__(self, persist_dir: str = "./chroma_video_db"):
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.chroma = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.chroma.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        self.frames_dir = Path("./frames")
        self.frames_dir.mkdir(exist_ok=True)

    def _resize_image(self, image_data: bytes) -> bytes:
        """Resize image if too large for the embedding API."""
        try:
            img = Image.open(io.BytesIO(image_data))
            if max(img.size) > MAX_IMAGE_DIMENSION:
                img.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION), Image.LANCZOS)
            # Convert to RGB if needed (handles PNG with alpha, etc.)
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=85)
            return buf.getvalue()
        except Exception:
            return image_data

    def _embed_image(self, image_data: bytes, mime_type: str = "image/jpeg") -> list[float]:
        """Embed a single image using Gemini Embedding 2."""
        image_data = self._resize_image(image_data)
        part = types.Part.from_bytes(data=image_data, mime_type="image/jpeg")
        result = self.client.models.embed_content(
            model=EMBED_MODEL,
            contents=[part],
        )
        return result.embeddings[0].values

    def _embed_images_batch(self, images: list[tuple[bytes, str]]) -> list[list[float]]:
        """Embed multiple images in batches (API limit: 6 images per request)."""
        all_embeddings = []
        batch_size = 6  # Gemini Embedding 2 limit

        for i in range(0, len(images), batch_size):
            batch = images[i:i + batch_size]
            parts = [types.Part.from_bytes(data=data, mime_type=mime) for data, mime in batch]
            result = self.client.models.embed_content(
                model=EMBED_MODEL,
                contents=parts,
            )
            all_embeddings.extend([e.values for e in result.embeddings])

        return all_embeddings

    def extract_frames(self, video_path: str, fps: float = 1.0) -> list[dict]:
        """Extract frames from video using ffmpeg."""
        video_id = uuid.uuid4().hex[:8]
        output_dir = self.frames_dir / video_id
        output_dir.mkdir(exist_ok=True)

        # Get video duration
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "csv=p=0", video_path],
            capture_output=True, text=True,
        )
        duration = float(result.stdout.strip()) if result.stdout.strip() else 0

        # Extract frames
        subprocess.run(
            ["ffmpeg", "-i", video_path, "-vf", f"fps={fps}",
             "-q:v", "2", str(output_dir / "frame_%04d.jpg"), "-y"],
            capture_output=True,
        )

        # Collect frame info
        frames = []
        for frame_file in sorted(output_dir.glob("frame_*.jpg")):
            frame_num = int(frame_file.stem.split("_")[1])
            timestamp = (frame_num - 1) / fps  # 0-indexed
            frames.append({
                "path": str(frame_file),
                "timestamp": timestamp,
                "frame_num": frame_num,
                "video_id": video_id,
            })

        return frames, duration, video_id

    def ingest_video(
        self,
        video_path: str,
        filename: str,
        fps: float = 1.0,
        on_progress=None,
    ) -> dict:
        """Ingest a video: extract frames, embed each, store in ChromaDB."""
        frames, duration, video_id = self.extract_frames(video_path, fps)

        if not frames:
            return {"error": "No frames extracted", "video_id": video_id}

        # Read all frame images
        frame_data = []
        for f in frames:
            with open(f["path"], "rb") as fh:
                frame_data.append((fh.read(), "image/jpeg"))

        # Embed in batches
        total = len(frame_data)
        embeddings = []
        batch_size = 6

        for i in range(0, total, batch_size):
            batch = frame_data[i:i + batch_size]
            parts = [types.Part.from_bytes(data=self._resize_image(data), mime_type="image/jpeg") for data, mime in batch]
            result = self.client.models.embed_content(
                model=EMBED_MODEL,
                contents=parts,
            )
            embeddings.extend([e.values for e in result.embeddings])
            if on_progress:
                on_progress(min(i + batch_size, total), total)

        # Store in ChromaDB
        ids = []
        metadatas = []
        documents = []

        for i, frame in enumerate(frames):
            frame_id = f"{video_id}_f{frame['frame_num']:04d}"
            ids.append(frame_id)
            metadatas.append({
                "video_id": video_id,
                "video_filename": filename,
                "timestamp": frame["timestamp"],
                "frame_num": frame["frame_num"],
                "frame_path": frame["path"],
                "total_frames": total,
                "duration": duration,
                "fps": fps,
            })
            documents.append(f"Frame {frame['frame_num']} at {frame['timestamp']:.1f}s from {filename}")

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

        return {
            "video_id": video_id,
            "filename": filename,
            "duration": round(duration, 1),
            "frames_extracted": total,
            "fps": fps,
        }

    def find_moment(
        self,
        image_data: bytes,
        mime_type: str = "image/jpeg",
        top_k: int = 5,
        video_id: str = None,
    ) -> list[dict]:
        """Find the video moment matching an image query."""
        # Embed the query image
        embedding = self._embed_image(image_data, mime_type)

        # Search
        where = {"video_id": video_id} if video_id else None
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            where=where,
            include=["metadatas", "distances"],
        )

        moments = []
        for i in range(len(results["ids"][0])):
            meta = results["metadatas"][0][i]
            score = 1 - results["distances"][0][i]
            moments.append({
                "timestamp": meta["timestamp"],
                "frame_num": meta["frame_num"],
                "video_filename": meta["video_filename"],
                "video_id": meta["video_id"],
                "frame_path": meta["frame_path"],
                "score": round(score, 4),
                "time_formatted": self._format_time(meta["timestamp"]),
            })

        return moments

    def find_moment_by_text(
        self,
        query: str,
        top_k: int = 5,
        video_id: str = None,
    ) -> list[dict]:
        """Find video moments matching a text description."""
        result = self.client.models.embed_content(
            model=EMBED_MODEL,
            contents=[query],
        )
        embedding = result.embeddings[0].values

        where = {"video_id": video_id} if video_id else None
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            where=where,
            include=["metadatas", "distances"],
        )

        moments = []
        for i in range(len(results["ids"][0])):
            meta = results["metadatas"][0][i]
            score = 1 - results["distances"][0][i]
            moments.append({
                "timestamp": meta["timestamp"],
                "frame_num": meta["frame_num"],
                "video_filename": meta["video_filename"],
                "video_id": meta["video_id"],
                "frame_path": meta["frame_path"],
                "score": round(score, 4),
                "time_formatted": self._format_time(meta["timestamp"]),
            })

        return moments

    def describe_moment(self, frame_path: str) -> str:
        """Use Gemini to describe what's happening in a frame."""
        with open(frame_path, "rb") as f:
            data = f.read()
        part = types.Part.from_bytes(data=data, mime_type="image/jpeg")
        response = self.client.models.generate_content(
            model=DESCRIBE_MODEL,
            contents=[part, "Describe what's happening in this video frame in one sentence."],
        )
        return response.text.strip()

    def list_videos(self) -> list[dict]:
        """List all ingested videos."""
        all_data = self.collection.get(include=["metadatas"])
        videos = {}
        for meta in all_data["metadatas"]:
            vid = meta["video_id"]
            if vid not in videos:
                videos[vid] = {
                    "video_id": vid,
                    "filename": meta["video_filename"],
                    "duration": meta["duration"],
                    "total_frames": meta["total_frames"],
                    "fps": meta["fps"],
                }
        return list(videos.values())

    def delete_video(self, video_id: str) -> bool:
        """Delete all frames for a video."""
        try:
            all_data = self.collection.get(where={"video_id": video_id})
            if all_data["ids"]:
                self.collection.delete(ids=all_data["ids"])
            return True
        except Exception:
            return False

    @staticmethod
    def _format_time(seconds: float) -> str:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}:{secs:02d}"
