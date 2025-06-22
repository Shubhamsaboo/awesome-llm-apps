from agno.agent import Agent
from agno.models.together import Together
from dotenv import load_dotenv
import os

load_dotenv()

# Define the content analysis agent
content_analysis_agent = Agent(
    name="content-analysis-agent",
    model=Together(
        id="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        api_key=os.getenv("TOGETHER_API_KEY")
    ),
    description="""
        You are a content analysis agent that evaluates transcribed speech for structure, clarity, and filler words.
        You will return grammar corrections, identified filler words, and suggestions for content improvement.
    """,
    instructions=[
        "You will be provided with a transcript of spoken content.",
        "Your task is to analyze the transcript and identify:",
        "- Grammar and syntax corrections.",
        "- Filler words and their frequency.",
        "- Suggestions for improving clarity and structure.",
        "The response MUST be in the following JSON format:",
        "{",
            '"grammar_corrections": [list of corrections],',
            '"filler_words": { "word": count, ... },',
            '"suggestions": [list of suggestions]',
        "}",
        "Ensure the response is in proper JSON format with keys and values in double quotes.",
        "Do not include any additional text outside the JSON response."
    ],
    markdown=True,
    show_tool_calls=True,
    debug_mode=True
)

# # Example usage
# if __name__ == "__main__":
#     # Sample transcript from the Voice Analysis Agent
#     transcript = (
#         "So, um, I was thinking that, like, we could actually start the project soon. "
#         "You know, it's basically ready, and, uh, we just need to finalize some details."
#     )
#     prompt = f"Analyze the following transcript:\n\n{transcript}"
#     content_analysis_agent.print_response(prompt, stream=True)

    # # Run agent and return the response as a variable
    # response: RunResponse = content_analysis_agent.run(prompt)
    # # Print the response in markdown format
    # pprint_run_response(response, markdown=True)