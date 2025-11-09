"""
Enhanced XAI Finance Agent with IBKR Portfolio Integration
Combines AI-powered financial analysis with real-time portfolio monitoring
"""

import os
from agno.agent import Agent
from agno.models.xai import xAI
from agno.tools.yfinance import YFinanceTools
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.os import AgentOS

from ibkr_tools import IBKRPortfolioTools
from notifications import NotificationManager


# Configuration
IBKR_CONFIG = {
    'host': os.getenv('IBKR_HOST', '127.0.0.1'),
    'port': int(os.getenv('IBKR_PORT', 7497)),  # 7497 for TWS paper, 7496 for live
    'client_id': int(os.getenv('IBKR_CLIENT_ID', 1)),
}

# Email notification config (optional)
EMAIL_CONFIG = {
    'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
    'smtp_port': int(os.getenv('SMTP_PORT', 587)),
    'sender_email': os.getenv('SENDER_EMAIL', ''),
    'sender_password': os.getenv('SENDER_PASSWORD', ''),
    'recipients': os.getenv('RECIPIENTS', '').split(',') if os.getenv('RECIPIENTS') else []
} if os.getenv('SENDER_EMAIL') else None

# Webhook configs (optional)
SLACK_WEBHOOK = os.getenv('SLACK_WEBHOOK_URL', None)
DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK_URL', None)


# Initialize IBKR tools
print("Initializing IBKR Portfolio Tools...")
ibkr_tools = IBKRPortfolioTools(
    host=IBKR_CONFIG['host'],
    port=IBKR_CONFIG['port'],
    client_id=IBKR_CONFIG['client_id']
)

# Initialize notification manager
notification_manager = NotificationManager(
    email_config=EMAIL_CONFIG,
    slack_webhook=SLACK_WEBHOOK,
    discord_webhook=DISCORD_WEBHOOK
)

# Create the enhanced AI finance agent with IBKR integration
agent = Agent(
    name="xAI IBKR Finance Agent",
    model=xAI(id="grok-beta"),
    tools=[
        # IBKR Portfolio Tools
        ibkr_tools,
        # Market Data Tools
        YFinanceTools(
            stock_price=True,
            analyst_recommendations=True,
            stock_fundamentals=True,
            company_info=True,
            income_statements=True,
            balance_sheet=True
        ),
        # Web Search
        DuckDuckGoTools()
    ],
    instructions=[
        "You are an advanced financial analyst with access to real IBKR portfolio data.",
        "Always use tables to display financial/numerical data.",
        "For text data use bullet points and small paragraphs.",
        "When analyzing portfolio positions, consider risk management and diversification.",
        "Provide actionable insights and clear recommendations.",
        "When discussing price movements, mention potential catalysts and market context.",
        "Always consider both technical and fundamental factors in your analysis."
    ],
    debug_mode=True,
    markdown=True,
)

# Create AgentOS UI
agent_os = AgentOS(agents=[agent])
app = agent_os.get_app()


# Example queries you can try in the playground:
EXAMPLE_QUERIES = """
Example queries to try:

Portfolio Analysis:
- "Show me my current portfolio positions"
- "What's my account summary?"
- "Analyze the performance of my AAPL position"
- "What's my total portfolio value?"

Market Analysis:
- "Get real-time price for TSLA"
- "What are analyst recommendations for NVDA?"
- "Show me the fundamentals of MSFT"
- "Compare my portfolio holdings with market performance"

Combined Analysis:
- "Which of my positions are underperforming and why?"
- "Should I rebalance my portfolio based on current market conditions?"
- "What news might be affecting my holdings today?"
- "Analyze my portfolio's exposure to tech sector risk"
"""


if __name__ == "__main__":
    print("="*70)
    print("🚀 XAI Finance Agent with IBKR Integration")
    print("="*70)
    print("\n📊 Features:")
    print("  ✓ Real-time IBKR portfolio access")
    print("  ✓ AI-powered financial analysis")
    print("  ✓ Market data via YFinance")
    print("  ✓ Web search capabilities")
    print("\n⚙️  IBKR Configuration:")
    print(f"  Host: {IBKR_CONFIG['host']}")
    print(f"  Port: {IBKR_CONFIG['port']}")
    print(f"  Client ID: {IBKR_CONFIG['client_id']}")
    print("\n🔔 Notifications:")
    print(f"  Email: {'✓ Configured' if EMAIL_CONFIG else '✗ Not configured'}")
    print(f"  Slack: {'✓ Configured' if SLACK_WEBHOOK else '✗ Not configured'}")
    print(f"  Discord: {'✓ Configured' if DISCORD_WEBHOOK else '✗ Not configured'}")
    print("\n" + "="*70)
    print("\n📝 " + EXAMPLE_QUERIES)
    print("="*70)
    print("\n🌐 Starting AgentOS playground...")
    print("   Open your browser to the URL shown below\n")

    # Start the AgentOS server
    agent_os.serve(app="xai_finance_agent_ibkr:app", reload=True)
