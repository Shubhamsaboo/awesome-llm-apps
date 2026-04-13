from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import time
import uuid
import zipfile
import io
import os
import json
import asyncio
import tempfile
import shutil
import re
import logging
import traceback
from adk_optimizer import SkillOptimizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB total
MAX_FILE_SIZE = 1 * 1024 * 1024     # 1 MB per file
MAX_FILE_COUNT = 50
SESSION_TTL = 3600  # 1 hour
ALLOWED_EXTENSIONS = {
    ".md", ".txt", ".json", ".yaml", ".yml", ".py", ".js", ".ts",
    ".html", ".css", ".xml", ".toml", ".cfg", ".ini", ".sh",
}

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions: Dict[str, dict] = {}


class AnalyzeRequest(BaseModel):
    session_id: str
    gemini_api_key: str


class SessionConfig(BaseModel):
    session_id: str
    scenarios: List[dict]
    evals: List[dict]


class RegenerateRequest(BaseModel):
    session_id: str
    gemini_api_key: str


class StartRequest(BaseModel):
    gemini_api_key: str
    max_rounds: Optional[int] = Field(default=20, gt=0, le=50)


def parse_skill_frontmatter(content: str) -> dict:
    """Parse YAML frontmatter from SKILL.md"""
    if not content.startswith("---"):
        return {}
    try:
        parts = content.split("---", 2)
        if len(parts) < 3:
            return {}
        frontmatter = parts[1].strip()
        metadata = {}
        for line in frontmatter.split("\n"):
            line = line.strip()
            if ":" in line and not line.startswith(" "):
                key, value = line.split(":", 1)
                metadata[key.strip()] = value.strip().strip('"')
        return metadata
    except Exception:
        return {}


def create_session_from_files(skill_files: dict, file_list: list) -> dict:
    """Create a session dict from skill files"""
    skill_md = None
    for name, content in skill_files.items():
        if name.endswith("SKILL.md"):
            skill_md = content
            break
    if not skill_md:
        raise HTTPException(status_code=400, detail="No SKILL.md found")
    metadata = parse_skill_frontmatter(skill_md)
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "skill_files": skill_files,
        "file_list": file_list,
        "metadata": metadata,
        "status": "uploaded",
        "scenarios": None,
        "evals": None,
        "experiments": [],
        "changelog": [],
        "current_skill_md": skill_md,
        "original_skill_md": skill_md,
        "created_at": time.time(),
    }
    return {"session_id": session_id, "file_list": file_list, "metadata": metadata}


def _is_allowed_file(name: str) -> bool:
    """Check if file extension is in the allowed text-file list."""
    _, ext = os.path.splitext(name)
    return ext.lower() in ALLOWED_EXTENSIONS


def _is_safe_path(name: str) -> bool:
    """Reject path traversal attempts."""
    return ".." not in name and not os.path.isabs(name)


@app.post("/api/upload")
async def upload_skill(file: UploadFile = File(...)):
    """Accept zip file or multiple files, extract, return file list + parsed SKILL.md metadata"""
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip files are accepted")
    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail=f"Upload exceeds {MAX_UPLOAD_SIZE // (1024*1024)}MB limit")
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            skill_files = {}
            file_list = []
            for name in zf.namelist():
                if name.endswith("/") or name.startswith("__MACOSX") or "/.DS_Store" in name or name.endswith(".DS_Store"):
                    continue
                if not _is_safe_path(name):
                    logger.warning(f"Skipping unsafe zip entry: {name}")
                    continue
                if not _is_allowed_file(name):
                    logger.info(f"Skipping non-text file: {name}")
                    continue
                raw = zf.read(name)
                if len(raw) > MAX_FILE_SIZE:
                    logger.warning(f"Skipping oversized file: {name} ({len(raw)} bytes)")
                    continue
                if len(file_list) >= MAX_FILE_COUNT:
                    logger.warning("Max file count reached, skipping remaining entries")
                    break
                file_content = raw.decode("utf-8", errors="ignore")
                skill_files[name] = file_content
                file_list.append(name)

            # Normalize paths: strip common prefix directory
            if file_list:
                common = os.path.commonpath(file_list)
                if common and common != file_list[0]:
                    skill_files = {os.path.relpath(k, common): v for k, v in skill_files.items()}
                    file_list = [os.path.relpath(f, common) for f in file_list]

            return create_session_from_files(skill_files, file_list)
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Invalid zip file")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Error processing file")


