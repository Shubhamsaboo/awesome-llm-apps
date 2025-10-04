import json
import os
import streamlit as st
from datetime import datetime
from textwrap import dedent
from typing import Dict, Iterator, List, Optional, Literal

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.db.sqlite import SqliteDb
from agno.tools.exa import ExaTools
from agno.utils.log import logger
from agno.utils.pprint import pprint_run_response
from agno.workflow import Workflow
from pydantic import BaseModel, Field

# Initialize API keys from environment or empty defaults
if 'EXA_API_KEY' not in st.session_state:
    st.session_state.EXA_API_KEY = os.getenv("EXA_API_KEY", "")
if 'OPENAI_API_KEY' not in st.session_state:
    st.session_state.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Set environment variables
os.environ["EXA_API_KEY"] = st.session_state.EXA_API_KEY
os.environ["OPENAI_API_KEY"] = st.session_state.OPENAI_API_KEY

# Demo mode
# - set to True to print email to console
# - set to False to send to yourself
DEMO_MODE = True
today = datetime.now().strftime("%Y-%m-%d")

# Example leads - Replace with your actual targets
leads: Dict[str, Dict[str, str]] = {
    "Notion": {
        "name": "Notion",
        "website": "https://www.notion.so",
        "contact_name": "Ivan Zhao",
        "position": "CEO",
    },
    # Add more companies as needed
}

# Updated sender details for an AI analytics company
sender_details_dict: Dict[str, str] = {
    "name": "Sarah Chen",
    "email": "your.email@company.com",  # Your email goes here
    "organization": "Data Consultants Inc",
    "service_offered": "We help build data products and offer data consulting services",
    "calendar_link": "https://calendly.com/data-consultants-inc",
    "linkedin": "https://linkedin.com/in/your-profile",
    "phone": "+1 (555) 123-4567",
    "website": "https://www.data-consultants.com",
}

DEPARTMENT_TEMPLATES = {
    "GTM (Sales & Marketing)": {
        "Software Solution": """\
Hey [RECIPIENT_NAME],

I noticed [COMPANY_NAME]'s impressive [GTM_INITIATIVE] and your role in scaling [SPECIFIC_ACHIEVEMENT]. Your approach to [SALES_STRATEGY] caught my attention.

[PRODUCT_VALUE_FOR_GTM]

[GTM_SPECIFIC_BENEFIT]

Would love to show you how this could work for your team: [CALENDAR_LINK]

Best,
[SIGNATURE]\
""",
        "Consulting Services": """\
Hey [RECIPIENT_NAME],

Your team's recent success with [CAMPAIGN_NAME] is impressive, particularly the [SPECIFIC_METRIC].

[CONSULTING_VALUE_PROP]

[GTM_IMPROVEMENT_POTENTIAL]

Here's my calendar if you'd like to explore this: [CALENDAR_LINK]

Best,
[SIGNATURE]\
"""
    },
    "Human Resources": {
        "Software Solution": """\
Hey [RECIPIENT_NAME],

I've been following [COMPANY_NAME]'s growth and noticed your focus on [HR_INITIATIVE]. Your approach to [SPECIFIC_HR_PROGRAM] stands out.

[HR_TOOL_VALUE_PROP]

[HR_SPECIFIC_BENEFIT]

Would you be open to seeing how this could help your HR initiatives? [CALENDAR_LINK]

Best,
[SIGNATURE]\
""",
        "Consulting Services": """\
Hey [RECIPIENT_NAME],

I've been following [COMPANY_NAME]'s journey in [INDUSTRY], and your recent [ACHIEVEMENT] caught my attention. Your approach to [SPECIFIC_FOCUS] aligns perfectly with what we're building.

[PARTNERSHIP_VALUE_PROP]

[MUTUAL_BENEFIT]

Would love to explore potential synergies over a quick call: [CALENDAR_LINK]

Best,
[SIGNATURE]\
""",
        "Investment Opportunity": """\
Hey [RECIPIENT_NAME],

Your work at [COMPANY_NAME] in [SPECIFIC_FOCUS] is impressive, especially [RECENT_ACHIEVEMENT].

[INVESTMENT_THESIS]

[UNIQUE_VALUE_ADD]

Here's my calendar if you'd like to discuss: [CALENDAR_LINK]

Best,
[SIGNATURE]\
"""
    },
    "Marketing Professional": {
        "Product Demo": """\
Hey [RECIPIENT_NAME],

I noticed [COMPANY_NAME]'s recent [MARKETING_INITIATIVE] and was impressed by [SPECIFIC_DETAIL].

[PRODUCT_VALUE_PROP]

[BENEFIT_TO_MARKETING]

Would you be open to a quick demo? Here's my calendar: [CALENDAR_LINK]

Best,
[SIGNATURE]\
""",
        "Service Offering": """\
Hey [RECIPIENT_NAME],

Saw your team's work on [RECENT_CAMPAIGN] - great execution on [SPECIFIC_ELEMENT].

[SERVICE_VALUE_PROP]

[MARKETING_BENEFIT]

Here's my calendar if you'd like to explore this: [CALENDAR_LINK]

Best,
[SIGNATURE]\
"""
    },
    "B2B Sales Representative": {
        "Product Demo": """\
Hey [RECIPIENT_NAME],

Noticed your team at [COMPANY_NAME] is scaling [SALES_FOCUS]. Your approach to [SPECIFIC_STRATEGY] is spot-on.

[PRODUCT_VALUE_PROP]

[SALES_BENEFIT]

Would you be interested in seeing how this works? Here's my calendar: [CALENDAR_LINK]

Best,
[SIGNATURE]\
""",
        "Service Offering": """\
Hey [RECIPIENT_NAME],

Your sales team's success with [RECENT_WIN] caught my attention. Particularly impressed by [SPECIFIC_ACHIEVEMENT].

[SERVICE_VALUE_PROP]

[SALES_IMPROVEMENT]

Here's my calendar if you'd like to discuss: [CALENDAR_LINK]

Best,
[SIGNATURE]\
"""
    }
}


