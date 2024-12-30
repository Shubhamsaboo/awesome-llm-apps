import typing as t
import os
import sys
import io
from typing import Generator, Any
from datetime import datetime
import subprocess
import streamlit as st
from duckduckgo_search import DDGS
from openai import OpenAI

# Initialize session state
if "OPENAI_API_KEY" not in st.session_state:
    st.session_state.OPENAI_API_KEY = None
    
if "agents" not in st.session_state:
    st.session_state.agents = None

# Add a session state variable to store terminal output
if "terminal_output" not in st.session_state:
    st.session_state.terminal_output = ""

def setup_sidebar() -> None:
    """Configure the Streamlit sidebar with API key input."""
    with st.sidebar:
        st.title("Configuration")
        api_key = st.text_input("OpenAI API Key", type="password")
        if api_key:
            st.session_state.OPENAI_API_KEY = api_key
            # Set environment variable before any PraisonAI imports
            os.environ["OPENAI_API_KEY"] = api_key

# Only import PraisonAI-related modules after environment variable is set
def get_praisonai_imports():
    """Import PraisonAI modules after environment variable is set.
    
    Returns:
        tuple: (Agent, Task, PraisonAIAgents, BaseTool) classes
    """
    from praisonaiagents import Agent, Task, PraisonAIAgents
    from praisonai_tools import BaseTool
    return Agent, Task, PraisonAIAgents, BaseTool

class InternetSearchTool:
    """Placeholder class that will be properly initialized after imports."""
    pass

def initialize_agents(api_key: str) -> None:
    """Initialize agents with the provided API key.
    
    Args:
        api_key: OpenAI API key to use for the agents
    """
    if st.session_state.agents is None:
        try:
            # Import PraisonAI modules only after API key is set
            Agent, Task, PraisonAIAgents, BaseTool = get_praisonai_imports()
            
            # Now define the actual InternetSearchTool
            class InternetSearchTool(BaseTool):
                name: str = "InternetSearchTool"
                description: str = "Search Internet for relevant information"

                def _run(self, query: str) -> list:
                    ddgs = DDGS()
                    results = ddgs.text(keywords=query, region='wt-wt', safesearch='moderate', max_results=5)
                    return results
            
            # Create agents using the imported classes
            st.session_state.agents = create_agents(api_key, Agent, InternetSearchTool)
        except Exception as e:
            st.error(f"Failed to initialize agents: {str(e)}")
            return None

def create_agents(api_key: str, Agent: type, InternetSearchTool: type) -> tuple:
    """Create and return agent instances with the provided API key.
    
    Args:
        api_key: OpenAI API key to use for the agents
        Agent: The Agent class from PraisonAI
        InternetSearchTool: The InternetSearchTool class
        
    Returns:
        tuple: Tuple of agent instances
    """
    # Set the API key in environment for praisonaiagents
    os.environ["OPENAI_API_KEY"] = api_key
    
    knowledge_agent = Agent(
        name="KnowledgeBuilder",
        role="Research and Knowledge Specialist",
        goal="Create comprehensive knowledge base from internet research",
        backstory="""You are an expert researcher who excels at gathering, analyzing, 
        and organizing information from various internet sources on a given topic.""",
        verbose=True,
        llm="gpt-4o",
        tools=[InternetSearchTool()],
        markdown=True
    )
    
    roadmap_agent = Agent(
        name="RoadmapArchitect",
        role="Learning Path Designer",
        goal="Create detailed hierarchical learning roadmaps",
        backstory="""You are a curriculum design expert who specializes in creating 
        clear, structured learning paths.""",
        llm="gpt-4o",
        tools=[],
        markdown=True
    )
    
    resource_agent = Agent(
        name="ResourceCurator",
        role="Learning Resource Specialist",
        goal="Find and validate high-quality learning resources",
        backstory="""You are an expert at finding and validating educational resources.""",
        llm="gpt-4o",
        tools=[InternetSearchTool()],
        markdown=True
    )
    
    practice_agent = Agent(
        name="PracticeDesigner",
        role="Exercise Creator",
        goal="Create comprehensive practice materials",
        backstory="""You create engaging exercises and interview questions that reinforce 
        learning.""",
        llm="gpt-4o",
        tools=[],
        markdown=True
    )
    
    return knowledge_agent, roadmap_agent, resource_agent, practice_agent

