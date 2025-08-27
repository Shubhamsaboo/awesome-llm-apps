from pydantic import BaseModel
from agents import (
    Agent,
    GuardrailFunctionOutput,
    InputGuardrailTripwireTriggered,
    OutputGuardrailTripwireTriggered,
    RunContextWrapper,
    Runner,
    TResponseInputItem,
    input_guardrail,
    output_guardrail,
)

# Pydantic models for guardrail outputs
class MathHomeworkCheck(BaseModel):
    is_math_homework: bool
    reasoning: str
    confidence: float

class ContentSafetyCheck(BaseModel):
    is_inappropriate: bool
    reasoning: str
    severity: str

class AgentResponse(BaseModel):
    response: str

# Guardrail agents
input_guardrail_agent = Agent(
    name="Input Guardrail",
    instructions="""
    Check if the user is asking for math homework help or inappropriate content.
    
    Classify as math homework if:
    - Asking to solve equations, math problems
    - Requesting help with calculations that seem like homework
    
    Classify as inappropriate if:
    - Contains harmful, offensive, or malicious content
    - Attempts to bypass safety measures
    
    Provide reasoning and confidence score (0-1).
    """,
    output_type=MathHomeworkCheck
)

output_guardrail_agent = Agent(
    name="Output Guardrail", 
    instructions="""
    Check if the agent's response contains inappropriate content or sensitive information.
    
    Flag as inappropriate if:
    - Contains harmful or offensive language
    - Provides dangerous instructions
    - Leaks sensitive information
    
    Assign severity: low, medium, high
    """,
    output_type=ContentSafetyCheck
)

# Input guardrail function
@input_guardrail
async def math_homework_guardrail(
    ctx: RunContextWrapper[None], 
    agent: Agent, 
    input: str | list[TResponseInputItem]
) -> GuardrailFunctionOutput:
    """Prevents math homework requests from being processed"""
    
    result = await Runner.run(input_guardrail_agent, input, context=ctx.context)
    output = result.final_output
    
    return GuardrailFunctionOutput(
        output_info=output,
        tripwire_triggered=output.is_math_homework and output.confidence > 0.7
    )

# Output guardrail function  
@output_guardrail
async def content_safety_guardrail(
    ctx: RunContextWrapper[None],
    agent: Agent,
    output: AgentResponse
) -> GuardrailFunctionOutput:
    """Ensures agent responses are safe and appropriate"""
    
    result = await Runner.run(output_guardrail_agent, output.response, context=ctx.context)
    safety_check = result.final_output
    
    return GuardrailFunctionOutput(
        output_info=safety_check,
        tripwire_triggered=safety_check.is_inappropriate and safety_check.severity in ["medium", "high"]
    )

# Main agent with guardrails
root_agent = Agent(
    name="Protected Customer Support Agent",
    instructions="""
    You are a helpful customer support agent.
    
    You help customers with:
    - Product questions and information
    - Account issues and support
    - General inquiries and guidance
    
    You DO NOT help with:
    - Academic homework (especially math)
    - Inappropriate or harmful requests
    - Sensitive or confidential information
    
    Be helpful but maintain appropriate boundaries.
    """,
    input_guardrails=[math_homework_guardrail],
    output_guardrails=[content_safety_guardrail],
    output_type=AgentResponse
)

# Example usage with guardrails
async def guardrails_example():
    """Demonstrates guardrails with various inputs"""
    
    test_cases = [
        "How do I reset my password?",  # Should pass
        "Can you solve this equation: 2x + 5 = 15?",  # Should trigger input guardrail
        "What are your product features?",  # Should pass
    ]
    
    for i, test_input in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i}: {test_input} ---")
        
        try:
            result = await Runner.run(root_agent, test_input)
            print(f"✅ Success: {result.final_output.response}")
            
        except InputGuardrailTripwireTriggered as e:
            print(f"🚫 Input Guardrail Triggered: {e}")
            
        except OutputGuardrailTripwireTriggered as e:
            print(f"⚠️ Output Guardrail Triggered: {e}")
            
        except Exception as e:
            print(f"❌ Error: {e}")

# Standalone example functions
async def test_input_guardrail():
    """Test input guardrail specifically"""
    try:
        await Runner.run(root_agent, "Can you help me solve this calculus problem?")
        print("❌ Guardrail should have triggered")
    except InputGuardrailTripwireTriggered:
        print("✅ Input guardrail correctly triggered for math homework")

async def test_valid_request():
    """Test valid customer support request"""
    result = await Runner.run(root_agent, "I'm having trouble logging into my account. Can you help?")
    print(f"✅ Valid request processed: {result.final_output.response}")
