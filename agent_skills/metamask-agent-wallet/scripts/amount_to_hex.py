#!/usr/bin/env python3
"""Convert a human-readable token amount to 0x-prefixed hex for EVM calldata.

Usage:
    python3 amount_to_hex.py <amount> <decimals>

Examples:
    python3 amount_to_hex.py 1.5 18       # 1.5 ETH  -> 0x14d1120d7b160000
    python3 amount_to_hex.py 100 6        # 100 USDC -> 0x5f5e100
    python3 amount_to_hex.py 0.001 8      # 0.001 WBTC -> 0x186a0
"""

import sys
from decimal import Decimal, InvalidOperation, localcontext


def fail(message):
    print(f"error: {message}", file=sys.stderr)
    sys.exit(1)


if len(sys.argv) != 3:
    print(f"Usage: {sys.argv[0]} <amount> <decimals>", file=sys.stderr)
    sys.exit(1)

raw_amount, raw_decimals = sys.argv[1], sys.argv[2]

if not raw_decimals.isdigit() or int(raw_decimals) > 255:
    fail(f"decimals must be an integer from 0 to 255, got {raw_decimals!r}")
decimals = int(raw_decimals)

try:
    amount = Decimal(raw_amount)
except InvalidOperation:
    fail(f"amount is not a number: {raw_amount!r}")
if not amount.is_finite() or amount < 0:
    fail(f"amount must be a finite, non-negative number, got {raw_amount!r}")

with localcontext() as ctx:
    # Enough precision that scaling never rounds a large amount.
    ctx.prec = 400
    scaled = amount.scaleb(decimals)
if scaled != scaled.to_integral_value():
    # Refuse rather than truncate: submitting a smaller amount than the user
    # asked for is worse than stopping.
    fail(f"{raw_amount} has more than {decimals} decimal places and cannot be represented exactly")

print(hex(int(scaled)))
