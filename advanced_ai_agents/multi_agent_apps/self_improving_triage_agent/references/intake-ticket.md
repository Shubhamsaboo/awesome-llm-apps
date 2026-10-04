# Ticket Intake

Load this only when the input is a Jira/Linear/GitHub ticket. A ticket is
**intake material, not evidence**: it carries a narrative written by a person,
often second-hand, sometimes wrong. It tells you where to look; it never tells
you what happened.

## Map the ticket onto the intake fields

| Intake field | Where it usually hides in a ticket |
|---|---|
| Trace / correlation IDs | pasted stack traces, attached screenshots, comment threads, `curl` repros |
| User hypothesis | the title, and any "I think / probably / looks like" in the body |
| Symptom window | `created`, "started after", "since the deploy", first comment timestamp |
| Environment | labels, components, the project key, "on staging" in the body |
| Already ruled out | comments where someone checked something and moved on |
| Reporter's role | whether they own the service or are a passer-by — changes how much weight the hypothesis carries |

Pull the IDs out first. One trace ID in a comment is worth more than the whole
description.

## The title is a hypothesis, not a finding

"Checkout broken by yesterday's deploy" asserts a cause. Treat it as the
reporter's theory and test it like any other — see the hypothesis rules in
`SKILL.md`. Ticket titles are where mis-routes come from: they name a *symptom
owner*, and the fix usually lives elsewhere.

## Decide what you can actually produce

**With telemetry** — proceed to the evidence path. The ticket has done its job by
seeding intake.

**Without telemetry** — stop. Output an **evidence request**, not an RCA:

1. `insufficient_evidence` stated plainly in the first line.
2. The reporter's hypothesis, restated so they can confirm you understood it.
3. What you would need, most decisive first.
4. **The exact query to run**, in their stack's syntax.
5. What each result would rule in or out — so the query is worth running.
6. A provisional routing guess, explicitly labelled unverified.

### Query templates

Substitute the service, window, and any trace ID from the ticket.

**GCP Logs Explorer**

```
resource.type="k8s_container"
resource.labels.container_name="<service>"
severity>=WARNING
timestamp>="<window_start>" AND timestamp<="<window_end>"
```
With a trace ID: `trace="projects/<project>/traces/<trace_id>"`

**AWS CloudWatch Logs Insights**

```
fields @timestamp, @message, @logStream
| filter @message like /(?i)(error|exception|timeout)/
| sort @timestamp desc
| limit 200
```
With a trace ID: `| filter @message like /<trace_id>/`

Pipe whatever comes back through `scripts/normalize_evidence.py`, then take the
evidence path.

## Why declining is the correct answer here

A ticket-only RCA fails `ev_quotes_log`, `ev_correlation_id`, and
`ev_no_fabrication` by construction — there is nothing to cite. An agent that
writes one anyway produces confident, well-formatted fiction, which is worse than
silence because it looks like work. `references/rca-golden-set.json` includes a
ticket-only case whose expected verdict is `insufficient_evidence`; a confident
answer there scores **zero**, and a correct-by-guess answer scores only partial
credit, because an unevidenced right answer teaches misplaced trust.
