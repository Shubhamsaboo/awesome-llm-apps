"""
AI Salt Review Agent
---------------------
An AI agent with its own account on Salt (https://saltapp.ai) that pauses a
task to ask a real human for a yes/no decision -- no webhook server, no UI
you have to build, no polling loop in your own product code.

How it works:
1. The script registers itself as a brand-new Salt agent account (a root
   agent, per Salt's "One Account" model -- it needs no owning human and no
   email/password). This only happens once; the resulting API key is
   printed so you can export it and skip registration next time.
2. You open the Salt app, search for the agent's username, and say hello.
   Salt calls this "opening a chat" -- every new 1:1 an agent is added to
   fires a `chat_opened` event so the agent knows a door opened.
3. Claude turns your plain-English question into a short approve/deny
   prompt and the agent posts it into that chat as an interactive card
   (Salt's declarative "blocks" cards -- see CARD_PROTOCOL_SPEC.md in the
   salt-api repo). Cards are structured data, not end-to-end-encrypted
   message ciphertext, which is what makes this simple: no PGP needed to
   post one.
4. The agent has no public webhook, so it discovers your chat by reading
   its own inbox with a short, bounded poll of GET /api/v1/agent/updates
   ("socket mode"). The button tap itself is read a different way: the
   script polls the card's OWN interaction log (GET /api/v1/cards/:id)
   instead. That inbox keeps exactly one forward-only cursor per agent
   server-side, so a second reader of the same agent's inbox (another
   script, a webhook host, a re-run while the first is still waiting)
   would silently steal rows from it and permanently advance the ack --
   a card's own interaction log has no such shared cursor, so any number
   of concurrent "did anyone tap this card yet?" checks can each poll it
   without interfering with one another or with anything else reading
   this agent's inbox.

Everything here is plain REST + one Claude call. There is no Salt SDK
dependency (salt-agent-sdk/saltapp-python are not yet on npm/PyPI) --
this talks directly to the documented /api/v1 endpoints with `requests`.

Setup
-----
1. pip install -r requirements.txt
2. export ANTHROPIC_API_KEY="sk-ant-..."
3. Run it:

     python salt_review_agent.py --username salt-demo-reviewer-1 \
         --task "Should I refund this customer's $20 order?"

   The first run prints an API key -- save it:

     export SALT_API_KEY="..."

   and re-run; the script skips registration when SALT_API_KEY is set.

4. When the script says "Waiting for you to open a chat...", open Salt,
   search for the username you passed above, and start the conversation.
   Then tap Approve or Deny on the card it sends.

Salt is end-to-end encrypted chat where humans and AI agents are equal
contacts -- an agent can message, ask, invoice, and get paid. This example
only uses the "ask" half. Learn more: https://saltapp.ai
"""

import argparse
import json
import os
import sys
import time

import requests
from anthropic import Anthropic

API_BASE = os.environ.get("SALT_API_BASE", "https://saltapp.ai/api/v1")
AUTH_BASE = os.environ.get("SALT_AUTH_BASE", "https://saltapp.ai/auth")

# How long we're willing to wait for a human to show up / answer, and how
# often we check. This is a short-lived CLI demo, not a long-running
# service -- a real integration should hold a websocket
# (AgentUpdatesChannel) or run as a proper daemon instead of polling.
POLL_TIMEOUT_SECONDS = 2  # server clamps this to 2s anyway
MAX_WAIT_SECONDS = 300
POLL_PAUSE_SECONDS = 2

# Neither GET /api/v1/cards/:id nor the agent inbox holds a request open the
# way the old (removed) card_interaction-over-agent/updates approach could,
# so this loop paces its own empty iterations with a real sleep rather than
# spinning as fast as the network round-trip allows. Mirrors salt-mcp's
# MIN_EMPTY_POLL_MS / saltapp-agentkit's MIN_EMPTY_POLL_SECONDS (both 1s).
MIN_EMPTY_POLL_SECONDS = 1.0


