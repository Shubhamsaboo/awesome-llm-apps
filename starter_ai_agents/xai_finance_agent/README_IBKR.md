# 📊 XAI Finance Agent with IBKR Portfolio Integration

A powerful AI-powered financial analysis system that combines **xAI's Grok** model with **Interactive Brokers (IBKR)** portfolio data to provide real-time portfolio monitoring, intelligent analysis, and automated price alerts.

## 🎯 Features

### Portfolio Analysis
- ✅ Real-time IBKR portfolio access
- ✅ Position performance tracking
- ✅ Account summary and metrics
- ✅ P&L analysis (realized & unrealized)
- ✅ Real-time price data for any ticker

### AI-Powered Insights
- 🤖 Natural language portfolio queries
- 🤖 Intelligent market analysis
- 🤖 Risk assessment and recommendations
- 🤖 News sentiment analysis
- 🤖 Automated daily summaries

### Price Monitoring & Alerts
- 🔔 Price threshold alerts (above/below)
- 🔔 Percentage change alerts
- 🔔 Portfolio volatility monitoring
- 🔔 Multi-channel notifications (Email, Slack, Discord)
- 🔔 AI-generated alert analysis

## 📋 Prerequisites

### 1. IBKR Account Setup
- Active IBKR account (paper trading or live)
- **TWS (Trader Workstation)** or **IB Gateway** installed
- API access enabled in TWS/Gateway settings

### 2. Enable IBKR API Access

**For TWS:**
1. Open TWS
2. Go to **File → Global Configuration → API → Settings**
3. Check **"Enable ActiveX and Socket Clients"**
4. Note the **Socket port** (default: 7497 for paper, 7496 for live)
5. Add `127.0.0.1` to **Trusted IP Addresses**
6. Uncheck **"Read-Only API"** if you want full access
7. Click **OK** and restart TWS

**For IB Gateway:**
1. Open IB Gateway
2. Go to **Configure → Settings → API → Settings**
3. Same steps as TWS above
4. Default ports: 4001 (paper), 4000 (live)

