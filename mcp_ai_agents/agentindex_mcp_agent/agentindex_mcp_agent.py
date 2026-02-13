"""
AgentIndex MCP Agent - Discover AI agents for any task
Uses AgentIndex (agentcrawl.dev) to search 39,000+ indexed agents
"""

from agentcrawl import AgentIndex


def discover_agents(query, category=None, min_quality=0.0):
    """Search for AI agents matching a natural language query."""
    client = AgentIndex()

    params = {"need": query, "min_quality": min_quality}
    if category:
        params["category"] = category

    results = client.discover(**params)

    print(f"\n Found {len(results)} agents for: '{query}'\n")
    for i, agent in enumerate(results[:5], 1):
        print(f"  {i}. {agent['name']}")
        print(f"     Score: {agent.get('quality_score', 'N/A')}")
        print(f"     Source: {agent.get('source', 'N/A')}")
        print(f"     URL: {agent.get('url', 'N/A')}")
        print()

    return results


def main():
    print("AgentIndex MCP Agent - AI Agent Discovery")
    print("=" * 50)

    examples = [
        ("code review tool", "coding"),
        ("translate documents", None),
        ("data visualization", "data"),
    ]

    for query, category in examples:
        discover_agents(query, category=category)


if __name__ == "__main__":
    main()