@app.post("/api/upload-files")
async def upload_files(files: List[UploadFile] = File(...)):
    """Accept multiple files (folder upload via webkitdirectory)"""
    if len(files) > MAX_FILE_COUNT:
        raise HTTPException(status_code=413, detail=f"Too many files (max {MAX_FILE_COUNT})")
    skill_files = {}
    file_list = []
    total_size = 0
    for f in files:
        if f.filename.startswith(".") or "/.DS_Store" in (f.filename or "") or "__MACOSX" in (f.filename or ""):
            continue
        name = f.filename or "unknown"
        if not _is_safe_path(name):
            logger.warning(f"Skipping unsafe path: {name}")
            continue
        if not _is_allowed_file(name):
            logger.info(f"Skipping non-text file: {name}")
            continue
        content = await f.read()
        total_size += len(content)
        if total_size > MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=413, detail=f"Total upload exceeds {MAX_UPLOAD_SIZE // (1024*1024)}MB limit")
        if len(content) > MAX_FILE_SIZE:
            logger.warning(f"Skipping oversized file: {name} ({len(content)} bytes)")
            continue
        skill_files[name] = content.decode("utf-8", errors="ignore")
        file_list.append(name)

    # Normalize paths: strip common prefix directory
    if file_list:
        common = os.path.commonpath(file_list)
        if common and common != file_list[0]:
            skill_files = {os.path.relpath(k, common): v for k, v in skill_files.items()}
            file_list = [os.path.relpath(f, common) for f in file_list]

    return create_session_from_files(skill_files, file_list)


@app.post("/api/analyze")
async def analyze_skill(request: AnalyzeRequest):
    """Generate scenarios + evals using Gemini"""
    if request.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    session = sessions[request.session_id]
    try:
        optimizer = SkillOptimizer(api_key=request.gemini_api_key)
        analysis = await optimizer.analyze_skill(session["skill_files"])
        session["scenarios"] = analysis["scenarios"]
        session["evals"] = analysis["evals"]
        session["status"] = "analyzed"
        return {"scenarios": analysis["scenarios"], "evals": analysis["evals"]}
    except Exception as e:
        logger.error(f"Analysis error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Analysis failed. Check your API key and try again.")


@app.post("/api/regenerate")
async def regenerate_config(request: RegenerateRequest):
    """Regenerate scenarios/evals for a session"""
    analyze_req = AnalyzeRequest(session_id=request.session_id, gemini_api_key=request.gemini_api_key)
    return await analyze_skill(analyze_req)


@app.post("/api/update-config")
async def update_config(config: SessionConfig):
    """Save user's selected/edited scenarios + evals"""
    if config.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    session = sessions[config.session_id]
    session["scenarios"] = config.scenarios
    session["evals"] = config.evals
    session["status"] = "configured"
    return {"status": "ok"}


