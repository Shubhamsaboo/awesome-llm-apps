# Orallexa — AI Trading Operating System 📊

**9 ML models. Adversarial reasoning. One-click execution.**

[Orallexa](https://github.com/alex-jb/orallexa-ai-trading-agent) is an end-to-end AI trading intelligence system that runs 9 ML models simultaneously, synthesizes their signals through Claude AI reasoning, and executes paper trades automatically.

**👉 [GitHub Repository](https://github.com/alex-jb/orallexa-ai-trading-agent) | [Live Demo](https://orallexa-ui.vercel.app)**

## Features

- **9 ML Model Ensemble**
    - Random Forest, XGBoost, Logistic Regression (classical ML)
    - EMAformer Transformer (AAAI 2026 architecture)
    - Salesforce MOIRAI-2, Amazon Chronos-2 (foundation models)
    - DDPM Diffusion generating 50 probabilistic price paths
    - PPO Reinforcement Learning with Sharpe-based reward
    - Graph Attention Network propagating signals across 17 related stocks
    - All models scored and ranked by Sharpe ratio automatically

- **Claude AI Synthesis Layer**
    - Structured reasoning with transparent probability breakdown
    - Risk plan with entry, stop-loss, and target levels
    - Dual-tier model routing: Haiku for speed (~$0.001), Sonnet for depth (~$0.005)
    - Cost per full analysis: ~$0.003

- **Real-time Dashboard**
    - Next.js 16 + React 19 with Art Deco dark theme
    - Live WebSocket price streaming every 5 seconds
    - ML Scoreboard showing all 9 models side-by-side
    - Signal change detection and breaking alerts
    - EN/ZH bilingual support

- **Daily Intelligence Pipeline**
    - 50+ ticker market scan with parallel fetch
    - Sector rotation detection across 13 ETFs
    - FinBERT sentiment analysis on live news
    - AI morning brief with conviction picks
    - One-click social content generation

- **Paper Trading Execution**
    - Alpaca integration with bracket orders
    - Automated stop-loss and take-profit
    - Decision execution log and trade journal

- **Desktop AI Coach**
    - Floating pixel bull assistant
    - Voice input (Whisper) + voice output (TTS)
    - Screenshot any chart for Claude Vision analysis

## How to Run

1. Clone the repository:
```bash
git clone https://github.com/alex-jb/orallexa-ai-trading-agent.git
cd orallexa-ai-trading-agent
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
echo "ANTHROPIC_API_KEY=your_key" > .env
```

3. Start the API server:
```bash
python api_server.py
```

4. Start the dashboard:
```bash
cd orallexa-ui && npm install && npm run dev
```

5. Open http://localhost:3000

Or use Docker: `docker compose up --build`

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | FastAPI, Python 3.11 |
| Frontend | Next.js 16, React 19, Tailwind CSS 4 |
| AI | Claude Sonnet 4.6 + Haiku 4.5 |
| ML | scikit-learn, XGBoost, PyTorch |
| Data | yfinance |
| NLP | FinBERT, VADER |
| Trading | Alpaca paper trading |
| Orchestration | LangGraph |
