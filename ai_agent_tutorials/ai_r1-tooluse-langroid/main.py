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

# Model Constants
DEEPSEEK_MODEL: str = "deepseek-reasoner"
CLAUDE_MODEL: str = "claude-3-5-sonnet-20241022"

# Load environment variables
load_dotenv()

class ArchitecturePattern(str, Enum):
    MICROSERVICES = "microservices"
    MONOLITHIC = "monolithic"
    SERVERLESS = "serverless"
    EVENT_DRIVEN = "event_driven"
    LAYERED = "layered"

class SecurityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

class ScalabilityRequirement(str, Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    ENTERPRISE = "enterprise"

class DatabaseType(str, Enum):
    SQL = "sql"
    NOSQL = "nosql"
    GRAPH = "graph"
    TIME_SERIES = "time_series"
    HYBRID = "hybrid"

class DevTool(BaseModel):
    name: str
    purpose: str
    complexity: int = Field(ge=1, le=10)
    setup_time_minutes: int
    learning_curve: int = Field(ge=1, le=10)
    alternatives: List[str]

class InfrastructureComponent(BaseModel):
    service_name: str
    provider: str
    estimated_cost: float
    scaling_capability: ScalabilityRequirement
    region: Optional[str]
    backup_strategy: Optional[str]

class ComplianceStandard(str, Enum):
    HIPAA = "hipaa"
    GDPR = "gdpr"
    SOC2 = "soc2"
    HITECH = "hitech"
    ISO27001 = "iso27001"
    PCI_DSS = "pci_dss"

class DataClassification(str, Enum):
    PHI = "protected_health_information"
    PII = "personally_identifiable_information"
    CONFIDENTIAL = "confidential"
    PUBLIC = "public"

class IntegrationType(str, Enum):
    HL7 = "hl7"
    FHIR = "fhir"
    DICOM = "dicom"
    REST = "rest"
    SOAP = "soap"
    CUSTOM = "custom"

class DataProcessingType(str, Enum):
    REAL_TIME = "real_time"
    BATCH = "batch"
    HYBRID = "hybrid"

class MLCapability(BaseModel):
    """Defines machine learning capabilities and requirements"""
    model_type: str = Field(..., description="Type of ML model (e.g., diagnostic, predictive, monitoring)")
    training_frequency: str = Field(..., description="How often the model needs retraining")
    input_data_types: List[str] = Field(..., description="Types of data the model processes")
    performance_requirements: Dict[str, float] = Field(..., description="Required metrics like accuracy, latency")
    hardware_requirements: Dict[str, str] = Field(..., description="GPU/CPU/Memory requirements")
    regulatory_constraints: List[str] = Field(..., description="Regulatory requirements for ML models")

class DataIntegration(BaseModel):
    """Defines integration points with external systems"""
    system_name: str
    integration_type: IntegrationType
    data_frequency: str = Field(..., description="Frequency of data exchange")
    data_volume: str = Field(..., description="Expected data volume per time unit")
    transformation_rules: List[str] = Field(..., description="Data transformation requirements")
    error_handling: Dict[str, str] = Field(..., description="Error handling strategies")
    fallback_mechanism: Optional[str] = Field(None, description="Fallback approach when integration fails")

class SecurityMeasure(BaseModel):
    """Enhanced security measures for healthcare systems"""
    measure_type: str
    implementation_priority: int = Field(ge=1, le=5, description="Priority level for implementation")
    compliance_standards: List[ComplianceStandard]
    estimated_setup_time_days: int
    data_classification: DataClassification
    encryption_requirements: Dict[str, str] = Field(..., description="Encryption requirements for different states")
    access_control_policy: Dict[str, List[str]] = Field(..., description="Role-based access control definitions")
    audit_requirements: List[str] = Field(..., description="Audit logging requirements")

class PerformanceRequirement(BaseModel):
    """System performance requirements"""
    metric_name: str = Field(..., description="Name of the performance metric")
    threshold: float = Field(..., description="Required threshold value")
    measurement_unit: str = Field(..., description="Unit of measurement")
    criticality: int = Field(ge=1, le=5, description="How critical is this metric")
    monitoring_frequency: str = Field(..., description="How often to monitor this metric")

class ArchitectureDecision(BaseModel):
    pattern: ArchitecturePattern
    reasoning: str
    trade_offs: Dict[str, List[str]]
    estimated_implementation_time_months: float

class TechnicalDebtItem(BaseModel):
    description: str
    severity: int = Field(ge=1, le=5)
    estimated_fix_time_days: int
    affected_components: List[str]
    potential_risks: List[str]

class ProjectAnalysis(BaseModel):
    """Enhanced project analysis for healthcare systems"""
    architecture_decision: ArchitectureDecision
    recommended_tools: List[DevTool]
    infrastructure: List[InfrastructureComponent]
    security_measures: List[SecurityMeasure]
    database_choice: DatabaseType
    technical_debt_assessment: List[TechnicalDebtItem]
    estimated_team_size: int
    critical_path_components: List[str]
    risk_assessment: Dict[str, str]
    maintenance_considerations: List[str]
    
    # New healthcare-specific fields
    compliance_requirements: List[ComplianceStandard] = Field(
        ..., description="Required compliance standards"
    )
    data_integrations: List[DataIntegration] = Field(
        ..., description="External system integrations"
    )
    ml_capabilities: List[MLCapability] = Field(
        ..., description="ML model requirements and capabilities"
    )
    performance_requirements: List[PerformanceRequirement] = Field(
        ..., description="System performance requirements"
    )
    data_retention_policy: Dict[str, str] = Field(
        ..., description="Data retention requirements by type"
    )
    disaster_recovery: Dict[str, Any] = Field(
        ..., description="Disaster recovery and business continuity plans"
    )
    interoperability_standards: List[str] = Field(
        ..., description="Required healthcare interoperability standards"
    )

class ModelChain:
    def __init__(self, deepseek_api_key: str, anthropic_api_key: str) -> None:
        self.client = OpenAI(
            api_key=deepseek_api_key,
            base_url="https://api.deepseek.com" 
        )
        self.claude_client = anthropic.Anthropic(api_key=anthropic_api_key)
        
        self.deepseek_messages: List[Dict[str, str]] = []
        self.claude_messages: List[Dict[str, Any]] = []
        self.current_model: str = CLAUDE_MODEL

    def get_deepseek_reasoning(self, user_input: str) -> str:    
        start_time = time.time()

        system_prompt = """You are an expert software architect and technical advisor. Analyze the user's project requirements 
        and provide structured reasoning about architecture, tools, and implementation strategies. Your output must be a valid 
        JSON that matches the ProjectAnalysis schema. Consider scalability, security, maintenance, and technical debt in your analysis.
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
            
            # Validate the reasoning content as ProjectAnalysis
            try:
                project_analysis = ProjectAnalysis.parse_raw(reasoning_content)
                formatted_reasoning = json.dumps(json.loads(reasoning_content), indent=2)
                
                with st.expander("💭 Technical Analysis", expanded=True):
                    st.json(formatted_reasoning)
                    elapsed_time = time.time() - start_time
                    time_str = f"{elapsed_time/60:.1f} minutes" if elapsed_time >= 60 else f"{elapsed_time:.1f} seconds"
                    st.caption(f"⏱️ Analysis completed in {time_str}")

                return reasoning_content

            except Exception as validation_error:
                st.error(f"Invalid analysis format: {str(validation_error)}")
                return "Error in analysis format"

        except Exception as e:
            st.error(f"Error in DeepSeek analysis: {str(e)}")
            return "Error occurred while analyzing"

    def get_claude_response(self, user_input: str, reasoning: str) -> str:
        system_prompt = """You are a senior software architect and implementation advisor. Using the provided technical analysis, 
        give detailed, actionable advice for implementing the solution. Include code snippets, configuration examples, and 
        step-by-step implementation guidelines where appropriate. Focus on practical implementation details while maintaining 
        best practices and addressing potential challenges."""

        user_message = {
            "role": "user",
            "content": [{"type": "text", "text": user_input}]
        }

        assistant_prefill = {
            "role": "assistant",
            "content": [{"type": "text", "text": f"<thinking>{reasoning}</thinking>"}]
        }

        messages = [assistant_prefill]
        
        try:
            # Create expander for Claude's response
            with st.expander("🤖 Claude's Response", expanded=True):
                response_placeholder = st.empty()
                
                with self.claude_client.messages.stream(
                    model=self.current_model,
                    messages=messages,
                    max_tokens=8000
                ) as stream:
                    full_response = ""
                    for text in stream.text_stream:
                        full_response += text
                        response_placeholder.markdown(full_response)

                self.claude_messages.extend([user_message, {
                    "role": "assistant", 
                    "content": [{"type": "text", "text": full_response}]
                }])

                return full_response

        except Exception as e:
            st.error(f"Error in Claude response: {str(e)}")
            return "Error occurred while getting response"

def main() -> None:
    """Main function to run the Streamlit app."""
    st.title("🤖 AI Project with Deepseek + R1")

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
                reasoning = chain.get_deepseek_reasoning(prompt)
            
            
            with st.spinner("✍️ Responding..."):
                response = chain.get_claude_response(prompt, reasoning)
                st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()