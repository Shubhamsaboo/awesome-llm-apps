from typing import Literal, Tuple, Dict, Optional
import os
import time
import json
import base64
import requests
import PyPDF2

import streamlit as st
from phi.agent import Agent
from phi.model.openai import OpenAIChat
from phi.tools.resend_tools import ResendTools
from phi.tools.zoom import ZoomTool
from phi.utils.log import logger


# Constants
FROM_EMAIL = "madhushantan@voxlingua.co.site"
RESEND_API_KEY = "re_5R"


def get_zoom_credentials() -> Tuple[str, str, str]:
    """Get Zoom credentials from Streamlit secrets."""
    try:
        account_id = st.secrets["ZOOM_ACCOUNT_ID"]
        client_id = st.secrets["ZOOM_CLIENT_ID"]
        client_secret = st.secrets["ZOOM_CLIENT_SECRET"]
    except Exception as e:
        st.error("Please configure Zoom credentials in Streamlit secrets")
        st.stop()
    
    return account_id, client_id, client_secret


class CustomZoomTool(ZoomTool):
    def __init__(
        self,
        account_id: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        name: str = "zoom_tool",
    ):
        super().__init__(
            account_id=account_id,
            client_id=client_id,
            client_secret=client_secret,
            name=name
        )
        self.token_url = "https://zoom.us/oauth/token"
        self.access_token = None
        self.token_expires_at = 0

    def get_access_token(self) -> str:
        if self.access_token and time.time() < self.token_expires_at:
            return str(self.access_token)

        try:
            auth_header = base64.b64encode(
                f"{self.client_id}:{self.client_secret}".encode()
            ).decode()
            
            headers = {
                "Authorization": f"Basic {auth_header}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            data = {
                "grant_type": "account_credentials",
                "account_id": self.account_id
            }

            response = requests.post(self.token_url, headers=headers, data=data)
            response.raise_for_status()

            token_info = response.json()
            self.access_token = token_info["access_token"]
            expires_in = token_info["expires_in"]
            self.token_expires_at = time.time() + expires_in - 60

            # Set the token in parent class
            self._ZoomTool__access_token = self.access_token
            return str(self.access_token)

        except requests.RequestException as e:
            logger.error(f"Error fetching access token: {e}")
            return ""


# Role requirements as a constant dictionary
ROLE_REQUIREMENTS: Dict[str, str] = {
    "ai_ml_engineer": """
        Required Skills:
        - Python, PyTorch/TensorFlow
        - Machine Learning algorithms and frameworks
        - Deep Learning and Neural Networks
        - Data preprocessing and analysis
        - MLOps and model deployment
        - RAG, LLM, Finetuning and Prompt Engineering
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
        - Kubernetes, Docker, CI/CD
    """
}


def init_session_state() -> None:
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
            model="gpt-4o",
            api_key=st.session_state.openai_api_key
        ),
        description="You are an expert technical recruiter who analyzes resumes.",
        instructions=[
            "Analyze the resume against the provided job requirements",
            "Be lenient with AI/ML candidates who show strong potential",
            "Consider project experience as valid experience",
            "Value hands-on experience with key technologies",
            "Return a JSON response with selection decision and feedback"
        ],
        markdown=True
    )


