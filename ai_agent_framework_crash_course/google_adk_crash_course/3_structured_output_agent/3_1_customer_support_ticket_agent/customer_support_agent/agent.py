from typing import List, Optional
from enum import Enum
from google.adk.agents import LlmAgent
from pydantic import BaseModel, Field

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    CRITICAL = "critical"

class SupportTicket(BaseModel):
    title: str = Field(description="A concise summary of the issue")
    description: str = Field(description="Detailed description of the problem")
    priority: Priority = Field(description="The ticket priority level")
    category: str = Field(description="The department this ticket belongs to")
    steps_to_reproduce: Optional[List[str]] = Field(
        description="Steps to reproduce the issue (for technical problems)",
        default=None
    )
    estimated_resolution_time: str = Field(
        description="Estimated time to resolve this issue"
    )

root_agent = LlmAgent(
    name="customer_support_agent",
    model="gemini-3-flash-preview",
    description="Creates structured support tickets from user reports",
    instruction="""
    You are a support ticket creation assistant.
    
    Based on user problem descriptions, create well-structured support tickets with appropriate priority levels, categories, and resolution estimates.
    
    IMPORTANT: Response must be valid JSON matching the SupportTicket schema with these fields:
    - "title": Concise summary of the issue
    - "description": Detailed problem description
    - "priority": One of "low", "medium", "high", or "critical"
    - "category": Department (e.g., "Technical", "Billing", "Account", "Product")
    - "steps_to_reproduce": List of steps (for technical issues) or null
    - "estimated_resolution_time": Estimated resolution time (e.g., "2-4 hours", "1-2 days")
    
    Format your response as valid JSON only.
    """,
    output_schema=SupportTicket,
    output_key="support_ticket"
) 