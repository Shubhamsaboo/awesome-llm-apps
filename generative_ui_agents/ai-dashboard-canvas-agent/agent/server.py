from fastapi import FastAPI
from ag_ui_adk import add_adk_fastapi_endpoint

from agent import dashboard_agent

from dotenv import load_dotenv
load_dotenv()


# Create FastAPI app
app = FastAPI(title="ADK Middleware Dashboard Agent")

# Add the ADK endpoint
add_adk_fastapi_endpoint(app, dashboard_agent, path="/")

if __name__ == "__main__":
    import os
    import uvicorn

    if not os.getenv("GOOGLE_API_KEY"):
        print("⚠️  Warning: GOOGLE_API_KEY environment variable not set!")
        print("   Set it with: export GOOGLE_API_KEY='your-key-here'")
        print("   Get a key from: https://makersuite.google.com/app/apikey")
        print()

    port = int(os.getenv("PORT", 8000))
    should_reload = not (os.getenv("AGENT_RELOAD", "true").lower() == "false")
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=should_reload)
