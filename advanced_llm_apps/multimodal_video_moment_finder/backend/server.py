"""
Video Moment Finder — FastAPI Server

Upload videos, then find exact moments using images or text.
Pure visual matching via Gemini Embedding 2.
"""

import asyncio
import os
import tempfile
import time

from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path

from video_store import VideoStore

app = FastAPI(title="Multimodal Video Moment Finder")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frame images
frames_dir = Path("./frames")
frames_dir.mkdir(exist_ok=True)
app.mount("/frames", StaticFiles(directory="frames"), name="frames")

# Serve uploaded videos
uploads_dir = Path("./uploads")
uploads_dir.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

store = VideoStore()


from typing import Optional

class TextSearchRequest(BaseModel):
    query: str
    video_id: Optional[str] = None
    top_k: int = 5


@app.post("/upload-video")
async def upload_video(
    file: UploadFile = File(...),
    fps: float = Form(1.0),
):
    """Upload and process a video. Extracts frames and embeds each one."""
    data = await file.read()
    if len(data) > 100 * 1024 * 1024:  # 100MB limit
        raise HTTPException(400, "Video too large (100MB max)")

    # Save video
    video_path = uploads_dir / f"{file.filename}"
    with open(video_path, "wb") as f:
        f.write(data)

    # Process
    result = store.ingest_video(str(video_path), file.filename, fps=fps)

    if "error" in result:
        raise HTTPException(500, result["error"])

    return result


@app.post("/find-moment")
async def find_moment(
    image: UploadFile = File(...),
    video_id: Optional[str] = Form(None),
    top_k: int = Form(5),
):
    """Find video moments matching an uploaded image."""
    data = await image.read()
    mime = image.content_type or "image/jpeg"
    try:
        moments = store.find_moment(data, mime, top_k=top_k, video_id=video_id)
    except Exception as e:
        raise HTTPException(500, f"Embedding error: {str(e)}")

    # Add descriptions for top moments
    for m in moments[:3]:
        try:
            m["description"] = store.describe_moment(m["frame_path"])
        except Exception:
            m["description"] = ""

    # Convert frame paths to URLs
    for m in moments:
        frame_path = m["frame_path"]
        # Make relative to frames dir
        rel = os.path.relpath(frame_path, "frames")
        m["frame_url"] = f"/frames/{rel}"

    return {"moments": moments, "query_type": "image"}


@app.post("/find-moment-text")
async def find_moment_text(req: TextSearchRequest):
    """Find video moments matching a text description."""
    moments = store.find_moment_by_text(
        req.query, top_k=req.top_k, video_id=req.video_id,
    )

    for m in moments[:3]:
        try:
            m["description"] = store.describe_moment(m["frame_path"])
        except Exception:
            m["description"] = ""

    for m in moments:
        frame_path = m["frame_path"]
        rel = os.path.relpath(frame_path, "frames")
        m["frame_url"] = f"/frames/{rel}"

    return {"moments": moments, "query_type": "text"}


@app.get("/videos")
async def list_videos():
    """List all processed videos."""
    videos = store.list_videos()
    # Add video URLs
    for v in videos:
        v["video_url"] = f"/uploads/{v['filename']}"
    return {"videos": videos}


@app.delete("/videos/{video_id}")
async def delete_video(video_id: str):
    ok = store.delete_video(video_id)
    if not ok:
        raise HTTPException(404, "Video not found")
    return {"deleted": video_id}


@app.get("/health")
async def health():
    videos = store.list_videos()
    total_frames = sum(v["total_frames"] for v in videos)
    return {
        "status": "ok",
        "videos": len(videos),
        "total_frames": total_frames,
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8890"))
    uvicorn.run(app, host="0.0.0.0", port=port)