@app.get("/api/stream/{session_id}")
async def stream_progress(session_id: str):
    """SSE endpoint streaming optimization progress"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    session = sessions[session_id]

    async def event_generator():
        if "event_queue" not in session:
            session["event_queue"] = asyncio.Queue()
        queue = session["event_queue"]
        try:
            while True:
                event = await queue.get()
                if event is None:
                    break
                yield f"data: {json.dumps(event)}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            if "event_queue" in session:
                del session["event_queue"]

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@app.post("/api/start/{session_id}")
async def start_optimization(session_id: str, request: StartRequest):
    """Start optimization in background task"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    session = sessions[session_id]
    if not session.get("scenarios") or not session.get("evals"):
        raise HTTPException(status_code=400, detail="Must configure scenarios and evals first")
    if session.get("status") == "running":
        raise HTTPException(status_code=400, detail="Optimization already running")

    session["status"] = "running"
    session["stop_requested"] = False
    # Pre-create the event queue so events aren't lost before SSE connects
    session["event_queue"] = asyncio.Queue()
    gemini_key = request.gemini_api_key

    async def run_optimization():
        logger.info(f"Starting optimization for session {session_id}")
        optimizer = SkillOptimizer(api_key=gemini_key)

        async def callback(event):
            logger.info(f"Callback event: {event['type']}")
            if "event_queue" in session:
                await session["event_queue"].put(event)
            if event["type"] == "baseline":
                session["experiments"].append({
                    "experiment_id": 0,
                    "pass_rate": event["data"].get("score", 0),
                    "status": "baseline",
                    "per_eval": event["data"].get("per_eval", []),
                })
            elif event["type"] == "experiment_result":
                session["experiments"].append({
                    "experiment_id": event["data"].get("round", len(session["experiments"])),
                    "pass_rate": event["data"].get("score", 0),
                    "status": "keep" if event["data"].get("kept") else "discard",
                    "per_eval": event["data"].get("per_eval", []),
                    "description": event["data"].get("description", ""),
                    "strategy": event["data"].get("strategy", ""),
                })
            elif event["type"] == "complete":
                session["status"] = "complete"
                data = event["data"]
                ml = data.get("mutation_log", [])
                # Transform to match frontend ResultsStep expectations
                session["final_result"] = {
                    "baseline_score": data.get("baseline_score", 0),
                    "final_score": data.get("final_score", 0),
                    "improved_skill_md": data.get("improved_skill_md", ""),
                    "original_skill_md": session.get("original_skill_md", ""),
                    "score_history": data.get("score_history", []),
                    "experiments_run": len(ml),
                    "kept": sum(1 for m in ml if m.get("kept")),
                    "discarded": sum(1 for m in ml if not m.get("kept")),
                    "changelog": [
                        {
                            "description": m.get("description", m.get("diagnosis", "")),
                            "reasoning": m.get("diagnosis", ""),
                            "status": "keep" if m.get("kept") else "discard",
                            "score_before": m.get("score_before", 0),
                            "score_after": m.get("score_after", 0),
                            "strategy": m.get("strategy_type", ""),
                        }
                        for m in ml
                    ],
                    "mutation_log": ml,
                    "strategy_stats": data.get("strategy_stats", {}),
                }
                session["current_skill_md"] = data.get("improved_skill_md", "")
                if "event_queue" in session:
                    await session["event_queue"].put(None)

        try:
            result = await optimizer.optimize(
                skill_files=session["skill_files"],
                scenarios=session["scenarios"],
                evals=session["evals"],
                max_rounds=request.max_rounds,
                callback=callback,
            )
            logger.info(f"Optimization complete: {result['baseline_score']}% -> {result['final_score']}%")
            # Don't overwrite final_result if callback already set it with transformed data
            if not session.get("final_result"):
                ml = result.get("mutation_log", [])
                session["final_result"] = {
                    "baseline_score": result.get("baseline_score", 0),
                    "final_score": result.get("final_score", 0),
                    "improved_skill_md": result.get("improved_skill_md", ""),
                    "original_skill_md": session.get("original_skill_md", ""),
                    "score_history": result.get("score_history", []),
                    "experiments_run": len(ml),
                    "kept": sum(1 for m in ml if m.get("kept")),
                    "discarded": sum(1 for m in ml if not m.get("kept")),
                    "changelog": [
                        {
                            "description": m.get("description", m.get("diagnosis", "")),
                            "reasoning": m.get("diagnosis", ""),
                            "status": "keep" if m.get("kept") else "discard",
                            "score_before": m.get("score_before", 0),
                            "score_after": m.get("score_after", 0),
                            "strategy": m.get("strategy_type", ""),
                        }
                        for m in ml
                    ],
                    "mutation_log": ml,
                }
            session["current_skill_md"] = result["improved_skill_md"]
            session["status"] = "complete"
        except Exception as e:
            logger.error(f"Optimization error: {traceback.format_exc()}")
            session["status"] = "error"
            session["error"] = str(e)
            if "event_queue" in session:
                await session["event_queue"].put({"type": "error", "data": {"message": str(e)}})
                await session["event_queue"].put(None)

    asyncio.create_task(run_optimization())
    return {"status": "started"}