### 3. API Keys
- **XAI API Key**: Get from [console.x.ai](https://console.x.ai/)

## 🚀 Installation & Setup

### Step 1: Clone Repository
```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/starter_ai_agents/xai_finance_agent
```

### Step 2: Install Dependencies
```bash
pip install -r requirements_ibkr.txt
```

### Step 3: Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
nano .env
```

**Required Configuration:**
```bash
XAI_API_KEY=your-xai-api-key
IBKR_HOST=127.0.0.1
IBKR_PORT=7497  # Adjust based on your setup
```

**Optional Notification Configuration:**
```bash
# Email (Gmail example)
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password  # Use Gmail App Password
RECIPIENTS=alert-recipient@example.com

# Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK

# Discord
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR/WEBHOOK
```

### Step 4: Start IBKR Connection
1. **Launch TWS or IB Gateway**
2. **Log in** to your account
3. Keep it **running** (API needs active connection)

## 💻 Usage

### Mode 1: Interactive Agent (Playground UI)

Start the interactive agent with IBKR integration:

```bash
python xai_finance_agent_ibkr.py
```

Then open your browser to the provided URL (typically `http://localhost:8000`)

**Example Queries:**
- "Show me my current portfolio positions"
- "What's my account summary?"
- "Analyze the performance of my AAPL position"
- "Which of my positions are underperforming and why?"
- "Should I rebalance my portfolio based on current market conditions?"
- "Get real-time price for TSLA"
- "Compare my NVDA holdings with analyst recommendations"

### Mode 2: Background Monitoring with Alerts

Run continuous portfolio monitoring with automated alerts:

```bash
python ibkr_monitor.py
```

This will:
- ✅ Monitor all portfolio positions
- ✅ Check price alerts every 60 seconds (configurable)
- ✅ Send notifications when conditions are met
- ✅ Track portfolio volatility
- ✅ Generate AI analysis for triggered alerts

**Customize alerts in `ibkr_monitor.py`:**

```python
# Alert when AAPL goes above $200
monitor.add_alert_condition(
    PriceAlertCondition(
        symbol='AAPL',
        condition_type='above',
        threshold=200.0
    )
)

# Alert when TSLA drops 5% from current price
monitor.add_alert_condition(
    PriceAlertCondition(
        symbol='TSLA',
        condition_type='percent_change_down',
        threshold=5.0,
        reference_price=250.0  # Current price
    )
)

# Alert when NVDA rises 3% from current price
monitor.add_alert_condition(
    PriceAlertCondition(
        symbol='NVDA',
        condition_type='percent_change_up',
        threshold=3.0,
        reference_price=880.0
    )
)
```

## 🔧 Advanced Configuration

### Custom Tools Integration

You can extend the IBKR tools with additional functionality:

```python
from ibkr_tools import IBKRPortfolioTools

# Create custom tools instance
ibkr = IBKRPortfolioTools(host='127.0.0.1', port=7497)

# Use directly in your code
positions = ibkr.get_portfolio_positions()
account = ibkr.get_account_summary()
price = ibkr.get_real_time_price('AAPL')
analysis = ibkr.analyze_position_performance('TSLA')
```

### Notification Channels

Configure multiple notification channels:

```python
from notifications import NotificationManager

notifier = NotificationManager(
    email_config={
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'sender_email': 'your-email@gmail.com',
        'sender_password': 'app-password',
        'recipients': ['recipient@example.com']
    },
    slack_webhook='https://hooks.slack.com/services/YOUR/WEBHOOK',
    discord_webhook='https://discord.com/api/webhooks/YOUR/WEBHOOK'
)

# Send alerts
notifier.send_alert(
    title="Portfolio Alert",
    message="AAPL crossed $200!",
    channels=['email', 'slack']  # Choose channels
)
```

### Scheduled Daily Summaries

Add daily portfolio summaries using the scheduler:

```python
import schedule
from ibkr_monitor import IBKRPortfolioMonitor

# Schedule daily summary at 9 AM
schedule.every().day.at("09:00").do(monitor.generate_daily_summary)

while True:
    schedule.run_pending()
    time.sleep(60)
```

## 📊 Available Tools & Methods

### IBKR Portfolio Tools
- `get_portfolio_positions()` - All current positions
- `get_account_summary()` - Account metrics and cash
- `get_portfolio_value()` - Total portfolio value
- `analyze_position_performance(symbol)` - Deep dive into a position
- `get_real_time_price(symbol)` - Live market data

### Price Alert Conditions
- `above` - Price crosses above threshold
- `below` - Price crosses below threshold
- `percent_change_up` - Price rises by X% from reference
- `percent_change_down` - Price drops by X% from reference

## 🛠️ Troubleshooting

### Connection Issues

**Error: "Could not connect to IBKR"**
- ✅ Ensure TWS/Gateway is running
- ✅ Check API is enabled in settings
- ✅ Verify correct port number in .env
- ✅ Confirm `127.0.0.1` is in Trusted IPs
- ✅ Try restarting TWS/Gateway

**Error: "Connection refused"**
- ✅ Check if another application is using the same client_id
- ✅ Change `IBKR_CLIENT_ID` in .env to a different number

### Email Notifications Not Working

**Gmail Users:**
1. Enable 2-Factor Authentication
2. Generate an **App Password**: [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. Use the app password in `SENDER_PASSWORD` (not your regular password)

**Other Providers:**
- Update `SMTP_SERVER` and `SMTP_PORT` for your provider
- Check provider documentation for SMTP settings

### Data Issues

**No portfolio positions showing:**
- ✅ Ensure you're connected to correct account
- ✅ Check if using paper vs live account
- ✅ Verify positions exist in TWS

**Delayed price data:**
- ✅ IBKR API provides real-time for subscribed data
- ✅ Delayed data for non-subscribed symbols
- ✅ Check market hours (pre-market, regular, after-hours)

## 🔐 Security Best Practices

1. **Never commit .env file** - Already in .gitignore
2. **Use app-specific passwords** for email
3. **Secure webhook URLs** - Don't share publicly
4. **Paper trading first** - Test with paper account before live
5. **Read-only API** - Enable if you only need monitoring (not trading)

## 📚 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  XAI Finance Agent                       │
│              (Grok-beta Language Model)                  │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────────┐
        │         AgentOS Framework             │
        │    (Orchestration & UI Layer)         │
        └──────────────────────────────────────┘
                           │
        ┌──────────────────┴──────────────────┐
        │                                      │
        ▼                                      ▼
┌───────────────────┐              ┌─────────────────────┐
│   IBKR Tools      │              │  Market Data Tools  │
│                   │              │                     │
│ • Portfolio Data  │              │ • YFinance          │
│ • Account Info    │              │ • DuckDuckGo        │
│ • Real-time Price │              │ • Web Search        │
│ • Performance     │              │                     │
└────────┬──────────┘              └─────────────────────┘
         │
         ▼
┌──────────────────┐
│  IB Gateway/TWS  │
│  (IBKR API)      │
└──────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│      Notification Manager         │
│                                   │
│  • Email (SMTP)                   │
│  • Slack (Webhooks)               │
│  • Discord (Webhooks)             │
│  • Console Output                 │
└──────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│     Portfolio Monitor             │
│                                   │
│  • Price Alerts                   │
│  • Volatility Tracking            │
│  • Daily Summaries                │
│  • AI Analysis                    │
└──────────────────────────────────┘
```

## 🎓 Example Use Cases

### 1. Morning Portfolio Review
```python
# Ask the agent in playground:
"Give me a comprehensive morning briefing on my portfolio including:
1. Overnight price movements
2. Pre-market movers
3. Any significant news affecting my holdings
4. Recommended actions for today"
```

### 2. Risk Management
```python
# Set up volatility monitoring
monitor.monitor_portfolio_volatility(threshold_percent=5.0)

# Get AI risk assessment
"Analyze my portfolio's risk exposure and suggest hedging strategies"
```

### 3. Earnings Season
```python
# Set alerts for positions with upcoming earnings
"Which of my holdings have earnings this week and what are the analyst expectations?"

# Add price alerts around earnings
monitor.add_alert_condition(
    PriceAlertCondition('NVDA', 'percent_change_up', 5.0, reference_price=880.0)
)
```

### 4. Sector Rotation
```python
"Analyze my portfolio's sector allocation and compare it with current market trends. Should I rotate into defensive sectors?"
```

## 🤝 Contributing

Contributions welcome! Feel free to:
- Add new IBKR tools
- Implement additional notification channels
- Enhance AI analysis prompts
- Add new alert condition types

## 📄 License

This project is part of the awesome-llm-apps repository.

## ⚠️ Disclaimer

This software is for educational and informational purposes only. It does not constitute financial advice. Always do your own research and consult with qualified financial advisors before making investment decisions. Trading involves risk and you can lose money.

## 🔗 Resources

- [IBKR API Documentation](https://interactivebrokers.github.io/tws-api/)
- [ib_insync Documentation](https://ib-insync.readthedocs.io/)
- [xAI API Docs](https://docs.x.ai/)
- [AgentOS Documentation](https://docs.agno.com/)

---

Built with ❤️ using xAI Grok, IBKR API, and AgentOS