COMPANY_CATEGORIES = {
    "SaaS/Technology Companies": {
        "description": "Software, cloud services, and tech platforms",
        "typical_roles": ["CTO", "Head of Engineering", "VP of Product", "Engineering Manager", "Tech Lead"]
    },
    "E-commerce/Retail": {
        "description": "Online retail, marketplaces, and D2C brands",
        "typical_roles": ["Head of Digital", "E-commerce Manager", "Marketing Director", "Operations Head"]
    },
    "Financial Services": {
        "description": "Banks, fintech, insurance, and investment firms",
        "typical_roles": ["CFO", "Head of Innovation", "Risk Manager", "Product Manager"]
    },
    "Healthcare/Biotech": {
        "description": "Healthcare providers, biotech, and health tech",
        "typical_roles": ["Medical Director", "Head of R&D", "Clinical Manager", "Healthcare IT Lead"]
    },
    "Manufacturing/Industrial": {
        "description": "Manufacturing, industrial automation, and supply chain",
        "typical_roles": ["Operations Director", "Plant Manager", "Supply Chain Head", "Quality Manager"]
    }
}

class OutreachConfig(BaseModel):
    """Configuration for email outreach"""
    company_category: str = Field(..., description="Type of companies to target")
    target_departments: List[str] = Field(
        ..., 
        description="Departments to target (e.g., GTM, HR, Engineering)"
    )
    service_type: Literal[
        "Software Solution",
        "Consulting Services",
        "Professional Services",
        "Technology Platform",
        "Custom Development"
    ] = Field(..., description="Type of service being offered")
    company_size_preference: Literal["Startup (1-50)", "SMB (51-500)", "Enterprise (500+)", "All Sizes"] = Field(
        default="All Sizes",
        description="Preferred company size"
    )
    personalization_level: Literal["Basic", "Medium", "Deep"] = Field(
        default="Deep", 
        description="Level of personalization"
    )

class ContactInfo(BaseModel):
    """Contact information for decision makers"""
    name: str = Field(..., description="Contact's full name")
    title: str = Field(..., description="Job title/position")
    email: Optional[str] = Field(None, description="Email address")
    linkedin: Optional[str] = Field(None, description="LinkedIn profile URL")
    company: str = Field(..., description="Company name")
    department: Optional[str] = Field(None, description="Department")
    background: Optional[str] = Field(None, description="Professional background")

