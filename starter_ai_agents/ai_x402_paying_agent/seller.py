"""Local x402 seller — a tiny paid API you run yourself.

Two endpoints, priced in fractions of a cent, paid in testnet USDC on Base Sepolia
through the public x402.org facilitator. Nothing here costs real money: the buyer
funds their wallet from a free faucet, and you are the seller, so every payment in
this tutorial goes from your test wallet to your own address.

Usage:
    export SELLER_ADDRESS='0x...'   # any EVM address you control (it just receives)
    uvicorn seller:app --port 4021

SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import os
import random
import sys
from datetime import datetime, timezone

from fastapi import FastAPI
from x402 import x402ResourceServer
from x402.http import HTTPFacilitatorClient  # defaults to https://x402.org/facilitator (testnet)
from x402.http.middleware.fastapi import payment_middleware
from x402.mechanisms.evm.exact.server import ExactEvmScheme

PAY_TO = os.environ.get("SELLER_ADDRESS")
if not PAY_TO:
    sys.exit("Set SELLER_ADDRESS to an EVM address that should receive the (testnet) payments.")

NETWORK = "eip155:84532"  # Base Sepolia; the facilitator settles testnet USDC for free

server = x402ResourceServer(HTTPFacilitatorClient())
server.register(NETWORK, ExactEvmScheme())

ROUTES = {
    "GET /api/fortune": {"accepts": {"scheme": "exact", "network": NETWORK, "payTo": PAY_TO, "price": "$0.001"}},
    "GET /api/dice": {"accepts": {"scheme": "exact", "network": NETWORK, "payTo": PAY_TO, "price": "$0.002"}},
}

app = FastAPI(title="x402 demo seller")
app.middleware("http")(payment_middleware(ROUTES, server))

FORTUNES = [
    "The bug you are hunting is in the file you refuse to reopen.",
    "A small refactor today prevents a large rewrite in December.",
    "Your next deploy will be boring. This is the highest compliment.",
    "Trust the failing test; it is the only one telling the truth.",
    "You will receive a pull request you actually enjoy reviewing.",
    "An agent that can pay for data never has to beg for API keys.",
]


@app.get("/api/fortune")
def fortune():
    return {
        "fortune": random.choice(FORTUNES),
        "issued_at": datetime.now(timezone.utc).isoformat(),
        "paid": True,
    }


@app.get("/api/dice")
def dice(sides: int = 20):
    sides = max(2, min(sides, 1000))
    return {
        "roll": random.randint(1, sides),
        "sides": sides,
        "rolled_at": datetime.now(timezone.utc).isoformat(),
        "paid": True,
    }
