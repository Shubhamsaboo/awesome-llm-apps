"""
IBKR Portfolio Monitor with XAI Finance Agent
Monitors portfolio positions and sends alerts based on price action
"""

import time
from typing import List, Dict, Optional
from datetime import datetime
from ib_insync import IB, Stock, util
from agno.agent import Agent
from agno.models.xai import xAI
from agno.utils.log import logger

from ibkr_tools import IBKRPortfolioTools
from notifications import NotificationManager, PriceAlertCondition


class IBKRPortfolioMonitor:
    """Monitor IBKR portfolio and send notifications on price movements"""

    def __init__(
        self,
        ibkr_tools: IBKRPortfolioTools,
        notification_manager: NotificationManager,
        agent: Agent,
        check_interval: int = 60
    ):
        """
        Initialize portfolio monitor

        Args:
            ibkr_tools: IBKR tools instance
            notification_manager: Notification manager instance
            agent: XAI agent for analysis
            check_interval: Seconds between checks (default: 60)
        """
        self.ibkr_tools = ibkr_tools
        self.notification_manager = notification_manager
        self.agent = agent
        self.check_interval = check_interval
        self.alert_conditions: List[PriceAlertCondition] = []
        self.last_prices: Dict[str, float] = {}
        self.running = False

    def add_alert_condition(self, condition: PriceAlertCondition):
        """Add a price alert condition"""
        self.alert_conditions.append(condition)
        logger.info(f"Added alert: {condition.get_description()}")

    def remove_alert_condition(self, symbol: str):
        """Remove all alert conditions for a symbol"""
        self.alert_conditions = [c for c in self.alert_conditions if c.symbol != symbol]
        logger.info(f"Removed alerts for {symbol}")

    def get_portfolio_symbols(self) -> List[str]:
        """Get list of symbols in portfolio"""
        if not self.ibkr_tools._connect():
            return []

        try:
            positions = self.ibkr_tools.ib.portfolio()
            return [pos.contract.symbol for pos in positions]
        except Exception as e:
            logger.error(f"Error fetching portfolio symbols: {e}")
            return []

    def check_price_alerts(self):
        """Check all price alert conditions"""
        if not self.ibkr_tools._connect():
            logger.error("Could not connect to IBKR for price checks")
            return

        for condition in self.alert_conditions:
            try:
                # Get current price
                contract = Stock(condition.symbol, 'SMART', 'USD')
                self.ibkr_tools.ib.qualifyContracts(contract)
                ticker = self.ibkr_tools.ib.reqMktData(contract)
                self.ibkr_tools.ib.sleep(1)

                current_price = ticker.marketPrice()
                if current_price and current_price > 0:
                    # Check condition
                    if condition.check(current_price) and not condition.triggered:
                        # Alert triggered!
                        self._trigger_alert(condition, current_price)
                        condition.triggered = True

                    # Update last price
                    self.last_prices[condition.symbol] = current_price

            except Exception as e:
                logger.error(f"Error checking alert for {condition.symbol}: {e}")

    def _trigger_alert(self, condition: PriceAlertCondition, current_price: float):
        """Trigger an alert"""
        title = f"Price Alert: {condition.symbol}"
        message = f"""
{condition.get_description()}

Current Price: ${current_price:.2f}
Alert Triggered: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

You may want to review this position in your portfolio.
"""

        # Send notifications
        self.notification_manager.send_alert(title, message)

        # Ask AI agent for analysis
        try:
            analysis_prompt = f"""
The price alert has triggered for {condition.symbol} at ${current_price:.2f}.
Condition: {condition.get_description()}

Please provide:
1. Brief analysis of why the price might have moved
2. Key news or events affecting {condition.symbol}
3. Recommendation on what action to consider

Keep response concise and actionable.
"""
            response = self.agent.run(analysis_prompt)

            if response and response.content:
                ai_analysis = f"\n\n🤖 AI Analysis:\n{response.content}"
                self.notification_manager.send_alert(
                    f"AI Analysis: {condition.symbol}",
                    ai_analysis
                )

        except Exception as e:
            logger.error(f"Error getting AI analysis: {e}")

    def monitor_portfolio_volatility(self, threshold_percent: float = 5.0):
        """
        Monitor portfolio for significant price movements

        Args:
            threshold_percent: Percentage change to trigger alert
        """
        symbols = self.get_portfolio_symbols()

        for symbol in symbols:
            if symbol not in self.last_prices:
                # Initialize last price
                price_str = self.ibkr_tools.get_real_time_price(symbol)
                try:
                    # Parse price from string
                    price = float(price_str.split('$')[1].split('|')[0].strip())
                    self.last_prices[symbol] = price
                except:
                    continue
            else:
                # Check for significant movement
                current_price_str = self.ibkr_tools.get_real_time_price(symbol)
                try:
                    current_price = float(current_price_str.split('$')[1].split('|')[0].strip())
                    last_price = self.last_prices[symbol]

                    percent_change = abs((current_price - last_price) / last_price * 100)

                    if percent_change >= threshold_percent:
                        direction = "up" if current_price > last_price else "down"
                        title = f"Volatility Alert: {symbol}"
                        message = f"""
{symbol} has moved {percent_change:.2f}% {direction}

Previous: ${last_price:.2f}
Current: ${current_price:.2f}
Change: ${current_price - last_price:+.2f}

This is a significant movement that may require your attention.
"""
                        self.notification_manager.send_alert(title, message)
                        self.last_prices[symbol] = current_price

                except:
                    continue

    def generate_daily_summary(self):
        """Generate and send daily portfolio summary"""
        portfolio = self.ibkr_tools.get_portfolio_positions()
        account = self.ibkr_tools.get_account_summary()

        # Ask AI agent for summary
        try:
            summary_prompt = f"""
Here is my current portfolio:

{portfolio}

{account}

Please provide a brief daily summary including:
1. Overall portfolio performance
2. Top gainers and losers
3. Any positions that need attention
4. Market sentiment

Keep it concise and actionable.
"""
            response = self.agent.run(summary_prompt)

            if response and response.content:
                self.notification_manager.send_alert(
                    "Daily Portfolio Summary",
                    response.content
                )
        except Exception as e:
            logger.error(f"Error generating daily summary: {e}")

    def start_monitoring(self):
        """Start the monitoring loop"""
        self.running = True
        logger.info("Starting IBKR portfolio monitoring...")

        try:
            while self.running:
                logger.info(f"Checking alerts at {datetime.now().strftime('%H:%M:%S')}")

                # Check price alerts
                self.check_price_alerts()

                # Monitor portfolio volatility
                self.monitor_portfolio_volatility()

                # Sleep until next check
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
            self.running = False

        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
            self.running = False

    def stop_monitoring(self):
        """Stop the monitoring loop"""
        self.running = False
        logger.info("Stopping monitor...")