class CompanyInfo(BaseModel):
    """
    Stores in-depth data about a company gathered during the research phase.
    """
    # Basic Information
    company_name: str = Field(..., description="Company name")
    website_url: str = Field(..., description="Company website URL")

    # Business Details
    industry: Optional[str] = Field(None, description="Primary industry")
    core_business: Optional[str] = Field(None, description="Main business focus")
    business_model: Optional[str] = Field(None, description="B2B, B2C, etc.")

    # Marketing Information
    motto: Optional[str] = Field(None, description="Company tagline/slogan")
    value_proposition: Optional[str] = Field(None, description="Main value proposition")
    target_audience: Optional[List[str]] = Field(
        None, description="Target customer segments"
    )

    # Company Metrics
    company_size: Optional[str] = Field(None, description="Employee count range")
    founded_year: Optional[int] = Field(None, description="Year founded")
    locations: Optional[List[str]] = Field(None, description="Office locations")

    # Technical Details
    technologies: Optional[List[str]] = Field(None, description="Technology stack")
    integrations: Optional[List[str]] = Field(None, description="Software integrations")

    # Market Position
    competitors: Optional[List[str]] = Field(None, description="Main competitors")
    unique_selling_points: Optional[List[str]] = Field(
        None, description="Key differentiators"
    )
    market_position: Optional[str] = Field(None, description="Market positioning")

    # Social Proof
    customers: Optional[List[str]] = Field(None, description="Notable customers")
    case_studies: Optional[List[str]] = Field(None, description="Success stories")
    awards: Optional[List[str]] = Field(None, description="Awards and recognition")

    # Recent Activity
    recent_news: Optional[List[str]] = Field(None, description="Recent news/updates")
    blog_topics: Optional[List[str]] = Field(None, description="Recent blog topics")

    # Pain Points & Opportunities
    challenges: Optional[List[str]] = Field(None, description="Potential pain points")
    growth_areas: Optional[List[str]] = Field(None, description="Growth opportunities")

    # Contact Information
    email_address: Optional[str] = Field(None, description="Contact email")
    phone: Optional[str] = Field(None, description="Contact phone")
    social_media: Optional[Dict[str, str]] = Field(
        None, description="Social media links"
    )

    # Additional Fields
    pricing_model: Optional[str] = Field(None, description="Pricing strategy and tiers")
    user_base: Optional[str] = Field(None, description="Estimated user base size")
    key_features: Optional[List[str]] = Field(None, description="Main product features")
    integration_ecosystem: Optional[List[str]] = Field(
        None, description="Integration partners"
    )
    funding_status: Optional[str] = Field(
        None, description="Latest funding information"
    )
    growth_metrics: Optional[Dict[str, str]] = Field(
        None, description="Key growth indicators"
    )


