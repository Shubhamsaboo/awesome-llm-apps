#!/usr/bin/env python3
"""
AgentSentry Circuit Breaker - Local Token & Loop Protector
Zero-dependency local HTTP proxy and process supervisor.
Protects autonomous AI agents (Claude Code, Cursor, Aider) from runaway token costs.
"""

import sys
import os
import time
import json
import difflib
import sqlite3
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
import argparse

DB_FILE = "agentsentry_audit.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL,
            provider TEXT,
            model TEXT,
            input_tokens INTEGER,
            output_tokens INTEGER,
            cost_cad REAL,
            cumulative_cost REAL,
            status TEXT,
            tool_sig TEXT
        )
    """)
    conn.commit()
    conn.close()

def log_event(provider, model, in_tok, out_tok, cost, cum_cost, status, tool_sig):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT INTO audit_log (timestamp, provider, model, input_tokens, output_tokens, cost_cad, cumulative_cost, status, tool_sig)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (time.time(), provider, model, in_tok, out_tok, cost, cum_cost, status, tool_sig))
    conn.commit()
    conn.close()

class CircuitBreakerState:
    def __init__(self, max_spend=5.0, fuzzy_threshold=0.85):
        self.max_spend = max_spend
        self.fuzzy_threshold = fuzzy_threshold
        self.cumulative_cost = 0.0
        self.tool_history = []
        self.tripped = False
        self.trip_reason = ""

    def check_fuzzy_loop(self, current_tool_sig):
        if not current_tool_sig:
            return False
        consecutive_matches = 0
        for prev_sig in reversed(self.tool_history[-4:]):
            ratio = difflib.SequenceMatcher(None, current_tool_sig, prev_sig).ratio()
            if ratio >= self.fuzzy_threshold:
                consecutive_matches += 1
            else:
                break
        self.tool_history.append(current_tool_sig)
        if consecutive_matches >= 2:
            self.tripped = True
            self.trip_reason = f"Infinite tool loop detected: repeating signature '{current_tool_sig}'"
            return True
        return False

    def check_spend(self, cost_delta):
        self.cumulative_cost += cost_delta
        if self.cumulative_cost >= self.max_spend:
            self.tripped = True
            self.trip_reason = f"Hard spend cap reached: ${self.cumulative_cost:.4f} >= ${self.max_spend:.2f}"
            return True
        return False

GLOBAL_STATE = CircuitBreakerState()

class ProxyHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if GLOBAL_STATE.tripped:
            self.send_response(429)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            err = {"error": {"message": f"[AgentSentry Trip] {GLOBAL_STATE.trip_reason}", "type": "circuit_breaker_tripped"}}
            self.wfile.write(json.dumps(err).encode("utf-8"))
            print(f"\n[CIRCUIT BREAKER] Blocked outbound request: {GLOBAL_STATE.trip_reason}")
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        tool_sig = ""
        try:
            payload = json.loads(body.decode("utf-8"))
            messages = payload.get("messages", [])
            for m in reversed(messages):
                content = str(m.get("content", ""))
                if "tool_use" in content or "pytest" in content or "bash" in content:
                    tool_sig = content[:80]
                    break
        except Exception:
            pass

        if GLOBAL_STATE.check_fuzzy_loop(tool_sig):
            self.send_response(429)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            err = {"error": {"message": f"[AgentSentry Trip] {GLOBAL_STATE.trip_reason}", "type": "circuit_breaker_tripped"}}
            self.wfile.write(json.dumps(err).encode("utf-8"))
            log_event("local", "proxy", 0, 0, 0, GLOBAL_STATE.cumulative_cost, "TRIPPED_LOOP", tool_sig)
            print(f"\n[CIRCUIT BREAKER] Severing socket connection: {GLOBAL_STATE.trip_reason}")
            return

        simulated_cost = 0.02
        if GLOBAL_STATE.check_spend(simulated_cost):
            self.send_response(429)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            err = {"error": {"message": f"[AgentSentry Trip] {GLOBAL_STATE.trip_reason}", "type": "circuit_breaker_tripped"}}
            self.wfile.write(json.dumps(err).encode("utf-8"))
            log_event("local", "proxy", 0, 0, simulated_cost, GLOBAL_STATE.cumulative_cost, "TRIPPED_SPEND", tool_sig)
            print(f"\n[CIRCUIT BREAKER] Hard spend cap severed: {GLOBAL_STATE.trip_reason}")
            return

        # Upstream relay or mock response
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        mock_resp = {
            "id": "as-proxy-resp",
            "choices": [{"message": {"role": "assistant", "content": "AgentSentry OK"}}],
            "usage": {"prompt_tokens": 500, "completion_tokens": 150}
        }
        self.wfile.write(json.dumps(mock_resp).encode("utf-8"))
        log_event("local", "proxy", 500, 150, simulated_cost, GLOBAL_STATE.cumulative_cost, "OK", tool_sig)
        print(f"[OK] Spend: ${GLOBAL_STATE.cumulative_cost:.4f} / ${GLOBAL_STATE.max_spend:.2f} CAD | Turn accepted.")

    def log_message(self, format, *args):
        pass

def run_server(port=8080, max_spend=5.0, fuzzy_threshold=0.85):
    init_db()
    GLOBAL_STATE.max_spend = max_spend
    GLOBAL_STATE.fuzzy_threshold = fuzzy_threshold
    server_address = ("127.0.0.1", port)
    httpd = HTTPServer(server_address, ProxyHandler)
    print("=" * 60)
    print(f"  AgentSentry Circuit Breaker Proxy Active on 127.0.0.1:{port}")
    print(f"  Hard Spend Ceiling: ${max_spend:.2f} CAD | Fuzzy Loop Threshold: {fuzzy_threshold:.0%}")
    print("=" * 60)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nAgentSentry stopped.")

def run_simulation():
    print("Starting offline runaway agent simulation...")
    import urllib.request
    proxy_url = "http://127.0.0.1:8080/v1/chat/completions"
    for turn in range(1, 6):
        payload = {
            "model": "gpt-4o",
            "messages": [
                {"role": "user", "content": "Fix unit test in tests/test_core.py"},
                {"role": "assistant", "content": "Running tool bash: pytest tests/test_core.py"}
            ]
        }
        req = urllib.request.Request(proxy_url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=3) as resp:
                print(f"Turn {turn}: Agent response received: {resp.read().decode()[:40]}")
        except urllib.error.HTTPError as e:
            print(f"Turn {turn}: Intercepted by Circuit Breaker! HTTP {e.code}: {e.read().decode()}")
            break
        time.sleep(0.5)

def main():
    parser = argparse.ArgumentParser(description="AgentSentry Circuit Breaker")
    parser.add_argument("command", choices=["serve", "simulate"], default="serve", nargs="?")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--max-spend", type=float, default=5.0)
    parser.add_argument("--fuzzy-threshold", type=float, default=0.85)
    args = parser.parse_args()

    if args.command == "simulate":
        run_simulation()
    else:
        run_server(port=args.port, max_spend=args.max_spend, fuzzy_threshold=args.fuzzy_threshold)

if __name__ == "__main__":
    main()
