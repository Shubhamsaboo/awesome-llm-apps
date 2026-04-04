"""
AI Trading Intelligence Agent Team
===================================
Multi-agent adversarial debate system for trading decisions.

Architecture:
  1. Market Analyst  — fetches data + computes technical indicators (local)
  2. Bull AI         — argues the bullish case (Claude Haiku)
  3. Bear AI         — argues the bearish case (Claude Haiku)
  4. Judge AI        — synthesizes both sides, makes final call (Claude Sonnet)
  5. Risk Manager    — computes entry/stop/target (Claude Haiku)

Cost: ~$0.003 per analysis (80% Haiku, 20% Sonnet)
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import json
from datetime import datetime

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="AI Trading Intelligence", page_icon="📈", layout="wide")

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("📈 AI Trading Intelligence")
    st.caption("Multi-agent adversarial debate system")
    api_key = st.text_input("Anthropic API Key", type="password", help="Get from console.anthropic.com")
    ticker = st.text_input("Ticker", value="NVDA").upper()
    run = st.button("🔍 Analyze", type="primary", use_container_width=True)
    st.divider()
    st.markdown("""
    **How it works:**
    1. 📊 Fetch market data + indicators
    2. 🐂 Bull AI argues the case
    3. 🐻 Bear AI argues against
    4. ⚖️ Judge AI makes the call
    5. 🎯 Risk plan: entry/stop/target

    **Cost:** ~$0.003 per analysis

    [Full Project →](https://github.com/alex-jb/orallexa-ai-trading-agent)
    """)


# ── Technical Analysis ───────────────────────────────────────────────────────
def compute_indicators(df: pd.DataFrame) -> dict:
    """Compute key technical indicators and return a summary dict."""
    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    # Moving averages
    ma20 = close.rolling(20).mean()
    ma50 = close.rolling(50).mean()

    # RSI
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss.replace(0, 1e-9)
    rsi = 100 - (100 / (1 + rs))

    # MACD
    ema12 = close.ewm(span=12).mean()
    ema26 = close.ewm(span=26).mean()
    macd = ema12 - ema26
    macd_signal = macd.ewm(span=9).mean()
    macd_hist = macd - macd_signal

    # Bollinger Bands
    bb_mid = close.rolling(20).mean()
    bb_std = close.rolling(20).std()
    bb_upper = bb_mid + 2 * bb_std
    bb_lower = bb_mid - 2 * bb_std
    bb_pct = (close - bb_lower) / (bb_upper - bb_lower).replace(0, 1e-9)

    # ADX
    tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
    atr = tr.rolling(14).mean()
    plus_dm = (high - high.shift()).where((high - high.shift()) > (low.shift() - low), 0).clip(lower=0)
    minus_dm = (low.shift() - low).where((low.shift() - low) > (high - high.shift()), 0).clip(lower=0)
    plus_di = 100 * (plus_dm.rolling(14).mean() / atr.replace(0, 1e-9))
    minus_di = 100 * (minus_dm.rolling(14).mean() / atr.replace(0, 1e-9))
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, 1e-9)
    adx = dx.rolling(14).mean()

    # Volume
    vol_avg = volume.rolling(20).mean()
    vol_ratio = (volume / vol_avg.replace(0, 1e-9)).iloc[-1]

    return {
        "close": round(float(close.iloc[-1]), 2),
        "ma20": round(float(ma20.iloc[-1]), 2),
        "ma50": round(float(ma50.iloc[-1]), 2),
        "rsi": round(float(rsi.iloc[-1]), 1),
        "macd_hist": round(float(macd_hist.iloc[-1]), 4),
        "bb_pct": round(float(bb_pct.iloc[-1]), 2),
        "bb_upper": round(float(bb_upper.iloc[-1]), 2),
        "bb_lower": round(float(bb_lower.iloc[-1]), 2),
        "adx": round(float(adx.iloc[-1]), 1),
        "plus_di": round(float(plus_di.iloc[-1]), 1),
        "minus_di": round(float(minus_di.iloc[-1]), 1),
        "volume_ratio": round(float(vol_ratio), 2),
        "atr_pct": round(float(atr.iloc[-1] / close.iloc[-1] * 100), 2),
    }


# ── LLM Agents ───────────────────────────────────────────────────────────────
HAIKU = "claude-haiku-4-5-20251001"
SONNET = "claude-sonnet-4-6-20250514"


def call_claude(api_key: str, model: str, system: str, prompt: str, max_tokens: int = 500) -> str:
    """Call Claude API and return text response."""
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    resp = client.messages.create(
        model=model, max_tokens=max_tokens, system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text.strip()


def run_bull(api_key: str, ticker: str, summary: dict) -> str:
    system = "You are a bullish trading analyst. Your job is to find the STRONGEST case for buying this stock right now. Be specific, use the data provided, and be convincing."
    prompt = f"""Analyze {ticker} (${summary['close']}) and make the BULL case.

Technical Data:
- Price vs MA20: {'above' if summary['close'] > summary['ma20'] else 'below'} (MA20=${summary['ma20']}, MA50=${summary['ma50']})
- RSI: {summary['rsi']}
- MACD Histogram: {summary['macd_hist']}
- Bollinger %B: {summary['bb_pct']} (upper=${summary['bb_upper']}, lower=${summary['bb_lower']})
- ADX: {summary['adx']} (+DI={summary['plus_di']}, -DI={summary['minus_di']})
- Volume: {summary['volume_ratio']}x average
- ATR: {summary['atr_pct']}% of price

Give exactly 3 bullish arguments. Each must reference specific data points. Be direct and opinionated. Max 150 words total."""
    return call_claude(api_key, HAIKU, system, prompt)


def run_bear(api_key: str, ticker: str, summary: dict) -> str:
    system = "You are a bearish trading analyst. Your job is to find the STRONGEST case AGAINST buying this stock right now. Look for risks, overextension, and warning signs."
    prompt = f"""Analyze {ticker} (${summary['close']}) and make the BEAR case.

Technical Data:
- Price vs MA20: {'above' if summary['close'] > summary['ma20'] else 'below'} (MA20=${summary['ma20']}, MA50=${summary['ma50']})
- RSI: {summary['rsi']}
- MACD Histogram: {summary['macd_hist']}
- Bollinger %B: {summary['bb_pct']} (upper=${summary['bb_upper']}, lower=${summary['bb_lower']})
- ADX: {summary['adx']} (+DI={summary['plus_di']}, -DI={summary['minus_di']})
- Volume: {summary['volume_ratio']}x average
- ATR: {summary['atr_pct']}% of price

Give exactly 3 bearish arguments. Each must reference specific data points. Be direct and opinionated. Max 150 words total."""
    return call_claude(api_key, HAIKU, system, prompt)


def run_judge(api_key: str, ticker: str, summary: dict, bull_case: str, bear_case: str) -> dict:
    system = "You are an impartial trading judge. You weigh Bull and Bear arguments and make the final call. You must pick a side — no 'it depends'. Be decisive."
    prompt = f"""{ticker} at ${summary['close']}. RSI={summary['rsi']}, ADX={summary['adx']}, Vol={summary['volume_ratio']}x.

BULL CASE:
{bull_case}

BEAR CASE:
{bear_case}

Output ONLY valid JSON (no markdown):
{{"decision": "BUY|SELL|WAIT", "confidence": 65, "verdict": "2-3 sentence ruling explaining which side won and why", "risk_level": "LOW|MEDIUM|HIGH", "entry": {summary['close']}, "stop_loss": 0.0, "take_profit": 0.0, "position_pct": 5}}

Rules:
- decision: BUY, SELL, or WAIT
- confidence: 30-95 (never 100%)
- stop_loss / take_profit: actual dollar prices based on support/resistance
- position_pct: 1-10 (% of portfolio)"""
    text = call_claude(api_key, SONNET, system, prompt, max_tokens=400)
    text = text.replace("```json", "").replace("```", "").strip()
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1:
        return json.loads(text[start:end + 1])
    return {"decision": "WAIT", "confidence": 40, "verdict": text, "risk_level": "MEDIUM"}


# ── Main UI ──────────────────────────────────────────────────────────────────
if not run:
    st.title("📈 AI Trading Intelligence Agent Team")
    st.markdown("""
    ### How it works

    Most AI trading tools give you a number: *"BUY 73%"*. But **why?**

    This system runs an **adversarial debate**:

    | Agent | Role | Model | Cost |
    |-------|------|-------|------|
    | 🐂 Bull AI | Argues FOR buying | Claude Haiku | ~$0.001 |
    | 🐻 Bear AI | Argues AGAINST buying | Claude Haiku | ~$0.001 |
    | ⚖️ Judge AI | Makes the final call | Claude Sonnet | ~$0.005 |

    **Total cost: ~$0.003 per analysis** — 10x cheaper than GPT-4.

    Enter a ticker in the sidebar and click **Analyze** to see it in action.

    ---

    *Part of [Orallexa](https://github.com/alex-jb/orallexa-ai-trading-agent) — AI Trading Operating System with 9 ML models, walk-forward evaluation, and real-time dashboard.*
    """)
    st.stop()

if not api_key:
    st.error("Please enter your Anthropic API key in the sidebar.")
    st.stop()

# ── Run Analysis Pipeline ────────────────────────────────────────────────────
with st.spinner(f"📊 Fetching {ticker} data..."):
    try:
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)
        if df.empty:
            st.error(f"No data found for {ticker}")
            st.stop()
        # Flatten MultiIndex if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        summary = compute_indicators(df)
    except Exception as e:
        st.error(f"Failed to fetch data: {e}")
        st.stop()

# Show price + indicators
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(f"{ticker} Price", f"${summary['close']}")
with col2:
    rsi_delta = summary["rsi"] - 50
    st.metric("RSI", f"{summary['rsi']}", delta=f"{rsi_delta:+.0f} from neutral")
with col3:
    st.metric("ADX (Trend)", f"{summary['adx']}", delta="Strong" if summary["adx"] > 25 else "Weak")
with col4:
    st.metric("Volume", f"{summary['volume_ratio']}x avg", delta="High" if summary["volume_ratio"] > 1.5 else "Normal")

st.divider()

# ── Adversarial Debate ───────────────────────────────────────────────────────
col_bull, col_bear = st.columns(2)

with col_bull:
    with st.spinner("🐂 Bull AI analyzing..."):
        bull_case = run_bull(api_key, ticker, summary)
    st.markdown("### 🐂 Bull Case")
    st.success(bull_case)

with col_bear:
    with st.spinner("🐻 Bear AI analyzing..."):
        bear_case = run_bear(api_key, ticker, summary)
    st.markdown("### 🐻 Bear Case")
    st.error(bear_case)

st.divider()

# ── Judge Verdict ────────────────────────────────────────────────────────────
with st.spinner("⚖️ Judge deliberating..."):
    result = run_judge(api_key, ticker, summary, bull_case, bear_case)

decision = result.get("decision", "WAIT")
confidence = result.get("confidence", 50)
verdict = result.get("verdict", "")
risk = result.get("risk_level", "MEDIUM")

# Decision display
dec_color = {"BUY": "green", "SELL": "red", "WAIT": "orange"}.get(decision, "gray")
dec_emoji = {"BUY": "🟢", "SELL": "🔴", "WAIT": "🟡"}.get(decision, "⚪")

st.markdown(f"## ⚖️ Judge Verdict: {dec_emoji} **:{dec_color}[{decision}]** ({confidence}% confidence)")
st.info(f"**Ruling:** {verdict}")

# Risk plan
col_a, col_b, col_c, col_d = st.columns(4)
with col_a:
    st.metric("Entry", f"${result.get('entry', summary['close']):.2f}")
with col_b:
    sl = result.get("stop_loss", 0)
    st.metric("Stop Loss", f"${sl:.2f}" if sl else "—")
with col_c:
    tp = result.get("take_profit", 0)
    st.metric("Take Profit", f"${tp:.2f}" if tp else "—")
with col_d:
    st.metric("Position Size", f"{result.get('position_pct', 5)}%")

if result.get("stop_loss") and result.get("take_profit") and result.get("entry"):
    entry = result["entry"]
    sl = result["stop_loss"]
    tp = result["take_profit"]
    risk_amt = abs(entry - sl)
    reward_amt = abs(tp - entry)
    rr = reward_amt / risk_amt if risk_amt > 0 else 0
    st.caption(f"Risk/Reward: **{rr:.1f}:1** | Risk: ${risk_amt:.2f} | Reward: ${reward_amt:.2f}")

st.divider()
st.caption("⚠️ AI-generated analysis for research only. Not financial advice. Trade at your own risk.")
st.caption(f"Powered by [Orallexa](https://github.com/alex-jb/orallexa-ai-trading-agent) | Cost: ~$0.003 | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
