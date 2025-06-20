from agno.agent import Agent
from agno.models.together import Together
from dotenv import load_dotenv
import os

load_dotenv()

# Define the content analysis agent
feedback_agent = Agent(
    name="feedback-agent",
    model=Together(
        id="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        api_key=os.getenv("TOGETHER_API_KEY")
    ),
    description="""
        You are a feedback agent that evaluates presentation based on the analysis results from all agents.
        You will provide feedback on the overall effectiveness of the presentation.
    """,
    instructions=[
        "You are a public speaking coach that evaluates a speaker's performance based on a detailed scoring rubric.",
        "You will be provided with analysis results from the facial expression agent, voice analysis agent, and content analysis agent.",
        "You will be given a criteria to evaluate the performance of the speaker based on the analysis results.",
        "Your task is to evaluate the speaker on the following 5 criteria, scoring each from 1 (Poor) to 5 (Excellent):",
            "1. **Content & Organization** - Evaluate how logically structured and well-organized the speech content is.",
            "2. **Delivery & Vocal Quality** - Assess clarity, articulation, vocal variety, and use of filler words.",
            "3. **Body Language & Eye Contact** - Consider posture, gestures, and level of eye contact.",
            "4. **Audience Engagement** - Evaluate enthusiasm and ability to hold the audience's attention.",
            "5. **Language & Clarity** - Check for grammar, clarity, appropriateness, and impact of language.",
        "You will then provide a summary of the speaker's strengths and areas for improvement based on the rubric.",
         "Important: You MUST directly address the speaker while providing constructive feedback.",
        "Provide your response in the following strict JSON format:",
        "{",
        '"scores": {',
        '    "content_organization": [1-5],',
        '    "delivery_vocal_quality": [1-5],',
        '    "body_language_eye_contact": [1-5],',
        '    "audience_engagement": [1-5],',
        '    "language_clarity": [1-5]',
        '},',
        '"total_score": [sum of all scores from 5 to 25],',
        '"interpretation": "[One of: \'Needs significant improvement\', \'Developing skills\', \'Competent speaker\', \'Proficient speaker\', \'Outstanding speaker\']",',
        '"feedback_summary": "[Concise feedback summarizing the speaker\'s strengths and areas for improvement based on rubric.]"', 
        "}",
        "DO NOT include anything outside the JSON response.",
        "Ensure all keys and values are properly quoted and formatted.",
        "The response MUST be in proper JSON format with keys and values in double quotes.",
        "The final response MUST not include any other text or anything else other than the JSON response."
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