def create_email_agent(from_email: str) -> Agent:
    return Agent(
        model=OpenAIChat(
            model="gpt-4o",
            api_key=st.session_state.openai_api_key
        ),
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
    account_id, client_id, client_secret = get_zoom_credentials()
    
    zoom_tools = CustomZoomTool(
        account_id=account_id,
        client_id=client_id,
        client_secret=client_secret
    )

    return Agent(
        name="Interview Scheduler",
        model=OpenAIChat(
            model="gpt-4o",
            api_key=st.session_state.openai_api_key
        ),
        tools=[zoom_tools],
        description="You are an interview scheduling coordinator.",
        instructions=[
            f"You are an expert at scheduling technical interviews using Zoom.",
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
    try:
        response = analyzer.run(f"""
        Please analyze this resume against the following requirements and provide your response in valid JSON format:

        Role Requirements:
        {ROLE_REQUIREMENTS[role]}

        Resume Text:
        {resume_text}

        Your response must be a valid JSON object like this:
        {{
            "selected": true/false,
            "feedback": "Detailed feedback explaining the decision",
            "matching_skills": ["skill1", "skill2"],
            "missing_skills": ["skill3", "skill4"],
            "experience_level": "junior/mid/senior"
        }}

        Evaluation criteria:
        1. Match at least 70% of required skills
        2. Consider both theoretical knowledge and practical experience
        3. Value project experience and real-world applications
        4. Consider transferable skills from similar technologies
        5. Look for evidence of continuous learning and adaptability

        Important: Return ONLY the JSON object without any markdown formatting or backticks.
        """)
        
        # Extract the assistant's message content
        assistant_message = None
        for message in response.messages:
            if message.role == 'assistant':
                assistant_message = message.content
                break
        
        if not assistant_message:
            raise ValueError("No assistant message found in response.")
        result = json.loads(assistant_message.strip())
        
        if not isinstance(result, dict):
            raise ValueError("Response is not a JSON object")
            
        if "selected" not in result or "feedback" not in result:
            raise ValueError("Missing required fields in response")
            
        return result["selected"], result["feedback"]
            
    except (json.JSONDecodeError, ValueError) as e:
        st.error(f"Error processing response: {str(e)}")
        return False, f"Error analyzing resume: {str(e)}"


def send_selection_email(email_agent: Agent, to_email: str, role: str) -> None:
    email_agent.run(
        f"""
        Send an email to {to_email} regarding their selection for the {role} position.
        The email should:
        1. Congratulate them on being selected
        2. Explain the next steps in the process
        3. Mention that they will receive interview details shortly
        """
    )


def send_rejection_email(email_agent: Agent, to_email: str, role: str, feedback: str) -> None:
    email_agent.run(
        f"""
        Send an email to {to_email} regarding their application for the {role} position.
        Use this specific style:
        1. use all lowercase letters
        2. be empathetic and human
        3. mention specific feedback from: {feedback}
        4. encourage them to upskill and try again
        5. suggest some learning resources based on missing skills
        6. sign off with a friendly note

        The tone should be like a human writing a quick but thoughtful email.
        """
    )


def schedule_interview(scheduler: Agent, candidate_email: str, email_agent: Agent, role: str) -> None:
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
        meeting_details = json.loads(str(response))
        email_agent.run(
            f"""
            Send an email to {candidate_email} with the following interview details:
            
            Subject: Technical Interview Scheduled - {role} Position
            
            Include:
            1. Interview Date and Time: {meeting_details['start_time']} EST
            2. Duration: {meeting_details['duration']} minutes
            3. Zoom Meeting Link: {meeting_details['join_url']}
            4. Meeting ID: {meeting_details['meeting_id']}
            5. Preparation Instructions:
               - Review the job requirements
               - Prepare to discuss your technical experience
               - Have a stable internet connection
               - Join 5 minutes early
            """
        )
        
        st.success("Interview scheduled and Zoom details sent to your email!")
        
    except json.JSONDecodeError as e:
        st.error(f"Error scheduling the interview: {str(e)}")


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
                    is_selected, feedback = analyze_resume(
                        st.session_state.resume_text,
                        role,
                        resume_analyzer
                    )
                    
                    if is_selected:
                        st.success("Congratulations! Your skills match our requirements.")
                        st.session_state.analysis_complete = True
                        
                        # Show next steps
                        st.info("Click 'Proceed with Application' to continue with the interview process.")
                        
                        if st.button("Proceed with Application"):
                            try:
                                # Show processing status
                                with st.spinner("🔄 Processing your application..."):
                                    # 1. Create email agent for sending confirmation
                                    email_agent = create_email_agent(from_email=FROM_EMAIL)
                                    
                                    # 2. Create scheduler agent for Zoom meeting
                                    scheduler = create_scheduler_agent()
                                    
                                    # 3. First send selection email
                                    st.info("📧 Sending confirmation email...")
                                    send_selection_email(
                                        email_agent,
                                        st.session_state.candidate_email,
                                        role
                                    )
                                    
                                    # 4. Then schedule interview and send details
                                    st.info("📅 Scheduling your interview...")
                                    schedule_interview(
                                        scheduler,
                                        st.session_state.candidate_email,
                                        email_agent,
                                        role
                                    )
                                
                                # 5. Show final success message
                                st.success("""
                                    ✅ Application Successfully Processed!
                                    
                                    Here's what happens next:
                                    1. Check your email for the selection confirmation
                                    2. You'll receive another email with Zoom interview details
                                    3. Review the role requirements before the interview
                                    4. Make sure to join the interview 5 minutes early
                                """, icon="🎉")
                                
                                # Add a divider for better visibility
                                st.divider()
                                
                            except Exception as e:
                                st.error(f"An error occurred: {str(e)}")
                    else:
                        st.error("Thank you for applying. You're skillset and work is awesome but it doesn't match our requirements. Please check your email for detailed feedback on your application.")
                        email_agent = create_email_agent(from_email=FROM_EMAIL)
                        # Send rejection email
                        send_rejection_email(
                            email_agent,
                            st.session_state.candidate_email,
                            role,
                            feedback
                        )
                        if st.button("Upload Different Resume"):
                            st.session_state.resume_text = ""
                            st.rerun()

    # Reset button
    if st.sidebar.button("Reset Application"):
        for key in st.session_state.keys():
            if key != 'openai_api_key':
                del st.session_state[key]
        st.rerun()

if __name__ == "__main__":
    main()
