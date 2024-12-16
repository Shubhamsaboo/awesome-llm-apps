from typing import Literal, Tuple, Dict
import os
import time
import streamlit as st
from phi.agent import Agent
from phi.model.openai import OpenAIChat
from phi.tools.resend_tools import ResendTools
from phi.tools.zoom import ZoomTool
import PyPDF2
import json
import requests
from typing import Optional
from phi.utils.log import logger

# Constants
FROM_EMAIL = "madhushantan@voxlingua.co.site"
RESEND_API_KEY = "re_5R"

# Zoom credentials
ZOOM_ACCOUNT_ID = os.getenv("ZOOM_ACCOUNT_ID")
ZOOM_CLIENT_ID = os.getenv("ZOOM_CLIENT_ID")
ZOOM_CLIENT_SECRET = os.getenv("ZOOM_CLIENT_SECRET")

class CustomZoomTool(ZoomTool):
    def __init__(
        self,
        account_id: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        name: str = "zoom_tool",
    ):
        super().__init__(account_id=account_id, client_id=client_id, client_secret=client_secret, name=name)
        self.token_url = "https://zoom.us/oauth/token"
        self.access_token = None
        self.token_expires_at = 0

    def get_access_token(self) -> str:
        if self.access_token and time.time() < self.token_expires_at:
            return str(self.access_token)

        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {"grant_type": "account_credentials", "account_id": self.account_id}

        try:
            response = requests.post(
                self.token_url, headers=headers, data=data, auth=(self.client_id, self.client_secret)
            )
            response.raise_for_status()

            token_info = response.json()
            self.access_token = token_info["access_token"]
            expires_in = token_info["expires_in"]
            self.token_expires_at = time.time() + expires_in - 60

            self._set_parent_token(str(self.access_token))
            return str(self.access_token)
        except requests.RequestException as e:
            logger.error(f"Error fetching access token: {e}")
            return ""

    def _set_parent_token(self, token: str) -> None:
        if token:
            self._ZoomTool__access_token = token

# Role requirements as a constant dictionary
ROLE_REQUIREMENTS: Dict[str, str] = {
    "ai_ml_engineer": """
        Required Skills:
        - Python, PyTorch/TensorFlow
        - Machine Learning algorithms and frameworks
        - Deep Learning and Neural Networks
        - Data preprocessing and analysis
        - MLOps and model deployment
    """,
    "frontend_engineer": """
        Required Skills:
        - React/Vue.js/Angular
        - HTML5, CSS3, JavaScript/TypeScript
        - Responsive design
        - State management
        - Frontend testing
    """,
    "backend_engineer": """
        Required Skills:
        - Python/Java/Node.js
        - REST APIs
        - Database design and management
        - System architecture
        - Cloud services (AWS/GCP/Azure)
    """
}

def init_session_state():
    """Initialize session state variables."""
    if 'candidate_email' not in st.session_state:
        st.session_state.candidate_email = ""
    if 'openai_api_key' not in st.session_state:
        st.session_state.openai_api_key = ""
    if 'resume_text' not in st.session_state:
        st.session_state.resume_text = ""
    if 'analysis_complete' not in st.session_state:
        st.session_state.analysis_complete = False

def create_resume_analyzer() -> Agent:
    """Creates and returns a resume analysis agent."""
    if not st.session_state.openai_api_key:
        st.error("Please enter your OpenAI API key first.")
        return None
        
    return Agent(
        model=OpenAIChat(
            model="gpt-4",
            api_key=st.session_state.openai_api_key
        ),
        description="You are an expert technical recruiter who analyzes resumes.",
        instructions=[
            "Analyze the resume against the provided job requirements",
            "Evaluate technical skills and experience match",
            "Provide detailed feedback on candidate suitability",
            "Return a JSON response with selection decision and feedback"
        ],
        markdown=True
    )

def create_email_agent(from_email: str) -> Agent:
    """
    Creates and returns an email communication agent using Resend.
    
    Args:
        from_email: Email address to send from
        
    Returns:
        Agent: Configured email communication agent
    """
    return Agent(
        model=OpenAIChat(model="gpt-4"),
        tools=[ResendTools(from_email=from_email, api_key=RESEND_API_KEY)],
        description="You are a professional recruitment coordinator handling email communications.",
        instructions=[
            "Draft and send professional recruitment emails",
            "Include all necessary next steps and information",
            "Maintain a friendly yet professional tone"
        ],
        markdown=True,
        show_tool_calls=True
    )

