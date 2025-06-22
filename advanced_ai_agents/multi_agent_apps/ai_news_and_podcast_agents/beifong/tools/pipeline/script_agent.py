from agno.agent import Agent
from agno.models.openai import OpenAIChat
from pydantic import BaseModel, Field
from typing import List, Optional
from dotenv import load_dotenv
from textwrap import dedent
from datetime import datetime
import uuid

load_dotenv()


class Dialog(BaseModel):
    speaker: str = Field(..., description="The speaker name (SHOULD BE 'ALEX' OR 'MORGAN')")
    text: str = Field(
        ...,
        description="The spoken text content for this speaker based on the requested langauge, default is English",
    )


class Section(BaseModel):
    type: str = Field(..., description="The section type (intro, headlines, article, outro)")
    title: Optional[str] = Field(None, description="Optional title for the section (required for article type)")
    dialog: List[Dialog] = Field(..., description="List of dialog exchanges between speakers")


class PodcastScript(BaseModel):
    title: str = Field(..., description="The podcast episode title with date")
    sections: List[Section] = Field(..., description="List of podcast sections (intro, headlines, articles, outro)")


PODCAST_AGENT_DESCRIPTION = "You are a helpful assistant that can generate engaging podcast scripts for the given sources."
PODCAST_AGENT_INSTRUCTIONS = dedent("""
    You are a helpful assistant that can generate engaging podcast scripts for the given source content and query.
    For given content, create an engaging podcast script that should be at least 15 minutes worth of content and your allowed enhance the script beyond given sources if you know something additional info will be interesting to the discussion or not enough conents available.
    You use the provided sources to ground your podcast script generation process. Keep it engaging and interesting.
    
    IMPORTANT: Generate the entire script in the provided language. basically only text field needs to be in requested language,
    
    CONTENT GUIDELINES [THIS IS EXAMPLE YOU CAN CHANGE THE GUIDELINES ANYWAY BASED ON THE QUERY OR TOPIC DISCUSSED]:
    - Provide insightful analysis that helps the audience understand the significance
    - Include discussions on potential implications and broader context of each story
    - Explain complex concepts in an accessible but thorough manner
    - Make connections between current and relevant historical developments when applicable
    - Provide comparisons and contrasts with similar stories or trends when relevant
    
    PERSONALITY NOTES [THIS IS EXAMPLE YOU CAN CHANGE THE PERSONALITY OF ALEX AND MORGAN ANYWAY BASED ON THE QUERY OR TOPIC DISCUSSED]:
    - Alex is more analytical and fact-focused
    * Should reference specific details and data points
    * Should explain complex topics clearly
    * Should identify key implications of stories
    - Morgan is more focused on human impact, social context, and practical applications
    * Should analyze broader implications
    * Should consider ethical implications and real-world applications
    - Include natural, conversational banter and smooth transitions between topics
    - Each article discussion should go beyond the basic summary to provide valuable insights
    - Maintain a conversational but informed tone that would appeal to a general audience
    
    IMPORTNAT:
        - MAKE SURE PODCAST SCRIPS ARE AT LEAST 15 MINUTES LONG WHICH MEANS YOU NEED TO HAVE DETAILED DISCUSSIONS OFFCOURSE KEEP IT INTERESTING AND ENGAGING.
    """)


def format_search_results_for_podcast(
    search_results: List[dict],
) -> tuple[str, List[str]]:
    created_at = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    structured_content = []
    structured_content.append(f"PODCAST CREATION: {created_at}\n")
    sources = []
    for idx, search_result in enumerate(search_results):
        try:
            if search_result.get("confirmed", False):
                sources.append(search_result["url"])
                structured_content.append(
                    f"""
                                        SOURCE {idx + 1}:
                                        Title: {search_result['title']}
                                        URL: {search_result['url']}
                                        Content: {search_result.get('full_text') or search_result.get('description', '')}
                                        ---END OF SOURCE {idx + 1}---
                                        """.strip()
                )
        except Exception as e:
            print(f"Error processing search result: {e}")
    content_texts = "\n\n".join(structured_content)
    return content_texts, sources


def script_agent_run(
    query: str,
    search_results: List[dict],
    language_name: str,
) -> str:
    try:
        session_id = str(uuid.uuid4())
        content_texts, sources = format_search_results_for_podcast(search_results)
        if not content_texts:
            return {}
        podcast_script_agent = Agent(
            model=OpenAIChat(id="gpt-4o-mini"),
            instructions=PODCAST_AGENT_INSTRUCTIONS,
            description=PODCAST_AGENT_DESCRIPTION,
            use_json_mode=True,
            response_model=PodcastScript,
            session_id=session_id,
        )
        response = podcast_script_agent.run(
            f"query: {query}\n language_name: {language_name}\n content_texts: {content_texts}\n, IMPORTANT: texts should be in {language_name} language.",
            session_id=session_id,
        )
        response_dict = response.to_dict()
        response_dict = response_dict["content"]
        response_dict["sources"] = sources
        return response_dict
    except Exception as _:
        import traceback

        traceback.print_exc()
        return {}