def create_tasks(topic: str, agents: tuple) -> list:
    """Create tasks for the learning system.
    
    Args:
        topic: The learning topic to create tasks for
        agents: Tuple of (knowledge_agent, roadmap_agent, resource_agent, practice_agent)
        
    Returns:
        List of Task objects
    """
    # Import PraisonAI modules
    Agent, Task, PraisonAIAgents, BaseTool = get_praisonai_imports()
    
    knowledge_agent, roadmap_agent, resource_agent, practice_agent = agents
    
    return [
        Task(
            name="knowledge_base_creation",
            description=f"""Research {topic} thoroughly using internet sources. Create a comprehensive 
            knowledge base that covers fundamental concepts, advanced topics, and current developments. 
            Include key terminology, core principles, and practical applications.""",
            expected_output="Detailed knowledge base with structured information",
            agent=knowledge_agent
        ),
        Task(
            name="learning_roadmap",
            description=f"""Using the knowledge base for {topic}, create a detailed learning 
            roadmap. Break down the topic into logical subtopics, arrange them in order of progression, 
            and include estimated time commitments for each section.""",
            expected_output="Structured roadmap with organized subtopics",
            agent=roadmap_agent
        ),
        Task(
            name="resource_collection",
            description=f"""Find and validate high-quality learning resources for {topic}. Include:
            1. Technical blogs and articles
            2. GitHub repositories with examples and projects
            3. Official documentation and guides
            4. Video tutorials and courses
            Verify the credibility and relevance of each resource.""",
            expected_output="Curated list of validated learning resources",
            agent=resource_agent
        ),
        Task(
            name="practice_material_creation",
            description=f"""Create comprehensive practice materials on the {topic}, including:
            1. Progressive exercises from basic to advanced
            2. Quizzes to test understanding
            3. Hands-on project assignments
            4. Real-world application scenarios
            Ensure materials align with the roadmap progression.""",
            expected_output="Complete set of practice materials and projects",
            agent=practice_agent
        )
    ]

def run_learning_system(topic: str, api_key: str) -> dict:
    """Run the learning system with the provided topic and API key."""
    try:
        if st.session_state.agents is None:
            initialize_agents(api_key)
            
        if st.session_state.agents:
            # Import PraisonAI modules
            Agent, Task, PraisonAIAgents, BaseTool = get_praisonai_imports()
            
            tasks = create_tasks(topic, st.session_state.agents)
            
            # Set up agents system
            agents_system = PraisonAIAgents(
                agents=list(st.session_state.agents),
                tasks=tasks,
                verbose=True,
                process="hierarchical",
                manager_llm="gpt-4o"
            )
            
            # Create a Tee-like object to write to both StringIO and sys.stdout
            class Tee:
                def __init__(self, *files):
                    self.files = files

                def write(self, obj):
                    for f in self.files:
                        f.write(obj)

                def flush(self):
                    for f in self.files:
                        f.flush()

            # Capture terminal output
            old_stdout = sys.stdout
            new_stdout = io.StringIO()
            sys.stdout = Tee(new_stdout, old_stdout)  # Write to both StringIO and terminal
            
            result = agents_system.start()
            
            # Restore stdout and get the captured output
            sys.stdout = old_stdout
            terminal_output = new_stdout.getvalue()
            
            # Store the terminal output in session state
            st.session_state.terminal_output = terminal_output
            
            return result
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return None

def main() -> None:
    """Main Streamlit interface for the learning system."""
    st.title("AI Personal Learning Agent")
    setup_sidebar()
    
    if not st.session_state.OPENAI_API_KEY:
        st.warning("Please enter your OpenAI API key in the sidebar to continue.")
        return
    
    topic = st.text_input("What would you like to learn about?")
    
    # Add info message about terminal output
    st.info("""
        💡 **Real-time Progress Updates**
        - View real-time agent interactions in your terminal window
        - Terminal output will also appear here in the UI once processing is complete
        - Keep your terminal window open to monitor live progress
    """)
    
    if st.button("Generate Learning Plan") and topic:
        with st.spinner(f"Generating learning plan for: {topic}"):
            try:
                # Add the new informative message using st.chat_message
                with st.chat_message("assistant", avatar="🔧"):
                    st.markdown("""
                    **How the output handling works:**
                    The terminal output is displayed both in the Streamlit UI and in the terminal using a tee-like approach. 
                    This means the output is simultaneously written to:
                    - A StringIO buffer (for displaying in this UI later)
                    - The original sys.stdout (for real-time terminal viewing)
                    
                    You can watch the progress in real-time in your terminal, and the complete output will appear here once finished.
                    """)
                
                st.info("🔄 Processing... Check your terminal window for real-time updates!")
                result = run_learning_system(topic, st.session_state.OPENAI_API_KEY)
                if result:
                    st.success("Learning plan generated successfully!")
                    st.json(result)
            except Exception as e:
                st.error(f"Error generating learning plan: {str(e)}")
    elif topic:
        st.info("Click 'Generate Learning Plan' to start")
    
    # Update the terminal output display section
    if st.session_state.terminal_output:
        st.subheader("Terminal Output")
        st.info("This is a copy of the terminal output. For real-time updates during processing, please check your terminal window.")
        st.code(st.session_state.terminal_output, language="bash")

if __name__ == "__main__":
    main()