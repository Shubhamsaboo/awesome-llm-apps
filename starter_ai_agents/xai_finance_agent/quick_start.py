"""
Quick Start Script for XAI Finance Agent with IBKR
Interactive setup and testing tool
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def print_banner():
    """Print welcome banner"""
    print("\n" + "="*70)
    print("🚀 XAI Finance Agent with IBKR - Quick Start")
    print("="*70 + "\n")


def check_environment():
    """Check if environment is properly configured"""
    print("📋 Checking Configuration...\n")

    checks = {
        'XAI_API_KEY': os.getenv('XAI_API_KEY'),
        'IBKR_HOST': os.getenv('IBKR_HOST', '127.0.0.1'),
        'IBKR_PORT': os.getenv('IBKR_PORT', '7497'),
    }

    all_good = True
    for key, value in checks.items():
        status = "✅" if value else "❌"
        print(f"{status} {key}: {value if value else 'NOT SET'}")
        if not value and key == 'XAI_API_KEY':
            all_good = False

    print()

    if not all_good:
        print("⚠️  Required configuration missing!")
        print("\n📝 To fix:")
        print("1. Copy .env.example to .env")
        print("2. Edit .env and add your XAI_API_KEY")
        print("3. Run this script again\n")
        return False

    return True


def test_ibkr_connection():
    """Test IBKR connection"""
    print("🔌 Testing IBKR Connection...\n")

    try:
        from ibkr_tools import IBKRPortfolioTools

        host = os.getenv('IBKR_HOST', '127.0.0.1')
        port = int(os.getenv('IBKR_PORT', 7497))

        print(f"Attempting to connect to IBKR at {host}:{port}...")

        ibkr = IBKRPortfolioTools(host=host, port=port)

        if ibkr._connect():
            print("✅ Successfully connected to IBKR!\n")

            # Try to fetch some data
            print("Fetching portfolio data...\n")
            portfolio = ibkr.get_portfolio_positions()
            print(portfolio)
            print()

            account = ibkr.get_account_summary()
            print(account)
            print()

            ibkr._disconnect()
            return True
        else:
            print("❌ Failed to connect to IBKR\n")
            print("Troubleshooting steps:")
            print("1. Ensure TWS or IB Gateway is running")
            print("2. Check that API is enabled in TWS/Gateway settings")
            print("3. Verify the port number matches your configuration")
            print("4. Confirm 127.0.0.1 is in Trusted IP Addresses\n")
            return False

    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("\nRun: pip install -r requirements_ibkr.txt\n")
        return False
    except Exception as e:
        print(f"❌ Error: {e}\n")
        return False


def test_notifications():
    """Test notification setup"""
    print("🔔 Testing Notification Setup...\n")

    from notifications import NotificationManager

    # Check what's configured
    email_config = None
    if os.getenv('SENDER_EMAIL'):
        email_config = {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', 587)),
            'sender_email': os.getenv('SENDER_EMAIL'),
            'sender_password': os.getenv('SENDER_PASSWORD'),
            'recipients': os.getenv('RECIPIENTS', '').split(',') if os.getenv('RECIPIENTS') else []
        }

    slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
    discord_webhook = os.getenv('DISCORD_WEBHOOK_URL')

    print(f"Email: {'✅ Configured' if email_config else '⚠️  Not configured (optional)'}")
    print(f"Slack: {'✅ Configured' if slack_webhook else '⚠️  Not configured (optional)'}")
    print(f"Discord: {'✅ Configured' if discord_webhook else '⚠️  Not configured (optional)'}")
    print()

    # Create manager
    notifier = NotificationManager(
        email_config=email_config,
        slack_webhook=slack_webhook,
        discord_webhook=discord_webhook
    )

    # Ask if user wants to test
    if email_config or slack_webhook or discord_webhook:
        response = input("Would you like to send a test notification? (y/n): ")
        if response.lower() == 'y':
            print("\nSending test notification...")
            notifier.send_alert(
                "Test Alert",
                "This is a test notification from XAI Finance Agent with IBKR integration. If you received this, notifications are working!"
            )
            print("✅ Test notification sent!\n")

    return True


def show_menu():
    """Show main menu"""
    print("\n" + "="*70)
    print("What would you like to do?")
    print("="*70)
    print("\n1. Start Interactive Agent (Playground UI)")
    print("2. Start Portfolio Monitor (Background Alerts)")
    print("3. Test IBKR Connection")
    print("4. Test Notifications")
    print("5. View Example Queries")
    print("6. Exit")
    print()

    return input("Enter choice (1-6): ").strip()


def show_examples():
    """Show example queries"""
    print("\n" + "="*70)
    print("📝 Example Queries for Interactive Agent")
    print("="*70)

    examples = """
Portfolio Analysis:
• "Show me my current portfolio positions"
• "What's my account summary?"
• "Analyze the performance of my AAPL position"
• "What's my total portfolio value?"
• "Which positions have the highest unrealized P&L?"

Market Analysis:
• "Get real-time price for TSLA"
• "What are analyst recommendations for NVDA?"
• "Show me the fundamentals of MSFT"
• "What's the latest news on AAPL?"

Combined Analysis:
• "Which of my positions are underperforming and why?"
• "Should I rebalance my portfolio based on current market conditions?"
• "What news might be affecting my holdings today?"
• "Analyze my portfolio's exposure to tech sector risk"
• "Compare my holdings with their analyst price targets"

Risk Management:
• "What are the key risks in my current portfolio?"
• "Which positions should I consider reducing?"
• "How diversified is my portfolio?"
• "What's my exposure to interest rate risk?"
"""
    print(examples)


def main():
    """Main quick start flow"""
    print_banner()

    # Check environment
    if not check_environment():
        sys.exit(1)

    # Test IBKR connection
    ibkr_ok = test_ibkr_connection()

    if not ibkr_ok:
        response = input("\nIBKR connection failed. Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)

    # Test notifications
    test_notifications()

    # Main menu loop
    while True:
        choice = show_menu()

        if choice == '1':
            print("\n🚀 Starting Interactive Agent...\n")
            print("Press Ctrl+C to stop\n")
            import xai_finance_agent_ibkr
            break

        elif choice == '2':
            print("\n🚀 Starting Portfolio Monitor...\n")
            print("Press Ctrl+C to stop\n")
            import ibkr_monitor
            break

        elif choice == '3':
            test_ibkr_connection()

        elif choice == '4':
            test_notifications()

        elif choice == '5':
            show_examples()

        elif choice == '6':
            print("\n👋 Goodbye!\n")
            sys.exit(0)

        else:
            print("\n❌ Invalid choice. Please enter 1-6.\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Stopped by user. Goodbye!\n")
        sys.exit(0)