# Example usage
if __name__ == "__main__":
    # Configuration
    IBKR_HOST = '127.0.0.1'
    IBKR_PORT = 7497  # TWS paper trading port
    CHECK_INTERVAL = 60  # Check every 60 seconds

    # Email configuration (optional)
    email_config = {
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'sender_email': 'your-email@gmail.com',
        'sender_password': 'your-app-password',  # Use app password for Gmail
        'recipients': ['recipient@example.com']
    }

    # Initialize components
    ibkr_tools = IBKRPortfolioTools(host=IBKR_HOST, port=IBKR_PORT)

    notification_manager = NotificationManager(
        # email_config=email_config,  # Uncomment to enable email
        # slack_webhook='your-slack-webhook-url',  # Uncomment to enable Slack
    )

    # Create XAI agent
    agent = Agent(
        name="IBKR Portfolio Analyst",
        model=xAI(id="grok-beta"),
        tools=[ibkr_tools],
        instructions=[
            "You are a financial analyst specializing in portfolio analysis.",
            "Provide concise, actionable insights.",
            "Always use tables for numerical data.",
            "Focus on risk management and opportunities."
        ],
        markdown=True,
    )

    # Create monitor
    monitor = IBKRPortfolioMonitor(
        ibkr_tools=ibkr_tools,
        notification_manager=notification_manager,
        agent=agent,
        check_interval=CHECK_INTERVAL
    )

    # Add some example alerts
    # Alert when AAPL goes above $200
    monitor.add_alert_condition(
        PriceAlertCondition(
            symbol='AAPL',
            condition_type='above',
            threshold=200.0
        )
    )

    # Alert when TSLA drops 5% from current price
    # First get current price
    current_tsla = 250.0  # Replace with actual current price
    monitor.add_alert_condition(
        PriceAlertCondition(
            symbol='TSLA',
            condition_type='percent_change_down',
            threshold=5.0,
            reference_price=current_tsla
        )
    )

    print("="*60)
    print("IBKR Portfolio Monitor Started")
    print("="*60)
    print(f"Monitoring interval: {CHECK_INTERVAL} seconds")
    print(f"Active alerts: {len(monitor.alert_conditions)}")
    print("\nPress Ctrl+C to stop monitoring\n")
    print("="*60)

    # Start monitoring
    monitor.start_monitoring()
