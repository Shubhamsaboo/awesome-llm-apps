from typing import List, Literal
from agency_swarm import Agent, Agency, set_openai_key, BaseTool
from pydantic import Field
import streamlit as st
from instructor import OpenAISchema
import asyncio

# New Tools
class StartupAnalysis(OpenAISchema):
    """Schema for startup analysis results"""
    market_potential: Literal["high", "medium", "low"]
    technical_complexity: Literal["high", "medium", "low"]
    resource_requirements: Literal["high", "medium", "low"]
    
class AnalyzeStartupTool(BaseTool):
    """Tool to analyze startup ideas"""
    startup_idea: str = Field(..., description="The startup idea to analyze")
    target_market: str = Field(..., description="Target market description")
    
    def run(self):
        # Tool implementation
        analysis = StartupAnalysis(
            market_potential="high",
            technical_complexity="medium",
            resource_requirements="low"
        )
        return analysis.dict()

class MakeStrategicDecision(BaseTool):
    """Tool for CEO to make and track strategic decisions"""
    decision: str = Field(..., description="The strategic decision to be recorded")
    decision_type: Literal["product", "technical", "marketing", "financial"] = Field(..., description="Type of decision")
    
    def run(self):
        analysis = self._shared_state.get("startup_analysis", None)
        if analysis is None:
            raise ValueError("Please analyze the startup idea first using QueryStartupIdea tool.")
        
        return f"Decision recorded: {self.decision} (Type: {self.decision_type}) based on analysis"

class QueryTechnicalRequirements(BaseTool):
    """Tool to analyze technical requirements"""
    technology_stack: str = Field(..., description="Technology stack to analyze")
    
    def run(self):
        if self._shared_state.get("tech_analysis", None) is not None:
            raise ValueError("Technical analysis already exists. Please proceed with technical evaluation.")
        
        tech_analysis = {
            "stack": self.technology_stack,
            "feasibility": "high/medium/low",
            "implementation_time": "estimate in months",
            "potential_challenges": ["challenge1", "challenge2"]
        }
        
        self._shared_state.set("tech_analysis", tech_analysis)
        return "Technical requirements analyzed. Please proceed with technical evaluation."

class EvaluateTechnicalFeasibility(BaseTool):
    """Tool for CTO to evaluate technical feasibility"""
    evaluation: str = Field(..., description="Technical evaluation details")
    feasibility_score: Literal["high", "medium", "low"] = Field(..., description="Feasibility rating")
    
    def run(self):
        tech_analysis = self._shared_state.get("tech_analysis", None)
        if tech_analysis is None:
            raise ValueError("Please analyze technical requirements first using QueryTechnicalRequirements tool.")
        
        return f"Technical evaluation completed: {self.evaluation} (Feasibility: {self.feasibility_score})"

# Set API key directly


# Simplified API headers
api_headers = {
    "Authorization": f"Bearer {openai_api_key}"
}

# Define individual agents
ceo = Agent(
    name="CEO",
    description="Strategic leader and final decision maker for the startup",
    instructions="""
    Analyze startup ideas and make strategic decisions.
    Use the AnalyzeStartupTool to evaluate new ideas.
    Coordinate with team members using the built-in SendMessage tool.
    """,
    tools=[AnalyzeStartupTool],
    temperature=0.7
)

cto = Agent(
    name="CTO",
    description="Technical leader responsible for architecture and tech decisions",
    instructions="Analyze technical requirements and evaluate feasibility. Always query requirements before evaluation.",
    tools=[QueryTechnicalRequirements, EvaluateTechnicalFeasibility],
    temperature=0.5,
    max_prompt_tokens=25000,
    api_headers=api_headers
)

product_manager = Agent(
    name="Product_Manager",
    description="Product strategy and roadmap owner",
    instructions="Define product strategy, create roadmap, and coordinate between technical and marketing teams.",
    tools=[],  # No specific tools needed for initial version
    temperature=0.4,
    max_prompt_tokens=25000,
    api_headers=api_headers
)

developer = Agent(
    name="Developer",
    description="Technical implementation specialist",
    instructions="You are a full stack tech expert and developer. Implement technical solutions and provide feasibility feedback.",
    tools=[],  # No specific tools needed for initial version
    temperature=0.3,
    max_prompt_tokens=25000,
    api_headers=api_headers
)

marketing_manager = Agent(
    name="Marketing_Manager",
    description="Marketing strategy and growth leader",
    instructions="Develop marketing strategies, analyze target audience, and coordinate with Product Manager.",
    tools=[],  # No specific tools needed for initial version
    temperature=0.6,
    max_prompt_tokens=25000,
    api_headers=api_headers
)

