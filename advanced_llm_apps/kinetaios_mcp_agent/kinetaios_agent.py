#!/usr/bin/env python3
"""KinetAios MCP client example — drive a remote KinetAios agent workstation.

Pure `requests` + JSON-RPC over HTTP. No MCP SDK, no LLM API key:
the KinetAios instance (https://github.com/phinn/KinetAios) provides
the agent runtime, tools and memory. This script only talks MCP.

Usage:
    python kinetaios_agent.py --task "List files in /tmp and summarize them"
    python kinetaios_agent.py --token XXXX --port 18109 --task "..."
"""
import argparse
import json
import sys

import requests

# ── tiny JSON-RPC helper ──────────────────────────────────────────
_id = [0]


def rpc(base, headers, method, params=None, timeout=660):
    """POST /mcp with a JSON-RPC 2.0 request. KinetAios replies either
    application/json or an SSE frame (data: {...}) — both are handled."""
    _id[0] += 1
    body = {"jsonrpc": "2.0", "id": _id[0], "method": method, "params": params or {}}
    r = requests.post(f"{base}/mcp", json=body, headers=headers, timeout=timeout)
    r.raise_for_status()
    ct = r.headers.get("content-type", "")
    text = r.text.strip()
    if "text/event-stream" in ct:
        for line in text.splitlines():
            if line.startswith("data:"):
                payload = line[5:].strip()
                if payload:
                    return json.loads(payload)
        raise RuntimeError(f"no data frame in SSE response: {text[:200]}")
    return r.json()


def main():
    ap = argparse.ArgumentParser(description="Drive a KinetAios agent via MCP")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=18109)
    ap.add_argument("--token", required=True, help="MCP server token from KinetAios settings")
    ap.add_argument("--task", required=True, help="natural-language task for the remote agent")
    ap.add_argument("--max-turns", type=int, default=None, help="optional ReAct turn cap")
    args = ap.parse_args()

    base = f"http://{args.host}:{args.port}"
    headers = {
        "Authorization": f"Bearer {args.token}",
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
    }

    # 1) MCP handshake
    init = rpc(base, headers, "initialize", {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "kinetaios-example", "version": "1.0.0"},
    })
    server_info = (init.get("result") or {}).get("serverInfo", {})
    print(f"● connected: {server_info.get('name', '?')} v{server_info.get('version', '?')}")

    # 2) discover tools — KinetAios exposes run_agent / export_session / import_session …
    tools = rpc(base, headers, "tools/list")
    names = [t["name"] for t in (tools.get("result") or {}).get("tools", [])]
    print(f"● tools: {', '.join(names)}")
    if "run_agent" not in names:
        sys.exit("✗ run_agent not available on this server")

    # 3) run the task — KinetAios spawns a full autonomous agent (ReAct loop,
    #    shell/file/web tools, long-term memory) and returns the final text.
    print(f"● task: {args.task}\n● running (this can take minutes)…")
    call = rpc(base, headers, "tools/call", {
        "name": "run_agent",
        "arguments": {"prompt": args.task, **({"maxTurns": args.max_turns} if args.max_turns else {})},
    }, timeout=660)  # run_agent may run for minutes; server caps at 10 min

    result = call.get("result") or {}
    if "error" in call:
        sys.exit(f"✗ JSON-RPC error: {call['error']}")

    for item in result.get("content", []):
        if item.get("type") == "text":
            print("\n── agent answer ──\n" + item.get("text", ""))
    if result.get("isError"):
        sys.exit("\n✗ the agent reported an error (see text above)")


if __name__ == "__main__":
    main()
