"""
OpenAI Agents SDK Tutorial 2: Structured Output Agent - Support Tickets

This module demonstrates how to create an agent that returns structured data
using Pydantic models for support ticket creation.
"""

import os
from typing import List, Optional
from enum import Enum
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from agents import Agent, Runner

# Load environment variables
load_dotenv()

class Priority(str, Enum):
    """Priority levels for support tickets"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Category(str, Enum):
    """Support ticket categories"""
    TECHNICAL = "technical"
    BILLING = "billing"
    ACCOUNT = "account"
    PRODUCT = "product"
    GENERAL = "general"

class SupportTicket(BaseModel):
    """Structured support ticket model"""
    title: str = Field(description="A concise summary of the issue")
    description: str = Field(description="Detailed description of the problem")
    priority: Priority = Field(description="The ticket priority level")
    category: Category = Field(description="The department this ticket belongs to")
    customer_name: Optional[str] = Field(
        description="Customer name if mentioned",
        default=None
    )
    steps_to_reproduce: Optional[List[str]] = Field(
        description="Steps to reproduce the issue (for technical problems)",
        default=None
    )
    estimated_resolution_time: str = Field(
        description="Estimated time to resolve this issue"
    )
    urgency_keywords: List[str] = Field(
        description="Keywords that indicate urgency or importance",
        default=[]
    )

# Create the support ticket agent
support_ticket_agent = Agent(
    name="Support Ticket Creator",
    instructions="""
    You are a support ticket creation assistant that converts customer complaints 
    and issues into well-structured support tickets.
    
    Based on customer descriptions, create structured support tickets with:
    - Clear, concise titles
    - Detailed problem descriptions
    - Appropriate priority levels (low/medium/high/critical)
    - Correct categories (technical/billing/account/product/general)
    - Customer names if mentioned
    - Steps to reproduce for technical issues
    - Realistic resolution time estimates
    - Keywords that indicate urgency
    
    Priority Guidelines:
    - CRITICAL: System down, security issues, data loss
    - HIGH: Core features not working, urgent business impact
    - MEDIUM: Important features affected, moderate business impact
    - LOW: Minor issues, feature requests, general questions
    
    Category Guidelines:
    - TECHNICAL: App crashes, login issues, performance problems
    - BILLING: Payment issues, subscription problems, invoice questions
    - ACCOUNT: Profile issues, access problems, account settings
    - PRODUCT: Feature requests, product feedback, functionality questions
    - GENERAL: General inquiries, documentation, training
    
    Resolution Time Guidelines:
    - Critical: "1-4 hours"
    - High: "4-24 hours"  
    - Medium: "1-3 business days"
    - Low: "3-7 business days"
    
    Always return a valid JSON object matching the SupportTicket schema.
    """,
    output_type=SupportTicket
)

def demonstrate_support_tickets():
    """Demonstrate the support ticket agent with various examples"""
    print("🎯 OpenAI Agents SDK - Tutorial 2: Support Ticket Agent")
    print("=" * 60)
    print()
    
    # Test cases with different types of issues
    test_cases = [
        {
            "description": "Billing Issue",
            "complaint": "Hi, I'm John Smith and I noticed my credit card was charged twice for last month's premium subscription. I only signed up once but see two $29.99 charges on my statement from January 15th. This needs to be resolved quickly as it's affecting my budget."
        },
        {
            "description": "Technical Issue", 
            "complaint": "The mobile app keeps crashing whenever I try to upload photos. I'm using an iPhone 14 with iOS 17. Steps: 1) Open app 2) Go to gallery 3) Select photo 4) Tap upload 5) App crashes immediately. This is blocking my work completely!"
        },
        {
            "description": "Account Issue",
            "complaint": "I can't log into my account. My username is mary.johnson@email.com and I keep getting 'invalid credentials' even though I'm sure my password is correct. I've tried resetting it but never received the email. I need access urgently for a client meeting tomorrow."
        },
        {
            "description": "Low Priority Request",
            "complaint": "Hey there! I was wondering if you could add a dark mode feature to the app? It would be really nice to have, especially for us night owls. Not urgent at all, just a suggestion. Thanks!"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"=== Test Case {i}: {test_case['description']} ===")
        print(f"Customer Complaint:")
        print(f'"{test_case["complaint"]}"')
        print()
        
        try:
            # Generate structured support ticket
            result = Runner.run_sync(support_ticket_agent, test_case["complaint"])
            ticket = result.final_output
            
            print("Generated Support Ticket:")
            print(f"📋 Title: {ticket.title}")
            print(f"🏷️  Category: {ticket.category.value.title()}")
            print(f"⚡ Priority: {ticket.priority.value.title()}")
            if ticket.customer_name:
                print(f"👤 Customer: {ticket.customer_name}")
            print(f"📝 Description: {ticket.description}")
            if ticket.steps_to_reproduce:
                print(f"🔄 Steps to Reproduce:")
                for step in ticket.steps_to_reproduce:
                    print(f"   • {step}")
            print(f"⏱️  Estimated Resolution: {ticket.estimated_resolution_time}")
            if ticket.urgency_keywords:
                print(f"🚨 Urgency Keywords: {', '.join(ticket.urgency_keywords)}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()
        print("-" * 60)
        print()

def interactive_mode():
    """Interactive mode for creating support tickets"""
    print("=== Interactive Support Ticket Creation ===")
    print("Describe a customer issue and I'll create a structured support ticket.")
    print("Type 'quit' to exit.")
    print()
    
    while True:
        complaint = input("Customer Complaint: ").strip()
        
        if complaint.lower() in ['quit', 'exit', 'bye']:
            print("Goodbye!")
            break
        
        if not complaint:
            continue
        
        try:
            print("\nGenerating support ticket...")
            result = Runner.run_sync(support_ticket_agent, complaint)
            ticket = result.final_output
            
            print("\n" + "="*50)
            print("📋 SUPPORT TICKET CREATED")
            print("="*50)
            print(f"Title: {ticket.title}")
            print(f"Category: {ticket.category.value.title()}")
            print(f"Priority: {ticket.priority.value.title()}")
            if ticket.customer_name:
                print(f"Customer: {ticket.customer_name}")
            print(f"Description: {ticket.description}")
            if ticket.steps_to_reproduce:
                print("Steps to Reproduce:")
                for i, step in enumerate(ticket.steps_to_reproduce, 1):
                    print(f"  {i}. {step}")
            print(f"Estimated Resolution: {ticket.estimated_resolution_time}")
            if ticket.urgency_keywords:
                print(f"Urgency Keywords: {', '.join(ticket.urgency_keywords)}")
            print("="*50)
            print()
            
        except Exception as e:
            print(f"❌ Error: {e}")
            print()

def main():
    """Main function"""
    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not found in environment variables")
        print("Please create a .env file with your OpenAI API key")
        return
    
    try:
        # Run demonstrations
        demonstrate_support_tickets()
        
        # Interactive mode
        interactive_mode()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
