from typing import Optional, List, Dict, Any, Union
import os
import time
import streamlit as st
from openai import OpenAI
import anthropic
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from enum import Enum
import json
from agno.agent import Agent, RunResponse
from agno.models.anthropic import Claude

# Model Constants
DEEPSEEK_MODEL: str = "deepseek-reasoner"
CLAUDE_MODEL: str = "claude-3-5-sonnet-20241022"

class ArchitecturePattern(str, Enum):
    """Architectural patterns for system design."""
    MICROSERVICES = "microservices"  # Decomposed into small, independent services
    MONOLITHIC = "monolithic"  # Single, unified codebase
    SERVERLESS = "serverless"  # Function-as-a-Service architecture
    EVENT_DRIVEN = "event_driven"  # Asynchronous event-based communication

class DatabaseType(str, Enum):
    """Types of database systems."""
    SQL = "sql"  # Relational databases with ACID properties
    NOSQL = "nosql"  # Non-relational databases for flexible schemas
    HYBRID = "hybrid"  # Combined SQL and NoSQL approach

class ComplianceStandard(str, Enum):
    """Regulatory compliance standards."""
    HIPAA = "hipaa"  # Healthcare data protection
    GDPR = "gdpr"  # EU data privacy regulation
    SOC2 = "soc2"  # Service organization security controls
    ISO27001 = "iso27001"  # Information security management

class ArchitectureDecision(BaseModel):
    """Represents architectural decisions and their justifications."""
    pattern: ArchitecturePattern
    rationale: str = Field(..., min_length=50)  # Detailed explanation for the choice
    trade_offs: Dict[str, List[str]] = Field(..., alias="trade_offs")  # Pros and cons
    estimated_cost: Dict[str, float]  # Cost breakdown

class SecurityMeasure(BaseModel):
    """Security controls and implementation details."""
    measure_type: str  # Type of security measure
    implementation_priority: int = Field(..., ge=1, le=5)  # Priority level 1-5
    compliance_standards: List[ComplianceStandard]  # Applicable standards
    data_classification: str  # Data sensitivity level

class InfrastructureResource(BaseModel):
    """Infrastructure components and specifications."""
    resource_type: str  # Type of infrastructure resource
    specifications: Dict[str, str]  # Technical specifications
    scaling_policy: Dict[str, str]  # Scaling rules and thresholds
    estimated_cost: float  # Estimated cost per resource

class TechnicalAnalysis(BaseModel):
    """Complete technical analysis of the system architecture."""
    architecture_decision: ArchitectureDecision  # Core architecture choices
    infrastructure_resources: List[InfrastructureResource]  # Required resources
    security_measures: List[SecurityMeasure]  # Security controls
    database_choice: DatabaseType  # Database architecture
    compliance_requirements: List[ComplianceStandard] = []  # Required standards
    performance_requirements: List[Dict[str, Union[str, float]]] = []  # Performance metrics
    risk_assessment: Dict[str, str] = {}  # Identified risks and mitigations


