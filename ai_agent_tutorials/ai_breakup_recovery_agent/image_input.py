from agno.agent import Agent
from agno.media import Image
from agno.models.google import Gemini
from agno.tools.duckduckgo import DuckDuckGoTools
from PIL import Image as PILImage
from io import BytesIO
import os

def load_image(image_data):
    """Load and prepare image using PIL"""
    # Convert image data to PIL Image
    img = PILImage.open(image_data).convert('RGB')
    
    # Convert PIL image to bytes
    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    img_bytes = buffered.getvalue()
    
    return img_bytes

def create_chat_analysis_agent():
    """Creates a specialized agent for analyzing chat patterns"""
    return Agent(
        name="Chat Analysis Agent",
        role="You are a specialized agent that analyzes chat screenshots for relationship patterns and communication issues.",
        instructions=[
            "Analyze the chat screenshot for the following patterns:",
            "1. Communication Patterns: Identify recurring themes, response times, and conversation flow",
            "2. Passive-Aggression: Look for subtle hostile or manipulative language",
            "3. Manipulation: Identify gaslighting, guilt-tripping, or controlling behaviors",
            "4. Mixed Signals: Detect inconsistent messages or unclear intentions",
            "Provide a detailed analysis with specific examples from the chat",
            "Format the output clearly with sections for each pattern type",
            "Be objective and focus on observable patterns rather than making assumptions",
        ],
        model=Gemini(
            id="gemini-2.0-flash",
            api_key=os.environ.get("GEMINI_API_KEY")
        ),
        tools=[DuckDuckGoTools()],
        markdown=True,
    )

def analyze_chat_screenshot(image_data):
    """Analyze a chat screenshot using the specialized agent"""
    try:
        # Load and process the image
        image_bytes = load_image(image_data)
        
        # Create the chat analysis agent
        agent = create_chat_analysis_agent()
        
        # Analyze the chat screenshot
        response = agent.run(
            "Please analyze this chat screenshot for communication patterns, passive-aggression, manipulation, and mixed signals.",
            images=[Image(content=image_bytes)]
        )
        
        return response.content
        
    except Exception as e:
        return f"Error analyzing chat screenshot: {str(e)}"