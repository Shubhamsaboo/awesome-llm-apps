from agno.agent import Agent, RunResponse
from agno.models.together import Together
from agents.tools.facial_expression_tool import analyze_facial_expressions as facial_expression_tool
from agno.utils.pprint import pprint_run_response
from dotenv import load_dotenv
import os

load_dotenv()

# Define the facial expression agent
facial_expression_agent = Agent(
    name="facial-expression-agent",
    model=Together(id="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free", api_key=os.getenv("TOGETHER_API_KEY")), 
    tools=[facial_expression_tool],
    description=
    '''
        You are a facial expression agent that will analyze facial expressions in videos to detect emotions and engagement.
        You will return the emotion timeline and engagement metrics.
    ''',
    instructions=[
        "You will be provided with a video file of a person speaking in a public setting.",
        "Your task is to analyze the facial expressions in the video to detect emotions and engagement.",
        "You will analyze the video frame by frame to detect and classify facial expressions such as happiness, sadness, anger, surprise, and neutrality.",
        "You will also analyze the engagement metrics such as eye contact count and smile count",
        "The response MUST be in the following JSON format:",
        "{",
            '"emotion_timeline": [emotion_timeline]',
                "engagement_metrics: {",
                    '"eye_contact_frequency": [eye contact_frequency]',
                    '"smile_frequency": [smile_frequency]',
                "}",
        "}",
        "The response MUST be in proper JSON format with keys and values in double quotes.",
        "The final response MUST not include any other text or anything else other than the JSON response.",
        "The final response MUST not include any backslashes in the JSON response.",
        "The final response MUST be a valid JSON object and MUST not have any unterminated strings in the JSON response."
    ],
    markdown=True,
    show_tool_calls=True,
    debug_mode=True
)

# video = "../../videos/my_video.mp4"
# prompt = f"Analyze facial expressions in the video file to detect emotions and engagement in the following video: {video}"
# facial_expression_agent.print_response(prompt, stream=True)

# # Run agent and return the response as a variable
# response: RunResponse = facial_expression_agent.run(prompt)
# # Print the response in markdown format
# pprint_run_response(response, markdown=True)