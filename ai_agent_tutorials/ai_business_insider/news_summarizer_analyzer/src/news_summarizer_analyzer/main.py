import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from crew import NewsSummarizerAnalyzerCrew
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI()

# Add CORS middleware with both localhost and deployed URLs
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ai-business-insider.streamlit.app",
        "http://localhost:8501",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    logger.info("Health check requested")
    return {
        "status": "healthy",
        "environment": os.getenv("ENVIRONMENT", "production")
    }

crew = NewsSummarizerAnalyzerCrew()

class TopicRequest(BaseModel):
    topic: str

@app.post("/analyze")
async def analyze_topic(request: TopicRequest) -> dict:
    """
    Analyzes a given topic using the NewsSummarizerAnalyzerCrew.
    """
    try:
        logger.info(f"Analyzing topic: {request.topic}")
        crew_output = crew.kickoff(request.topic)
        
        result = {
            "summary": crew_output.raw,
            "tasks": [
                {
                    "description": task.description,
                    "output": task.raw
                }
                for task in crew_output.tasks_output
            ]
        }
        
        logger.info("Analysis completed successfully")
        return result
    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
