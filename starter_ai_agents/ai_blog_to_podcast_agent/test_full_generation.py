
import os
from uuid import uuid4
from agno.agent import Agent
from agno.run.agent import RunOutput
from agno.models.openai import OpenAIChat
from podcast_utils import (
    extract_text_from_html,
    fetch_url_with_curl,
    synthesize_aiff_with_say,
    get_openai_api_key,
)

# Set the API key
os.environ["OPENAI_API_KEY"] = get_openai_api_key()

url = "https://www.linkedin.com/posts/michaelmansard_monetization-subscriptionbusiness-outcome-share-7470739017278394369-RLTF/?utm_source=share&utm_medium=member_desktop&rcm=ACoAAAukpLsBCcIP7ycPgCOqjUJ-_u7JUkYEDaY"

print(f"--- Starting Pipeline for {url} ---")

try:
    # 1. Fetch HTML
    print("Fetching HTML...")
    html = fetch_url_with_curl(url)
    
    # 2. Extract Text
    print("Extracting text...")
    article_text = extract_text_from_html(html)
    print(f"Extracted {len(article_text)} characters.")

    # 3. Summarize
    print("Generating summary with Agno Agent (GPT-4o)...")
    agent = Agent(
        name="Blog Summarizer",
        model=OpenAIChat(id="gpt-4o"),
        instructions=[
            "Create a concise, engaging summary (max 2000 characters) suitable for a podcast.",
            "The summary should be conversational and capture the main points.",
            "Ignore any sign-in or cookie boilerplate from the input."
        ],
    )
    
    response: RunOutput = agent.run(
        f"Summarize this LinkedIn post for a podcast:\n\n{article_text[:12000]}"
    )
    summary = response.content if hasattr(response, 'content') else str(response)
    
    print("\n--- Summary ---")
    print(summary)
    print("----------------\n")

    # 4. Synthesize Audio
    audio_path = f"/tmp/test-podcast-{uuid4()}.aiff"
    print(f"Synthesizing audio to {audio_path}...")
    synthesize_aiff_with_say(summary, audio_path)
    print("Success! Audio file generated.")

except Exception as e:
    print(f"Error during execution: {e}")