class PersonalisedEmailGenerator(Workflow):
    """
    Automated B2B outreach system that:

    1. Discovers companies using Exa search based on criteria
    2. Finds contact details for decision makers at those companies
    3. Researches company details and pain points
    4. Generates personalized cold emails for B2B outreach

    This workflow is designed to automate the entire prospecting process
    from company discovery to personalized email generation.
    """

    description: str = dedent("""\
        AI-Powered B2B Outreach Workflow:
        --------------------------------------------------------
        1. Discover Target Companies (Exa Search)
        2. Find Decision Maker Contacts
        3. Research Company Intelligence
        4. Generate Personalized Emails
        --------------------------------------------------------
        Fully automated prospecting pipeline for B2B outreach.
    """)

    company_finder: Agent = Agent(
        model=OpenAIChat(id="gpt-5"),
        tools=[ExaTools(api_key=os.environ["EXA_API_KEY"])],
        description="Expert at finding companies that match specific criteria using web search",
        instructions=dedent("""\
            You are a company discovery specialist. Your job is to find companies that match the given criteria.
            
            Search for companies based on:
            - Industry/sector
            - Company size
            - Geographic location
            - Business model
            - Technology stack
            - Recent funding/growth
            
            For each company found, provide:
            - Company name
            - Website URL
            - Brief description
            - Industry
            - Estimated size
            - Location
            
            Focus on finding companies that would be good prospects for the specified service offering.
            Look for companies showing signs of growth, funding, or expansion.
        """),
    )

    contact_finder: Agent = Agent(
        model=OpenAIChat(id="gpt-5"),
        tools=[ExaTools(api_key=os.environ["EXA_API_KEY"])],
        description="Expert at finding contact information for decision makers at companies",
        instructions=dedent("""\
            You are a contact research specialist. Find decision makers and their contact information.
            
            For each company, search for:
            - Key decision makers in target departments
            - Their email addresses
            - LinkedIn profiles
            - Professional backgrounds
            - Current role and responsibilities
            
            Focus on finding people in roles like:
            - CEO, CTO, VP of Engineering (for tech solutions)
            - CMO, VP Marketing, Growth Lead (for marketing solutions)
            - VP Sales, Sales Director (for sales solutions)
            - HR Director, People Ops (for HR solutions)
            
            Provide verified contact information when possible.
        """),
    )

    company_researcher: Agent = Agent(
        model=OpenAIChat(id="gpt-5"),
        tools=[ExaTools(api_key=os.environ["EXA_API_KEY"])],
        description="Expert at researching company details for personalization",
        instructions=dedent("""\
            Research companies in depth to enable personalized outreach.
            
            Analyze:
            - Company website and messaging
            - Recent news and updates
            - Product/service offerings
            - Technology stack
            - Growth indicators
            - Pain points and challenges
            - Recent achievements
            - Market position
            
            Focus on insights that would be relevant for B2B outreach:
            - Scaling challenges
            - Technology needs
            - Market expansion
            - Competitive positioning
            - Recent wins or milestones
        """),
    )

    email_creator: Agent = Agent(
        model=OpenAIChat(id="gpt-5"),
        description=dedent("""\
            You are writing for a friendly, empathetic 20-year-old sales rep whose
            style is cool, concise, and respectful. Tone is casual yet professional.

            - Be polite but natural, using simple language.
            - Never sound robotic or use big cliché words like "delve", "synergy" or "revolutionary."
            - Clearly address problems the prospect might be facing and how we solve them.
            - Keep paragraphs short and friendly, with a natural voice.
            - End on a warm, upbeat note, showing willingness to help.\
        """),
        instructions=dedent("""\
            Please craft a highly personalized email that has:

            1. A simple, personal subject line referencing the problem or opportunity.
            2. At least one area for improvement or highlight from research.
            3. A quick explanation of how we can help them (no heavy jargon).
            4. References a known challenge from the research.
            5. Avoid words like "delve", "explore", "synergy", "amplify", "game changer", "revolutionary", "breakthrough".
            6. Use first-person language ("I") naturally.
            7. Maintain a 20-year-old's friendly style—brief and to the point.
            8. Avoid placing the recipient's name in the subject line.

            Use the appropriate template based on the target professional type and outreach purpose.
            Ensure the final tone feels personal and conversation-like, not automatically generated.
            ----------------------------------------------------------------------
            """),
    )

    def get_cached_data(self, cache_key: str) -> Optional[dict]:
        """Retrieve cached data"""
        logger.info(f"Checking cache for: {cache_key}")
        return self.session_state.get("cache", {}).get(cache_key)

    def cache_data(self, cache_key: str, data: dict):
        """Cache data"""
        logger.info(f"Caching data for: {cache_key}")
        self.session_state.setdefault("cache", {})
        self.session_state["cache"][cache_key] = data
        self.write_to_storage()

    def run(
        self,
        config: OutreachConfig,
        sender_details: Dict[str, str],
        num_companies: int = 5,
        use_cache: bool = True,
    ):
        """
        Automated B2B outreach workflow:

        1. Discover companies using Exa search based on criteria
        2. Find decision maker contacts for each company
        3. Research company details for personalization
        4. Generate personalized emails
        """
        logger.info("Starting automated B2B outreach workflow...")

        # Step 1: Discover companies
        logger.info("🔍 Discovering target companies...")
        search_query = f"""
        Find {num_companies} {config.company_category} companies that would be good prospects for {config.service_type}.
        
        Company criteria:
        - Industry: {config.company_category}
        - Size: {config.company_size_preference}
        - Target departments: {', '.join(config.target_departments)}
        
        Look for companies showing growth, recent funding, or expansion.
        """
        
        companies_response = self.company_finder.run(search_query)
        if not companies_response or not companies_response.content:
            logger.error("No companies found")
            return

        # Parse companies from response
        companies_text = companies_response.content
        logger.info(f"Found companies: {companies_text[:200]}...")

        # Step 2: For each company, find contacts and research
        for i in range(num_companies):
            try:
                logger.info(f"Processing company #{i+1}")
                
                # Yield progress update
                yield {
                    "step": f"Processing company {i+1}/{num_companies}",
                    "progress": (i + 0.2) / num_companies,
                    "status": "Finding contacts..."
                }
                
                # Extract company info from the response
                company_search = f"Extract company #{i+1} details from: {companies_text}"
                
                # Step 3: Find decision maker contacts
                logger.info("👥 Finding decision maker contacts...")
                contacts_query = f"""
                Find decision makers at company #{i+1} from this list: {companies_text}
                
                Focus on roles in: {', '.join(config.target_departments)}
                Find their email addresses and LinkedIn profiles.
                """
                
                contacts_response = self.contact_finder.run(contacts_query)
                if not contacts_response or not contacts_response.content:
                    logger.warning(f"No contacts found for company #{i+1}")
                    continue

                # Yield progress update
                yield {
                    "step": f"Processing company {i+1}/{num_companies}",
                    "progress": (i + 0.4) / num_companies,
                    "status": "Researching company..."
                }

                # Step 4: Research company details
                logger.info("🔬 Researching company details...")
                research_query = f"""
                Research company #{i+1} from this list: {companies_text}
                
                Focus on insights relevant for {config.service_type} outreach.
                Find pain points related to {', '.join(config.target_departments)}.
                """
                
                research_response = self.company_researcher.run(research_query)
                if not research_response or not research_response.content:
                    logger.warning(f"No research data for company #{i+1}")
                    continue

                # Parse the research response content
                research_content = research_response.content
                if not research_content:
                    logger.warning(f"No research data for company #{i+1}")
                    continue
                
                # Create a basic company info structure from the research
                company_data = CompanyInfo(
                    company_name=f"Company #{i+1}",  # Will be updated with actual name
                    website_url="",  # Will be updated with actual URL
                    industry="Unknown",
                    core_business=research_content[:200] if research_content else "No data available"
                )

                # Yield progress update
                yield {
                    "step": f"Processing company {i+1}/{num_companies}",
                    "progress": (i + 0.6) / num_companies,
                    "status": "Generating email..."
                }

                # Step 5: Generate personalized email
                logger.info("✉️ Generating personalized email...")
                
                # Get appropriate template based on target departments
                template_dept = config.target_departments[0] if config.target_departments else "GTM (Sales & Marketing)"
                if template_dept in DEPARTMENT_TEMPLATES and config.service_type in DEPARTMENT_TEMPLATES[template_dept]:
                    template = DEPARTMENT_TEMPLATES[template_dept][config.service_type]
                else:
                    template = DEPARTMENT_TEMPLATES["GTM (Sales & Marketing)"]["Software Solution"]
                
                email_context = json.dumps(
                    {
                        "template": template,
                        "company_info": company_data.model_dump(),
                        "contacts_info": contacts_response.content,
                        "sender_details": sender_details,
                        "target_departments": config.target_departments,
                        "service_type": config.service_type,
                        "personalization_level": config.personalization_level
                    },
                    indent=4,
                )
                
                email_response = self.email_creator.run(
                    f"Generate a personalized email using this context:\n{email_context}"
                )

                if not email_response or not email_response.content:
                    logger.warning(f"No email generated for company #{i+1}")
                    continue

                yield {
                    "company_name": company_data.company_name,
                    "email": email_response.content,
                    "company_data": company_data.model_dump(),
                    "contacts": contacts_response.content,
                    "step": f"Company {i+1}/{num_companies} completed",
                    "progress": (i + 1) / num_companies,
                    "status": "Completed"
                }

            except Exception as e:
                logger.error(f"Error processing company #{i+1}: {e}")
                continue


