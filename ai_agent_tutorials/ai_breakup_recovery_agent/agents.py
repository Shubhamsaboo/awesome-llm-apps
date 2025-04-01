from agno.agent import Agent
from agno.team.team import Team
from agno.models.google import Gemini
from agno.tools.duckduckgo import DuckDuckGoTools
from PIL import Image
import easyocr
import os

# --- Therapist Agent ---
def create_therapist_agent():
    return Agent(
        name="Therapist Agent",
        role="You are a therapist who validates feelings and encourages reflection without judgment.",
        instructions=[
            "Listen to the user's feelings with empathy and compassion.",
            "Ask reflective questions to help them explore their emotions.",
            "Offer coping strategies without being dismissive.",
            "Validate their experiences and provide emotional support.",
        ],
        model=Gemini(
            id="gemini-2.0-flash",
            api_key=os.environ.get("GEMINI_API_KEY")
        ),
        tools=[DuckDuckGoTools()],
        add_datetime_to_instructions=True,     # Add timestamp context
        show_tool_calls=True,
        markdown=True
    )

# --- Closure Agent ---
def create_closure_agent():
    return Agent(
        name="Closure Agent",
        role="You write emotional closure messages the user *should not* send.",
        instructions=[
            "Create emotional messages that express raw, honest feelings.",
            "The messages should NOT be sent — they are only for emotional release.",
            "Format the output clearly with a header: **Message Drafts You Shouldn't Send**",
            "Ensure the tone is heartfelt, authentic, and honest.",
        ],
        model=Gemini(
            id="gemini-2.0-flash",
            api_key=os.environ.get("GEMINI_API_KEY")
        ),
        tools=[DuckDuckGoTools()],
        add_datetime_to_instructions=True,    # Add timestamp context
        show_tool_calls=True,
        markdown=True
    )


 # --- Routine Planner Agent ---
def create_routine_agent():
    """Creates the Routine Planner Agent with recovery routines."""
    return Agent(
        name="Routine Planner Agent",
        role="Create a realistic daily routine to help someone emotionally recover after a breakup.",
        instructions=[
            "Suggest a balanced daily routine with healthy habits.",
            "Include time for self-reflection, creative outlets, and physical activities.",
            "Suggest social interactions, like reconnecting with friends or family.",
            "Include healthy distractions, such as hobbies, reading, or new experiences.",
            "Format the output clearly with a header: **Daily Recovery Routine**",
        ],
        model=Gemini(
            id="gemini-2.0-flash",
            api_key=os.environ.get("GEMINI_API_KEY")
        ),
        tools=[DuckDuckGoTools()],
        add_datetime_to_instructions=True,
        show_tool_calls=True,
        markdown=True
    )   

# --- Brutal Honesty Agent ---
def create_honesty_agent():
    """Creates the Brutal Honesty Agent with no-nonsense, direct responses."""
    return Agent(
        name="Brutal Honesty Agent",
        role="Be brutally honest and objective about what went wrong and why the user needs to move on. No sugar-coating.",
        instructions=[
            "Give raw, direct, and objective feedback about the breakup.",
            "Explain why the relationship failed with clear, straightforward reasoning.",
            "Use blunt, factual language. No sugar-coating or emotional cushioning.",
            "Include reasons why the user should move on, based on the situation.",
            "Format the output clearly with a header: **Brutal Honesty**",
        ],
        # model=Gemini(id="gemini-2.0-flash"),
        model=Gemini(
            id="gemini-2.0-flash",
            api_key=os.environ.get("GEMINI_API_KEY")
        ),
        tools=[DuckDuckGoTools()],
        add_datetime_to_instructions=True,
        show_tool_calls=True,
        markdown=True
    )


# # --- Texts Analyzer Agent (Updated with easyocr) ---
# def extract_text_with_easyocr(image):
#     """Extract text from image using EasyOCR."""
#     reader = easyocr.Reader(['en'])  # Specify language
#     results = reader.readtext(image)

#     # Extract and combine text
#     extracted_text = " ".join([result[1] for result in results])
#     return extracted_text

# --- Team Leader (Breakup Recovery Team) ---
def create_breakup_team():
    return Team(
        name="Breakup Recovery Team",
        mode="coordinate",  # Team execution mode: coordinate or parallel
        # model=Gemini(id="gemini-2.0-flash"),
        model=Gemini(
            id="gemini-2.0-flash",
            api_key=os.environ.get("GEMINI_API_KEY")
        ),
        members=[
            create_therapist_agent(),
            create_closure_agent(),
            create_routine_agent(),   # Added Routine Planner Agent
            create_honesty_agent(),   # Added Brutal Honesty Agent
            # extract_text_with_easyocr()
        ],
        description="You are a team helping someone recover from a breakup.",
        instructions=[
            "First, ask the Therapist Agent to help the user explore their emotions.",
            "Then, ask the Closure Agent to create unsent emotional messages.",
            "Next, ask the Routine Planner Agent to suggest a healthy daily routine.",
            "Finally, ask the Brutal Honesty Agent to give direct and objective feedback.",
            "Summarize and refine all responses into a personalized recovery guide.",
            "Ensure the responses are supportive, encouraging, and insightful.",
            "Use markdown formatting for clear, readable output.",
        ],
        add_datetime_to_instructions=True,   # Add timestamp context
        show_members_responses=True,         # Display individual agent responses
        markdown=True,
    )
