from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
import uvicorn
import os
import aiofiles
from contextlib import asynccontextmanager
from routers import article_router, podcast_router, source_router, task_router, podcast_config_router, async_podcast_agent_router, social_media_router
from services.db_init import init_databases
from dotenv import load_dotenv


load_dotenv()

CLIENT_BUILD_PATH = os.environ.get(
    "CLIENT_BUILD_PATH",
    "../web/build",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up application...")
    os.makedirs("databases", exist_ok=True)
    os.makedirs("browsers", exist_ok=True)
    os.makedirs("podcasts/audio", exist_ok=True)
    os.makedirs("podcasts/images", exist_ok=True)
    os.makedirs("podcasts/recordings", exist_ok=True)
    await init_databases()
    if not os.path.exists(CLIENT_BUILD_PATH):
        print(f"WARNING: React client build path not found: {CLIENT_BUILD_PATH}")
    print("Application startup complete!")
    yield
    print("Shutting down application...")
    print("Shutdown complete")


app = FastAPI(title="Beifong API", description="Beifong API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(article_router.router, prefix="/api/articles", tags=["articles"])
app.include_router(source_router.router, prefix="/api/sources", tags=["sources"])
app.include_router(podcast_router.router, prefix="/api/podcasts", tags=["podcasts"])
app.include_router(task_router.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(podcast_config_router.router, prefix="/api/podcast-configs", tags=["podcast-configs"])
app.include_router(async_podcast_agent_router.router, prefix="/api/podcast-agent", tags=["podcast-agent"])
app.include_router(social_media_router.router, prefix="/api/social-media", tags=["social-media"])


@app.get("/stream-audio/{filename}")
async def stream_audio(filename: str, request: Request):
    audio_path = os.path.join("podcasts/audio", filename)
    if not os.path.exists(audio_path):
        return Response(status_code=404, content="Audio file not found")
    file_size = os.path.getsize(audio_path)
    range_header = request.headers.get("Range", "").strip()
    start = 0
    end = file_size - 1
    if range_header:
        try:
            range_data = range_header.replace("bytes=", "").split("-")
            start = int(range_data[0]) if range_data[0] else 0
            end = int(range_data[1]) if len(range_data) > 1 and range_data[1] else file_size - 1
        except ValueError:
            return Response(status_code=400, content="Invalid range header")
    end = min(end, file_size - 1)
    content_length = end - start + 1
    headers = {
        "Accept-Ranges": "bytes",
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Content-Length": str(content_length),
        "Content-Disposition": f"inline; filename={filename}",
        "Content-Type": "audio/wav",
    }

    async def file_streamer():
        async with aiofiles.open(audio_path, "rb") as f:
            await f.seek(start)
            remaining = content_length
            chunk_size = 64 * 1024
            while remaining > 0:
                chunk = await f.read(min(chunk_size, remaining))
                if not chunk:
                    break
                remaining -= len(chunk)
                yield chunk

    status_code = 206 if range_header else 200
    return StreamingResponse(file_streamer(), status_code=status_code, headers=headers)


@app.get("/stream-recording/{session_id}/{filename}")
async def stream_recording(session_id: str, filename: str, request: Request):
    recording_path = os.path.join("podcasts/recordings", session_id, filename)
    if not os.path.exists(recording_path):
        return Response(status_code=404, content="Recording video not found")
    file_size = os.path.getsize(recording_path)
    range_header = request.headers.get("Range", "").strip()
    start = 0
    end = file_size - 1
    if range_header:
        try:
            range_data = range_header.replace("bytes=", "").split("-")
            start = int(range_data[0]) if range_data[0] else 0
            end = int(range_data[1]) if len(range_data) > 1 and range_data[1] else file_size - 1
        except ValueError:
            return Response(status_code=400, content="Invalid range header")
    end = min(end, file_size - 1)
    content_length = end - start + 1
    headers = {
        "Accept-Ranges": "bytes",
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Content-Length": str(content_length),
        "Content-Disposition": f"inline; filename={filename}",
        "Content-Type": "video/webm",
    }

    async def file_streamer():
        async with aiofiles.open(recording_path, "rb") as f:
            await f.seek(start)
            remaining = content_length
            chunk_size = 64 * 1024
            while remaining > 0:
                chunk = await f.read(min(chunk_size, remaining))
                if not chunk:
                    break
                remaining -= len(chunk)
                yield chunk

    status_code = 206 if range_header else 200
    return StreamingResponse(file_streamer(), status_code=status_code, headers=headers)


app.mount("/audio", StaticFiles(directory="podcasts/audio"), name="audio")
app.mount("/server_static", StaticFiles(directory="static"), name="server_static")
app.mount("/podcast_img", StaticFiles(directory="podcasts/images"), name="podcast_img")
if os.path.exists(os.path.join(CLIENT_BUILD_PATH, "static")):
    app.mount("/static", StaticFiles(directory=os.path.join(CLIENT_BUILD_PATH, "static")), name="react_static")


@app.get("/favicon.ico")
async def favicon():
    favicon_path = os.path.join(CLIENT_BUILD_PATH, "favicon.ico")
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    return {"detail": "Favicon not found"}


@app.get("/manifest.json")
async def manifest():
    manifest_path = os.path.join(CLIENT_BUILD_PATH, "manifest.json")
    if os.path.exists(manifest_path):
        return FileResponse(manifest_path)
    return {"detail": "Manifest not found"}


@app.get("/logo{rest_of_path:path}")
async def logo(rest_of_path: str):
    logo_path = os.path.join(CLIENT_BUILD_PATH, f"logo{rest_of_path}")
    if os.path.exists(logo_path):
        return FileResponse(logo_path)
    return {"detail": "Logo not found"}


@app.get("/{full_path:path}")
async def serve_react(full_path: str, request: Request):
    if full_path.startswith("api/") or request.url.path.startswith("/api/"):
        return {"detail": "Not Found"}
    index_path = os.path.join(CLIENT_BUILD_PATH, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        return {"detail": "React client not found. Build the client or set the correct CLIENT_BUILD_PATH."}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False, timeout_keep_alive=120, timeout_graceful_shutdown=120)