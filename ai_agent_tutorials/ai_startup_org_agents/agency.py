from typing import List, Literal, Dict, Optional
from agency_swarm import Agent, Agency, set_openai_key, BaseTool
from pydantic import Field
import streamlit as st
from instructor import OpenAISchema
import asyncio

# Schema Classes
class ProjectRequirements(OpenAISchema):
    """Schema for project requirements analysis"""
    project_scope: str
    complexity: Literal["high", "medium", "low"]
    estimated_timeline: str
    key_deliverables: List[str]
    technical_requirements: List[str]
    budget_range: str
    potential_challenges: List[str]

class TechnicalSpecification(OpenAISchema):
    """Schema for technical architecture and specifications"""
    architecture_type: str
    core_technologies: List[str]
    api_requirements: List[str]
    database_design: Dict[str, List[str]]
    security_requirements: List[str]
    scalability_considerations: List[str]
    estimated_development_hours: int

# Tools
class AnalyzeProjectRequirements(BaseTool):
    """Tool for comprehensive project analysis"""
    project_description: str = Field(..., description="Client's project description")
    business_requirements: str = Field(..., description="Business requirements and goals")
    budget_constraints: Optional[str] = Field(None, description="Budget constraints if any")
    
    def run(self):
        prompt = f"""
        Analyze this project request:
        Project: {self.project_description}
        Business Requirements: {self.business_requirements}
        Budget Constraints: {self.budget_constraints}
        
        Provide a comprehensive analysis including:
        1. Project scope and complexity
        2. Estimated timeline
        3. Key deliverables
        4. Technical requirements
        5. Potential challenges
        """
        return self._llm.invoke(prompt)

class CreateTechnicalSpecification(BaseTool):
    """Tool for creating detailed technical specifications"""
    requirements: str = Field(..., description="Project requirements")
    tech_context: Optional[str] = Field(None, description="Additional technical context")
    
    def run(self):
        prompt = f"""
        Create technical specifications for:
        Requirements: {self.requirements}
        Technical Context: {self.tech_context or 'None provided'}
        
        Provide detailed technical analysis including:
        1. Architecture type and patterns
        2. Core technologies and frameworks
        3. API requirements
        4. Database design
        5. Security requirements
        6. Scalability considerations
        7. Development effort estimation
        """
        return self._llm.invoke(prompt)

