#!/usr/bin/env python3
"""Deterministic eval for the metamask-agent-wallet skill.

Exercises the skill's two bundled scripts without a real wallet or network:

- scripts/amount_to_hex.py converts exact amounts and refuses ones it cannot
  represent, instead of truncating them.
- scripts/x402_pay.py runs against a stub `mm` on PATH (it prints a Node
  warning and an AWAITING_MFA NDJSON notice, like the real CLI) and a loopback
  x402 server whose offer and receipt each test controls. It checks approval
  binding, settlement reporting, chain support, and the MCP path.

    python3 agent_skills/evals/metamask-agent-wallet/test_metamask_agent_wallet.py

Python stdlib only. Everything runs in a temp dir on 127.0.0.1.
"""

import base64
import json
import os
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "..", "metamask-agent-wallet", "scripts")
AMOUNT = os.path.join(SCRIPTS, "amount_to_hex.py")
X402 = os.path.join(SCRIPTS, "x402_pay.py")
PAY_TO = "0x" + "d" * 40
ASSET = "0x" + "e" * 40
checks = []


def check(name, condition, detail=""):
    checks.append(bool(condition))
    status = "PASS" if condition else "FAIL"
    suffix = " - %s" % detail if detail and not condition else ""
    print("  %s %s%s" % (status, name, suffix))


def run(args, env=None):
    result = subprocess.run(
        [sys.executable, *args], capture_output=True, text=True, env=env, timeout=60
    )
    return result.returncode, result.stdout, result.stderr


FAKE_MM = r'''#!/usr/bin/env python3
import json, sys
a = sys.argv[1:]
if a[:2] == ["chains", "list"]:
    print("(node:1) ExperimentalWarning: fetch is experimental")
    print(json.dumps({"ok": True, "data": {"chains": [
        {"key": "base", "name": "Base", "chainId": 8453, "caip2": "eip155:8453"}]}}))
elif a[:2] == ["token", "assets"]:
    print(json.dumps({"ok": True, "data": {"assets": [{"symbol": "USDC", "decimals": 6}]}}))
elif a[:2] == ["wallet", "address"]:
    print(json.dumps({"ok": True, "data": {"address": "0x" + "a" * 40}}))
elif a[:2] == ["wallet", "sign-typed-data"]:
    print(json.dumps({"_notice": {"kind": "AWAITING_MFA", "pollingId": "p1"}}))
    print(json.dumps({"ok": True, "data": {"signature": "0x" + "b" * 130}}))
else:
    print(json.dumps({"ok": False, "error": "unexpected: " + " ".join(a)}))
'''


