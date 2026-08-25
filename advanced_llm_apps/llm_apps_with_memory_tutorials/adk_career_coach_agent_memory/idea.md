# Idea / Blueprint — AI Career Coach

This document explains what we're building and how all the pieces fit
together, before any code gets written. It's meant to be readable on its own —
no prior context needed.

## What this is

An AI career coach for job seekers, built as a chat app. You talk to it about
your job search — your resume, an upcoming interview, a skill you want to
learn, how much to ask for in salary negotiations — and it routes your
question to the right specialist automatically. The thing that makes it
useful, rather than just another chatbot, is that it **remembers you**: your
experience, the kind of roles you're targeting, your tech stack, which
companies you like, offers you've turned down, and where you've struggled in
past interviews. That memory persists across every conversation, even if you
close the app and come back two months later, and it directly shapes the
advice you get.

## Why memory is the whole point

Without memory, every conversation starts from zero. You'd have to re-explain
your background every single time: "I'm a backend engineer with 4 years of
experience, I'm applying to fintech companies, I keep struggling with system
design questions..." — every time, forever.

With memory, that context builds up and gets reused automatically. Here's the
concrete difference:

**Today**, you tell it: *"I have an Amazon interview next week."*
It has enough context from past conversations to know you're a backend
engineer, you're targeting fintech-style companies, and system design is your
weak point — so it can immediately suggest a focused prep plan instead of
asking you to explain your whole background again.

**Two months later**, you ask: *"What should I focus on?"*
Instead of a generic "work on your resume and practice interviewing" answer,
it can say something like: *"Since you've been targeting backend roles in
fintech, have struggled with distributed systems interview questions, and
want to work remotely, I'd prioritize practicing system design and looking
at these three companies..."*

That second example only works because the app remembered specific,
personal facts about you across a long gap in time. That's the feature this
whole build is designed around.

## The four specialists, and why routing between them matters

A career coach isn't one skill, it's several different skills bundled
together, the same way a real career coaching service might have different
people handle different things:

| Specialist | What it actually does | Example question it should handle |
|---|---|---|
| **Resume Agent** | Fetches your resume on file and gives feedback tailored to a specific role you're applying for | "Can you review my resume for a backend role?" |
| **Interview Agent** | Runs mock interview practice and gives feedback | "I have an Amazon interview next week, can we practice?" |
| **Skills/Roadmap Agent** | Identifies skill gaps and suggests what to learn next | "I keep failing system design rounds, what should I study?" |
| **Salary Agent** | Gives a realistic salary range and negotiation advice | "What should I expect to be offered for a senior backend role in Seattle?" |

These genuinely need different knowledge and a different tone: giving resume
feedback and negotiating salary are not the same skill, and mashing them into
one generic "career bot" tends to produce shallow, generic answers to
everything. Splitting them into separate specialist agents, each with a
narrow job, lets each one be actually good at its one thing.

A fifth agent, the **career_orchestrator**, sits in front of all four. It
doesn't answer questions itself — its only job is to read your message
(plus whatever memory tells it about you) and decide which one specialist
should handle it. If your message is genuinely ambiguous, it asks a
clarifying question instead of guessing which specialist you meant.

**A deliberate design choice:** the orchestrator hands your message to
**one** specialist per turn, not several at once. This keeps the system
simple and predictable — one message, one clear routing decision, one
answer. The alternative (splitting one message across multiple specialists
and merging their answers together) is possible but adds real complexity for
little benefit here, since memory already gives each specialist enough
context to give a well-rounded answer on its own.

## How a message actually flows through the system

```
                                                 ┌────────────────────────┐
                                                 │        Mem0            │
                                                 │  (backed by Qdrant)    │
                                                 │  remembers you across  │
                                                 │  every conversation    │
                                                 └───────┬────────┬──────┘
                                                          │        │
                                                (1) look up│        │(5) save
                                                 what we    │        │  new info
                                                 know        ▼        │
  you ──(type a message)──► [Streamlit chat] ──► "message + what we know about you"
                              ▲                          │
                              │ (6) show the reply        │ (2) send to agent
                              │                           ▼
                              │                  ┌───────────────────┐
                              │                  │   ADK Runner       │
                              │                  │ (+ current chat    │
                              │                  │    state for now)  │
                              │                  └─────────┬──────────┘
                              │                            │ (3) picks the
                              │                            │  right specialist
                              │                  ┌─────────▼──────────┐
                              │                  │ career_orchestrator │
                              │                  │   (root agent)      │
                              │                  └───┬─────┬─────┬────┘
                              │                      │     │     │
                              │                 Resume Interview  Skills/  Salary
                              │                  Agent   Agent   Roadmap  Agent
                              │                      │     │    Agent │      │
                              │                      ▼     ▼     ▼    ▼
                              │                 [tool]   [tool] [tool] [tool]
                              │                      │     │     │     │
                              └──────(4) the answer◄─┴─────┴─────┴─────┘
```

