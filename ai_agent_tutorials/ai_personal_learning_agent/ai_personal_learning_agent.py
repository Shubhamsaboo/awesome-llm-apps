import streamlit as st
from phi.agent import Agent, RunResponse
from phi.model.openai import OpenAIChat
from composio_phidata import Action, ComposioToolSet
import os
from phi.tools.arxiv_toolkit import ArxivToolkit
from phi.utils.pprint import pprint_run_response
from phi.tools.duckduckgo import DuckDuckGo

# Set page configuration
st.set_page_config(page_title="Learning Path Generator", layout="centered")

# Initialize session state for API keys and topic
if 'openai_api_key' not in st.session_state:
    st.session_state['openai_api_key'] = ''
if 'composio_api_key' not in st.session_state:
    st.session_state['composio_api_key'] = ''
if 'topic' not in st.session_state:
    st.session_state['topic'] = ''

# Streamlit sidebar for API keys
with st.sidebar:
    st.title("API Keys Configuration")
    st.session_state['openai_api_key'] = st.text_input("Enter your OpenAI API Key", type="password").strip()
    st.session_state['composio_api_key'] = st.text_input("Enter your Composio API Key", type="password").strip()
    
    # Add info about terminal responses
    st.info("Note: You can also view detailed agent responses\nin your terminal after execution.")

# Validate API keys
if not st.session_state['openai_api_key'] or not st.session_state['composio_api_key']:
    st.error("Please enter both OpenAI and Composio API keys in the sidebar.")
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

# Create the KnowledgeBuilder agent
knowledge_agent = Agent(
    name="KnowledgeBuilder",
    role="Research and Knowledge Specialist", 
    model=OpenAIChat(id="gpt-4o", api_key=st.session_state['openai_api_key']),
    tools=[google_docs_tool],
    instructions=[
        "Create a comprehensive knowledge base that covers fundamental concepts, advanced topics, and current developments of the given topic.",
        "Include key terminology, core principles, and practical applications and make it as a detailed report that anyone who's starting out can read and get maximum value out of it.",
        "Make sure it is formatted in a way that is easy to read and understand. DONT FORGET TO CREATE THE GOOGLE DOCUMENT.",
        "Open a new Google Doc and write down the response of the agent neatly with great formatting and structure in it. **Include the Google Doc link in your response.**",
    ],
    show_tool_calls=True,
    markdown=True,
)

