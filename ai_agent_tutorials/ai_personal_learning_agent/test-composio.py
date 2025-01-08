import streamlit as st
from phi.agent import Agent, RunResponse
from phi.model.openai import OpenAIChat
from composio_phidata import Action, ComposioToolSet
import os

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

# Validate API keys
if not st.session_state['openai_api_key'] or not st.session_state['composio_api_key']:
    st.error("Please enter both OpenAI and Composio API keys in the sidebar.")
    st.stop()

# Set the OpenAI API key and Composio API key from session state
os.environ["OPENAI_API_KEY"] = st.session_state['openai_api_key']

try:
    composio_toolset = ComposioToolSet(api_key=st.session_state['composio_api_key'])
    google_docs_tool = composio_toolset.get_tools(actions=[Action.GOOGLEDOCS_CREATE_DOCUMENT])[0]
except Exception as e:
    st.error(f"Error initializing ComposioToolSet: {e}")
    st.stop()

# Create the KnowledgeBuilder agent
knowledge_agent = Agent(
    name="KnowledgeBuilder",
    role="Research and Knowledge Specialist",
    model=OpenAIChat(id="gpt-4o"),
    tools=[google_docs_tool],
    instructions=[
        "Research the given topic thoroughly using internet sources.",
        "Create a comprehensive knowledge base that covers fundamental concepts, advanced topics, and current developments.",
        "Include key terminology, core principles, and practical applications and make it as a detailed report that anyone who's starting out can read and get maximum value out of it.",
        "Always include sources and citations for your findings.",
        "Open a new Google Doc and write down the response of the agent in it.",
    ],
    show_tool_calls=True,
    markdown=True,
)

# Create the RoadmapArchitect agent
roadmap_agent = Agent(
    name="RoadmapArchitect",
    role="Learning Path Designer",
    model=OpenAIChat(id="gpt-4o"),
    tools=[google_docs_tool],
    instructions=[
        "Using the knowledge base for the given topic, create a detailed learning roadmap.",
        "Break down the topic into logical subtopics and arrange them in order of progression, a detailed report of roadmap that includes all the subtopics in order to be an expert in this topic.",
        "Include estimated time commitments for each section.",
        "Present the roadmap in a clear, structured format.",
        "Open a new Google Doc and write down the response of the agent in it.",
    ],
    show_tool_calls=True,
    markdown=True,
)

# Create the ResourceCurator agent
resource_agent = Agent(
    name="ResourceCurator",
    role="Learning Resource Specialist",
    model=OpenAIChat(id="gpt-4o"),
    tools=[google_docs_tool],
    instructions=[
        "Find and validate high-quality learning resources for the given topic.",
        "Include technical blogs, GitHub repositories, official documentation, video tutorials, and courses.",
        "Verify the credibility and relevance of each resource.",
        "Present the resources in a curated list with descriptions and quality assessments.",
        "Open a new Google Doc and write down the response of the agent in it.",
    ],
    show_tool_calls=True,
    markdown=True,
)

# Create the PracticeDesigner agent
practice_agent = Agent(
    name="PracticeDesigner",
    role="Exercise Creator",
    model=OpenAIChat(id="gpt-4o"),
    tools=[google_docs_tool],
    instructions=[
        "Create comprehensive practice materials for the given topic.",
        "Include progressive exercises, quizzes, hands-on projects, and real-world application scenarios.",
        "Ensure the materials align with the roadmap progression.",
        "Provide detailed solutions and explanations for all practice materials.",
        "Open a new Google Doc and write down the response of the agent in it.",
    ],
    show_tool_calls=True,
    markdown=True,
)

# Streamlit main UI
st.title("Learning Path and Resource Generator")
st.markdown("Enter a topic to generate a detailed learning path and resources")

# Query bar for topic input
st.session_state['topic'] = st.text_input("Enter the topic you want to learn about:", placeholder="e.g., Machine Learning, LoRA, etc.")

# Start button
if st.button("Start"):
    if not st.session_state['topic']:
        st.error("Please enter a topic.")
    else:
        # Display loading animations while generating responses
        with st.spinner("Generating Knowledge Base..."):
            knowledge_response = knowledge_agent.run(
                f"Create a comprehensive knowledge base for the topic: {st.session_state['topic']}"
            )
        with st.spinner("Generating Learning Roadmap..."):
            roadmap_response = roadmap_agent.run(
                f"Create a detailed learning roadmap for the topic: {st.session_state['topic']}"
            )
        with st.spinner("Curating Learning Resources..."):
            resource_response = resource_agent.run(
                f"Curate high-quality learning resources for the topic: {st.session_state['topic']}"
            )
        with st.spinner("Creating Practice Materials..."):
            practice_response = practice_agent.run(
                f"Create comprehensive practice materials for the topic: {st.session_state['topic']}"
            )

        # Display responses with Google Doc links in Streamlit UI
        st.markdown("### KnowledgeBuilder Response:")
        st.write(knowledge_response.content)  # Use `message` instead of `content`
        if hasattr(knowledge_response, 'tool_calls') and knowledge_response.tool_calls:
            st.markdown(f"**Google Doc Link:** [View Document]({knowledge_response.tool_calls[0].result})")

        st.markdown("### RoadmapArchitect Response:")
        st.write(roadmap_response.content)  # Use `message` instead of `content`
        if hasattr(roadmap_response, 'tool_calls') and roadmap_response.tool_calls:
            st.markdown(f"**Google Doc Link:** [View Document]({roadmap_response.tool_calls[0].result})")

        st.markdown("### ResourceCurator Response:")
        st.write(resource_response.content)  # Use `message` instead of `content`
        if hasattr(resource_response, 'tool_calls') and resource_response.tool_calls:
            st.markdown(f"**Google Doc Link:** [View Document]({resource_response.tool_calls[0].result})")

        st.markdown("### PracticeDesigner Response:")
        st.write(practice_response.content)  # Use `message` instead of `content`
        if hasattr(practice_response, 'tool_calls') and practice_response.tool_calls:
            st.markdown(f"**Google Doc Link:** [View Document]({practice_response.tool_calls[0].result})")

        # Print responses to the terminal
        print("\n\n--- KnowledgeBuilder Response ---")
        print(knowledge_response.content)
        if hasattr(knowledge_response, 'tool_calls') and knowledge_response.tool_calls:
            print(f"Google Doc Link: {knowledge_response.tool_calls[0].result}")

        print("\n\n--- RoadmapArchitect Response ---")
        print(roadmap_response.content)
        if hasattr(roadmap_response, 'tool_calls') and roadmap_response.tool_calls:
            print(f"Google Doc Link: {roadmap_response.tool_calls[0].result}")

        print("\n\n--- ResourceCurator Response ---")
        print(resource_response.content)
        if hasattr(resource_response, 'tool_calls') and resource_response.tool_calls:
            print(f"Google Doc Link: {resource_response.tool_calls[0].result}")

        print("\n\n--- PracticeDesigner Response ---")
        print(practice_response.content)
        if hasattr(practice_response, 'tool_calls') and practice_response.tool_calls:
            print(f"Google Doc Link: {practice_response.tool_calls[0].result}")

# Information about the agents
st.markdown("---")
st.markdown("### About the Agents:")
st.markdown("""
- **KnowledgeBuilder**: Researches the topic and creates a detailed knowledge base.
- **RoadmapArchitect**: Designs a structured learning roadmap for the topic.
- **ResourceCurator**: Curates high-quality learning resources.
- **PracticeDesigner**: Creates practice materials, exercises, and projects.
""")

