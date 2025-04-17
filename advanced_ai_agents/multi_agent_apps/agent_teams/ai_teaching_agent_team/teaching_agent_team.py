import streamlit as st
from agno.agent import Agent, RunResponse
from agno.models.openai import OpenAIChat
from composio_phidata import Action, ComposioToolSet
import os
from agno.tools.arxiv import ArxivTools
from agno.utils.pprint import pprint_run_response
from agno.tools.serpapi import SerpApiTools

# Set page configuration
st.set_page_config(page_title="👨‍🏫 AI Teaching Agent Team", layout="centered")

# Initialize session state for API keys and topic
if 'openai_api_key' not in st.session_state:
    st.session_state['openai_api_key'] = ''
if 'composio_api_key' not in st.session_state:
    st.session_state['composio_api_key'] = ''
if 'serpapi_api_key' not in st.session_state:
    st.session_state['serpapi_api_key'] = ''
if 'topic' not in st.session_state:
    st.session_state['topic'] = ''

# Streamlit sidebar for API keys
with st.sidebar:
    st.title("API Keys Configuration")
    st.session_state['openai_api_key'] = st.text_input("Enter your OpenAI API Key", type="password").strip()
    st.session_state['composio_api_key'] = st.text_input("Enter your Composio API Key", type="password").strip()
    st.session_state['serpapi_api_key'] = st.text_input("Enter your SerpAPI Key", type="password").strip()
    
    # Add info about terminal responses
    st.info("Note: You can also view detailed agent responses\nin your terminal after execution.")

# Validate API keys
if not st.session_state['openai_api_key'] or not st.session_state['composio_api_key'] or not st.session_state['serpapi_api_key']:
    st.error("Please enter OpenAI, Composio, and SerpAPI keys in the sidebar.")
    st.stop()

# Set the OpenAI API key and Composio API key from session state
os.environ["OPENAI_API_KEY"] = st.session_state['openai_api_key']

try:
    composio_toolset = ComposioToolSet(api_key=st.session_state['composio_api_key'])
    google_docs_tool = composio_toolset.get_tools(actions=[Action.GOOGLEDOCS_CREATE_DOCUMENT])[0]
    google_docs_tool_update = composio_toolset.get_tools(actions=[Action.GOOGLEDOCS_UPDATE_EXISTING_DOCUMENT])[0]
except Exception as e:
    st.error(f"Error initializing ComposioToolSet: {e}")
    st.stop()

# Create the Professor agent (formerly KnowledgeBuilder)
professor_agent = Agent(
    name="Professor",
    role="Research and Knowledge Specialist", 
    model=OpenAIChat(id="gpt-4o-mini", api_key=st.session_state['openai_api_key']),
    tools=[google_docs_tool],
    instructions=[
        "Create a comprehensive knowledge base that covers fundamental concepts, advanced topics, and current developments of the given topic.",
        "Exlain the topic from first principles first. Include key terminology, core principles, and practical applications and make it as a detailed report that anyone who's starting out can read and get maximum value out of it.",
        "Make sure it is formatted in a way that is easy to read and understand. DONT FORGET TO CREATE THE GOOGLE DOCUMENT.",
        "Open a new Google Doc and write down the response of the agent neatly with great formatting and structure in it. **Include the Google Doc link in your response.**",
    ],
    show_tool_calls=True,
    markdown=True,
)

# Create the Academic Advisor agent (formerly RoadmapArchitect)
academic_advisor_agent = Agent(
    name="Academic Advisor",
    role="Learning Path Designer",
    model=OpenAIChat(id="gpt-4o-mini", api_key=st.session_state['openai_api_key']),
    tools=[google_docs_tool],
    instructions=[
        "Using the knowledge base for the given topic, create a detailed learning roadmap.",
        "Break down the topic into logical subtopics and arrange them in order of progression, a detailed report of roadmap that includes all the subtopics in order to be an expert in this topic.",
        "Include estimated time commitments for each section.",
        "Present the roadmap in a clear, structured format. DONT FORGET TO CREATE THE GOOGLE DOCUMENT.",
        "Open a new Google Doc and write down the response of the agent neatly with great formatting and structure in it. **Include the Google Doc link in your response.**",

    ],
    show_tool_calls=True,
    markdown=True
)

# Create the Research Librarian agent (formerly ResourceCurator)
research_librarian_agent = Agent(
    name="Research Librarian",
    role="Learning Resource Specialist",
    model=OpenAIChat(id="gpt-4o-mini", api_key=st.session_state['openai_api_key']),
    tools=[google_docs_tool, SerpApiTools(api_key=st.session_state['serpapi_api_key']) ],
    instructions=[
        "Make a list of high-quality learning resources for the given topic.",
        "Use the SerpApi search tool to find current and relevant learning materials.",
        "Using SerpApi search tool, Include technical blogs, GitHub repositories, official documentation, video tutorials, and courses.",
        "Present the resources in a curated list with descriptions and quality assessments. DONT FORGET TO CREATE THE GOOGLE DOCUMENT.",
        "Open a new Google Doc and write down the response of the agent neatly with great formatting and structure in it. **Include the Google Doc link in your response.**",
    ],
    show_tool_calls=True,
    markdown=True,
)