def create_scheduler_agent() -> Agent:
    """
    Creates and returns a meeting scheduler agent that creates Zoom meetings.
    
    Returns:
        Agent: Configured meeting scheduler agent
    """
    zoom_tools = CustomZoomTool(
        account_id=ZOOM_ACCOUNT_ID,
        client_id=ZOOM_CLIENT_ID,
        client_secret=ZOOM_CLIENT_SECRET
    )

    return Agent(
        name="Interview Scheduler",
        model=OpenAIChat(
            model="gpt-4",
            api_key=st.session_state.openai_api_key
        ),
        tools=[zoom_tools],
        description="You are an interview scheduling coordinator.",
        instructions=[
            "You are an expert at scheduling technical interviews using Zoom.",
            "Schedule interviews during business hours (9 AM - 5 PM EST)",
            "Create meetings with proper titles and descriptions",
            "Ensure all meeting details are included in responses",
            "Use ISO 8601 format for dates",
            "Handle scheduling errors gracefully"
        ],
        markdown=True,
        show_tool_calls=True
    )

def extract_text_from_pdf(pdf_file) -> str:
    """
    Extract text from uploaded PDF file.
    
    Args:
        pdf_file: Streamlit uploaded file object
    
    Returns:
        str: Extracted text from PDF
    """
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        st.error(f"Error extracting PDF text: {str(e)}")
        return ""

def analyze_resume(
    resume_text: str,
    role: Literal["ai_ml_engineer", "frontend_engineer", "backend_engineer"],
    analyzer: Agent
) -> Tuple[bool, str]:
    """
    Analyzes resume text against role requirements.
    
    Args:
        resume_text: Extracted text from resume
        role: Selected role
        analyzer: Resume analyzer agent
    
    Returns:
        Tuple[bool, str]: (is_selected, feedback)
    """
    response = analyzer.run(
        f"""
        Please analyze this resume against the following requirements and provide your response in valid JSON format:

        Role Requirements:
        {ROLE_REQUIREMENTS[role]}

        Resume Text:
        {resume_text}

        Your response must be a valid JSON object like this:
        {{
            "selected": true,
            "feedback": "Detailed feedback explaining the decision",
            "matching_skills": ["skill1", "skill2"],
            "missing_skills": ["skill3", "skill4"],
            "experience_level": "junior/mid/senior"
        }}

        Ensure your response is properly formatted JSON with double quotes around property names and string values.
        """
    )
    
    try:
        # Convert RunResponse to string and clean it up
        response_text = str(response).strip()
        
        # Debug logging
        logger.info(f"Raw response: {response_text}")
        
        # Try to find JSON in the response
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            # Debug logging
            logger.info(f"Extracted JSON string: {json_str}")
            
            try:
                result = json.loads(json_str)
                if "selected" in result and "feedback" in result:
                    return result["selected"], result["feedback"]
                else:
                    st.error("Response missing required fields")
                    return False, "Error: Invalid response format"
            except json.JSONDecodeError as e:
                st.error(f"JSON parsing error: {str(e)}")
                # Try to clean up common JSON formatting issues
                cleaned_json = json_str.replace("'", '"')  # Replace single quotes with double quotes
                try:
                    result = json.loads(cleaned_json)
                    return result["selected"], result["feedback"]
                except:
                    return False, "Error: Could not parse response"
        else:
            st.error("No JSON found in response")
            return False, "Error: Invalid response format"
            
    except Exception as e:
        logger.error(f"Error in analyze_resume: {str(e)}")
        logger.error(f"Full response: {response}")
        return False, f"Error analyzing resume: {str(e)}"

def send_selection_email(email_agent: Agent, to_email: str, role: str) -> None:
    """
    Sends selection email to candidate using Resend.
    
    Args:
        email_agent: The email communication agent
        to_email: Candidate's email address
        role: The role being applied for
    """
    email_agent.run(
        f"""
        Send an email to {to_email} regarding their selection for the {role} position.
        The email should:
        1. Congratulate them on being selected
        2. Explain the next steps in the process
        3. Mention that they will receive interview details shortly
        """
    )