def generate_agent_keypair(display_name: str):
    """A brand-new OpenPGP keypair for the agent's Salt identity.

    Salt never accepts a plaintext private key and never stores one for a
    root agent -- you keep this key on your own infrastructure. We only
    ever send the *public* key to Salt.
    """
    import pgpy
    from pgpy.constants import PubKeyAlgorithm, KeyFlags, HashAlgorithm, SymmetricKeyAlgorithm, CompressionAlgorithm

    key = pgpy.PGPKey.new(PubKeyAlgorithm.RSAEncryptOrSign, 2048)
    uid = pgpy.PGPUID.new(display_name)
    key.add_uid(
        uid,
        usage={KeyFlags.Sign, KeyFlags.EncryptCommunications, KeyFlags.EncryptStorage},
        hashes=[HashAlgorithm.SHA256],
        ciphers=[SymmetricKeyAlgorithm.AES256],
        compression=[CompressionAlgorithm.Uncompressed],
    )
    return key, str(key.pubkey)


def register_agent(username: str, display_name: str) -> str:
    """Registers a root Salt agent (no owning human) and returns its api key."""
    config = requests.get(f"{API_BASE}/config", timeout=10).json()
    terms_version = config["terms_version"]
    privacy_version = config["privacy_version"]

    _, public_key = generate_agent_keypair(display_name)

    resp = requests.post(
        AUTH_BASE,
        json={
            "account_type": "Agent",
            "username": username,
            "display_name": display_name,
            "public_key": public_key,
            "listed": False,
            "accepted_terms_version": terms_version,
            "accepted_privacy_version": privacy_version,
        },
        timeout=15,
    )
    if resp.status_code >= 400:
        raise RuntimeError(f"Salt registration failed ({resp.status_code}): {resp.text}")

    body = resp.json()
    api_key = body.get("api_key")
    if not api_key:
        raise RuntimeError(f"Salt registration returned no api_key: {body}")
    return api_key


def poll_updates(api_key: str, after: int, timeout: int = POLL_TIMEOUT_SECONDS):
    """One short poll of the agent's own inbox (Salt's 'socket mode')."""
    resp = requests.get(
        f"{API_BASE}/agent/updates",
        params={"after": after, "timeout": timeout},
        headers={"api-key": api_key},
        timeout=timeout + 5,
    )
    resp.raise_for_status()
    return resp.json()  # {"updates": [...], "cursor": N}


def wait_for_chat_opened(api_key: str):
    """Blocks (with a bounded, printed-progress poll) until a human opens a chat.

    This is the one thing this example still reads from the agent's own
    inbox (GET /api/v1/agent/updates, Salt's "socket mode"): a brand-new,
    single-purpose demo agent like this one has no other consumer racing
    it for that inbox's one forward-only cursor, so it's the right tool
    for "has anyone shown up yet?" -- unlike the card-tap wait below,
    which needs to survive being run more than once against the same card.

    Returns (chat_id, opener_id, opener_display_name).
    """
    after = 0
    deadline = time.monotonic() + MAX_WAIT_SECONDS
    while time.monotonic() < deadline:
        data = poll_updates(api_key, after)
        after = data["cursor"]
        for update in data["updates"]:
            if update["event"] == "chat_opened":
                body = json.loads(update["body"])
                opener = body["opened_by"]
                return body["chat"]["id"], opener["id"], opener["display_name"]
        print(".", end="", flush=True)
        time.sleep(POLL_PAUSE_SECONDS)
    raise TimeoutError("Nobody opened a chat with the agent in time. Try again.")


def compose_prompt(task: str) -> str:
    """Asks Claude to turn a plain task description into one short question."""
    client = Anthropic()
    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=100,
        messages=[{
            "role": "user",
            "content": (
                "Turn this into a single, specific yes/no question for a human "
                "reviewer, under 200 characters, no preamble, just the question:\n\n"
                f"{task}"
            ),
        }],
    )
    return message.content[0].text.strip()


def post_review_card(api_key: str, chat_id: int, question: str) -> int:
    """Posts a Salt 'blocks' card with Approve/Deny buttons into the chat.

    Cards are structured data (CARD_PROTOCOL_SPEC.md), not encrypted message
    ciphertext, so posting one is a plain authenticated REST call.
    """
    resp = requests.post(
        f"{API_BASE}/cards",
        json={
            "chat_id": chat_id,
            "text": "An agent needs a decision from you.",
            "state": {
                "blocks": [
                    {"type": "section", "text": question},
                    {
                        "type": "actions",
                        "elements": [
                            {"type": "button", "action_id": "approve", "label": "Approve", "style": "primary"},
                            {"type": "button", "action_id": "deny", "label": "Deny", "style": "danger"},
                        ],
                    },
                ]
            },
        },
        headers={"api-key": api_key},
        timeout=15,
    )
    if resp.status_code >= 400:
        raise RuntimeError(f"Couldn't post the card ({resp.status_code}): {resp.text}")
    return resp.json()["resource_id"]  # the card's id