@app.post("/api/stop/{session_id}")
async def stop_optimization(session_id: str):
    """Stop optimization"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    session = sessions[session_id]
    session["stop_requested"] = True
    session["status"] = "stopped"
    if "event_queue" in session:
        await session["event_queue"].put(None)
    return {"status": "stopped"}


@app.get("/api/download/{session_id}")
async def download_skill(session_id: str):
    """Download improved skill as zip"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    session = sessions[session_id]
    if not session.get("current_skill_md"):
        raise HTTPException(status_code=400, detail="No improved skill available")
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, "improved_skill.zip")
    try:
        with zipfile.ZipFile(zip_path, "w") as zf:
            for filename, content in session["skill_files"].items():
                if filename.endswith("SKILL.md"):
                    zf.writestr(filename, session["current_skill_md"])
                else:
                    zf.writestr(filename, content)
            if session.get("final_result"):
                changelog_content = json.dumps(session["final_result"]["changelog"], indent=2)
                zf.writestr("CHANGELOG.json", changelog_content)
        return FileResponse(zip_path, media_type="application/zip", filename="improved_skill.zip")
    finally:
        asyncio.create_task(cleanup_temp_dir(temp_dir))


async def cleanup_temp_dir(temp_dir: str):
    await asyncio.sleep(60)
    try:
        shutil.rmtree(temp_dir)
    except Exception:
        pass


@app.get("/api/examples")
async def list_examples():
    """List available example skills"""
    examples_dir = os.path.join(os.path.dirname(__file__), "..", "example_skills")
    examples = []
    if os.path.exists(examples_dir):
        for name in sorted(os.listdir(examples_dir)):
            skill_dir = os.path.join(examples_dir, name)
            skill_md_path = os.path.join(skill_dir, "SKILL.md")
            if os.path.isdir(skill_dir) and os.path.exists(skill_md_path):
                with open(skill_md_path, "r") as f:
                    content = f.read()
                metadata = parse_skill_frontmatter(content)
                examples.append({"name": metadata.get("name", name), "description": metadata.get("description", ""), "path": name})
    return {"examples": examples}


@app.post("/api/examples/{example_name}/load")
async def load_example(example_name: str):
    """Load an example skill as if it were uploaded"""
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", example_name):
        raise HTTPException(status_code=400, detail="Invalid example name")
    examples_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "example_skills"))
    skill_dir = os.path.realpath(os.path.join(examples_dir, example_name))
    if not skill_dir.startswith(examples_dir + os.sep):
        raise HTTPException(status_code=400, detail="Invalid example name")
    if not os.path.isdir(skill_dir):
        raise HTTPException(status_code=404, detail="Example skill not found")
    skill_files = {}
    file_list = []
    for root, dirs, files in os.walk(skill_dir):
        for fname in files:
            if fname.startswith("."):
                continue
            full_path = os.path.join(root, fname)
            rel_path = os.path.relpath(full_path, skill_dir)
            with open(full_path, "r") as f:
                skill_files[rel_path] = f.read()
            file_list.append(rel_path)
    return create_session_from_files(skill_files, file_list)


@app.get("/api/status/{session_id}")
async def get_status(session_id: str):
    """Poll-based status endpoint. Returns all experiments so far."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    session = sessions[session_id]
    return {
        "status": session.get("status", "unknown"),
        "experiments": session.get("experiments", []),
        "error": session.get("error"),
        "final_result": session.get("final_result"),
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


async def _cleanup_expired_sessions():
    """Periodically remove sessions older than SESSION_TTL."""
    while True:
        await asyncio.sleep(300)  # every 5 minutes
        now = time.time()
        expired = [
            sid for sid, s in sessions.items()
            if now - s.get("created_at", now) > SESSION_TTL
            and s.get("status") not in ("running",)
        ]
        for sid in expired:
            del sessions[sid]
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired session(s)")


@app.on_event("startup")
async def startup():
    asyncio.create_task(_cleanup_expired_sessions())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8891)
