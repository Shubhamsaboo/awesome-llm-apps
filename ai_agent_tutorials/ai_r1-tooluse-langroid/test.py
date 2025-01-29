from enum import Enum
from typing import List, Dict, Union
from pydantic import BaseModel, Field, ValidationError
import streamlit as st
from openai import OpenAI
import anthropic
import json
import re
import os
from dotenv import load_dotenv
from phi.agent import Agent, RunResponse
from phi.model.anthropic import Claude

load_dotenv()

# --------------------------
# Enums & Data Models
# --------------------------
class ArchitecturePattern(str, Enum):
    MICROSERVICES = "microservices"
    MONOLITHIC = "monolithic"
    SERVERLESS = "serverless"
    EVENT_DRIVEN = "event_driven"

class DatabaseType(str, Enum):
    SQL = "sql"
    NOSQL = "nosql"
    HYBRID = "hybrid"

class ComplianceStandard(str, Enum):
    HIPAA = "hipaa"
    GDPR = "gdpr"
    SOC2 = "soc2"
    ISO27001 = "iso27001"

class ArchitectureDecision(BaseModel):
    pattern: ArchitecturePattern
    rationale: str = Field(..., min_length=50)
    trade_offs: Dict[str, List[str]] = Field(..., alias="trade_offs")
    estimated_cost: Dict[str, float]

class SecurityMeasure(BaseModel):
    measure_type: str
    implementation_priority: int = Field(..., ge=1, le=5)
    compliance_standards: List[ComplianceStandard]
    data_classification: str

class InfrastructureResource(BaseModel):
    resource_type: str
    specifications: Dict[str, str]
    scaling_policy: Dict[str, str]
    estimated_cost: float

class TechnicalAnalysis(BaseModel):
    architecture_decision: ArchitectureDecision
    infrastructure_resources: List[InfrastructureResource]
    security_measures: List[SecurityMeasure]
    database_choice: DatabaseType
    compliance_requirements: List[ComplianceStandard] = []
    performance_requirements: List[Dict[str, Union[str, float]]] = []
    risk_assessment: Dict[str, str] = {}

# --------------------------
# Core Implementation
# --------------------------
class ArchitectureAnalyzer:
    def __init__(self, deepseek_api_key: str, anthropic_api_key: str):
        self.deepseek_client = OpenAI(
            api_key=deepseek_api_key,
            base_url="https://api.deepseek.com"
        )
        self.claude_agent = Agent(
            model=Claude(
                id="claude-3-5-sonnet-20241022",
                api_key=anthropic_api_key
            ),
            markdown=True,
        )
        self.reasoning_content = ""
        
        self.deepseek_prompt = f"""Analyze software requirements and return JSON with:
{{
  "architecture_decision": {{
    "pattern": "{'|'.join([e.value for e in ArchitecturePattern])}",
    "rationale": "technical justification",
    "trade_offs": {{"pros": [], "cons": []}},
    "estimated_cost": {{"development": float, "maintenance": float}}
  }},
  "infrastructure_resources": [{{"resource_type": "...", "specifications": {{}}, ...}}],
  "security_measures": [{{"measure_type": "...", "priority": 1-5, ...}}],
  "database_choice": "{'|'.join([e.value for e in DatabaseType])}",
  "compliance_requirements": ["..."],
  "performance_requirements": [{{"metric": "...", "target": float}}]
}}"""

    def _extract_json(self, text: str) -> dict:
        try:
            json_str = re.search(r'\{.*\}', text, re.DOTALL).group()
            return json.loads(json_str)
        except (AttributeError, json.JSONDecodeError) as e:
            st.error(f"JSON extraction failed: {str(e)}")
            st.text("Raw response:\n" + text)
            raise

    def analyze_requirements(self, user_input: str) -> TechnicalAnalysis:
        try:
            response1 = self.deepseek_client.chat.completions.create(
                model="deepseek-reasoner",
                messages=[
                    {"role": "system", "content": self.deepseek_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.2,
                max_tokens=2000
            )
            self.reasoning_content = response1.choices[0].message.reasoning_content
            json_data = self._extract_json(response1.choices[0].message.content)
            return TechnicalAnalysis(**json_data)
            
        except ValidationError as e:
            st.error(f"Validation error: {e.errors()}")
            st.json(json_data)
            raise

    def generate_report(self, analysis: TechnicalAnalysis) -> str:
        report_prompt = f"""Convert this technical analysis into a executive report:
{analysis.model_dump_json(indent=2)}

Use markdown with:
# Title
## Sections
- Bullet points
**Bold important items**
Tables for cost/performance"""

        response = self.claude_agent.run(report_prompt)
        return response.content

# --------------------------
# Streamlit UI
# --------------------------
def main():
    st.title("🏗️ AI Architecture Advisor")
    
    with st.sidebar:
        st.header("🔑 Setup")
        deepseek_api_key = st.text_input("DeepSeek Key", type="password")
        anthropic_api_key = st.text_input("Claude Key", type="password")
    
    if "analysis" not in st.session_state:
        st.session_state.analysis = None

    if prompt := st.chat_input("Describe your system requirements:"):
        if not all([deepseek_api_key, anthropic_api_key]):
            st.error("Missing API keys")
            return

        analyzer = ArchitectureAnalyzer(deepseek_api_key, anthropic_api_key)
        
        with st.status("🔨 Processing...", expanded=True):
            try:
                # Analysis Phase
                st.write("🧠 Analyzing requirements...")
                analysis = analyzer.analyze_requirements(prompt)
                st.session_state.analysis = analysis
                with st.expander("reasoning"):
                    st.markdown(analyzer.reasoning_content)

                # Reporting Phase
                st.write("📊 Generating report...")
                report = analyzer.generate_report(analysis)
                
                # Display Results
                st.success("Analysis complete!")
                st.markdown(report)
                
                with st.expander("📁 Raw Analysis Data"):
                    st.json(analysis.model_dump_json())

            except Exception as e:
                st.error(f"Processing failed: {str(e)}")

if __name__ == "__main__":
    main()