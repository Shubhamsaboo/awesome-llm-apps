import logging
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
from datetime import datetime

from backend.agents import AnalysisOrchestrator
from backend.output import ReportGenerator

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Agent Analyst", description="Trend analysis for app store reviews")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalysisRequest(BaseModel):
    app_identifier: str
    target_date: Optional[str] = None
    use_existing: Optional[bool] = False
    resume_extraction: Optional[bool] = False
    clear_progress: Optional[bool] = False  # Force fresh start
    keep_old_llm: Optional[bool] = False  # Continue with old LLM settings (Subtask 3)


class AnalysisResponse(BaseModel):
    status: str
    message: Optional[str] = None
    app_name: Optional[str] = None
    total_reviews: Optional[int] = None
    topics_extracted: Optional[int] = None
    trend_analysis: Optional[dict] = None  # CRITICAL: Add this field!
    report_markdown: Optional[str] = None
    report_html: Optional[str] = None


# Mount static files FIRST
frontend_path = Path("frontend")
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/style.css", response_class=FileResponse)
@app.get("/style_optimized.css", response_class=FileResponse)
def serve_css():
    """Serve CSS file with correct MIME type"""
    # Try optimized version first
    css_path = Path("frontend/style_optimized.css")
    if css_path.exists():
        return FileResponse(css_path, media_type="text/css", headers={"Cache-Control": "no-cache"})
    # Fallback to original
    css_path = Path("frontend/style.css")
    if css_path.exists():
        return FileResponse(css_path, media_type="text/css", headers={"Cache-Control": "no-cache"})
    raise HTTPException(status_code=404, detail="CSS file not found")


@app.get("/app.js", response_class=FileResponse)
@app.get("/app_optimized.js", response_class=FileResponse)
def serve_js():
    """Serve JavaScript file with correct MIME type"""
    # Try optimized version first
    js_path = Path("frontend/app_optimized.js")
    if js_path.exists():
        return FileResponse(js_path, media_type="application/javascript", headers={"Cache-Control": "no-cache"})
    # Fallback to original
    js_path = Path("frontend/app.js")
    if js_path.exists():
        return FileResponse(js_path, media_type="application/javascript", headers={"Cache-Control": "no-cache"})
    raise HTTPException(status_code=404, detail="JS file not found")


@app.get("/", response_class=FileResponse)
def serve_root():
    """Serve frontend HTML at root"""
    # Try optimized version first
    html_path = Path("frontend/index_optimized.html")
    if html_path.exists():
        return FileResponse(html_path, media_type="text/html")
    # Fallback to original
    html_path = Path("frontend/index.html")
    if html_path.exists():
        return FileResponse(html_path, media_type="text/html")
    raise HTTPException(status_code=404, detail="Frontend not found")


@app.get("/index.html", response_class=FileResponse)
def serve_frontend():
    """Serve frontend HTML"""
    # Try optimized version first
    html_path = Path("frontend/index_optimized.html")
    if html_path.exists():
        return FileResponse(html_path, media_type="text/html")
    # Fallback to original
    html_path = Path("frontend/index.html")
    if html_path.exists():
        return FileResponse(html_path, media_type="text/html")
    raise HTTPException(status_code=404, detail="Frontend not found")


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "AI Agent Analyst is running"}


@app.post("/check-existing")
def check_existing_data(request: dict):
    """Check if existing data exists for an app"""
    try:
        from backend.utils.progress_tracker import ProgressTracker
        from backend.scraper import PlayStoreScraper

        app_identifier = request.get("app_identifier")
        if not app_identifier:
            raise ValueError("app_identifier is required")

        logger.info(f"[CHECK-EXISTING] Received app_identifier: {app_identifier}")

        # CRITICAL: Use scraper to find app and get exact app_id (same as orchestrator)
        scraper = PlayStoreScraper()
        app_info = scraper.find_app(app_identifier)

        if not app_info:
            logger.warning(f"[CHECK-EXISTING] App not found: {app_identifier}")
            return {"status": "not_found", "data": None}

        app_id = app_info.get("appId")
        if not app_id:
            raise ValueError(f"App ID not found in app info: {app_info}")

        # IMPORTANT: Same sanitization as in orchestrator (orchestrator.py:126-131)
        app_name = app_info.get("title", app_id.split(".")[-1])
        for char in ['<', '>', ':', '"', '/', '\\', '|', '?', '*']:
            app_name = app_name.replace(char, '_')
        app_name = app_name.replace(" ", "_").lower()

        logger.info(f"[CHECK-EXISTING] Sanitized app_name: {app_name}")

        tracker = ProgressTracker(app_name)
        summary = tracker.get_existing_data_summary()
        
        if summary:
            logger.info(f"[CHECK-EXISTING] ✅ Found existing data for '{app_name}': {summary.get('total_reviews', 0)} reviews")
            logger.info(f"[CHECK-EXISTING] Summary structure: {list(summary.keys())}")
            return {
                "status": "found",
                "data": summary,
                "app_name": app_name  # Include app_name for frontend
            }
        else:
            logger.info(f"[CHECK-EXISTING] ❌ No existing data found for '{app_name}'")
            return {
                "status": "not_found",
                "data": None
            }
    except Exception as e:
        logger.error(f"Error checking existing data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/analyze")
