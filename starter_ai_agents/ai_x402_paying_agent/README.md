## 💸 AI x402 Paying Agent

An AI agent with its own crypto wallet that **pays for the data it needs** — no API keys, no subscriptions, no signup.

Ask a question in plain English. Claude decides which paid API answers it and calls a fetch tool. The API responds `402 Payment Required` with a price quote; the agent automatically pays it (a few cents in USDC on Base, via the open [x402](https://www.x402.org/) standard, now under the Linux Foundation) and answers from the data it just bought.

This is the payment rail built for AI agents: machine-speed, per-call, no account anywhere.

### Features

- **Agent-driven tool use** — Claude picks the right paid endpoint for the question and quotes the returned data
- **Automatic 402 payment** — the `x402` SDK signs a USDC payment on Base when an API challenges; typical calls cost $0.015–0.02
- **Hard budget cap** — a per-call price ceiling (`MAX_PRICE_USDC`, default $0.05) so a misconfigured agent can never overspend
- **No-LLM mode** — `--direct <URL>` pays and fetches any x402 URL with just a wallet, so you can see the payment flow in isolation
- **Generic** — the demo points at three live endpoints (memecoin rug-check, ERC-20 honeypot check, stablecoin vault APYs), but the payment code works with any x402-enabled API

> **Disclosure:** the demo endpoints are run by the tutorial author's company ([PulseNetwork](https://pulse.theaslangroupllc.com)). The agent code is vendor-neutral — point it at any x402 seller.

### How to get Started?

1. Clone the GitHub repository

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/starter_ai_agents/ai_x402_paying_agent
```

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Fund a wallet

Create a fresh EVM wallet (e.g. in MetaMask) and send it **$1 of USDC on Base** plus nothing else — x402 payments need no gas token. Export the private key:

```bash
export X402_PRIVATE_KEY='0x...'
```

⚠️ Use a dedicated throwaway wallet for agent spending — never your main wallet.

4. Set your Anthropic API key (skip for `--direct` mode)

```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

5. Run the agent

```bash
# Full agent: natural-language question → paid data → answer
python x402_paying_agent.py "What are the best stablecoin vault APYs right now?"

python x402_paying_agent.py "Run a safety check on the BONK token: DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"

# Payment flow only, no LLM needed:
python x402_paying_agent.py --direct "https://onchainpulse.theaslangroupllc.com/api/vault-apy"
```

### How it works

```
you ──question──▶ Claude ──tool call──▶ GET paid API
                                          │ 402 Payment Required ($0.02)
                                          ▼
                                   x402 SDK signs USDC payment
                                          │ retry with payment header
                                          ▼
                                     200 OK + data ──▶ Claude answers
```

The whole payment negotiation is 3 HTTP requests and settles on-chain in seconds. A run of this demo costs a few cents total.