def init_session_state() -> None:
    """Initialize session state variables"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'api_key' not in st.session_state:
        st.session_state.api_key = None

def main() -> None:
    st.set_page_config(page_title="AI Services Agency", layout="wide")
    init_session_state()
    
    st.title("🚀 AI Services Agency")
    
    # API Configuration
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
        
    # Initialize agents with the provided API key
    set_openai_key(st.session_state.api_key)
    api_headers = {"Authorization": f"Bearer {st.session_state.api_key}"}
    
    # Project Input Form
    with st.form("project_form"):
        st.subheader("Project Details")
        
        project_name = st.text_input("Project Name")
        project_description = st.text_area(
            "Project Description",
            help="Describe the project, its goals, and any specific requirements"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            project_type = st.selectbox(
                "Project Type",
                ["Web Application", "Mobile App", "API Development", 
                 "Data Analytics", "AI/ML Solution", "Other"]
            )
            timeline = st.selectbox(
                "Expected Timeline",
                ["1-2 months", "3-4 months", "5-6 months", "6+ months"]
            )
        
        with col2:
            budget_range = st.selectbox(
                "Budget Range",
                ["$10k-$25k", "$25k-$50k", "$50k-$100k", "$100k+"]
            )
            priority = st.selectbox(
                "Project Priority",
                ["High", "Medium", "Low"]
            )
        
        tech_requirements = st.text_area(
            "Technical Requirements (optional)",
            help="Any specific technical requirements or preferences"
        )
        
        special_considerations = st.text_area(
            "Special Considerations (optional)",
            help="Any additional information or special requirements"
        )
        
        submitted = st.form_submit_button("Analyze Project")
        
        if submitted and project_name and project_description:
            try:
                # Set OpenAI key
                set_openai_key(st.session_state.api_key)
                
                # Create agents
                ceo = Agent(
                    name="Project Director",
                    description="Experienced project director with expertise in technical project evaluation.",
                    instructions="""
                    - Lead project analysis and strategic planning
                    - Evaluate project feasibility and resource requirements
                    - Make high-level decisions on project direction
                    """,
                    tools=[AnalyzeProjectRequirements],
                    api_headers=api_headers,
                    temperature=0.7,
                    max_prompt_tokens=25000
                )

                cto = Agent(
                    name="Technical Architect",
                    description="Senior technical architect with deep expertise in system design.",
                    instructions="""
                    - Design technical architecture and evaluate feasibility
                    - Make technology stack recommendations
                    - Review technical specifications
                    """,
                    tools=[CreateTechnicalSpecification],
                    api_headers=api_headers,
                    temperature=0.5,
                    max_prompt_tokens=25000
                )

                product_manager = Agent(
                    name="Product Manager",
                    description="Experienced product manager focused on delivery excellence.",
                    instructions="""
                    - Manage project scope and timeline
                    - Define product requirements
                    - Ensure product quality
                    """,
                    api_headers=api_headers,
                    temperature=0.4,
                    max_prompt_tokens=25000
                )

                developer = Agent(
                    name="Lead Developer",
                    description="Senior developer with full-stack expertise.",
                    instructions="""
                    - Plan technical implementation
                    - Provide effort estimates
                    - Review technical feasibility
                    """,
                    api_headers=api_headers,
                    temperature=0.3,
                    max_prompt_tokens=25000
                )

                client_manager = Agent(
                    name="Client Success Manager",
                    description="Experienced client manager focused on project delivery.",
                    instructions="""
                    - Ensure client satisfaction
                    - Manage expectations
                    - Handle feedback
                    """,
                    api_headers=api_headers,
                    temperature=0.6,
                    max_prompt_tokens=25000
                )

                # Create agency
                agency = Agency(
                    [
                        ceo, cto, product_manager, developer, client_manager,
                        [ceo, cto],
                        [ceo, product_manager],
                        [ceo, developer],
                        [ceo, client_manager],
                        [cto, developer],
                        [product_manager, developer],
                        [product_manager, client_manager]
                    ],
                    async_mode='threading',
                    shared_files='shared_files'
                )
                
                # Prepare project info
                project_info = {
                    "name": project_name,
                    "description": project_description,
                    "type": project_type,
                    "timeline": timeline,
                    "budget": budget_range,
                    "priority": priority,
                    "technical_requirements": tech_requirements,
                    "special_considerations": special_considerations
                }

                st.session_state.messages.append({"role": "user", "content": str(project_info)})
                # Create tabs and run analysis
                with st.spinner("AI Services Agency is analyzing your project..."):
                    try:
                        # Get analysis from each agent using agency.get_completion()
                        ceo_response = agency.get_completion(
                            message=f"Analyze this project proposal: {str(project_info)}",
                            recipient_agent=ceo,
                            additional_instructions="Provide a strategic analysis of the project using the AnalyzeProjectRequirements tool to make best possible strategic decisions for the project."

                        )
                        
                        cto_response = agency.get_completion(
                            message=f"Analyze technical requirements: {str(project_info)}",
                            recipient_agent=cto,
                            additional_instructions="Evaluate technical feasibility using CreateTechnicalSpecification tool, eventually building a scalable and efficient tech product for the startup."
                        )
                        
                        pm_response = agency.get_completion(
                            message=f"Analyze project management aspects: {str(project_info)}",
                            recipient_agent=product_manager,
                            additional_instructions="Focus on product-market fit and roadmap development, and coordinate with technical and marketing teams."
                        )

                        developer_response = agency.get_completion(
                            message=f"Analyze technical implementation based on CTO's specifications: {str(project_info)}",
                            recipient_agent=developer,
                            additional_instructions="Provide technical implementation details, optimal tech stack you would be using including the costs of cloud services (if any) and feasibility feedback, and coordinate with product manager and CTO to build the required products for the startup."
                        )
                        
                        client_response = agency.get_completion(
                            message=f"Analyze client success aspects: {str(project_info)}",
                            recipient_agent=client_manager,
                            additional_instructions="Provide detailed go-to-market strategy and customer acquisition plan, and coordinate with product manager."
                        )
                        
                        # Create tabs for different analyses
                        tabs = st.tabs([
                            "CEO's Project Analysis",
                            "CTO's Technical Specification",
                            "Product Manager's Plan",
                            "Developer's Implementation",
                            "Client Success Strategy"
                        ])
                        
                        with tabs[0]:
                            st.markdown("## CEO's Strategic Analysis")
                            st.markdown(ceo_response)
                            st.session_state.messages.append({"role": "assistant", "content": ceo_response})
                        
                        with tabs[1]:
                            st.markdown("## CTO's Technical Specification")
                            st.markdown(cto_response)
                            st.session_state.messages.append({"role": "assistant", "content": cto_response})
                        
                        with tabs[2]:
                            st.markdown("## Product Manager's Plan")
                            st.markdown(pm_response)
                            st.session_state.messages.append({"role": "assistant", "content": pm_response})
                        
                        with tabs[3]:
                            st.markdown("## Lead Developer's Development Plan")
                            st.markdown(developer_response)
                            st.session_state.messages.append({"role": "assistant", "content": developer_response})
                        
                        with tabs[4]:
                            st.markdown("## Client Success Strategy")
                            st.markdown(client_response)
                            st.session_state.messages.append({"role": "assistant", "content": client_response})

                    except Exception as e:
                        st.error(f"Error during analysis: {str(e)}")
                        st.error("Please check your inputs and API key and try again.")

            except Exception as e:
                st.error(f"Error during analysis: {str(e)}")
                st.error("Please check your API key and try again.")

    # Add history management in sidebar
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