def analyze_reviews(request: AnalysisRequest) -> AnalysisResponse:
    """
    Analyze reviews for a given app.
    
    Args:
        request: AnalysisRequest with app_identifier and target_date
        
    Returns:
        AnalysisResponse with analysis results
    """
    try:
        logger.info(f"[ANALYZE] ========== NEW REQUEST ==========")
        logger.info(f"[ANALYZE] app_identifier: {request.app_identifier}")
        logger.info(f"[ANALYZE] use_existing: {request.use_existing}")
        logger.info(f"[ANALYZE] resume_extraction: {request.resume_extraction}")
        logger.info(f"[ANALYZE] clear_progress: {request.clear_progress}")

        if not request.app_identifier:
            raise ValueError("app_identifier is required")

        # Run analysis (orchestrator will handle clear_progress internally with proper app_name)
        orchestrator = AnalysisOrchestrator()
        result = orchestrator.run_analysis(
            request.app_identifier,
            request.target_date,
            use_existing=request.use_existing,
            resume_extraction=request.resume_extraction,
            clear_progress=request.clear_progress
        )

        logger.info(f"[ANALYZE] Orchestrator returned status: {result.get('status')}")

        # Handle special statuses - return them properly
        if result.get("status") == "existing_data_found":
            logger.info(f"[ANALYZE] ⚠️  Status is existing_data_found - This should NOT happen when use_existing=True!")
            existing_data = result.get("existing_data")

            # Log for debugging
            logger.info(f"[ANALYZE] existing_data type: {type(existing_data)}")
            logger.info(f"[ANALYZE] existing_data: {existing_data}")

            # Ensure structure is correct
            if not existing_data:
                logger.error("existing_data is None in result!")
                raise HTTPException(status_code=500, detail="Internal error: existing_data is None")

            # Return with proper structure
            return {
                "status": "existing_data_found",
                "app_name": result.get("app_name"),
                "existing_data": existing_data,
                "message": result.get("message", "Existing data found")
            }
        
        if result.get("status") == "llm_changed":
            return {
                "status": "llm_changed",
                "previous_llm": result.get("previous_llm"),
                "current_llm": result.get("current_llm"),
                "existing_data": result.get("existing_data"),
                "message": result.get("message", "LLM provider changed")
            }
        
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))
        
        # Generate reports
        report_generator = ReportGenerator()
        trend_analysis = result.get("trend_analysis", {})
        target_date = request.target_date or datetime.now().strftime("%Y-%m-%d")
        app_name = result.get("app_name", "app")

        logger.info(f"[ANALYZE] ✅ Analysis successful!")
        logger.info(f"[ANALYZE] trend_analysis keys: {list(trend_analysis.keys()) if trend_analysis else 'None'}")
        logger.info(f"[ANALYZE] Recommendations count: {len(trend_analysis.get('actionable_recommendations', []))}")
        logger.info(f"[ANALYZE] Severity scores count: {len(trend_analysis.get('severity_scores', {}))}")

        markdown_report = report_generator.generate_markdown_report(
            trend_analysis, app_name, target_date
        )
        html_report = report_generator.generate_html_report(
            trend_analysis, app_name, target_date
        )

        response_data = {
            "status": "success",
            "app_name": app_name,
            "total_reviews": result.get("total_reviews", 0),
            "topics_extracted": result.get("topics_extracted", 0),
            "trend_analysis": trend_analysis,  # Include trend analysis for frontend
            "report_markdown": markdown_report,
            "report_html": html_report,
        }

        logger.info(f"[ANALYZE] Response keys: {list(response_data.keys())}")
        logger.info(f"[ANALYZE] Sending response to frontend...")

        return response_data
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/report/{report_file}", response_class=FileResponse)
def get_report(report_file: str):
    """Serve generated reports"""
    try:
        filepath = Path("output") / report_file
        if not filepath.exists():
            raise HTTPException(status_code=404, detail="Report not found")
        
        if report_file.endswith(".md"):
            return FileResponse(filepath, media_type="text/markdown")
        elif report_file.endswith(".html"):
            return FileResponse(filepath, media_type="text/html")
        else:
            return FileResponse(filepath)
            
    except Exception as e:
        logger.error(f"Error retrieving report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
