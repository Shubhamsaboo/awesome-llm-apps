from typing import Literal, Tuple, Dict, Optional
import os
import time
import json
import requests
import PyPDF2
from datetime import datetime, timedelta

import streamlit as st
from phi.agent import Agent
from phi.model.openai import OpenAIChat
from phi.tools.email import EmailTools
from phi.tools.zoom import ZoomTool
from phi.utils.log import logger
from dotenv import load_dotenv

load_dotenv()

# Constants
FROM_EMAIL = "ryomensukuna64@gmail.com"

ACCOUNT_ID = os.getenv("ZOOM_ACCOUNT_ID")
CLIENT_ID = os.getenv("ZOOM_CLIENT_ID")
CLIENT_SECRET = os.getenv("ZOOM_CLIENT_SECRET")




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
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {"grant_type": "account_credentials", "account_id": self.account_id}

        try:
            response = requests.post(
                self.token_url, 
                headers=headers, 
                data=data,
                auth=(self.client_id, self.client_secret)  # Use basic auth
            )
            response.raise_for_status()

            token_info = response.json()
            self.access_token = token_info["access_token"]
            expires_in = token_info["expires_in"]
            self.token_expires_at = time.time() + expires_in - 60

            # Update this line to use the helper method
            self._set_parent_token(str(self.access_token))
            return str(self.access_token)

        except requests.RequestException as e:
            logger.error(f"Error fetching access token: {e}")
            return ""

    def _set_parent_token(self, token: str) -> None:
        """Helper method to set the token in the parent ZoomTool class"""
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
    """Initialize only necessary session state variables."""
    defaults = {
        'candidate_email': "",
        'openai_api_key': "",
        'resume_text': "",
        'analysis_complete': False,
        'is_selected': False
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def create_resume_analyzer() -> Agent:
    """Creates and returns a resume analysis agent."""
    if not st.session_state.openai_api_key:
        st.error("Please enter your OpenAI API key first.")
        return None

    return Agent(
        model=OpenAIChat(
            id="gpt-4o",
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

def create_email_agent() -> Agent:
    return Agent(
        model=OpenAIChat(
            id="gpt-4o",
            api_key=st.session_state.openai_api_key
        ),
        tools=[EmailTools(
            receiver_email=st.session_state.candidate_email,
            sender_email=FROM_EMAIL,
            sender_name="AI Recruitment Team",
            sender_passkey=os.getenv("EMAIL_PASSKEY")
        )],
        description="You are a professional recruitment coordinator handling email communications.",
        instructions=[
            "Draft and send professional recruitment emails",
            "Act like a human writing an email and use all lowercase letters",
            "Maintain a friendly yet professional tone",
            "Always end emails with exactly: 'best,\nthe ai recruiting team'",
            "Never include the sender's or receiver's name in the signature",
            "The name of the company is 'AI Recruiting Team'"
        ],
        markdown=True,
        show_tool_calls=True
    )


def create_scheduler_agent() -> Agent:

    zoom_tools = CustomZoomTool(account_id=ACCOUNT_ID, client_id=CLIENT_ID, client_secret=CLIENT_SECRET)

    return Agent(
        name="Interview Scheduler",
        model=OpenAIChat(
            id="gpt-4o",
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
        4. The name of the company is 'AI Recruiting Team'
        """
    )


def send_rejection_email(email_agent: Agent, to_email: str, role: str, feedback: str) -> None:
    """
    Send a rejection email with constructive feedback.
    """
    email_agent.run(
        f"""
        Send an email to {to_email} regarding their application for the {role} position.
        Use this specific style:
        1. use all lowercase letters
        2. be empathetic and human
        3. mention specific feedback from: {feedback}
        4. encourage them to upskill and try again
        5. suggest some learning resources based on missing skills
        6. end the email with exactly:
           best,
           the ai recruiting team
        
        Do not include any names in the signature.
        The tone should be like a human writing a quick but thoughtful email.
        """
    )


def schedule_interview(scheduler: Agent, candidate_email: str, email_agent: Agent, role: str) -> None:
    """
    Basic interview scheduler that creates a Zoom meeting and sends email details.
    Schedules interviews during business hours (9 AM - 5 PM EST).
    """
    try:
        # Calculate tomorrow at 2 PM EST (instead of UTC)
        tomorrow = datetime.now() + timedelta(days=1)
        interview_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
        
        # 1. Schedule the meeting with EST timezone specification
        meeting_response = scheduler.run(
            f"Schedule a 60-minute meeting titled '{role} Technical Interview' "
            f"for tomorrow at 2 PM EST (Eastern Time) 2024 with attendee {candidate_email}. "
            f"Ensure the meeting is between 9 AM - 5 PM EST only."
        )
        
        # 2. Send email notification
        email_agent.run(
            f"Send an email to {candidate_email} about their scheduled interview for "
            f"the {role} position. Include the Zoom meeting link from: {meeting_response}. "
            f"Make sure to specify that the time is in EST timezone."
        )
        
        st.success("Interview scheduled successfully!")
        
    except Exception as e:
        logger.error(f"Error scheduling interview: {str(e)}")
        st.error("Unable to schedule interview. Please try again.")


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
                email_agent = create_email_agent()  # Create email agent here
                
                if resume_analyzer and email_agent:
                    print("DEBUG: Starting resume analysis")
                    is_selected, feedback = analyze_resume(
                        st.session_state.resume_text,
                        role,
                        resume_analyzer
                    )
                    print(f"DEBUG: Analysis complete - Selected: {is_selected}, Feedback: {feedback}")

                    if is_selected:
                        st.success("Congratulations! Your skills match our requirements.")
                        st.session_state.analysis_complete = True
                        st.session_state.is_selected = True
                        st.rerun()
                    else:
                        st.warning("Unfortunately, your skills don't match our requirements.")
                        st.write(f"Feedback: {feedback}")
                        
                        # Send rejection email
                        with st.spinner("Sending feedback email..."):
                            try:
                                send_rejection_email(
                                    email_agent=email_agent,
                                    to_email=email,
                                    role=role,
                                    feedback=feedback
                                )
                                st.info("We've sent you an email with detailed feedback.")
                            except Exception as e:
                                logger.error(f"Error sending rejection email: {e}")
                                st.error("Could not send feedback email. Please try again.")

    if st.session_state.get('analysis_complete') and st.session_state.get('is_selected', False):
        st.success("Congratulations! Your skills match our requirements.")
        st.info("Click 'Proceed with Application' to continue with the interview process.")
        
        if st.button("Proceed with Application", key="proceed_button"):
            print("DEBUG: Proceed button clicked")  # Debug
            with st.spinner("🔄 Processing your application..."):
                try:
                    print("DEBUG: Creating email agent")  # Debug
                    email_agent = create_email_agent()
                    print(f"DEBUG: Email agent created: {email_agent}")  # Debug
                    
                    print("DEBUG: Creating scheduler agent")  # Debug
                    scheduler_agent = create_scheduler_agent()
                    print(f"DEBUG: Scheduler agent created: {scheduler_agent}")  # Debug

                    # 3. Send selection email
                    with st.status("📧 Sending confirmation email...", expanded=True) as status:
                        print(f"DEBUG: Attempting to send email to {st.session_state.candidate_email}")  # Debug
                        send_selection_email(
                            email_agent,
                            st.session_state.candidate_email,
                            role
                        )
                        print("DEBUG: Email sent successfully")  # Debug
                        status.update(label="✅ Confirmation email sent!")

                    # 4. Schedule interview
                    with st.status("📅 Scheduling interview...", expanded=True) as status:
                        print("DEBUG: Attempting to schedule interview")  # Debug
                        schedule_interview(
                            scheduler_agent,
                            st.session_state.candidate_email,
                            email_agent,
                            role
                        )
                        print("DEBUG: Interview scheduled successfully")  # Debug
                        status.update(label="✅ Interview scheduled!")

                    print("DEBUG: All processes completed successfully")  # Debug
                    st.success("""
                        🎉 Application Successfully Processed!
                        
                        Please check your email for:
                        1. Selection confirmation ✅
                        2. Interview details with Zoom link 🔗
                        
                        Next steps:
                        1. Review the role requirements
                        2. Prepare for your technical interview
                        3. Join the interview 5 minutes early
                    """)

                except Exception as e:
                    print(f"DEBUG: Error occurred: {str(e)}")  # Debug
                    print(f"DEBUG: Error type: {type(e)}")  # Debug
                    import traceback
                    print(f"DEBUG: Full traceback: {traceback.format_exc()}")  # Debug
                    st.error(f"An error occurred: {str(e)}")
                    st.error("Please try again or contact support.")

    # Reset button
    if st.sidebar.button("Reset Application"):
        for key in st.session_state.keys():
            if key != 'openai_api_key':
                del st.session_state[key]
        st.rerun()

if __name__ == "__main__":
    main()