# Create the Teaching Assistant agent (formerly PracticeDesigner)
teaching_assistant_agent = Agent(
    name="Teaching Assistant",
    role="Exercise Creator",
    model=OpenAIChat(id="gpt-4o-mini", api_key=st.session_state['openai_api_key']),
    tools=[google_docs_tool, SerpApiTools(api_key=st.session_state['serpapi_api_key'])],
    instructions=[
        "Create comprehensive practice materials for the given topic.",
        "Use the SerpApi search tool to find example problems and real-world applications.",
        "Include progressive exercises, quizzes, hands-on projects, and real-world application scenarios.",
        "Ensure the materials align with the roadmap progression.",
        "Provide detailed solutions and explanations for all practice materials.DONT FORGET TO CREATE THE GOOGLE DOCUMENT.",
        "Open a new Google Doc and write down the response of the agent neatly with great formatting and structure in it. **Include the Google Doc link in your response.**",
    ],
    show_tool_calls=True,
    markdown=True,
)

# Streamlit main UI
st.title("👨‍🏫 AI Teaching Agent Team")
st.markdown("Enter a topic to generate a detailed learning path and resources")

# Add info message about Google Docs
st.info("📝 The agents will create detailed Google Docs for each section (Professor, Academic Advisor, Research Librarian, and Teaching Assistant). The links to these documents will be displayed below after processing.")

# Query bar for topic input
st.session_state['topic'] = st.text_input("Enter the topic you want to learn about:", placeholder="e.g., Machine Learning, LoRA, etc.")

# Start button
if st.button("Start"):
    if not st.session_state['topic']:
        st.error("Please enter a topic.")
    else:
        # Display loading animations while generating responses
        with st.spinner("Generating Knowledge Base..."):
            professor_response: RunResponse = professor_agent.run(
                f"the topic is: {st.session_state['topic']},Don't forget to add the Google Doc link in your response.",
                stream=False
            )
            
        with st.spinner("Generating Learning Roadmap..."):
            academic_advisor_response: RunResponse = academic_advisor_agent.run(
                f"the topic is: {st.session_state['topic']},Don't forget to add the Google Doc link in your response.",
                stream=False
            )
            
        with st.spinner("Curating Learning Resources..."):
            research_librarian_response: RunResponse = research_librarian_agent.run(
                f"the topic is: {st.session_state['topic']},Don't forget to add the Google Doc link in your response.",
                stream=False
            )
            
        with st.spinner("Creating Practice Materials..."):
            teaching_assistant_response: RunResponse = teaching_assistant_agent.run(
                f"the topic is: {st.session_state['topic']},Don't forget to add the Google Doc link in your response.",
                stream=False
            )

        # Extract Google Doc links from the responses
        def extract_google_doc_link(response_content):
            # Assuming the Google Doc link is embedded in the response content
            # You may need to adjust this logic based on the actual response format
            if "https://docs.google.com" in response_content:
                return response_content.split("https://docs.google.com")[1].split()[0]
            return None

        professor_doc_link = extract_google_doc_link(professor_response.content)
        academic_advisor_doc_link = extract_google_doc_link(academic_advisor_response.content)
        research_librarian_doc_link = extract_google_doc_link(research_librarian_response.content)
        teaching_assistant_doc_link = extract_google_doc_link(teaching_assistant_response.content)

        # Display Google Doc links at the top of the Streamlit UI
        st.markdown("### Google Doc Links:")
        if professor_doc_link:
            st.markdown(f"- **Professor Document:** [View Document](https://docs.google.com{professor_doc_link})")
        if academic_advisor_doc_link:
            st.markdown(f"- **Academic Advisor Document:** [View Document](https://docs.google.com{academic_advisor_doc_link})")
        if research_librarian_doc_link:
            st.markdown(f"- **Research Librarian Document:** [View Document](https://docs.google.com{research_librarian_doc_link})")
        if teaching_assistant_doc_link:
            st.markdown(f"- **Teaching Assistant Document:** [View Document](https://docs.google.com{teaching_assistant_doc_link})")

        # Display responses in the Streamlit UI using pprint_run_response
        st.markdown("### Professor Response:")
        st.markdown(professor_response.content)
        pprint_run_response(professor_response, markdown=True)
        st.divider()
        
        st.markdown("### Academic Advisor Response:")
        st.markdown(academic_advisor_response.content)
        pprint_run_response(academic_advisor_response, markdown=True)
        st.divider()

        st.markdown("### Research Librarian Response:")
        st.markdown(research_librarian_response.content)
        pprint_run_response(research_librarian_response, markdown=True)
        st.divider()

        st.markdown("### Teaching Assistant Response:")
        st.markdown(teaching_assistant_response.content)
        pprint_run_response(teaching_assistant_response, markdown=True)
        st.divider()
# Information about the agents
st.markdown("---")
st.markdown("### About the Agents:")
st.markdown("""
- **Professor**: Researches the topic and creates a detailed knowledge base.
- **Academic Advisor**: Designs a structured learning roadmap for the topic.
- **Research Librarian**: Curates high-quality learning resources.
- **Teaching Assistant**: Creates practice materials, exercises, and projects.
""")
