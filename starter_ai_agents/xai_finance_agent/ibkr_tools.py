"""
Custom IBKR Tools for Portfolio Analysis
Integrates Interactive Brokers API with xAI Finance Agent
"""

from typing import Optional, List, Dict, Any
from ib_insync import IB, util, Stock, Contract
import pandas as pd
from agno.tools import Toolkit
from agno.utils.log import logger


class IBKRPortfolioTools(Toolkit):
    """Tools for analyzing IBKR portfolio and market data"""

    def __init__(
        self,
        host: str = '127.0.0.1',
        port: int = 7497,
        client_id: int = 1,
        account: Optional[str] = None
    ):
        """
        Initialize IBKR connection

        Args:
            host: TWS/Gateway host (default: localhost)
            port: TWS port 7497 (paper: 7497, live: 7496) or Gateway port 4001/4002
            client_id: Unique client ID
            account: IBKR account number (optional)
        """
        super().__init__(name="ibkr_portfolio_tools")
        self.host = host
        self.port = port
        self.client_id = client_id
        self.account = account
        self.ib = None

        # Register tools
        self.register(self.get_portfolio_positions)
        self.register(self.get_account_summary)
        self.register(self.get_portfolio_value)
        self.register(self.analyze_position_performance)
        self.register(self.get_real_time_price)

    def _connect(self) -> bool:
        """Establish connection to IBKR"""
        try:
            if self.ib is None or not self.ib.isConnected():
                self.ib = IB()
                self.ib.connect(self.host, self.port, clientId=self.client_id)
                logger.info(f"Connected to IBKR on {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to IBKR: {e}")
            return False

    def _disconnect(self):
        """Safely disconnect from IBKR"""
        if self.ib and self.ib.isConnected():
            self.ib.disconnect()
            logger.info("Disconnected from IBKR")

    def get_portfolio_positions(self) -> str:
        """
        Get current portfolio positions from IBKR account

        Returns:
            Formatted string with portfolio positions
        """
        if not self._connect():
            return "Error: Could not connect to IBKR. Ensure TWS/Gateway is running."

        try:
            positions = self.ib.portfolio()

            if not positions:
                return "No positions found in portfolio."

            # Create DataFrame for better formatting
            data = []
            for pos in positions:
                data.append({
                    'Symbol': pos.contract.symbol,
                    'Quantity': pos.position,
                    'Market Price': f"${pos.marketPrice:.2f}",
                    'Market Value': f"${pos.marketValue:.2f}",
                    'Avg Cost': f"${pos.averageCost:.2f}",
                    'Unrealized PnL': f"${pos.unrealizedPNL:.2f}",
                    'Realized PnL': f"${pos.realizedPNL:.2f}"
                })

            df = pd.DataFrame(data)
            return f"Portfolio Positions:\n\n{df.to_string(index=False)}"

        except Exception as e:
            return f"Error fetching portfolio: {str(e)}"

    def get_account_summary(self) -> str:
        """
        Get account summary including cash, equity, and margin

        Returns:
            Formatted account summary
        """
        if not self._connect():
            return "Error: Could not connect to IBKR."

        try:
            account_values = self.ib.accountValues()

            # Key metrics to display
            key_metrics = [
                'TotalCashValue', 'NetLiquidation', 'UnrealizedPnL',
                'RealizedPnL', 'GrossPositionValue', 'BuyingPower'
            ]

            summary = {}
            for av in account_values:
                if av.tag in key_metrics:
                    summary[av.tag] = f"${float(av.value):,.2f}"

            result = "Account Summary:\n\n"
            for key, value in summary.items():
                result += f"{key}: {value}\n"

            return result

        except Exception as e:
            return f"Error fetching account summary: {str(e)}"

    def get_portfolio_value(self) -> str:
        """
        Get total portfolio value

        Returns:
            Total portfolio value
        """
        if not self._connect():
            return "Error: Could not connect to IBKR."

        try:
            account_values = self.ib.accountValues()

            for av in account_values:
                if av.tag == 'NetLiquidation':
                    return f"Total Portfolio Value: ${float(av.value):,.2f}"

            return "Could not retrieve portfolio value"

        except Exception as e:
            return f"Error: {str(e)}"

    def analyze_position_performance(self, symbol: str) -> str:
        """
        Analyze performance of a specific position

        Args:
            symbol: Stock symbol to analyze

        Returns:
            Performance analysis for the position
        """
        if not self._connect():
            return "Error: Could not connect to IBKR."

        try:
            positions = self.ib.portfolio()

            position = next((p for p in positions if p.contract.symbol == symbol.upper()), None)

            if not position:
                return f"No position found for {symbol}"

            pnl_percent = (position.unrealizedPNL / (position.averageCost * abs(position.position))) * 100

            analysis = f"""
Position Analysis for {symbol}:

Quantity: {position.position}
Average Cost: ${position.averageCost:.2f}
Current Price: ${position.marketPrice:.2f}
Market Value: ${position.marketValue:,.2f}

Performance:
Unrealized P&L: ${position.unrealizedPNL:,.2f} ({pnl_percent:.2f}%)
Realized P&L: ${position.realizedPNL:,.2f}
"""
            return analysis

        except Exception as e:
            return f"Error analyzing position: {str(e)}"

    def get_real_time_price(self, symbol: str, exchange: str = 'SMART') -> str:
        """
        Get real-time price for a ticker

        Args:
            symbol: Stock symbol
            exchange: Exchange (default: SMART)

        Returns:
            Current price information
        """
        if not self._connect():
            return "Error: Could not connect to IBKR."

        try:
            contract = Stock(symbol, exchange, 'USD')
            self.ib.qualifyContracts(contract)

            ticker = self.ib.reqMktData(contract)
            self.ib.sleep(2)  # Wait for data

            if ticker.marketPrice():
                return f"{symbol}: ${ticker.marketPrice():.2f} | Bid: ${ticker.bid:.2f} | Ask: ${ticker.ask:.2f} | Volume: {ticker.volume}"
            else:
                return f"No market data available for {symbol}"

        except Exception as e:
            return f"Error fetching price: {str(e)}"