# Create the RoadmapArchitect agent
roadmap_agent = Agent(
    name="RoadmapArchitect",
    role="Learning Path Designer",
    model=OpenAIChat(id="gpt-4o", api_key=st.session_state['openai_api_key']),
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

# Create the ResourceCurator agent
resource_agent = Agent(
    name="ResourceCurator",
    role="Learning Resource Specialist",
    model=OpenAIChat(id="gpt-4o", api_key=st.session_state['openai_api_key']),
    tools=[google_docs_tool, ArxivToolkit(), DuckDuckGo(fixed_max_results=10)],
    instructions=[
        "Find and validate high-quality learning resources for the given topic.",
        "Use the DuckDuckGo search tool to find current and relevant learning materials.",
        "Include technical blogs, GitHub repositories, official documentation, video tutorials, and courses.",
        "Verify the credibility and relevance of each resource.",
        "Present the resources in a curated list with descriptions and quality assessments. DONT FORGET TO CREATE THE GOOGLE DOCUMENT.",
        "Open a new Google Doc and write down the response of the agent neatly with great formatting and structure in it. **Include the Google Doc link in your response.**",
    ],
    show_tool_calls=True,
    markdown=True,
)

# Create the PracticeDesigner agent
practice_agent = Agent(
    name="PracticeDesigner",
    role="Exercise Creator",
    model=OpenAIChat(id="gpt-4o", api_key=st.session_state['openai_api_key']),
    tools=[google_docs_tool, DuckDuckGo(fixed_max_results=10)],
    instructions=[
        "Create comprehensive practice materials for the given topic.",
        "Use the DuckDuckGo search tool to find example problems and real-world applications.",
        "Include progressive exercises, quizzes, hands-on projects, and real-world application scenarios.",
        "Ensure the materials align with the roadmap progression.",
        "Provide detailed solutions and explanations for all practice materials.DONT FORGET TO CREATE THE GOOGLE DOCUMENT.",
        "Open a new Google Doc and write down the response of the agent neatly with great formatting and structure in it. **Include the Google Doc link in your response.**",
    ],
    show_tool_calls=True,
    markdown=True,
)

# Streamlit main UI
st.title("AI Learning Roadmap Agent")
st.markdown("Enter a topic to generate a detailed learning path and resources")

# Add info message about Google Docs
st.info("📝 The agents will create detailed Google Docs for each section (Knowledge Base, Learning Roadmap, Resources, and Practice Materials). The links to these documents will be displayed below after processing.")

# Query bar for topic input
st.session_state['topic'] = st.text_input("Enter the topic you want to learn about:", placeholder="e.g., Machine Learning, LoRA, etc.")

# Start button
if st.button("Start"):
    if not st.session_state['topic']:
        st.error("Please enter a topic.")
    else:
        # Display loading animations while generating responses
        with st.spinner("Generating Knowledge Base..."):
            knowledge_response: RunResponse = knowledge_agent.run(
                f"the topic is: {st.session_state['topic']},Don't forget to add the Google Doc link in your response.",
                stream=False
            )
            
        with st.spinner("Generating Learning Roadmap..."):
            roadmap_response: RunResponse = roadmap_agent.run(
                f"the topic is: {st.session_state['topic']},Don't forget to add the Google Doc link in your response.",
                stream=False
            )
            
        with st.spinner("Curating Learning Resources..."):
            resource_response: RunResponse = resource_agent.run(
                f"the topic is: {st.session_state['topic']},Don't forget to add the Google Doc link in your response.",
                stream=False
            )
            
        with st.spinner("Creating Practice Materials..."):
            practice_response: RunResponse = practice_agent.run(
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

        knowledge_doc_link = extract_google_doc_link(knowledge_response.content)
        roadmap_doc_link = extract_google_doc_link(roadmap_response.content)
        resource_doc_link = extract_google_doc_link(resource_response.content)
        practice_doc_link = extract_google_doc_link(practice_response.content)

        # Display Google Doc links at the top of the Streamlit UI
        st.markdown("### Google Doc Links:")
        if knowledge_doc_link:
            st.markdown(f"- **KnowledgeBuilder Document:** [View Document](https://docs.google.com{knowledge_doc_link})")
        if roadmap_doc_link:
            st.markdown(f"- **RoadmapArchitect Document:** [View Document](https://docs.google.com{roadmap_doc_link})")
        if resource_doc_link:
            st.markdown(f"- **ResourceCurator Document:** [View Document](https://docs.google.com{resource_doc_link})")
        if practice_doc_link:
            st.markdown(f"- **PracticeDesigner Document:** [View Document](https://docs.google.com{practice_doc_link})")

        # Display responses in the Streamlit UI using pprint_run_response
        st.markdown("### KnowledgeBuilder Response:")
        st.markdown(knowledge_response.content)
        pprint_run_response(knowledge_response, markdown=True)
        st.divider()
        st.markdown("### RoadmapArchitect Response:")
        st.markdown(roadmap_response.content)
        pprint_run_response(roadmap_response, markdown=True)
        st.divider()

        st.markdown("### ResourceCurator Response:")
        st.markdown(resource_response.content)
        pprint_run_response(resource_response, markdown=True)
        st.divider()

        st.markdown("### PracticeDesigner Response:")
        st.markdown(practice_response.content)
        pprint_run_response(practice_response, markdown=True)
        st.divider()
# Information about the agents
st.markdown("---")
st.markdown("### About the Agents:")
st.markdown("""
- **KnowledgeBuilder**: Researches the topic and creates a detailed knowledge base.
- **RoadmapArchitect**: Designs a structured learning roadmap for the topic.
- **ResourceCurator**: Curates high-quality learning resources.
- **PracticeDesigner**: Creates practice materials, exercises, and projects.
""")