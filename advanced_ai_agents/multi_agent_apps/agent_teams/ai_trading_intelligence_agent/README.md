# 📈 AI Trading Intelligence Agent Team

A multi-agent AI trading system where **Bull and Bear AIs debate** before every decision. Uses 3 specialized Claude AI agents (Bull Analyst, Bear Analyst, Judge) plus technical analysis to produce structured trading signals with transparent reasoning.

## Features

- **Adversarial Debate**: Bull AI argues for, Bear AI argues against, Judge AI makes the final call
- **Technical Analysis**: 20+ indicators (RSI, MACD, Bollinger Bands, ADX, etc.) via yfinance
- **Risk Management**: Entry, stop-loss, take-profit with risk/reward ratio
- **Transparent Reasoning**: Every decision shows exactly why — not just "BUY 73%"
- **Cost Efficient**: ~$0.003 per analysis using Haiku + Sonnet dual-tier routing

## How It Works

```
Market Data → Technical Indicators → Bull AI (Haiku) → Bear AI (Haiku) → Judge (Sonnet) → Decision + Risk Plan
```

Each analysis produces:
- **Decision**: BUY / SELL / WAIT with confidence %
- **Bull Case**: 3 bullish arguments with data
- **Bear Case**: 3 bearish arguments with data
- **Judge Verdict**: Final ruling with reasoning
- **Risk Plan**: Entry, stop-loss, target, position size

## Getting Started

1. Get your Anthropic API key from [console.anthropic.com](https://console.anthropic.com)

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the app:
```bash
streamlit run ai_trading_intelligence_agent.py
```

4. Enter your API key in the sidebar and analyze any stock!

## Full Project

This is a standalone demo. The full system includes 9 ML models, walk-forward evaluation, real-time dashboard, and paper trading:

**[Orallexa — Full AI Trading OS](https://github.com/alex-jb/orallexa-ai-trading-agent)** | **[Live Demo](https://orallexa-ui.vercel.app)**
