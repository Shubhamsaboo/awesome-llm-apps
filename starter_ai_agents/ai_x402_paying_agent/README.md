## 💸 AI x402 Paying Agent

An AI agent with its own crypto wallet that **pays for the data it needs** — no API keys, no subscriptions, no signup.

Ask a question in plain English. Claude decides which paid API answers it and calls a fetch tool. The API responds `402 Payment Required` with a price quote; the agent automatically pays it in USDC via the open [x402](https://www.x402.org/) standard (now under the Linux Foundation) and answers from the data it just bought.

**Everything in this tutorial is free and self-contained.** You run the paid API yourself (`seller.py`, ~60 lines), payments settle in *testnet* USDC on Base Sepolia through the public [x402.org facilitator](https://www.x402.org/), and the buyer wallet is funded from a free faucet. You are both the buyer and the seller, so you watch the full payment loop with zero real money involved. The exact same agent code works on mainnet against any live x402 API.

### Features

- **Agent-driven tool use** — Claude picks the right paid endpoint for the question and quotes the returned data
- **Automatic 402 payment** — the `x402` SDK signs a USDC payment when an API challenges; the demo endpoints cost $0.001–0.002 in testnet USDC
- **Hard budget cap** — a per-call price ceiling (`MAX_PRICE_USDC`, default $0.05) so a misconfigured agent can never overspend
- **No-LLM mode** — `--direct <URL>` pays and fetches any x402 URL with just a wallet, so you can see the payment flow in isolation
- **Your own seller** — `seller.py` is a complete pay-per-call API in ~60 lines of FastAPI; reprice it, add endpoints, or point the agent at any other x402 seller

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

3. Create two throwaway wallets (buyer and seller)

Any EVM wallet works (MetaMask, or `python -c "from eth_account import Account; a=Account.create(); print(a.address, a.key.hex())"`). You need:

- a **buyer** wallet the agent spends from — export its private key
- a **seller** address that receives the payments — any second address you control (it only receives; it needs no funds and no key on the server)

```bash
export X402_PRIVATE_KEY='0x...'   # buyer wallet private key
export SELLER_ADDRESS='0x...'     # seller receive address
```

⚠️ Use dedicated throwaway wallets for this — never your main wallet.

4. Fund the buyer with free testnet USDC

Go to [faucet.circle.com](https://faucet.circle.com), pick **Base Sepolia**, paste the buyer address. You get test USDC instantly; no gas token is needed anywhere (x402 payments are gasless for both sides).

5. Start your paid API (terminal 1)

```bash
uvicorn seller:app --port 4021
```

Try it unpaid and watch the 402 challenge: `curl -i http://localhost:4021/api/fortune`

6. Set your Anthropic API key (skip for `--direct` mode)

```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

7. Run the agent (terminal 2)

```bash
# Full agent: natural-language question → paid data → answer
python x402_paying_agent.py "Roll me a d20 and read me my fortune"

# Payment flow only, no LLM needed:
python x402_paying_agent.py --direct "http://localhost:4021/api/fortune"
```

### How it works

```
you ──question──▶ Claude ──tool call──▶ GET your local paid API
                                          │ 402 Payment Required ($0.001)
                                          ▼
                                   x402 SDK signs USDC payment
                                          │ retry with payment header
                                          ▼
                              facilitator verifies + settles on Base Sepolia
                                          │
                                     200 OK + data ──▶ Claude answers
```

The whole payment negotiation is 3 HTTP requests and settles on-chain in seconds — and because you run the seller, you can watch both sides of it.

### Beyond the demo

- **Point it at the real economy** — swap the URL for any live x402-enabled API on a mainnet network; the agent code is identical. Directories of live x402 endpoints are linked from [x402.org](https://www.x402.org/).
- **Going to production: managed wallets** — this demo keeps the wallet as a raw private key so you can see every moving part. For a production agent, Coinbase's [CDP x402 SDK](https://docs.cdp.coinbase.com/x402/core-concepts/cdp-sdk) wraps the same open standard with managed wallets (no private key to store), client-side spend controls (per-payment caps, rolling daily limits, payee allowlists), and hosted settlement. The `MAX_PRICE_USDC` guard in this tutorial is a minimal version of the same idea — cap what an autonomous spender can spend before it spends it.