Step by step, in plain terms:

1. You type a message in the chat box.
2. Before doing anything else, the app searches Mem0 for anything it already
   knows about you that's relevant to what you just asked.
3. Your message plus that retrieved context gets handed to the ADK Runner,
   which passes it to the orchestrator agent.
4. The orchestrator reads it and hands it off to exactly one specialist
   (Resume, Interview, Skills/Roadmap, or Salary), which may call its own
   tool to look something up (a sample interview question, a salary
   benchmark, etc.) before answering.
5. The specialist's answer comes back through the orchestrator to the app.
6. The app saves your message into Mem0 -- just your side of the exchange,
   not the coach's reply. The long-term store is meant to hold facts about
   you (the candidate), not the advice the coach gave, so only your message
   goes in. This also means only one Mem0 write per turn instead of two,
   which matters because each write triggers its own LLM call internally.
7. The answer is shown to you in the chat window.

## Two very different kinds of "remembering"

There are two separate memory systems here, doing two different jobs, and
it's important not to confuse them:

- **The current conversation** — everything said in this chat session, kept
  by ADK for as long as the app is running. This is short-term and
  disposable: if the app restarts, this is gone. It exists just so the
  agent doesn't lose track of what you said two messages ago in the same
  conversation.
- **You, as a person, over time** — stored in Mem0, backed by a Qdrant
  vector database. This is what survives closing the app, restarting the
  server, or coming back after months. It's where the genuinely useful
  long-term facts live:
  - years of experience
  - roles you're targeting (e.g. "backend engineering, fintech companies")
  - your tech stack
  - companies you like, or have liked in the past
  - job offers you've turned down, and why
  - skills or topics you're actively trying to learn
  - interview topics or question types you've struggled with

The short-term memory keeps one conversation coherent. The long-term memory
is what makes the app feel like it actually knows you. Both are necessary,
and they're intentionally kept separate so restarting the app (which clears
the short-term memory) never causes it to forget who you are (which lives in
the long-term memory instead).

## Mock data — stand-ins for real data sources

To build and test this without needing real integrations yet, each
specialist's tool reads from a small, hardcoded Python dictionary instead of
a real API:

- `MOCK_RESUMES` — a resume on file for each candidate email (years of
  experience, current role, skills, a few bullet points)
- `MOCK_INTERVIEW_QUESTIONS` — a few sample interview questions, organized by
  company and interview type (e.g. Amazon behavioral, Amazon system design)
- `MOCK_LEARNING_RESOURCES` — a suggested next learning step for a handful of
  skills (e.g. "distributed systems" → a suggested resource)
- `MOCK_SALARY_DATA` — a rough salary range for a few role + location
  combinations

In a real, production version, these would become live data sources: a real
resume/profile store, a real interview question bank, a real course/learning
platform's catalog, and a real salary data provider (like Levels.fyi or
Glassdoor). Keeping them as simple dictionaries for now means the whole
system — routing, memory, tool-calling — can be built and tested end to end
before any real data integration work happens.

## What credentials this needs

Just one: a Google API key (for Gemini). It covers three things at once:

1. The actual chat responses from the orchestrator and all four specialists.
2. Mem0's own internal reasoning (it uses an LLM to decide what's worth
   remembering from a conversation).
3. Mem0's embeddings (the vector representations it uses to search your
   memories later).

All three are pointed at Gemini so a single key covers everything — no
separate OpenAI key, and no Qdrant server to install or pay for. Qdrant runs
in an embedded, on-disk mode (just a folder on the filesystem), which is
enough for a single-user demo like this one.

## Extension ideas (later, once the basics work end to end)

- A **Negotiation Agent** for when an actual offer is on the table and you
  need help deciding how to respond
- An **application tracker**: which companies you've applied to, and where
  each one currently stands
- Splitting the Interview Agent into separate behavioral and
  technical/system-design specialists if one agent starts feeling like it's
  covering too much ground