class Offer:
    """What the loopback x402 server returns; tests mutate it between calls."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.amount = "10000"
        self.pay_to = PAY_TO
        self.network = "eip155:8453"
        self.receipt = True


OFFER = Offer()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.headers.get("PAYMENT-SIGNATURE"):
            self.send_response(200)
            if OFFER.receipt:
                receipt = {"success": True, "transaction": "0x" + "c" * 64}
                self.send_header(
                    "PAYMENT-RESPONSE", base64.b64encode(json.dumps(receipt).encode()).decode()
                )
            self.end_headers()
            self.wfile.write(b'{"data": "premium"}')
            return
        required = {
            "x402Version": 2,
            "resource": {"url": "http://127.0.0.1:%d/premium" % self.server.server_port},
            "accepts": [{
                "scheme": "exact", "network": OFFER.network, "amount": OFFER.amount,
                "payTo": OFFER.pay_to, "asset": ASSET, "maxTimeoutSeconds": 60,
                "extra": {"name": "USD Coin", "version": "2"},
            }],
        }
        self.send_response(402)
        self.send_header(
            "PAYMENT-REQUIRED", base64.b64encode(json.dumps(required).encode()).decode()
        )
        self.end_headers()


def test_amount_to_hex():
    print("amount_to_hex.py")
    exact = {
        ("1.5", "18"): "0x14d1120d7b160000",
        ("100", "6"): "0x5f5e100",
        ("0.001", "8"): "0x186a0",
        ("1e3", "6"): "0x3b9aca00",
        ("0", "18"): "0x0",
        ("123456789012345678901234.5", "18"): hex(1234567890123456789012345 * 10 ** 17),
    }
    for (amount, decimals), want in exact.items():
        code, out, _ = run([AMOUNT, amount, decimals])
        check("%s with %s decimals -> %s" % (amount, decimals, want),
              code == 0 and out.strip() == want, out.strip())
    for amount, decimals, why in (
        ("0.1234567", "6", "more decimals than the token"),
        ("-1", "6", "negative"),
        ("abc", "6", "not a number"),
        ("inf", "6", "not finite"),
        ("1", "-1", "negative decimals"),
        ("1", "x", "non-integer decimals"),
    ):
        code, out, err = run([AMOUNT, amount, decimals])
        check("rejects %s %s (%s) without output" % (amount, decimals, why),
              code != 0 and not out.strip() and "error" in err, err.strip())


def test_x402(env, url):
    print("x402_pay.py over HTTP")

    def pay(*extra):
        return run([X402, "pay", url, "--confirm", *extra], env)

    OFFER.reset()
    code, out, err = run([X402, "inspect", url], env)
    options = json.loads(out)["options"] if code == 0 else []
    check("inspect lists one eligible option with an approvalId",
          len(options) == 1 and options[0]["eligible"] and options[0]["approvalId"], err)
    approved = options[0]["approvalId"] if options else ""
    check("inspect shows human amount and symbol",
          options and options[0].get("humanAmount") == "0.01" and options[0].get("symbol") == "USDC")

    code, out, err = pay()
    check("pay without --approved refuses to sign", code == 1 and "--approved" in err, err)

    code, out, err = pay("--approved", approved)
    result = json.loads(out) if code == 0 else {}
    check("approved, unchanged offer settles even with an MFA notice before the signature",
          result.get("status") == "settled" and result.get("transaction") == "0x" + "c" * 64,
          err or out)

    OFFER.amount = "990000"
    code, out, err = pay("--approved", approved)
    check("raised amount after approval is refused, nothing signed",
          code == 1 and "differ from the approved" in err, err or out)

    OFFER.reset()
    OFFER.pay_to = "0x" + "f" * 40
    code, out, err = pay("--approved", approved)
    check("changed payTo after approval is refused", code == 1 and "differ from the approved" in err)

    OFFER.reset()
    OFFER.receipt = False
    code, out, err = pay("--approved", approved)
    result = json.loads(out) if code == 0 else {}
    check("200 without a receipt reports paid_unverified, not settled",
          result.get("status") == "paid_unverified" and result.get("transaction") is None
          and "Do not pay again" in result.get("note", ""), err or out)

    OFFER.reset()
    OFFER.network = "eip155:999999"
    code, out, _ = run([X402, "inspect", url], env)
    option = json.loads(out)["options"][0] if code == 0 else {}
    check("CAIP-2 chain missing from `mm chains list` is not eligible",
          option.get("chainId") is None and option.get("eligible") is False)

    code, _, _ = run([X402, "pay", "http://example.com/premium", "--confirm", "--approved", "x"], env)
    check("plain http to a non-loopback host is refused", code == 1)


def test_mcp(env):
    print("x402_pay.py over MCP")
    challenge = {"result": {"isError": True, "structuredContent": {
        "x402Version": 2, "resource": {"url": "mcp://tool/premium"},
        "accepts": [{"scheme": "exact", "network": "eip155:8453", "amount": "5000",
                     "payTo": PAY_TO, "asset": ASSET, "maxTimeoutSeconds": 60,
                     "extra": {"name": "USD Coin", "version": "2"}}]}}}
    raw = json.dumps(challenge)
    code, out, err = run([X402, "mcp-inspect", "--challenge", raw], env)
    approved = json.loads(out)["options"][0]["approvalId"] if code == 0 else ""
    check("mcp-inspect prints an approvalId", bool(approved), err)

    code, out, err = run([X402, "mcp-sign", "--challenge", raw, "--confirm"], env)
    check("mcp-sign without --approved refuses", code == 1 and "--approved" in err)

    code, out, err = run([X402, "mcp-sign", "--challenge", raw, "--confirm", "--approved", approved], env)
    result = json.loads(out) if code == 0 else {}
    check("mcp-sign with the approved id signs the offered amount",
          result.get("status") == "signed"
          and result.get("payment", {}).get("accepted", {}).get("amount") == "5000", err)

    changed = raw.replace('"5000"', '"9000"')
    code, out, err = run([X402, "mcp-sign", "--challenge", changed, "--confirm", "--approved", approved], env)
    check("mcp-sign refuses a challenge whose terms changed", code == 1 and "differ from the approved" in err)


def main():
    test_amount_to_hex()
    with tempfile.TemporaryDirectory() as tmp:
        fake = os.path.join(tmp, "mm")
        with open(fake, "w", encoding="utf-8") as handle:
            handle.write(FAKE_MM.replace("#!/usr/bin/env python3", "#!" + sys.executable, 1))
        os.chmod(fake, 0o755)
        env = dict(os.environ, PATH=tmp + os.pathsep + os.environ.get("PATH", ""),
                   PYTHONDONTWRITEBYTECODE="1")
        server = HTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            test_x402(env, "http://127.0.0.1:%d/premium" % server.server_port)
            test_mcp(env)
        finally:
            server.shutdown()
    passed = sum(checks)
    print("\n%d/%d checks passed" % (passed, len(checks)))
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
