from typing import List, Literal
from agency_swarm import Agent, Agency, set_openai_key, BaseTool
from pydantic import Field
import streamlit as st
from instructor import OpenAISchema
import asyncio

# Custom Tools - Startup Analysis, Strategic Decision, Technical Requirements, Technical Feasibility
class StartupAnalysis(OpenAISchema):
    """Schema for startup analysis results"""
    market_potential: Literal["high", "medium", "low"]
    technical_complexity: Literal["high", "medium", "low"]
    resource_requirements: Literal["high", "medium", "low"]
    rationale: str = Field(description="Explanation for the analysis")
    
class AnalyzeStartupTool(BaseTool):
    """Tool to analyze startup ideas"""
    startup_idea: str = Field(..., description="The startup idea to analyze")
    target_market: str = Field(..., description="Target market description")
    
    def run(self):
        """Run startup analysis based on CEO's evaluation"""
        prompt = f"""
        Analyze this startup idea:
        Idea: {self.startup_idea}
        Target Market: {self.target_market}
        
        Provide a comprehensive analysis including:
        1. Market potential (high/medium/low)
        2. Technical complexity (high/medium/low)
        3. Resource requirements (high/medium/low)
        4. A brief rationale for your decisions
        
        Format your response as a StartupAnalysis object.
        """
        response = self._llm.invoke(prompt)
        analysis = StartupAnalysis.from_response(response)
        
        # Store analysis in shared state for other tools to access
        self._shared_state.set("startup_analysis", analysis)
        return analysis

class MakeStrategicDecision(BaseTool):
    """Tool for CEO to make and track strategic decisions"""
    decision: str = Field(..., description="The strategic decision to be made for this startup idea")
    decision_type: Literal["product", "technical", "marketing", "financial"] = Field(..., description="Type of decision")
    
    def run(self):
        """Execute and record strategic decision"""
        analysis = self._shared_state.get("startup_analysis")
        if not analysis:
            return "Please analyze the startup idea first using AnalyzeStartupTool"
        
        decision_record = {
            "decision": self.decision,
            "type": self.decision_type,
            "based_on_analysis": analysis
        }
        
        return f"Strategic decision recorded: {self.decision} (Type: {self.decision_type})"

class QueryTechnicalRequirements(BaseTool):
    """Tool to analyze technical requirements"""
    technology_stack: str = Field(..., description="Scalable technology stack to analyze and implement for this startup idea")
    
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

# Streamlit Interface
def init_session_state():
    """Initialize Streamlit session state variables."""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'api_key' not in st.session_state:
        st.session_state.api_key = None

