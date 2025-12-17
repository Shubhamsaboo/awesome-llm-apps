from google.adk.agents import LlmAgent
from pydantic import BaseModel, Field

class EmailContent(BaseModel):
    """Schema for email content with subject and body."""
    
    subject: str = Field(
        description="The subject line of the email. Should be concise and descriptive."
    )
    body: str = Field(
        description="The main content of the email. Should be well-formatted with proper greeting, paragraphs, and signature."
    )

root_agent = LlmAgent(
    name="email_generator_agent",
    model="gemini-3-flash-preview",
    description="Professional email generator that creates structured email content",
    instruction="""
    You are a professional email writing assistant. 
    
    IMPORTANT: Your response must be a JSON object with exactly these fields:
    - "subject": A concise, relevant subject line
    - "body": Well-formatted email content with greeting, main content, and closing
    
    Format your response as valid JSON only.
    """,
    output_schema=EmailContent,  # This is where the magic happens
    output_key="generated_email"  
)