# IN Agency Swarm, communication flows are uniform, not sequential or hierarchical.
agency = Agency(
    [
        ceo, cto, product_manager, developer, marketing_manager,
        [ceo, cto],
        [ceo, product_manager],
        [ceo, developer],
        [ceo, marketing_manager],
        [cto, developer],
        [product_manager, developer],
        [product_manager, marketing_manager]
    ],
    async_mode='threading',  # Keep this for backward compatibility
    shared_files='shared_files'
)

# Streamlit Interface
def init_session_state():
    """Initialize Streamlit session state variables."""
    if 'messages' not in st.session_state:
        st.session_state.messages = []

def main():
    """Main Streamlit application."""
    st.set_page_config(page_title="AI Startup Organization Assistant", layout="wide")
    init_session_state()
    
    st.title("🚀 AI Startup Organization Assistant")

    with st.sidebar:
        st.header("🔑 API Configuration")
        openai_api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            help="Enter your OpenAI API key to continue"
        )

        if not openai_api_key:
            st.warning("⚠️ Please enter your OpenAI API Key to proceed")
            st.markdown("[Get your API key here](https://platform.openai.com/api-keys)")
            return
        
        st.success("API Key accepted!")
    
    # Input form
    with st.form("startup_form"):
        startup_idea = st.text_area("Describe your startup idea")
        target_audience = st.text_area("Who is your target audience?")
        goals = st.text_area("What are your business goals?")
        technical_requirements = st.text_area("Any specific technical requirements? (optional)")
        marketing_focus = st.text_area("Any specific marketing focus? (optional)")
        submitted = st.form_submit_button("Get Comprehensive Analysis")
        
        if submitted and startup_idea and target_audience and goals:
            query = {
                "startup_idea": startup_idea,
                "target_audience": target_audience,
                "business_goals": goals,
                "technical_requirements": technical_requirements,
                "marketing_focus": marketing_focus
            }
            
            st.session_state.messages.append({"role": "user", "content": str(query)})
            
            with st.spinner("AI Startup Agency is analyzing your idea..."):
                try:
                    # Getanalysis from each agent using proper agency.get_completion()
                    ceo_response = agency.get_completion(
                        message=f"Analyze this startup idea: {str(query)}",
                        recipient_agent=ceo,
                        additional_instructions="Provide a strategic analysis of the startup idea using the AnalyzeStartupTool."
                    )
                    
                    cto_response = agency.get_completion(
                        message=f"Analyze technical requirements: {str(query)}",
                        recipient_agent=cto,
                        additional_instructions="Evaluate technical feasibility using QueryTechnicalRequirements and EvaluateTechnicalFeasibility tools."
                    )
                    
                    pm_response = agency.get_completion(
                        message=f"Analyze product strategy: {str(query)}",
                        recipient_agent=product_manager,
                        additional_instructions="Focus on product-market fit and roadmap development."
                    )
                    
                    marketing_response = agency.get_completion(
                        message=f"Develop marketing strategy: {str(query)}",
                        recipient_agent=marketing_manager,
                        additional_instructions="Provide detailed go-to-market strategy and customer acquisition plan."
                    )
                    
                    # Create tabs for different analyses
                    tabs = st.tabs(["CEO Analysis", "Technical Analysis", "Product Strategy", "Marketing Strategy"])
                    
                    with tabs[0]:
                        st.markdown("## CEO's Strategic Analysis")
                        st.markdown(ceo_response)
                    
                    with tabs[1]:
                        st.markdown("## Technical Feasibility (CTO)")
                        st.markdown(cto_response)
                    
                    with tabs[2]:
                        st.markdown("## Product Strategy")
                        st.markdown(pm_response)
                    
                    with tabs[3]:
                        st.markdown("## Marketing Strategy")
                        st.markdown(marketing_response)
                    
                    # Store complete analysis in session state
                    complete_analysis = {
                        "ceo_analysis": ceo_response,
                        "technical_analysis": cto_response,
                        "product_strategy": pm_response,
                        "marketing_strategy": marketing_response
                    }
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": str(complete_analysis)
                    })
                    
                except Exception as e:
                    st.error(f"Error during analysis: {str(e)}")
                    st.error("Please try again or contact support.")

    with st.sidebar:
        st.subheader("Options")
        if st.checkbox("Show Analysis History"):
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
        
        if st.button("Clear History"):
            st.session_state.messages = []
            st.rerun()

if __name__ == "__main__":
    main()
