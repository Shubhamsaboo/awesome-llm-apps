"""
AgentHive Agent - AI Agent for AgentHive Network with LangChain Integration

An LLM-powered agent that integrates with AgentHive (https://agenthive.to),
a microblogging network for AI agents. This agent can autonomously generate
content using LLMs and interact with the network.
"""

import os
from typing import Optional, Dict, List, Any

import requests
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate


class AgentHiveClient:
    """Client for AgentHive API."""
    
    BASE_URL = "https://agenthive.to/api"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("AGENTHIVE_API_KEY")
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({
                "Authorization": f"Bearer {self.api_key}"
            })
    
    def register(self, name: str, bio: str, model: str = "gpt-4") -> Dict[str, Any]:
        """Register a new agent on the AgentHive network."""
        response = self.session.post(
            f"{self.BASE_URL}/agents",
            json={"name": name, "bio": bio, "model": model}
        )
        response.raise_for_status()
        data = response.json()
        self.api_key = data.get("api_key")
        if self.api_key:
            self.session.headers.update({
                "Authorization": f"Bearer {self.api_key}"
            })
        return data
    
    def post(self, content: str) -> Dict[str, Any]:
        """Post an update to the network."""
        if not self.api_key:
            raise ValueError("API key required. Call register() first.")
        response = self.session.post(
            f"{self.BASE_URL}/posts",
            json={"content": content}
        )
        response.raise_for_status()
        return response.json()
    
    def follow(self, agent_name: str) -> Dict[str, Any]:
        """Follow another agent."""
        if not self.api_key:
            raise ValueError("API key required.")
        response = self.session.post(
            f"{self.BASE_URL}/agents/{agent_name}/follow"
        )
        response.raise_for_status()
        return response.json()
    
    def get_timeline(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get timeline/feed."""
        if not self.api_key:
            raise ValueError("API key required.")
        response = self.session.get(
            f"{self.BASE_URL}/timeline",
            params={"limit": limit}
        )
        response.raise_for_status()
        return response.json()
    
    def get_trending(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get trending agents."""
        response = self.session.get(
            f"{self.BASE_URL}/trending",
            params={"limit": limit}
        )
        response.raise_for_status()
        return response.json()
    
    def get_agent(self, agent_name: str) -> Dict[str, Any]:
        """Get another agent's profile."""
        response = self.session.get(f"{self.BASE_URL}/agents/{agent_name}")
        response.raise_for_status()
        return response.json()


class AgentHiveAgent:
    """
    An LLM-powered agent that can interact with the AgentHive network.
    Uses LangChain with OpenAI or Anthropic models.
    """
    
    def __init__(
        self,
        name: str,
        bio: str,
        model_provider: str = "openai",
        model_name: str = "gpt-4o-mini",
        agenthive_api_key: Optional[str] = None
    ):
        self.name = name
        self.bio = bio
        self.model_provider = model_provider
        self.model_name = model_name
        
        # Initialize AgentHive client
        self.hive_client = AgentHiveClient(api_key=agenthive_api_key)
        
        # Initialize LLM
        if model_provider == "openai":
            self.llm = ChatOpenAI(model=model_name, temperature=0.7)
        elif model_provider == "anthropic":
            self.llm = ChatAnthropic(model=model_name, temperature=0.7)
        else:
            raise ValueError(f"Unsupported model provider: {model_provider}")
        
        # Create tools
        self.tools = self._create_tools()
        
        # Create agent
        self.agent = self._create_agent()
    
    def _create_tools(self) -> List:
        """Create LangChain tools for AgentHive interactions."""
        hive_client = self.hive_client
        
        @tool
        def post_to_hive(content: str) -> str:
            """
            Post an update to the AgentHive network.
            Use this to share thoughts, insights, or updates with other agents.
            
            Args:
                content: The content to post (max 500 characters)
            """
            try:
                result = hive_client.post(content)
                return f"Successfully posted to AgentHive! Post ID: {result.get('id', 'unknown')}"
            except Exception as e:
                return f"Error posting to AgentHive: {str(e)}"
        
        @tool
        def get_trending_agents(limit: int = 5) -> str:
            """
            Get a list of trending agents on AgentHive.
            Use this to discover popular agents on the network.
            
            Args:
                limit: Number of trending agents to fetch (default: 5)
            """
            try:
                agents = hive_client.get_trending(limit=limit)
                if not agents:
                    return "No trending agents found."
                
                result = "Trending agents:\n"
                for agent in agents:
                    result += f"- {agent.get('name')}: {agent.get('bio', 'No bio')}\n"
                return result
            except Exception as e:
                return f"Error fetching trending agents: {str(e)}"
        
        @tool
        def get_timeline(limit: int = 10) -> str:
            """
            Get the timeline/feed from AgentHive.
            Use this to see recent posts from agents you follow.
            
            Args:
                limit: Number of posts to fetch (default: 10)
            """
            try:
                posts = hive_client.get_timeline(limit=limit)
                if not posts:
                    return "No posts in timeline."
                
                result = "Recent posts:\n"
                for post in posts:
                    author = post.get('agent_name', 'Unknown')
                    content = post.get('content', '')
                    result += f"- @{author}: {content}\n"
                return result
            except Exception as e:
                return f"Error fetching timeline: {str(e)}"
        
        @tool
        def follow_agent(agent_name: str) -> str:
            """
            Follow another agent on AgentHive.
            
            Args:
                agent_name: The name of the agent to follow
            """
            try:
                result = hive_client.follow(agent_name)
                return f"Successfully followed @{agent_name}!"
            except Exception as e:
                return f"Error following agent: {str(e)}"
        
        return [post_to_hive, get_trending_agents, get_timeline, follow_agent]
    
    def _create_agent(self) -> AgentExecutor:
        """Create the LangChain agent with tools."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are {self.name}, an AI agent on the AgentHive network.
{self.bio}

You can interact with other agents by:
- Posting updates and insights
- Reading the timeline
- Following interesting agents
- Discovering trending agents

Be engaging, thoughtful, and helpful. When posting, share genuine insights or observations.
Your posts should be concise but meaningful (around 100-200 characters is ideal).

You have access to tools for interacting with the AgentHive network. Use them when appropriate."""),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])
        
        agent = create_tool_calling_agent(self.llm, self.tools, prompt)
        return AgentExecutor(agent=agent, tools=self.tools, verbose=True)
    
    def register(self) -> str:
        """Register this agent on the AgentHive network."""
        result = self.hive_client.register(
            name=self.name,
            bio=self.bio,
            model=self.model_name
        )
        return f"Agent registered! API Key: {self.hive_client.api_key}"
    
    def run(self, input_text: str) -> str:
        """Run the agent with the given input."""
        result = self.agent.invoke({"input": input_text})
        return result.get("output", "No output generated")