class _RateLimited(Exception):
    def __init__(self, retry_after_seconds: int):
        self.retry_after_seconds = retry_after_seconds


def get_card(api_key: str, card_id: int, after=None) -> dict:
    """GET /api/v1/cards/:id -- one card's own interaction log, owner-only.

    ``interactions`` comes back newest first, capped at 50 server-side.
    ``after`` is either another interaction's id or an ISO 8601 timestamp;
    an unrecognised value fails OPEN server-side (the full list, never a
    500), so this never needs to validate its own cursor before sending it.
    """
    resp = requests.get(
        f"{API_BASE}/cards/{card_id}",
        params={"after": after} if after is not None else None,
        headers={"api-key": api_key},
        timeout=15,
    )
    if resp.status_code == 429:
        raise _RateLimited(int(resp.headers.get("Retry-After", "1")))
    resp.raise_for_status()
    return resp.json()


def wait_for_decision(api_key: str, card_id: int, expected_user_id):
    """Polls the card's OWN interaction log for a tap on one of its buttons.

    Deliberately does not touch GET /api/v1/agent/updates: that inbox
    keeps exactly one forward-only cursor PER AGENT, so a second consumer
    of the same agent's inbox -- another script, a webhook host, this
    same function being called again after a timeout -- would silently
    lose rows, and every ``after`` sent there advances the agent's ack for
    good. Reading one card by id has no such shared state: any number of
    concurrent "did anyone tap this card yet?" checks, for this ask or any
    other, can each resolve independently. Mirrors salt-mcp's
    ``pollForCardInteraction`` and saltapp-agentkit's ``poll_for_answer``.
    """
    deadline = time.monotonic() + MAX_WAIT_SECONDS
    after = None
    while time.monotonic() < deadline:
        try:
            card = get_card(api_key, card_id, after=after)
        except _RateLimited as e:
            time.sleep(e.retry_after_seconds)
            continue

        started_at = time.monotonic()
        interactions = card.get("interactions") or []
        # Newest first, per the route's contract -- advance the cursor to
        # the newest interaction id seen regardless of whether it matches,
        # so a resumed poll never re-reads a row it has already rejected.
        if interactions and interactions[0].get("id") is not None:
            after = interactions[0]["id"]

        match = next(
            (
                i for i in interactions
                if i.get("action_id") in ("approve", "deny")
                and str(i.get("user_id", "")).lower() == str(expected_user_id).lower()
            ),
            None,
        )
        if match:
            return match["action_id"]

        elapsed = time.monotonic() - started_at
        print(".", end="", flush=True)
        if elapsed < MIN_EMPTY_POLL_SECONDS:
            time.sleep(MIN_EMPTY_POLL_SECONDS - elapsed)
    raise TimeoutError("Nobody tapped a button in time. The card is still open in the chat.")


def main():
    parser = argparse.ArgumentParser(description="Ask a human for a decision via a Salt card.")
    parser.add_argument("--username", required=True, help="Handle to register the demo agent under (first run only).")
    parser.add_argument("--task", required=True, help="Plain-English description of the decision the agent needs.")
    args = parser.parse_args()

    api_key = os.environ.get("SALT_API_KEY")
    if not api_key:
        print(f"No SALT_API_KEY set -- registering a new Salt agent as @{args.username}...")
        api_key = register_agent(args.username, display_name="Review Agent")
        print(f"Registered. Save this for next time:\n\n  export SALT_API_KEY=\"{api_key}\"\n")

    print(f"Waiting for you to open a chat with @{args.username} in the Salt app...", end="", flush=True)
    chat_id, opener_id, opener_name = wait_for_chat_opened(api_key)
    print(f"\n{opener_name} opened a chat. Composing the question with Claude...")

    question = compose_prompt(args.task)
    print(f"Asking: {question}")

    card_id = post_review_card(api_key, chat_id, question)
    print("Card posted. Waiting for a tap...", end="", flush=True)

    decision = wait_for_decision(api_key, card_id, expected_user_id=opener_id)
    print(f"\n{opener_name} tapped: {decision.upper()}")


if __name__ == "__main__":
    sys.exit(main())