def schedule_interview(scheduler: Agent, candidate_email: str, email_agent: Agent, role: str) -> None:
    """
    Schedules Zoom interview and sends details via email.
    
    Args:
        scheduler: The interview scheduler agent
        candidate_email: Candidate's email address
        email_agent: The email agent for sending meeting details
        role: The role being applied for
    """
    # Schedule Zoom meeting
    response = scheduler.run(
        f"""
        Schedule a technical interview meeting with these specifications:
        - Title: "{role} Technical Interview"
        - Time: Schedule for next week during business hours (9 AM - 5 PM EST)
        - Duration: 60 minutes
        - Description: Technical interview for {role} position
        - Attendee: {candidate_email}
        
        Return the meeting details in JSON format including:
        - meeting_id
        - join_url
        - start_time
        - duration
        """
    )
    
    try:
        # Convert RunResponse to string before parsing JSON
        response_text = str(response)
        # Find the JSON part in the response
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            meeting_details = json.loads(json_str)
            
            # Send email with Zoom details
            email_agent.run(
                f"""
                Send an email to {candidate_email} with the following interview details:
                
                Subject: Technical Interview Scheduled - {role} Position
                
                The email should include:
                1. Interview Date and Time: {meeting_details['start_time']} EST
                2. Duration: {meeting_details['duration']} minutes
                3. Zoom Meeting Link: {meeting_details['join_url']}
                4. Meeting ID: {meeting_details['meeting_id']}
                5. Preparation Instructions:
                   - Review the job requirements
                   - Prepare to discuss your technical experience
                   - Have a stable internet connection
                   - Join 5 minutes early
                6. What to expect during the interview
                
                Make it professional and welcoming.
                """
            )
            
            st.success("Interview scheduled and Zoom details sent to your email!")
            
        else:
            st.error("Could not find meeting details in response")
            
    except (json.JSONDecodeError, KeyError) as e:
        st.error(f"Error scheduling the interview: {str(e)}")
        # Log the raw response for debugging
        logger.error(f"Raw response: {response}")

def main() -> None:
    """Main function to run the Streamlit application."""
    st.title("AI Recruitment System")
    
    # Initialize session state
    init_session_state()
    
    # Sidebar for API key
    with st.sidebar:
        st.header("Configuration")
        api_key = st.text_input(
            "Enter your OpenAI API key",
            type="password",
            value=st.session_state.openai_api_key,
            help="Get your API key from platform.openai.com"
        )
        if api_key:
            st.session_state.openai_api_key = api_key
    
    # Main content
    if not st.session_state.openai_api_key:
        st.warning("Please enter your OpenAI API key in the sidebar to continue.")
        return
        
    # Role selection with requirements display
    role = st.selectbox(
        "Select the role you're applying for:",
        ["ai_ml_engineer", "frontend_engineer", "backend_engineer"]
    )

    # Display requirements for selected role
    with st.expander("View Required Skills", expanded=True):
        st.markdown(ROLE_REQUIREMENTS[role])

    # Resume upload and processing
    resume_file = st.file_uploader("Upload your resume (PDF)", type=["pdf"])
    if resume_file and not st.session_state.resume_text:
        with st.spinner("Processing your resume..."):
            resume_text = extract_text_from_pdf(resume_file)
            if resume_text:
                st.session_state.resume_text = resume_text
                st.success("Resume processed successfully!")
            else:
                st.error("Could not process the PDF. Please try again.")
    
    # Email input with session state
    email = st.text_input(
        "Your email address",
        value=st.session_state.candidate_email,
        key="email_input"
    )
    st.session_state.candidate_email = email

    # Analysis and next steps
    if st.session_state.resume_text and email and not st.session_state.analysis_complete:
        if st.button("Analyze Resume"):
            with st.spinner("Analyzing your resume..."):
                resume_analyzer = create_resume_analyzer()
                if resume_analyzer:
                    # Show analysis in progress
                    analysis_placeholder = st.empty()
                    analysis_placeholder.info("Analyzing your skills match...")
                    
                    # Analyze resume
                    is_selected, feedback = analyze_resume(
                        st.session_state.resume_text,
                        role,
                        resume_analyzer
                    )
                    
                    # Clear the analysis placeholder
                    analysis_placeholder.empty()
                    
                    if is_selected:
                        st.success("Congratulations! Your skills match our requirements.")
                        st.session_state.analysis_complete = True
                        
                        # Show next steps
                        st.info("Click 'Proceed with Application' to continue with the interview process.")
                        
                        if st.button("Proceed with Application"):
                            with st.spinner("Setting up your interview..."):
                                email_agent = create_email_agent(from_email=FROM_EMAIL)
                                scheduler = create_scheduler_agent()
                                
                                # First send selection email
                                send_selection_email(
                                    email_agent,
                                    st.session_state.candidate_email,
                                    role
                                )
                                
                                # Then schedule interview and send details
                                schedule_interview(
                                    scheduler,
                                    st.session_state.candidate_email,
                                    email_agent,
                                    role
                                )
                    else:
                        st.error(f"Thank you for applying. {feedback}")
                        # Add a retry button
                        if st.button("Upload Different Resume"):
                            st.session_state.resume_text = ""
                            st.experimental_rerun()

    # Reset button
    if st.sidebar.button("Reset Application"):
        for key in st.session_state.keys():
            if key != 'openai_api_key':
                del st.session_state[key]
        st.experimental_rerun()

if __name__ == "__main__":
    main()
