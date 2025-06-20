from agno.team.team import Team
from agno.agent import Agent, RunResponse
from agno.models.together import Together
from agents.facial_expression_agent import facial_expression_agent
from agents.voice_analysis_agent import voice_analysis_agent
from agents.content_analysis_agent import content_analysis_agent
from agents.feedback_agent import feedback_agent
import os
from pydantic import BaseModel, Field

# Structured response
class CoordinatorResponse(BaseModel):
    facial_expression_response: str = Field(..., description="Response from facial expression agent")
    voice_analysis_response: str = Field(..., description="Response from voice analysis agent")
    content_analysis_response: str = Field(..., description="Response from content analysis agent")
    feedback_response: str = Field(..., description="Response from feedback agent")
    strengths: list[str] = Field(..., description="List of speaker's strengths")
    weaknesses: list[str] = Field(..., description="List of speaker's weaknesses")
    suggestions: list[str] = Field(..., description="List of suggestions for speaker to improve")

# Initialize a team of agents
coordinator_agent = Team(
    name="coordinator-agent",
    mode="coordinate",
    model=Together(id="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free", api_key=os.getenv("TOGETHER_API_KEY")),
    members=[facial_expression_agent, voice_analysis_agent, content_analysis_agent, feedback_agent],
    description="You are a public speaking coach who helps individuals improve their presentation skills through feedback and analysis.",
    instructions=[
        "You will be provided with a video file of a person speaking in a public setting.",
        "You will analyze the speaker's facial expressions, voice modulation, and content delivery to provide constructive feedback.",
        "Ask the facial expression agent to analyze the video file to detect emotions and engagement.",
        "Ask the voice analysis agent to analyze the audio file to detect speech rate, pitch variation, and volume consistency.",
        "Ask the content analysis agent to analyze the transcript given by voice analysis agent for structure, clarity, and filler words.", 
        "Ask the feedback agent to evaluate the analysis results from the facial expression agent, voice analysis agent, and content analysis agent to provide feedback on the overall effectiveness of the presentation, highlighting strengths and areas for improvement.",
        "Your response MUST include the exact responses from the facial expression agent, voice analysis agent, content analysis agent, and feedback agent.",
        "Additionally, your response MUST provide lists of the speaker's strengths, weaknesses, and suggestions for improvement based on all the responses and feedback provided by the feedback agent.",
        "Important: You MUST directly address the speaker while providing strengths, weaknesses, and suggestions for improvement in a clear and constructive manner.",
        "The response MUST be in the following strict JSON format:",
        "{",
            '"facial_expression_response": [facial_expression_agent_response],',
            '"voice_analysis_response": [voice_analysis_agent_response],',
            '"content_analysis_response": [content_analysis_agent_response],',
            '"feedback_response": [feedback_agent_response]',
            '"strengths": [speaker_strengths_list],',
            '"weaknesses": [speaker_weaknesses_list],',
            '"suggestions": [suggestions_for_improvement_list]',
        "}",
        "The response MUST be in strict JSON format with keys and values in double quotes.",
        "The values in the JSON response MUST NOT be null or empty.",
        "The final response MUST not include any other text or anything else other than the JSON response.",
        "The final response MUST not include any backslashes in the JSON response.",
        "The final response MUST be a valid JSON object and MUST not have any unterminated strings in the JSON response."
    ],
    add_datetime_to_instructions=True,
    add_member_tools_to_system_message=False,  # This can be tried to make the agent more consistently get the transfer tool call correct
    enable_agentic_context=True,  # Allow the agent to maintain a shared context and send that to members.
    share_member_interactions=True,  # Share all member responses with subsequent member requests.
    show_members_responses=True,
    response_model=CoordinatorResponse,
    use_json_mode=True,
    markdown=True,
    show_tool_calls=True,
    debug_mode=True
)

# # Example usage
# video = "../../videos/my_video.mp4"
# prompt = f"Analyze facial expressions, voice modulation, and content delivery in the following video: {video} and provide constructive feedback."
# coordinator_agent.print_response(prompt, stream=True)

# # Run agent and return the response as a variable
# response: RunResponse = coordinator_agent.run(prompt)
# # Print the response in markdown format
# pprint_run_response(response, markdown=True)