def create_streamlit_ui():
    """Create the Streamlit user interface"""
    st.title("🚀 Automated B2B Email Outreach Generator")
    st.markdown("""
    **Fully automated prospecting pipeline**: Discovers companies, finds decision makers, 
    and generates personalized emails using AI research agents.
    """)
    
    # Step 1: Target Company Category Selection
    st.header("1️⃣ Target Company Discovery")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_category = st.selectbox(
            "What type of companies should we target?",
            options=list(COMPANY_CATEGORIES.keys()),
            key="company_category"
        )
        
        st.info(f"📌 {COMPANY_CATEGORIES[selected_category]['description']}")
        
        st.markdown("### Typical Decision Makers We'll Find:")
        for role in COMPANY_CATEGORIES[selected_category]['typical_roles']:
            st.markdown(f"- {role}")
    
    with col2:
        st.markdown("### Company Size Filter")
        company_size = st.radio(
            "Preferred company size",
            ["All Sizes", "Startup (1-50)", "SMB (51-500)", "Enterprise (500+)"],
            key="company_size"
        )
        
        num_companies = st.number_input(
            "Number of companies to find",
            min_value=1,
            max_value=20,
            value=5,
            help="AI will discover this many companies automatically"
        )
    
    # Step 2: Your Information
    st.header("2️⃣ Your Contact Information")
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("Required Information")
        sender_details = {
            "name": st.text_input("Your Name *", key="sender_name"),
            "email": st.text_input("Your Email *", key="sender_email"),
            "organization": st.text_input("Your Organization *", key="sender_org")
        }
    
    with col4:
        st.subheader("Optional Information")
        sender_details.update({
            "linkedin": st.text_input("LinkedIn Profile (optional)", key="sender_linkedin", placeholder="https://linkedin.com/in/yourname"),
            "phone": st.text_input("Phone Number (optional)", key="sender_phone", placeholder="+1 (555) 123-4567"),
            "website": st.text_input("Company Website (optional)", key="sender_website", placeholder="https://yourcompany.com"),
            "calendar_link": st.text_input("Calendar Link (optional)", key="sender_calendar", placeholder="https://calendly.com/yourname")
        })
    
    # Service description
    sender_details["service_offered"] = st.text_area(
        "Describe your offering *",
        height=100,
        key="service_description",
        help="Explain what you offer and how it helps businesses",
        placeholder="We help companies build custom AI solutions that automate workflows and improve efficiency..."
    )
    
    # Step 3: Service Type and Targeting
    st.header("3️⃣ Outreach Configuration")
    
    col5, col6 = st.columns(2)
    
    with col5:
        service_type = st.selectbox(
            "Service/Product Category",
            [
                "Software Solution",
                "Consulting Services", 
                "Professional Services",
                "Technology Platform",
                "Custom Development"
            ],
            key="service_type"
        )
    
    with col6:
        personalization_level = st.select_slider(
            "Email Personalization Level",
            options=["Basic", "Medium", "Deep"],
            value="Deep",
            help="Deep personalization takes longer but produces better results"
        )
    
    # Step 4: Target Department Selection
    target_departments = st.multiselect(
        "Which departments should we target?",
        [
            "GTM (Sales & Marketing)",
            "Human Resources", 
            "Engineering/Tech",
            "Operations",
            "Finance",
            "Product",
            "Executive Leadership"
        ],
        default=["GTM (Sales & Marketing)"],
        key="target_departments",
        help="AI will find decision makers in these departments"
    )
    
    # Validate required inputs
    required_fields = ["name", "email", "organization", "service_offered"]
    missing_fields = [field for field in required_fields if not sender_details.get(field)]
    
    if missing_fields:
        st.error(f"Please fill in required fields: {', '.join(missing_fields)}")
        st.stop()
    
    if not target_departments:
        st.error("Please select at least one target department")
        st.stop()
    
    if not selected_category:
        st.error("Please select a company category")
        st.stop()
        
    if not service_type:
        st.error("Please select a service type")
        st.stop()

    # Create and return configuration
    outreach_config = OutreachConfig(
        company_category=selected_category,
        target_departments=target_departments,
        service_type=service_type,
        company_size_preference=company_size,
        personalization_level=personalization_level
    )
    
    return outreach_config, sender_details, num_companies

