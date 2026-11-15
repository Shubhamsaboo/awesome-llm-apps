# 🧾 Verifiable Agent Job — an MCP job that ends in proof, not just text

Most agent examples finish with output on a screen that nobody can check afterwards. This one runs a small job over the Model Context Protocol and finishes with a record anyone can verify and pick up: a receipt for every step, and a handover link that carries the whole job to a named person (or to a different AI).

It talks to [Zambo](https://zambo.dev/mcp), a remote MCP server with 153 tools. No API key, no LLM key, and nothing to install locally beyond `requests`.

## What it does

One chained job in a single session:

1. `live_price` for BTC, ETH, and SOL (three separate calls, one job)
2. `memory_remember` saves the finished brief
3. `handover` wraps the job for a named recipient, binding exactly this job's receipts into one record

Every step prints its receipt URL. Open any receipt and recompute it for free at [zambo.dev/verify](https://zambo.dev/verify/): the receipt proves the saved result was not changed after the fact. It does not prove the result was right, and the script says so; the verdict on the work stays with whoever picks the job up.

## Run it

```bash
pip install -r requirements.txt
python verifiable_agent_job.py                # hands over to Dana Whitfield
python verifiable_agent_job.py "Alex Rivera"  # or name your own recipient
```

Sample output:

```
job: verifiable-job-20261115-092404

[live_price] ok
    receipt: https://zambo.dev/run/f46caee1-8905-415c-b343-fe65af0117c0
[live_price] ok
    receipt: https://zambo.dev/run/24bbb117-4676-4cb2-b120-c44f7d8ae117
[live_price] ok
    receipt: https://zambo.dev/run/92adab6f-45f7-49fd-b264-b5ed4df47472
[memory_remember] ok
    receipt: https://zambo.dev/run/b05d5fb6-29d2-4741-8c04-44bdecf26d81
[handover] ok
    receipt: https://zambo.dev/handover/...

handover: https://zambo.dev/handover/...
Anyone with that link can pick the job up in a different AI and verify every step. The record does not expire.
```

## The free tier, honestly

The free tier covers one full run a day: every tool free once a day, plus 3 continue calls shared across tools, and one free wrap-up handover per day. Pickup, tool discovery, and receipt verification are always free.

If your network has already used today's free wrap-up, the last step answers differently: the job is **saved, not lost**, and the wrap completes the moment a Day Pass is active (or on tomorrow's free wrap). The script prints that state plainly when it happens. A Day Pass is $0.99 for 24 hours of unlimited calls: https://zambo.dev/day-pass/

## Ideas to extend it

- Swap the price chain for your own job: the pattern is the point (chain calls in one session, save the result, wrap it for a person).
- Pick the handover up in a second client (Claude, ChatGPT, another script) and verify the receipts there; the record is the interface.
- Gate a client delivery on the wrap: send the handover link instead of a screenshot, and let the client recheck the work themselves.

## Tech stack

- Python + `requests` (the MCP server answers plain JSON over streamable HTTP)
- Zambo MCP server: https://zambo.dev/mcp (receipt format: AER-1, IETF Internet-Draft draft-zambo-aer1-26)
