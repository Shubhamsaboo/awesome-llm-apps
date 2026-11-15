"""A verifiable agent job: a chained MCP run whose work anyone can check.

Most agent examples end with text on a screen. This one ends with proof.
It runs a small job against the Zambo MCP server (https://zambo.dev/mcp):

    live_price BTC -> live_price ETH -> live_price SOL
    -> memory_remember (save the brief)
    -> handover (wrap the job for a named human)

Every call carries the same job id, so the final handover binds exactly
this job's receipts into one record. Each step prints its receipt link;
anyone can open a receipt and recompute it for free, which proves the
saved result was not changed after the fact.

No API key and no LLM key are needed. The free tier covers one run a day
(every tool free once a day, plus 3 continue calls; one free wrap-up
handover per day, and pickup is always free). For unlimited runs, a
$0.99 Day Pass unlocks 24 hours: https://zambo.dev/day-pass/

Run:  python verifiable_agent_job.py [recipient name]
"""

import json
import re
import sys
import time

import requests

MCP_URL = "https://zambo.dev/mcp"
URL_RE = re.compile(r"https://zambo\.dev/(?:run|handover)/[^\s\"'\)\]]+")


class ZamboMCP:
    """Minimal JSON-RPC client for a remote MCP server (streamable HTTP)."""

    def __init__(self):
        self.http = requests.Session()
        self.http.headers.update({
            "Content-Type": "application/json",
            # The server answers plain JSON to this Accept value.
            "Accept": "application/json",
        })
        self.session_id = None
        self._next_id = 0

    def _post(self, payload):
        resp = self.http.post(MCP_URL, json=payload, timeout=60)
        sid = resp.headers.get("Mcp-Session-Id")
        if sid:
            self.session_id = sid
        resp.raise_for_status()
        return resp.json() if resp.content else {}

    def request(self, method, params=None):
        self._next_id += 1
        headers = {}
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        resp = self.http.post(
            MCP_URL,
            json={"jsonrpc": "2.0", "id": self._next_id,
                  "method": method, "params": params or {}},
            headers=headers, timeout=60)
        sid = resp.headers.get("Mcp-Session-Id")
        if sid:
            self.session_id = sid
        resp.raise_for_status()
        body = resp.json()
        if "error" in body:
            raise RuntimeError(f"{method} failed: {body['error']}")
        return body.get("result", {})

    def notify(self, method):
        headers = {}
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        self.http.post(MCP_URL,
                       json={"jsonrpc": "2.0", "method": method},
                       headers=headers, timeout=60)

    def initialize(self):
        self.request("initialize", {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "verifiable-agent-job", "version": "1.0.0"},
        })
        self.notify("notifications/initialized")

    def call_tool(self, name, arguments):
        result = self.request("tools/call",
                              {"name": name, "arguments": arguments})
        texts = [c.get("text", "") for c in result.get("content", [])
                 if c.get("type") == "text"]
        return "\n".join(texts), bool(result.get("isError"))


def show(step, text):
    link = URL_RE.search(text)
    print(f"[{step}] ok")
    print(f"    receipt: {link.group(0) if link else '(see output)'}")
    return text


def main():
    recipient = " ".join(sys.argv[1:]) or "Dana Whitfield"
    stamp = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    job_id = f"verifiable-job-{stamp}"

    client = ZamboMCP()
    client.initialize()
    print(f"job: {job_id}\n")

    def step(tool, args):
        text, is_error = client.call_tool(
            tool, {**args, "_session_id": job_id})
        if is_error:
            print(f"[{tool}] the call was refused:\n{text}\n")
            if "saved" in text.lower():
                print("This is the free tier working as designed, not a "
                      "failure: the steps above are receipted and the "
                      "job is saved. It wraps the moment a Day Pass is "
                      "active, or on tomorrow's free wrap. A $0.99 Day "
                      "Pass unlocks unlimited calls for 24 hours: "
                      "https://zambo.dev/day-pass/")
            else:
                print("The free tier covers one run a day. A $0.99 Day "
                      "Pass unlocks unlimited calls for 24 hours: "
                      "https://zambo.dev/day-pass/")
            sys.exit(1)
        return show(tool, text)

    prices = {}
    for symbol in ("BTC", "ETH", "SOL"):
        out = step("live_price", {"symbol": symbol})
        prices[symbol] = out.strip().splitlines()[0] if out.strip() else ""

    brief = (f"Price brief {job_id}: " +
             "; ".join(f"{s}: {p}" for s, p in prices.items()))
    step("memory_remember", {"fact": brief[:480]})

    wrap = step("handover", {
        "summary": f"Price brief for BTC, ETH and SOL, saved to memory. "
                   f"{brief}",
        "goal": "Give the recipient a price brief whose every step "
                "can be rechecked from its receipt.",
        "recipient": recipient,
        "next_steps": [
            "Open the handover link and pick the job up (pickup is free).",
            "Open any receipt and recompute it at https://zambo.dev/verify/ .",
            "Reply on the record with the decision, so the chain stays whole.",
        ],
    })

    link = URL_RE.search(wrap)
    print("\nhandover:", link.group(0) if link else "(see output above)")
    print("Anyone with that link can pick the job up in a different AI "
          "and verify every step. The record does not expire.")


if __name__ == "__main__":
    main()
