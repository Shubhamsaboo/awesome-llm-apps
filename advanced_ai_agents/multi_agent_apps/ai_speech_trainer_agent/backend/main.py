from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from agents.coordinator_agent import coordinator_agent
from agno.agent import RunResponse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Configure CORS to allow requests from your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # To be replaced with the frontend's origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define the request body model
class AnalysisRequest(BaseModel):
    video_url: str

# Define the entry point
@app.get("/")
async def root():
    return {"message": "Welcome to the video analysis API!"}

# Define the analysis endpoint
@app.post("/analyze")
async def analyze(request: AnalysisRequest):
    video_url = request.video_url
    prompt = f"Analyze the following video: {video_url}"
    response: RunResponse = coordinator_agent.run(prompt)

    # Assuming response.content is a Pydantic model or a dictionary
    json_compatible_response = jsonable_encoder(response.content)
    return JSONResponse(content=json_compatible_response)