class ModelChain:
    def __init__(self, deepseek_api_key: str, anthropic_api_key: str) -> None:
        self.client = OpenAI(
            api_key=deepseek_api_key,
            base_url="https://api.deepseek.com" 
        )
        self.claude_client = anthropic.Anthropic(api_key=anthropic_api_key)
        
        # Create Claude model with system prompt
        claude_model = Claude(
            id="claude-3-5-sonnet-20241022", 
            api_key=anthropic_api_key,
            system_prompt="""Given the user's query and the DeepSeek reasoning:
            1. Provide a detailed analysis of the architecture decisions
            2. Generate a project implementation roadmap
            3. Create a comprehensive technical specification document
            4. Format the output in clean markdown with proper sections
            5. Include diagrams descriptions in mermaid.js format"""
        )
        
        # Initialize agent with configured model
        self.agent = Agent(
            model=claude_model,
            markdown=True
        )
        
        self.deepseek_messages: List[Dict[str, str]] = []
        self.claude_messages: List[Dict[str, Any]] = []
        self.current_model: str = CLAUDE_MODEL
    def get_deepseek_reasoning(self, user_input: str) -> tuple[str, str]:    
        start_time = time.time()

        system_prompt = """You are an expert software architect and technical advisor. Analyze the user's project requirements 
        and provide structured reasoning about architecture, tools, and implementation strategies. 

        IMPORTANT: Reason why you are choosing a particular architecture pattern, database type, etc. for user understanding in your reasoning.
        
        IMPORTANT: Your response must be a valid JSON object (not a string or any other format) that matches the schema provided below.
        Do not include any explanatory text, markdown formatting, or code blocks - only return the JSON object.
        
        Schema:
        {
            "architecture_decision": {
                "pattern": "one of: microservices|monolithic|serverless|event_driven|layered",
                "rationale": "string",
                "trade_offs": {"advantage": ["list of strings"], "disadvantage": ["list of strings"]},
                "estimated_cost": {"implementation": float, "maintenance": float}
            },
            "infrastructure_resources": [{
                "resource_type": "string",
                "specifications": {"key": "value"},
                "scaling_policy": {"key": "value"},
                "estimated_cost": float
            }],
            "security_measures": [{
                "measure_type": "string",
                "implementation_priority": "integer 1-5",
                "compliance_standards": ["hipaa", "gdpr", "soc2", "hitech", "iso27001", "pci_dss"],
                "estimated_setup_time_days": "integer",
                "data_classification": "one of: protected_health_information|personally_identifiable_information|confidential|public",
                "encryption_requirements": {"key": "value"},
                "access_control_policy": {"role": ["permissions"]},
                "audit_requirements": ["list of strings"]
            }],
            "database_choice": "one of: sql|nosql|graph|time_series|hybrid",
            "ml_capabilities": [{
                "model_type": "string",
                "training_frequency": "string",
                "input_data_types": ["list of strings"],
                "performance_requirements": {"metric": float},
                "hardware_requirements": {"resource": "specification"},
                "regulatory_constraints": ["list of strings"]
            }],
            "data_integrations": [{
                "integration_type": "one of: hl7|fhir|dicom|rest|soap|custom",
                "data_format": "string",
                "frequency": "string",
                "volume": "string",
                "security_requirements": {"key": "value"}
            }],
            "performance_requirements": [{
                "metric_name": "string",
                "target_value": float,
                "measurement_unit": "string",
                "priority": "integer 1-5"
            }],
            "audit_config": {
                "log_retention_period": "integer",
                "audit_events": ["list of strings"],
                "compliance_mapping": {"standard": ["requirements"]}
            },
            "api_config": {
                "version": "string",
                "auth_method": "string",
                "rate_limits": {"role": "requests_per_minute"},
                "documentation_url": "string"
            },
            "error_handling": {
                "retry_policy": {"key": "value"},
                "fallback_strategies": ["list of strings"],
                "notification_channels": ["list of strings"]
            },
            "estimated_team_size": "integer",
            "critical_path_components": ["list of strings"],
            "risk_assessment": {"risk": "mitigation"},
            "maintenance_considerations": ["list of strings"],
            "compliance_requirements": ["list of compliance standards"],
            "data_retention_policy": {"data_type": "retention_period"},
            "disaster_recovery": {"key": "value"},
            "interoperability_standards": ["list of strings"]
        }

        Consider scalability, security, maintenance, and technical debt in your analysis.
        Focus on practical, modern solutions while being mindful of trade-offs."""

        try:
            deepseek_response = self.client.chat.completions.create(
                model="deepseek-reasoner",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                max_tokens=3000,
                stream=False   
            )

            reasoning_content = deepseek_response.choices[0].message.reasoning_content
            normal_content = deepseek_response.choices[0].message.content
            
            # Display the reasoning separately
            with st.expander("DeepSeek Reasoning", expanded=True):
                st.markdown(reasoning_content)
            
                
            with st.expander("💭 Technical Analysis", expanded=True):
                st.markdown(normal_content)
                elapsed_time = time.time() - start_time
                time_str = f"{elapsed_time/60:.1f} minutes" if elapsed_time >= 60 else f"{elapsed_time:.1f} seconds"
                st.caption(f"⏱️ Analysis completed in {time_str}")

                # Return both reasoning and normal content
                return reasoning_content, normal_content

        except Exception as e:
            st.error(f"Error in DeepSeek analysis: {str(e)}")
            return "Error occurred while analyzing", ""
        
    def get_claude_response(self, user_input: str, deepseek_output: tuple[str, str]) -> str:
        try:
            reasoning_content, normal_content = deepseek_output
            
            # Create expander for Claude's response
            with st.expander("🤖 Claude's Response", expanded=True):
                response_placeholder = st.empty()
                
                # Prepare the message with user input, reasoning and normal output
                message = f"""User Query: {user_input}

                DeepSeek Reasoning: {reasoning_content}

                DeepSeek Technical Analysis: {normal_content}
                Give detailed explanation for each key value pair in brief in the JSON object, and why we chose it clearly. Dont use your own opinions, use the reasoning and the structured output to explain the choices."""
                
                # Use Phi Agent to get response
                response: RunResponse = self.agent.run(
                    message=message
                )
                
                dub = response.content
                st.markdown(dub)
                return dub

        except Exception as e:
            st.error(f"Error in Claude response: {str(e)}")
            return "Error occurred while getting response"

def main() -> None:
    """Main function to run the Streamlit app."""
    st.title("🤖 AI System Architect Advisor with R1")

    # Add prompt guidance
    st.info("""
    📝 For best results, structure your prompt with:
    
    1. **Project Context**: Brief description of your project/system
    2. **Requirements**: Key functional and non-functional requirements
    3. **Constraints**: Any technical, budget, or time constraints
    4. **Scale**: Expected user base and growth projections
    5. **Security/Compliance**: Any specific security or regulatory needs
    
    Example:
    ```
    I need to build a healthcare data management system that:
    - Handles patient records and appointments
    - Needs to scale to 10,000 users
    - Must be HIPAA compliant
    - Budget constraint of $50k for initial setup
    - Should integrate with existing hospital systems
    ```
    """)

    # Sidebar for API keys
    with st.sidebar:
        st.header("⚙️ Configuration")
        deepseek_api_key = st.text_input("DeepSeek API Key", type="password")
        anthropic_api_key = st.text_input("Anthropic API Key", type="password")
        
        if st.button("🗑️ Clear Chat History"):
            st.session_state.messages = []
            st.rerun()

    # Initialize session state for messages
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("What would you like to know?"):
        if not deepseek_api_key or not anthropic_api_key:
            st.error("⚠️ Please enter both API keys in the sidebar.")
            return

        # Initialize ModelChain
        chain = ModelChain(deepseek_api_key, anthropic_api_key)

        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("🤔 Thinking..."):
                deepseek_output = chain.get_deepseek_reasoning(prompt)
            
            
            with st.spinner("✍️ Responding..."):
                response = chain.get_claude_response(prompt, deepseek_output)
                st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()