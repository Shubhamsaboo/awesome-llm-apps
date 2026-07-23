"""AI x402 Paying Agent — an agent that pays for its own data with USDC micropayments.

Ask a question → Claude picks a paid API → the agent hits it, gets an HTTP 402
Payment Required challenge, pays a few cents in USDC on Base from its own wallet,
and answers with the data. No API keys, no subscriptions, no signup.

Usage:
    python x402_paying_agent.py "Is this Solana memecoin a rug? <mint address>"
    python x402_paying_agent.py --direct "https://onchainpulse.theaslangroupllc.com/api/vault-apy"

SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from decimal import Decimal

import httpx
from eth_account import Account
from x402 import x402Client
from x402.http.clients.httpx import x402HttpxClient
from x402.mechanisms.evm import EthAccountSigner
from x402.mechanisms.evm.exact import ExactEvmScheme

USDC_DECIMALS = 6  # 1 USDC = 10**6 atomic units; x402 amounts are atomic strings

# Demo catalog: real pay-per-call endpoints (USDC on Base, a few cents each).
# The payment code is generic — swap in any x402-enabled API.
DEMO_ENDPOINTS = """
Available paid data endpoints (x402, USDC on Base):

1. Solana memecoin safety check — $0.015/call
   GET https://onchainpulse.theaslangroupllc.com/api/memecoin?mint=<solana_mint_address>
   Rug-pull risk signals for a Solana token: mint/freeze authority, holder concentration, liquidity.

2. EVM token safety check — $0.015/call
   GET https://onchainpulse.theaslangroupllc.com/api/evmtoken?address=<0x_token_address>&chain=<base|ethereum|...>
   Honeypot and contract-risk signals for an ERC-20 token.

3. Stablecoin vault APY rankings — $0.02/call
   GET https://onchainpulse.theaslangroupllc.com/api/vault-apy
   Live APY comparison across on-chain USDC/stablecoin yield vaults.
"""

SYSTEM_PROMPT = f"""You are a data agent with a crypto wallet. You can call paid APIs — when one
responds with HTTP 402 Payment Required, your fetch tool automatically pays the quoted price
in USDC and retrieves the data.

{DEMO_ENDPOINTS}

When the user's question maps to one of these endpoints, call fetch_paid_api with the full URL
(including query parameters). Answer from the returned data only — quote the key numbers.
If the question doesn't match any endpoint, say so instead of guessing."""

TOOLS = [
    {
        "name": "fetch_paid_api",
        "description": (
            "Fetch a URL, automatically paying an x402 HTTP 402 challenge in USDC if the API "
            "requires payment. Call this when the user's question requires paid data. "
            "Returns the response body as JSON text."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Full URL to fetch, including any query parameters.",
                }
            },
            "required": ["url"],
        },
    }
]


def build_paying_client(private_key: str, max_price_usdc: Decimal) -> httpx.AsyncClient:
    """httpx client that auto-pays 402 challenges, refusing anything above max_price_usdc."""
    signer = EthAccountSigner(Account.from_key(private_key))
    client = x402Client()
    cap_atomic = int(max_price_usdc * (10**USDC_DECIMALS))

    def _budget_cap(version, accepts):
        allowed = [
            a
            for a in accepts
            if int(getattr(a, "amount", None) or getattr(a, "max_amount_required", 0) or 0) <= cap_atomic
        ]
        if not allowed:
            raise ValueError(
                f"Refusing to pay: cheapest payment option exceeds the ${max_price_usdc} per-call cap. "
                "Raise MAX_PRICE_USDC if this is intentional."
            )
        return allowed

    client.register_policy(_budget_cap)
    client.register("eip155:*", ExactEvmScheme(signer))
    return x402HttpxClient(client, follow_redirects=True, timeout=60.0)


async def paid_fetch(url: str, private_key: str, max_price_usdc: Decimal) -> str:
    async with build_paying_client(private_key, max_price_usdc) as client:
        resp = await client.get(url)
        if resp.status_code != 200:
            return f"Request failed: HTTP {resp.status_code}: {resp.text[:300]}"
        return resp.text


def run_agent(question: str, private_key: str, max_price_usdc: Decimal) -> None:
    import anthropic

    client = anthropic.Anthropic()
    model = os.environ.get("CLAUDE_MODEL", "claude-opus-4-8")
    messages = [{"role": "user", "content": question}]

    while True:
        response = client.messages.create(
            model=model,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )
        if response.stop_reason != "tool_use":
            for block in response.content:
                if block.type == "text":
                    print(block.text)
            return

        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                url = block.input["url"]
                print(f"→ fetching (paying if challenged): {url}", file=sys.stderr)
                try:
                    result = asyncio.run(paid_fetch(url, private_key, max_price_usdc))
                except Exception as exc:  # payment refused, network error, etc.
                    result = f"Error: {exc}"
                tool_results.append(
                    {"type": "tool_result", "tool_use_id": block.id, "content": result}
                )
        messages.append({"role": "user", "content": tool_results})


def main() -> None:
    parser = argparse.ArgumentParser(description="AI agent that pays for its own data via x402")
    parser.add_argument("question", nargs="?", help="Question for the agent")
    parser.add_argument(
        "--direct",
        metavar="URL",
        help="Skip the LLM: pay-and-fetch this URL directly and print the JSON (wallet only, no Anthropic key needed)",
    )
    args = parser.parse_args()

    private_key = os.environ.get("X402_PRIVATE_KEY")
    if not private_key:
        sys.exit("Set X402_PRIVATE_KEY to a wallet private key holding a little USDC on Base.")
    max_price = Decimal(os.environ.get("MAX_PRICE_USDC", "0.05"))

    if args.direct:
        body = asyncio.run(paid_fetch(args.direct, private_key, max_price))
        try:
            print(json.dumps(json.loads(body), indent=2))
        except json.JSONDecodeError:
            print(body)
        return

    if not args.question:
        parser.error("Provide a question, or use --direct <URL>")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Set ANTHROPIC_API_KEY (or use --direct <URL> for the no-LLM payment demo).")
    run_agent(args.question, private_key, max_price)


if __name__ == "__main__":
    main()
