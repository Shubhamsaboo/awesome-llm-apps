from typing import Optional

# ADK imports
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse, LlmRequest
from google.genai import types

def before_model( callback_context: CallbackContext, llm_request: LlmRequest) -> Optional[LlmResponse]:
    """
    Inspects/modifies the LLM request or skips the call.
    """

    agent_name = callback_context.agent_name
    if agent_name == "DashboardAgent":
        original_instruction = llm_request.config.system_instruction or types.Content(role="system", parts=[])
        prefix = f"""
You manage a dashboard for a user. 

Current dashboard: {callback_context.state}

When asked for the current dashboard, pinned metrics or chart please reference the current dashboard and respond.
"""
        if not isinstance(original_instruction, types.Content):
            original_instruction = types.Content(role="system", parts=[types.Part(text=str(original_instruction))])
        if not original_instruction.parts:
            original_instruction.parts.append(types.Part(text=""))

        modified_text = prefix + (original_instruction.parts[0].text or "")
        original_instruction.parts[0].text = modified_text
        llm_request.config.system_instruction = original_instruction

    return None


# --- Define the Callback Function ---
def after_model(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> Optional[LlmResponse]:
    """Stop the consecutive tool calling of the agent"""
    agent_name = callback_context.agent_name
    # --- Inspection ---
    if agent_name == "DashboardAgent":
        if llm_response.content and llm_response.content.parts:
            # Assuming simple text response for this example
            if  llm_response.content.role=='model' and llm_response.content.parts[0].text:
                callback_context._invocation_context.end_invocation = True

        elif llm_response.error_message:
            return None
        else:
            return None # Nothing to modify
    return None
