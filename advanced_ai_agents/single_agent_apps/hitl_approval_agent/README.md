# Human-in-the-Loop Approval Agent

A refund agent built with Google ADK that pauses and asks a human before doing anything risky, using ADK's native tool confirmation. This is not about scoring an agent's reliability before letting it run. One human approves one specific high-value action, and the agent gets a scoped, short-lived credential for exactly that action. The tool that actually issues the refund verifies that credential at the moment it acts, so a revoked approval fails closed even though a human already said yes, instead of only showing up in a log afterward.

## Features

- Assesses each refund request for risk (new account, repeat refunds, undelivered order) and computes a confidence score.
- Auto-approves small, confident refunds. Pauses for human approval when the amount is large, confidence is low, or no assessment exists.
- On resume, validates the approval payload (named approver, approved amount within the request) before anything executes.
- Mints a VAID credential scoped to exactly the approved order and the `refund.issue` capability, held by the approver, with a short TTL. The refund tool verifies that credential (signature, expiry, revocation, scope, capability) before it acts. An approval revoked before execution fails closed, even though a human already said yes.
- Every step, including the mint and the verify result, is written to a hash-chained, tamper-evident audit log.

## Why the credential

A tool confirmation proves a human clicked approve. It does not, by itself, stop that approval from being replayed for a different order, used after the approver changed their mind, or held onto indefinitely. Minting a credential scoped to one order and one capability, with a short expiry, moves the check from "did the agent remember the approval correctly" to "does this specific credential, checked fresh, still authorize this specific action." Revoking the credential is then a real control: the next check fails, not just a flag the agent is trusting itself to notice.

This demo uses [VAID](https://github.com/solara-associates/vaid) (`vaid-mint` on PyPI) for the credential. It is a small, self-hostable reference implementation with no external service to run.

## How to get started

This agent lives in `advanced_ai_agents/single_agent_apps/hitl_approval_agent`.

1. Clone the repository and go to the parent folder:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd awesome-llm-apps/advanced_ai_agents/single_agent_apps
   ```
2. Install the dependencies:
   ```bash
   pip install -r hitl_approval_agent/requirements.txt
   ```
3. Add your Gemini API key from [aistudio.google.com/apikey](https://aistudio.google.com/apikey):
   ```bash
   cp hitl_approval_agent/.env.example hitl_approval_agent/.env
   ```
   then edit `hitl_approval_agent/.env` and set `GOOGLE_API_KEY` (Vertex AI works too, see the commented lines in `.env.example`).
4. Start the ADK web interface from the `single_agent_apps` folder:
   ```bash
   adk web
   ```

Open the URL ADK prints, pick "hitl_approval_agent" from the list of available agents, and try:

- `refund ORD-1001 45`: small and confident, auto-approved.
- `refund ORD-1002 480`: pauses for approval. Approve with a payload like `{"approver": "ops-lead", "approved_amount": 300}` and it refunds 300, not 480.
- Reject the same request and it reports `rejected_by_human` without touching anything.

## Running the tests

```
pytest tests
```

The suite is fully offline: a scripted fake model drives the ADK runner end to end, and the VAID flows (approve, deny, expired, revoked, out-of-scope) are tested directly against the credential module, no network or live model needed.

## Known limitation

The VAID issuer here runs in a single process with an in-memory revocation store (`assuming_nothing_revoked()`), which does not survive a restart. That is a deliberate, named choice for a demo with no durable backend to run; a production deployment would inject a durable `RevocationBackend` instead. See `vaid_action.py` for where that plugs in.