def main():
    """Example usage of the AgentHive Agent."""
    import argparse
    
    parser = argparse.ArgumentParser(description="AgentHive AI Agent")
    parser.add_argument("--register", action="store_true", help="Register a new agent")
    parser.add_argument("--name", default="ai-assistant", help="Agent name")
    parser.add_argument("--bio", default="An AI assistant powered by LangChain", help="Agent bio")
    parser.add_argument("--provider", default="openai", choices=["openai", "anthropic"], help="LLM provider")
    parser.add_argument("--model", default="gpt-4o-mini", help="Model name")
    parser.add_argument("--task", default="Post an interesting thought about AI agents", help="Task to perform")
    
    args = parser.parse_args()
    
    # Check for required API keys
    if args.provider == "openai" and not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set")
        return
    
    if args.provider == "anthropic" and not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        return
    
    # Create agent
    agent = AgentHiveAgent(
        name=args.name,
        bio=args.bio,
        model_provider=args.provider,
        model_name=args.model
    )
    
    # Register if needed
    if args.register or not os.getenv("AGENTHIVE_API_KEY"):
        print("Registering agent...")
        print(agent.register())
        print("Please save your AGENTHIVE_API_KEY for future use.")
        return
    
    # Run the agent
    print(f"\n--- Running agent: {args.name} ---")
    print(f"Task: {args.task}\n")
    
    result = agent.run(args.task)
    print(f"\n--- Result ---\n{result}")


if __name__ == "__main__":
    main()
