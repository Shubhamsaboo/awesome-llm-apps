# 🎯 Complete Setup Guide: XAI Finance Agent with IBKR

## Overview

This guide will walk you through building and deploying a complete XAI-powered finance agent that:
- ✅ Connects to your Interactive Brokers account
- ✅ Analyzes your real portfolio in real-time
- ✅ Sends intelligent price alerts and notifications
- ✅ Provides AI-powered investment insights
- ✅ Monitors market tickers continuously

---

## 📋 Step-by-Step Implementation Plan

### **PHASE 1: Prerequisites & Setup** (15-20 minutes)

#### Step 1.1: Install IBKR Software
1. Download **TWS (Trader Workstation)** or **IB Gateway** from [IBKR](https://www.interactivebrokers.com/en/trading/tws.php)
2. Install and log in to your account
3. Recommended: Start with **paper trading account** for testing

#### Step 1.2: Enable IBKR API Access
1. In TWS/Gateway, go to: **File → Global Configuration → API → Settings**
2. ✅ Check **"Enable ActiveX and Socket Clients"**
3. ✅ Set **Socket port**:
   - Paper Trading TWS: `7497`
   - Live Trading TWS: `7496`
   - Paper Trading Gateway: `4001`
   - Live Trading Gateway: `4000`
4. ✅ Add `127.0.0.1` to **Trusted IP Addresses**
5. ✅ Optionally check **"Read-Only API"** for monitoring-only (recommended for beginners)
6. Click **Apply** and **OK**
7. **Restart TWS/Gateway**

#### Step 1.3: Get XAI API Key
1. Go to [console.x.ai](https://console.x.ai/)
2. Sign up or log in
3. Create a new API key
4. Save it securely (you'll need it in Step 2.3)

#### Step 1.4: Set Up Notifications (Optional)

**For Email Notifications (Gmail):**
1. Enable 2-Factor Authentication on your Gmail
2. Go to [Google App Passwords](https://myaccount.google.com/apppasswords)
3. Create new app password for "Mail"
4. Save the 16-character password

**For Slack Notifications:**
1. Go to [Slack API](https://api.slack.com/messaging/webhooks)
2. Create incoming webhook for your workspace
3. Copy webhook URL

**For Discord Notifications:**
1. Go to your Discord server settings
2. Integrations → Webhooks → New Webhook
3. Copy webhook URL

---

### **PHASE 2: Installation** (5-10 minutes)

#### Step 2.1: Clone Repository
```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/starter_ai_agents/xai_finance_agent
```

#### Step 2.2: Install Python Dependencies
```bash
# Install all required packages
pip install -r requirements_ibkr.txt
```

This installs:
- `agno` - AgentOS framework
- `ib_insync` - IBKR API client
- `yfinance` - Market data
- `duckduckgo-search` - Web search
- `pandas`, `numpy` - Data processing
- `fastapi` - Web framework
- Other supporting libraries

#### Step 2.3: Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit with your favorite editor
nano .env
# or
vim .env
# or
code .env
```

**Minimum Required Configuration:**
```bash
# Required
XAI_API_KEY=your-xai-api-key-here
IBKR_HOST=127.0.0.1
IBKR_PORT=7497  # Adjust based on your setup

# Optional - Email
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-16-char-app-password
RECIPIENTS=alert-email@example.com

# Optional - Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Optional - Discord
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR/WEBHOOK/URL
```

---

### **PHASE 3: Testing** (5 minutes)

#### Step 3.1: Verify Setup
```bash
python quick_start.py
```

This interactive script will:
- ✅ Check your configuration
- ✅ Test IBKR connection
- ✅ Test notifications
- ✅ Show you what to do next

#### Step 3.2: Manual Connection Test (if needed)
```python
# Test IBKR connection manually
python -c "
from ibkr_tools import IBKRPortfolioTools
ibkr = IBKRPortfolioTools(host='127.0.0.1', port=7497)
if ibkr._connect():
    print('✅ Connection successful!')
    print(ibkr.get_portfolio_positions())
else:
    print('❌ Connection failed')
"
```

---

### **PHASE 4: Usage** (Start using!)

You have **two modes** of operation:

#### **MODE A: Interactive Agent (Recommended for beginners)**

Start the AI playground interface:
```bash
python xai_finance_agent_ibkr.py
```

1. Open browser to provided URL (usually `http://localhost:8000`)
2. Chat with your AI finance agent
3. Ask questions about your portfolio
4. Get real-time market analysis

**Example Conversations:**
```
You: "Show me my current portfolio"
Agent: [Displays your positions in a formatted table]

You: "How is my AAPL position performing?"
Agent: [Shows P&L, current price, analysis]

You: "Should I be worried about my tech exposure?"
Agent: [AI-powered risk analysis with recommendations]

You: "What's the latest news on TSLA?"
Agent: [Searches web and provides summary]
```

#### **MODE B: Background Monitor (For automated alerts)**

Start the portfolio monitoring service:
```bash
python ibkr_monitor.py
```

**Before starting**, edit `ibkr_monitor.py` to set your alerts:

```python
# Example: Alert when AAPL crosses $200
monitor.add_alert_condition(
    PriceAlertCondition(
        symbol='AAPL',
        condition_type='above',
        threshold=200.0
    )
)

# Example: Alert if TSLA drops 5%
current_tsla_price = 250.0  # Get current price first
monitor.add_alert_condition(
    PriceAlertCondition(
        symbol='TSLA',
        condition_type='percent_change_down',
        threshold=5.0,
        reference_price=current_tsla_price
    )
)

# Example: Alert if NVDA rises 3%
current_nvda_price = 880.0
monitor.add_alert_condition(
    PriceAlertCondition(
        symbol='NVDA',
        condition_type='percent_change_up',
        threshold=3.0,
        reference_price=current_nvda_price
    )
)
```

**What it does:**
- Checks prices every 60 seconds (configurable)
- Sends notifications when conditions are met
- Automatically gets AI analysis of price movements
- Monitors your entire portfolio for volatility
- Can generate daily summaries

---

### **PHASE 5: Customization** (Advanced)

#### Custom Alert Strategies

**1. Earnings Alert Strategy**
```python
# Before earnings, set tight alerts
monitor.add_alert_condition(
    PriceAlertCondition('NVDA', 'percent_change_up', 2.0, ref_price=880)
)
monitor.add_alert_condition(
    PriceAlertCondition('NVDA', 'percent_change_down', 2.0, ref_price=880)
)
```

**2. Stop-Loss Strategy**
```python
# Alert if position drops below your stop
monitor.add_alert_condition(
    PriceAlertCondition('AAPL', 'below', 180.0)  # Your stop loss price
)
```

**3. Take-Profit Strategy**
```python
# Alert when target price is reached
monitor.add_alert_condition(
    PriceAlertCondition('TSLA', 'above', 300.0)  # Your target
)
```

#### Daily Portfolio Summary

Add this to `ibkr_monitor.py` for automated daily summaries:

```python
import schedule
import time

# Schedule daily summary at 9 AM
schedule.every().day.at("09:00").do(monitor.generate_daily_summary)

# In your monitoring loop
while monitor.running:
    schedule.run_pending()
    monitor.check_price_alerts()
    time.sleep(60)
```

#### Custom Analysis Queries

Extend the agent with custom tools:

```python
from agno.tools import toolkit

@toolkit
def analyze_sector_exposure(portfolio_positions: str) -> str:
    """Analyze portfolio sector exposure"""
    # Your custom logic here
    return "Sector analysis results"

# Add to agent
agent.tools.append(analyze_sector_exposure)
```

---

## 🎓 Learning Path

### Week 1: Getting Started
- ✅ Set up and test connection
- ✅ Explore portfolio data in playground
- ✅ Set up 1-2 simple price alerts
- ✅ Test notifications

### Week 2: Active Monitoring
- ✅ Run background monitor daily
- ✅ Set up alerts for all positions
- ✅ Enable email/Slack notifications
- ✅ Review AI analyses

### Week 3: Advanced Usage
- ✅ Create custom alert strategies
- ✅ Set up daily summaries
- ✅ Integrate with your trading workflow
- ✅ Optimize notification preferences

### Week 4: Customization
- ✅ Build custom analysis tools
- ✅ Create sector rotation strategies
- ✅ Implement risk management rules
- ✅ Share insights with team (if applicable)

---

## 🔧 Troubleshooting

### Problem: "Could not connect to IBKR"

**Solutions:**
1. ✅ Check TWS/Gateway is running
2. ✅ Verify API is enabled (File → Global Configuration → API)
3. ✅ Confirm correct port in .env file
4. ✅ Check `127.0.0.1` is in Trusted IPs
5. ✅ Try different client_id in .env: `IBKR_CLIENT_ID=2`
6. ✅ Restart TWS/Gateway

### Problem: "No positions found"

**Solutions:**
1. ✅ Check you're using correct account (paper vs live)
2. ✅ Verify positions exist in TWS
3. ✅ Check account number in configuration
4. ✅ Try: `ibkr.ib.managedAccounts()` to see available accounts

### Problem: Email notifications not working

**Solutions:**
1. ✅ Use Gmail App Password, not regular password
2. ✅ Enable 2FA first, then create app password
3. ✅ Check SMTP settings match your provider
4. ✅ Test with simple script first
5. ✅ Check firewall/antivirus isn't blocking SMTP

### Problem: Price data seems delayed

**Explanation:**
- Real-time data requires market data subscription with IBKR
- Delayed data (15-20 min) provided for non-subscribed symbols
- Solution: Subscribe to real-time data in IBKR account settings

### Problem: Agent responses are slow

**Solutions:**
1. ✅ This is normal - AI analysis takes time
2. ✅ Consider using faster model if available
3. ✅ Reduce data requested in single query
4. ✅ Cache frequently requested data

---

## 📊 Architecture Overview

```
┌─────────────────────────────────────────┐
│  You (via Browser or Background Monitor)│
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│     XAI Finance Agent (Grok-beta)       │
│  • Natural Language Understanding        │
│  • Financial Analysis                    │
│  • Recommendation Engine                 │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│         AgentOS Framework                │
│  • Tool Orchestration                    │
│  • UI/API Layer                          │
│  • Session Management                    │
└───────────────┬─────────────────────────┘
                │
        ┌───────┴────────┐
        │                │
        ▼                ▼
┌──────────────┐  ┌─────────────────┐
│ IBKR Tools   │  │ Market Tools    │
│              │  │                 │
│ • Portfolio  │  │ • YFinance      │
│ • Positions  │  │ • Web Search    │
│ • Prices     │  │ • News          │
└──────┬───────┘  └─────────────────┘
       │
       ▼
┌──────────────────┐
│ Interactive      │
│ Brokers API      │
│ (TWS/Gateway)    │
└──────┬───────────┘
       │
       ▼
┌──────────────────────────┐
│ Notification Manager     │
│                          │
│ • Email (SMTP)           │
│ • Slack (Webhooks)       │
│ • Discord (Webhooks)     │
│ • Console                │
└──────────────────────────┘
```

---

## 🚀 Next Steps

After completing setup:

1. **Join the Community**
   - Star the [GitHub repo](https://github.com/Shubhamsaboo/awesome-llm-apps)
   - Share your experience
   - Contribute improvements

2. **Enhance Your Agent**
   - Add custom tools
   - Create trading strategies
   - Build dashboards
   - Integrate with other services

3. **Learn More**
   - [IBKR API Docs](https://interactivebrokers.github.io/tws-api/)
   - [xAI Documentation](https://docs.x.ai/)
   - [AgentOS Guides](https://docs.agno.com/)

4. **Stay Updated**
   - Watch repo for updates
   - Follow xAI releases
   - Monitor IBKR API changes

---

## ⚠️ Important Notes

### Risk Disclaimer
- This is a monitoring and analysis tool, not a trading bot
- Always verify AI recommendations with your own research
- Past performance doesn't guarantee future results
- Consult financial advisors for investment decisions
- Start with paper trading to test

### Security
- Never share your API keys or .env file
- Keep TWS/Gateway updated
- Use strong passwords
- Enable 2FA on all accounts
- Regularly review API permissions

### Compliance
- Ensure usage complies with IBKR Terms of Service
- Follow your jurisdiction's trading regulations
- Keep records of automated alerts
- Review broker's API usage limits

---

## 📞 Support

**Having Issues?**
1. Check this guide first
2. Review the troubleshooting section
3. Check the [Issues](https://github.com/Shubhamsaboo/awesome-llm-apps/issues) page
4. Open a new issue with details

**Want to Contribute?**
- Fork the repository
- Make improvements
- Submit pull request
- Share your custom tools/strategies

---

**Happy Trading! 🚀📈**

Remember: The best investment you can make is in your own education. Use this tool to learn, analyze, and make informed decisions!
