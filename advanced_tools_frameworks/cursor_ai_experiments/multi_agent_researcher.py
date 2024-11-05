import streamlit as st
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
import os

# Initialize the GPT-4 model
gpt4_model = None

def create_article_crew(topic):
    # Create agents
    researcher = Agent(
        role='Researcher',
        goal='Conduct thorough research on the given topic',
        backstory='You are an expert researcher with a keen eye for detail',
        verbose=True,
        allow_delegation=False,
        llm=gpt4_model
    )

    writer = Agent(
        role='Writer',
        goal='Write a detailed and engaging article based on the research, using proper markdown formatting',
        backstory='You are a skilled writer with expertise in creating informative content and formatting it beautifully in markdown',
        verbose=True,
        allow_delegation=False,
        llm=gpt4_model
    )

    editor = Agent(
        role='Editor',
        goal='Review and refine the article for clarity, accuracy, engagement, and proper markdown formatting',
        backstory='You are an experienced editor with a sharp eye for quality content and excellent markdown structure',
        verbose=True,
        allow_delegation=False,
        llm=gpt4_model
    )

    # Create tasks
    research_task = Task(
        description=f"Conduct comprehensive research on the topic: {topic}. Gather key information, statistics, and expert opinions.",
        agent=researcher,
        expected_output="A comprehensive research report on the given topic, including key information, statistics, and expert opinions."
    )

    writing_task = Task(
        description="""Using the research provided, write a detailed and engaging article. 
        Ensure proper structure, flow, and clarity. Format the article using markdown, including:
        1. A main title (H1)
        2. Section headings (H2)
        3. Subsection headings where appropriate (H3)
        4. Bullet points or numbered lists where relevant
        5. Emphasis on key points using bold or italic text
        Make sure the content is well-organized and easy to read.""",
        agent=writer,
        expected_output="A well-structured, detailed, and engaging article based on the provided research, formatted in markdown with proper headings and subheadings."
    )

    editing_task = Task(
        description="""Review the article for clarity, accuracy, engagement, and proper markdown formatting. 
        Ensure that:
        1. The markdown formatting is correct and consistent
        2. Headings and subheadings are used appropriately
        3. The content flow is logical and engaging
        4. Key points are emphasized correctly
        Make necessary edits and improvements to both content and formatting.""",
        agent=editor,
        expected_output="A final, polished version of the article with improved clarity, accuracy, engagement, and proper markdown formatting."
    )

    # Create the crew
    crew = Crew(
        agents=[researcher, writer, editor],
        tasks=[research_task, writing_task, editing_task],
        verbose=2,
        process=Process.sequential
    )

    return crew

# Streamlit app
st.set_page_config(page_title="Multi Agent AI Researcher", page_icon="📝")

# Custom CSS for better appearance
st.markdown("""
    <style>
    .stApp {
        max-width: 1800px;
        margin: 0 auto;
        font-family: Arial, sans-serif;
    }
    .st-bw {
        background-color: #f0f2f6;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
    }
    .stTextInput>div>div>input {
        background-color: #ffffff;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📝 Multi Agent AI Researcher")

# Sidebar for API key input
with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("Enter your OpenAI API Key:", type="password")
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
        gpt4_model = ChatOpenAI(model_name="gpt-4o-mini")
        st.success("API Key set successfully!")
    else:
        st.info("Please enter your OpenAI API Key to proceed.")

# Main content
st.markdown("Generate detailed articles on any topic using AI agents!")

topic = st.text_input("Enter the topic for the article:", placeholder="e.g., The Impact of Artificial Intelligence on Healthcare")

if st.button("Generate Article"):
    if not api_key:
        st.error("Please enter your OpenAI API Key in the sidebar.")
    elif not topic:
        st.warning("Please enter a topic for the article.")
    else:
        with st.spinner("🤖 AI agents are working on your article..."):
            crew = create_article_crew(topic)
            result = crew.kickoff()
            st.markdown(result)

st.markdown("---")
st.markdown("Powered by CrewAI and OpenAI :heart:")