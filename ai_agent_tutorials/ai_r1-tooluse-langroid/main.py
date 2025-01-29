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

class ArchitectureDecision(BaseModel):
    """Architecture decision details"""
    pattern: ArchitecturePattern
    rationale: str
    trade_offs: Dict[str, List[str]]
    estimated_cost: Dict[str, float]

class InfrastructureResource(BaseModel):
    """Infrastructure resource requirements"""
    resource_type: str
    specifications: Dict[str, str]
    scaling_policy: Dict[str, Any]
    estimated_cost: float

class DataIntegration(BaseModel):
    """Data integration specifications"""
    integration_type: IntegrationType
    data_format: str
    frequency: str
    volume: str
    security_requirements: Dict[str, str]

class PerformanceRequirement(BaseModel):
    """Performance requirements specification"""
    metric_name: str
    target_value: float
    measurement_unit: str
    priority: int

class AuditConfig(BaseModel):
    """Audit configuration settings"""
    log_retention_period: int
    audit_events: List[str]
    compliance_mapping: Dict[str, List[str]]

class APIConfig(BaseModel):
    """API configuration settings"""
    version: str
    auth_method: str
    rate_limits: Dict[str, int]
    documentation_url: str

class ErrorHandlingConfig(BaseModel):
    """Error handling configuration"""
    retry_policy: Dict[str, Any]
    fallback_strategies: List[str]
    notification_channels: List[str]

class ProjectAnalysis(BaseModel):
    """Enhanced project analysis for healthcare systems"""
    architecture_decision: ArchitectureDecision
    infrastructure_resources: List[InfrastructureResource]
    security_measures: List[SecurityMeasure]
    database_choice: DatabaseType
    estimated_team_size: int
    critical_path_components: List[str]
    risk_assessment: Dict[str, str]
    maintenance_considerations: List[str]
    
    # Healthcare-specific fields
    compliance_requirements: List[ComplianceStandard]
    data_integrations: List[DataIntegration]
    ml_capabilities: List[MLCapability]
    performance_requirements: List[PerformanceRequirement]
    data_retention_policy: Dict[str, str]
    disaster_recovery: Dict[str, Any]
    interoperability_standards: List[str]
    
    # New fields
    audit_config: AuditConfig
    api_config: APIConfig
    error_handling: ErrorHandlingConfig

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
        and provide structured reasoning about architecture, tools, and implementation strategies. 
        
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

                # Return the validated structured output for Claude
                return reasoning_content

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
                    system=system_prompt,
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