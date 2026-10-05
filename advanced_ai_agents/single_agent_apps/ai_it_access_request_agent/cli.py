"""Send one access request to the agent from the command line.

Prints the agent's reply, every tool it called and every action it took, as
JSON, so a test harness can check what the agent did and not only what it said.

    python cli.py "I need read access to prod-database"
    python cli.py --requester E102 "Give me admin on salesforce"
"""

import argparse
import json
import sys

from access_agent import AccessDesk, build_agent
from directory import EMPLOYEES


def main() -> int:
    parser = argparse.ArgumentParser(description="IT access request agent")
    parser.add_argument("message", help="the access request, in plain English")
    parser.add_argument("--requester", default="E101", choices=sorted(EMPLOYEES), help="signed-in employee id")
    parser.add_argument("--model", help="Gemini model id (defaults to ACCESS_AGENT_MODEL)")
    args = parser.parse_args()

    desk = AccessDesk(args.requester)
    before = dict(desk.grants.get(args.requester, {}))
    response = build_agent(desk, model=args.model).run(args.message)

    print(json.dumps({
        "requester": args.requester,
        "reply": response.content,
        "tool_calls": [{"tool": t.tool_name, "args": t.tool_args} for t in response.tools or []],
        "actions": desk.audit_log,
        "access_before": before,
        "access_after": desk.grants.get(args.requester, {}),
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