def main():
    """Main Streamlit application."""
    st.set_page_config(page_title="AI Startup Organization Assistant", layout="wide")
    init_session_state()
    
    st.title("🚀 AI Startup Organization Agency")

    with st.sidebar:
        st.header("🔑 API Configuration")
        openai_api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            help="Enter your OpenAI API key to continue"
        )

        if openai_api_key:
            st.session_state.api_key = openai_api_key
            st.success("API Key accepted!")
        else:
            st.warning("⚠️ Please enter your OpenAI API Key to proceed")
            st.markdown("[Get your API key here](https://platform.openai.com/api-keys)")
            return
        
        st.success("API Key accepted!")
        
    # Initialize agents with the provided API key
    set_openai_key(st.session_state.api_key)
    api_headers = {"Authorization": f"Bearer {st.session_state.api_key}"}
    
    # Define individual agents
    ceo = Agent(
        name="CEO",
        description="Strategic leader and final decision maker for the startup",
        instructions="""
        You are an experienced CEO with deep expertise in evaluating startup ideas.
        Your role involves two main responsibilities:

        1. ANALYZING STARTUP IDEAS:
        When analyzing startup ideas, carefully consider:
        - Market Potential (high/medium/low): market size, growth, competition, accessibility
        - Technical Complexity (high/medium/low): tech stack, scalability, timeline
        - Resource Requirements (high/medium/low): capital, team, marketing costs
        
        2. MAKING STRATEGIC DECISIONS:
        After analysis, you should make clear strategic decisions:
        - Product decisions: features, roadmap, priorities
        - Technical decisions: architecture, stack choices
        - Marketing decisions: go-to-market strategy, channels
        - Financial decisions: funding, resource allocation

        Process:
        1. First use AnalyzeStartupTool to evaluate the idea
        2. Then use MakeStrategicDecision to record your strategic choices
        3. Always base decisions on your previous analysis
        
        Provide clear, actionable insights and decisions.
        """,
        tools=[AnalyzeStartupTool, MakeStrategicDecision],
        temperature=0.7,
        max_prompt_tokens=25000,
        api_headers=api_headers
    )

    cto = Agent(
        name="CTO",
        description="Technical leader responsible for architecture and tech decisions",
        instructions="Analyze technical requirements and evaluate feasibility. Always query requirements before evaluation",
        tools=[QueryTechnicalRequirements, EvaluateTechnicalFeasibility],
        temperature=0.5,
        max_prompt_tokens=25000,
        api_headers=api_headers
    )

    product_manager = Agent(
        name="Product_Manager",
        description="Product strategy and roadmap owner",
        instructions="Define product strategy, create roadmap, and coordinate between technical and marketing teams.",
        temperature=0.4,
        max_prompt_tokens=25000,
        api_headers=api_headers
    )

    developer = Agent(
        name="Developer",
        description="Technical implementation specialist",
        instructions="You are a full stack tech expert and developer. Implement technical solutions and provide feasibility feedback.",
        temperature=0.3,
        max_prompt_tokens=25000,
        api_headers=api_headers
    )

    marketing_manager = Agent(
        name="Marketing_Manager",
        description="Marketing strategy and growth leader",
        instructions="Develop marketing strategies, analyze target audience, and coordinate with Product Manager.",
        temperature=0.6,
        max_prompt_tokens=25000,
        api_headers=api_headers
    )

    # Initializing the agency with communication paths
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
        async_mode='threading',  # Runs agent tasks in separate threads for concurrent execution
        shared_files='shared_files'
    )

    # Input form
    with st.form("startup_form"):
        startup_idea = st.text_area("Describe your startup idea in a sentence or two")
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
                        additional_instructions="Provide a strategic analysis of the startup idea using the AnalyzeStartupTool and use MakeStrategicDecision tool to make best possible strategic decisions for the startup."
                    )
                    
                    cto_response = agency.get_completion(
                        message=f"Analyze technical requirements: {str(query)}",
                        recipient_agent=cto,
                        additional_instructions="Evaluate technical feasibility using QueryTechnicalRequirements and EvaluateTechnicalFeasibility tools, eventually building a scalable and efficient tech product for the startup."
                    )
                    
                    pm_response = agency.get_completion(
                        message=f"Analyze product strategy: {str(query)}",
                        recipient_agent=product_manager,
                        additional_instructions="Focus on product-market fit and roadmap development, and coordinate with technical and marketing teams."
                    )

                    developer_response = agency.get_completion(
                        message=f"Analyze technical implementation and the tech stack decided by CTO to build required products for the startup: {str(query)}",
                        recipient_agent=developer,
                        additional_instructions="Provide technical implementation details, optimal tech stack you would be using including the costs of cloud services (if any) and feasibility feedback, and coordinate with product manager and CTO to build the required products for the startup."
                    )
                    
                    marketing_response = agency.get_completion(
                        message=f"Develop marketing strategy: {str(query)}",
                        recipient_agent=marketing_manager,
                        additional_instructions="Provide detailed go-to-market strategy and customer acquisition plan, and coordinate with product manager."
                    )
                    
                    # Create tabs for different analyses
                    tabs = st.tabs(["CEO Analysis", "Technical Analysis", "Product Strategy", "Marketing Strategy", "Developer's Feedback"])
                    
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
                    
                    with tabs[4]:
                        st.markdown("## Developer's Feedback")
                        st.markdown(developer_response)
                    
                    # Store complete analysis in session state
                    complete_analysis = {
                        "ceo_analysis": ceo_response,
                        "technical_analysis": cto_response,
                        "product_strategy": pm_response,
                        "marketing_strategy": marketing_response,
                        "developer_feedback": developer_response
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