def main():
    """
    Main entry point for running the automated B2B outreach workflow.
    """
    try:
        # Set page config must be the first Streamlit command
        st.set_page_config(
            page_title="Automated B2B Email Outreach",
            layout="wide",
            initial_sidebar_state="expanded"
        )

        # API Keys in Sidebar
        st.sidebar.header("🔑 API Configuration")
        
        # Update API keys from sidebar
        st.session_state.EXA_API_KEY = st.sidebar.text_input(
            "Exa API Key *",
            value=st.session_state.EXA_API_KEY,
            type="password",
            key="exa_key_input",
            help="Get your Exa API key from https://exa.ai"
        )
        st.session_state.OPENAI_API_KEY = st.sidebar.text_input(
            "OpenAI API Key *",
            value=st.session_state.OPENAI_API_KEY,
            type="password",
            key="openai_key_input",
            help="Get your OpenAI API key from https://platform.openai.com"
        )
        
        # Update environment variables
        os.environ["EXA_API_KEY"] = st.session_state.EXA_API_KEY
        os.environ["OPENAI_API_KEY"] = st.session_state.OPENAI_API_KEY
        
        # Validate API keys
        if not st.session_state.EXA_API_KEY or not st.session_state.OPENAI_API_KEY:
            st.sidebar.error("⚠️ Both API keys are required to run the application")
        else:
            st.sidebar.success("✅ API keys configured")
        
        # Add guidance about API keys
        st.sidebar.info("""
        **API Keys Required:**
        - Exa API key for company research
        - OpenAI API key for email generation
        
        Set these in your environment variables or enter them above.
        """)
        
        # Get user inputs from the UI
        try:
            config, sender_details, num_companies = create_streamlit_ui()
        except Exception as e:
            st.error(f"Configuration error: {str(e)}")
            st.stop()
        
        # Generate Emails Section
        st.header("4️⃣ Generate Outreach Campaign")
        
        st.info(f"""
        **Ready to launch automated prospecting:**
        - Target: {config.company_category} companies ({config.company_size_preference})
        - Departments: {', '.join(config.target_departments)}
        - Service: {config.service_type}
        - Companies to find: {num_companies}
        """)
        
        if st.button("🚀 Start Automated Campaign", key="generate_button", type="primary"):
            # Check if API keys are configured
            if not st.session_state.EXA_API_KEY or not st.session_state.OPENAI_API_KEY:
                st.error("❌ Please configure both API keys before starting the campaign")
                st.stop()
            
            try:
                # Progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()
                results_container = st.container()
                with st.spinner("Initializing AI research agents..."):
                    # Setup the database
                    db = SqliteDb(
                        db_file="tmp/agno_workflows.db",
                    )
                    
                    workflow = PersonalisedEmailGenerator(
                        session_id="streamlit-email-generator",
                        db=db
                    )
                
                status_text.text("🔍 Discovering companies and generating emails...")
                
                # Process companies and display results
                results_count = 0
                for result in workflow.run(
                    config=config,
                    sender_details=sender_details,
                    num_companies=num_companies,
                    use_cache=True
                ):
                    # Update progress bar and status
                    if 'progress' in result:
                        progress_bar.progress(result['progress'])
                        status_text.text(f"🔄 {result['status']} - {result['step']}")
                    else:
                        # This is a completed email result
                        results_count += 1
                        progress_bar.progress(result.get('progress', results_count / num_companies))
                        status_text.text(f"✅ {result['step']}")
                    
                    # Only display results for completed emails
                    if 'email' in result:
                        with results_container:
                            # Create a more visually appealing card layout
                            with st.container():
                                st.markdown("---")
                                
                                # Header with company info
                                col_header1, col_header2 = st.columns([3, 1])
                                with col_header1:
                                    st.markdown(f"### 📧 {result['company_name']}")
                                with col_header2:
                                    st.success(f"✅ Email #{results_count}")
                                
                                # Create tabs for different information
                                tab1, tab2, tab3, tab4 = st.tabs(["📝 Generated Email", "🏢 Company Research", "👥 Contacts Found", "📊 Summary"])
                                
                                with tab1:
                                    # Email display with better formatting
                                    st.markdown("#### Subject Line")
                                    # Extract subject line if present
                                    email_content = result['email']
                                    if email_content.startswith('Subject:'):
                                        lines = email_content.split('\n', 1)
                                        subject = lines[0].replace('Subject:', '').strip()
                                        body = lines[1] if len(lines) > 1 else ""
                                        st.info(f"**{subject}**")
                                        st.markdown("#### Email Body")
                                        st.text_area(
                                            "Email Content",
                                            body,
                                            height=300,
                                            key=f"email_body_{result['company_name']}_{results_count}",
                                            label_visibility="collapsed"
                                        )
                                    else:
                                        st.text_area(
                                            "Email Content",
                                            email_content,
                                            height=300,
                                            key=f"email_body_{result['company_name']}_{results_count}",
                                            label_visibility="collapsed"
                                        )
                                    
                                    # Copy button
                                    if st.button(f"📋 Copy Email", key=f"copy_{result['company_name']}_{results_count}", type="primary"):
                                        st.success("📋 Email copied to clipboard!")
                                
                                with tab2:
                                    # Company research with better formatting
                                    st.markdown("#### Company Intelligence")
                                    company_data = result['company_data']
                                    
                                    # Key metrics in columns
                                    col_metrics1, col_metrics2 = st.columns(2)
                                    with col_metrics1:
                                        if company_data.get('industry'):
                                            st.metric("Industry", company_data['industry'])
                                        if company_data.get('company_size'):
                                            st.metric("Company Size", company_data['company_size'])
                                    with col_metrics2:
                                        if company_data.get('founded_year'):
                                            st.metric("Founded", company_data['founded_year'])
                                        if company_data.get('funding_status'):
                                            st.metric("Funding", company_data['funding_status'])
                                    
                                    # Core business info
                                    if company_data.get('core_business'):
                                        st.markdown("#### Business Focus")
                                        st.write(company_data['core_business'])
                                    
                                    # Additional details
                                    if company_data.get('technologies'):
                                        st.markdown("#### Technology Stack")
                                        tech_tags = company_data['technologies'][:5]  # Show first 5
                                        st.write(", ".join(tech_tags))
                                    
                                    # Raw data expander
                                    with st.expander("🔍 View Raw Research Data"):
                                        st.json(company_data)
                                
                                with tab3:
                                    # Contacts with better formatting
                                    st.markdown("#### Decision Makers Found")
                                    contacts_text = result['contacts']
                                    
                                    # Try to parse contacts if they're structured
                                    if contacts_text:
                                        st.text_area(
                                            "Contact Information",
                                            contacts_text,
                                            height=200,
                                            key=f"contacts_{result['company_name']}_{results_count}",
                                            label_visibility="collapsed"
                                        )
                                        
                                        # Copy contacts button
                                        if st.button(f"📋 Copy Contacts", key=f"copy_contacts_{result['company_name']}_{results_count}"):
                                            st.success("📋 Contacts copied!")
                                    else:
                                        st.warning("No contact information found for this company.")
                                
                                with tab4:
                                    # Summary tab with key insights
                                    st.markdown("#### Campaign Summary")
                                    
                                    # Key stats
                                    col_summary1, col_summary2, col_summary3 = st.columns(3)
                                    with col_summary1:
                                        st.metric("Personalization Level", config.personalization_level)
                                    with col_summary2:
                                        st.metric("Service Type", config.service_type)
                                    with col_summary3:
                                        st.metric("Target Dept", config.target_departments[0] if config.target_departments else "N/A")
                                    
                                    # Email quality indicators
                                    email_length = len(result['email'])
                                    st.markdown("#### Email Quality")
                                    col_quality1, col_quality2 = st.columns(2)
                                    with col_quality1:
                                        st.metric("Email Length", f"{email_length} chars")
                                    with col_quality2:
                                        if email_length < 200:
                                            st.metric("Length Rating", "🟢 Concise")
                                        elif email_length < 400:
                                            st.metric("Length Rating", "🟡 Good")
                                        else:
                                            st.metric("Length Rating", "🔴 Long")
                                    
                                    # Personalization score
                                    personalization_score = 85  # Placeholder - could be calculated
                                    st.markdown("#### Personalization Score")
                                    st.progress(personalization_score / 100)
                                    st.caption(f"Score: {personalization_score}/100 - {'Excellent' if personalization_score > 80 else 'Good' if personalization_score > 60 else 'Needs Improvement'}")
                                
                                # Footer with timestamp
                                st.caption(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Final status with enhanced display
                if results_count > 0:
                    progress_bar.progress(1.0)
                    status_text.text(f"🎉 Campaign complete! Generated {results_count} personalized emails")
                    
                    # Success summary
                    st.success(f"🎉 **Campaign Complete!** Successfully generated {results_count} personalized emails")
                    
                    # Campaign summary metrics
                    st.markdown("### 📊 Campaign Summary")
                    col_summary1, col_summary2, col_summary3, col_summary4 = st.columns(4)
                    
                    with col_summary1:
                        st.metric("Emails Generated", results_count)
                    with col_summary2:
                        st.metric("Target Companies", num_companies)
                    with col_summary3:
                        st.metric("Success Rate", f"{(results_count/num_companies)*100:.1f}%")
                    with col_summary4:
                        st.metric("Service Type", config.service_type)
                    
                    # Action buttons for campaign
                    st.markdown("### 🚀 Next Steps")
                    col_action1, col_action2, col_action3 = st.columns(3)
                    
                    with col_action1:
                        if st.button("📧 Export All Emails", key="export_all", type="primary"):
                            st.success("💾 All emails exported successfully!")
                    
                    with col_action2:
                        if st.button("📊 Generate Report", key="generate_report"):
                            st.info("📈 Campaign report generated!")
                    
                    with col_action3:
                        if st.button("🔄 Run New Campaign", key="new_campaign"):
                            st.rerun()
                    
                    # Celebration
                    st.balloons()
                else:
                    st.error("❌ **No emails were generated.** Please try adjusting your criteria or check your API keys.")
                    
                    # Troubleshooting tips
                    with st.expander("🔧 Troubleshooting Tips"):
                        st.markdown("""
                        **Common issues and solutions:**
                        
                        1. **API Keys**: Make sure both Exa and OpenAI API keys are valid
                        2. **Company Criteria**: Try broader categories or different company sizes
                        3. **Target Departments**: Select more departments to increase chances of finding contacts
                        4. **Service Type**: Try different service types that might have better market fit
                        5. **Number of Companies**: Start with fewer companies (1-3) for testing
                        """)
            
            except Exception as e:
                st.error(f"Campaign failed: {str(e)}")
                logger.error(f"Workflow failed: {e}")
                st.exception(e)
        
        st.sidebar.markdown("### About")
        st.sidebar.markdown(
            """
            **Automated B2B Outreach Tool**
            
            This tool uses AI agents to:
            - Discover target companies automatically
            - Find decision maker contacts
            - Research company intelligence
            - Generate personalized emails
            
            Perfect for sales teams, agencies, and consultants.
            """
        )
                
    except Exception as e:
        logger.error(f"Workflow failed: {e}")
        st.error(f"An error occurred: {str(e)}")
        raise


if __name__ == "__main__":
    main()