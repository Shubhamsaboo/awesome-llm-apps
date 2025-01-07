import autogen
from typing import List, Dict, Any
import os
from dotenv import load_dotenv
from autogen import AssistantAgent, UserProxyAgent
from composio_autogen import ComposioToolSet, App

# Load environment variables
load_dotenv()

def setup_config() -> Dict[str, Any]:
    config_list = [
        {
            "model": "gpt-4o",
            "api_key": os.getenv("OPENAI_API_KEY"),  # Use environment variable for API key
        }
    ]

    llm_config = {
        "config_list": config_list,
    }
    return llm_config

def create_agents(llm_config: Dict[str, Any]) -> List[autogen.Agent]:
    """Create and return all agents with enhanced reporting capabilities."""
    user_proxy = autogen.UserProxyAgent(
        name="User_proxy",
        system_message="""You are a human admin who oversees the learning process and ensures 
            that the learning goals are met. Request detailed reports from each agent and ensure 
            the system stops after all agents have completed their tasks.""",
        code_execution_config={
            "last_n_messages": 2,
            "work_dir": "groupchat",
            "use_docker": False,
        },
        human_input_mode="TERMINATE",
    )

    knowledge_agent = autogen.AssistantAgent(
        name="KnowledgeBuilder",
        llm_config=llm_config,
        system_message="""You are an expert researcher who excels at gathering, analyzing, 
            and organizing information from various internet sources on a given topic.
            
            For each topic, provide a detailed report including:
            1. Core concepts and fundamentals
            2. Latest developments and trends
            3. Key research papers and publications
            4. Expert opinions and insights
            5. Comprehensive bibliography
            
            Format your findings in a clear, structured manner with citations.""",
    )

    roadmap_agent = autogen.AssistantAgent(
        name="RoadmapArchitect",
        llm_config=llm_config,
        system_message="""You are a curriculum design expert who specializes in creating 
            clear, structured learning paths.
            
            For each topic, create a detailed learning roadmap including:
            1. Prerequisites and foundation knowledge
            2. Learning objectives and outcomes
            3. Milestone achievements
            4. Timeline estimates
            5. Progress tracking metrics
            6. Assessment criteria
            
            Present your roadmap with clear progression stages.""",
    )

    resource_agent = autogen.AssistantAgent(
        name="ResourceCurator",
        llm_config=llm_config,
        system_message="""You are an expert at finding and validating educational resources.
            
            For each topic, compile a comprehensive resource report including:
            1. Textbooks and academic materials
            2. Online courses and MOOCs
            3. Video tutorials and lectures
            4. Interactive learning platforms
            5. Community forums and discussion groups
            6. Quality assessment of each resource
            7. Cost and accessibility information
            
            Validate and rate each resource based on credibility and effectiveness.""",
    )

    practice_agent = autogen.AssistantAgent(
        name="PracticeDesigner",
        llm_config=llm_config,
        system_message="""You create engaging exercises and interview questions that reinforce learning.
            
            For each topic, develop a complete practice package including:
            1. Conceptual understanding questions
            2. Practical exercises and projects
            3. Real-world case studies
            4. Self-assessment quizzes
            5. Interview preparation materials
            6. Coding challenges (if applicable)
            7. Feedback and evaluation criteria
            
            Provide detailed solutions and explanations for all practice materials.""",
    )

    return [user_proxy, knowledge_agent, roadmap_agent, resource_agent, practice_agent]

def main() -> None:
    """Initialize and run the group chat with enhanced reporting capabilities."""
    llm_config = setup_config()
    agents = create_agents(llm_config)
    
    # Define a termination message to stop the system after all agents complete their tasks
    termination_message = "TERMINATE"

    groupchat = autogen.GroupChat(
        agents=agents,
        messages=[],
        max_round=5,  # Set max_round to 4 to ensure the system stops after all agents run
        speaker_selection_method="round_robin",  # Ensure each agent gets a turn
    )
    
    manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)
    
    # Get the user proxy agent (first agent in the list)
    user_proxy = agents[0]
    
    user_proxy.initiate_chat(
        manager,
        message="""Please provide comprehensive reports on the topic: KV Cache. Each agent should 
        contribute their expertise according to their role. Ensure all reports are detailed 
        and well-structured. After all agents have completed their tasks, the system should stop."""
    )

if __name__ == "__main__":
    main()

