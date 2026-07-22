# 🎙️ Thinking Out Loud 

Ramble at your agent by voice. Audit what it heard before it acts.

Voice dictation already lets you think out loud for ten minutes, and LLMs are already good at reconstructing the mess. The danger sits one step later: the model fills every gap in your ramble confidently. "The usual model" silently becomes a specific model. The idea you reversed mid-ramble survives as fact. Then an agent with tools starts building on a misreading it fully believes, and you find out an hour of generated work later.

This skill is a contract for that moment: the agent acts on nothing until it echoes back a short structured audit of everything it absorbed, with its own guesses quarantined from your words. You correct three lines instead of debugging a built artifact.

<img width="1390" height="782" alt="thinking_out_loud" src="https://github.com/user-attachments/assets/81030cf9-1537-408a-ad8e-0ab6b6acbc58" />


## Install

```bash
npx skills add https://github.com/Shubhamsaboo/awesome-llm-apps/tree/main/agent_skills/thinking-out-loud
```

The [skills CLI](https://skills.sh) installs the folder for compatible
coding agents. You can also copy this directory into an agent's skills
directory.

## Run

Dictate a ramble into your agent, mess encouraged. It auto-triggers on
ramble-shaped input, especially with an opener like:

> switching to speech recognition sorry for any typos. so the thing i
> keep coming back to is...

You get back the echo: a one-sentence mission, your locked decisions and
constraints, open questions, a ledger of flips and parked tangents, and
the model's additions (inferred and guessed) to correct first. Fix what
is wrong, optionally take a short interview on the open items, approve,
and choose where the brief gets saved.

To ramble across several messages instead, invoke it first ("let me
think out loud for a bit"); the agent replies only "listening..." until
you say "done".

## Why not just ask for follow-up questions?

- Questions verify what the model doubts; the echo verifies what the
  model believes. Confident misreadings never feel unclear, so they
  never become questions.
- Questions sample three or four points; the echo audits the entire
  transfer, and you verify by recognition, just reading and spotting
  what is wrong.

## Verify

The behavior spec lives in
[`agent_skills/evals/thinking-out-loud/`](../evals/thinking-out-loud/).
Run each prompt in `evals.json` in a fresh session with the skill
installed and check the listed expectations; `trigger-cases.json` covers
when the skill must and must not fire. The skill is prompt-only: no
scripts, no network calls, and it never saves anything without asking.

## Files

```text
thinking-out-loud/
|-- SKILL.md
|-- README.md
`-- references/echo-format.md
```

Part of [awesome-llm-apps](https://github.com/Shubhamsaboo/awesome-llm-apps).
Apache-2.0. Last verified: July 2026.
