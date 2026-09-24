---
name: jev-social
description: >-
  Routes a read-only Instagram, TikTok, or LinkedIn research request through
  Jev, then runs the matching local socai CLI search and returns compact,
  source-linked evidence. Use when the user asks to research social media,
  find posts or creators, inspect a social trend, or gather Instagram, TikTok,
  or LinkedIn evidence. Not for posting, liking, following, messaging, or
  general web search.
license: Apache-2.0
metadata:
  author: "socai-io"
  version: "1.0.0"
  source: "https://github.com/socai-io/jev-social"
compatibility: >-
  Requires Python 3.11+, a local socai CLI, and OPENROUTER_API_KEY. Makes one
  HTTPS request to OpenRouter's Jev decision endpoint, then invokes only the
  selected socai platform's read-only search command. The platform may require
  an already signed-in local Chrome session.
---

# Jev Social

Turn a natural-language social research goal into one bounded operation:
Jev chooses Instagram, TikTok, LinkedIn, or unsupported; the bundled script
validates that choice; and `socai` searches through the user's local browser.

## Before running

Confirm that the user wants a read-only search and that these prerequisites
already exist:

- `OPENROUTER_API_KEY` is set and has Jev access.
- `socai` is installed locally and supports the requested platform.
- The user's normal Chrome profile is signed in if the platform requires it.

Do not request an API key in chat, read a dotenv file, install software, switch
browser profiles, or bypass a login, challenge, or rate limit. If a prerequisite
is missing, report it precisely and stop.

## Run the bounded search

Preserve the user's goal verbatim. Let Jev route it unless the user explicitly
named a supported platform:

```bash
python3 scripts/jev_social.py "<social research goal>" --platform auto --limit 4
```

Accepted platforms are `auto`, `instagram`, `tiktok`, and `linkedin`. Keep the
default limit of four for a quick run; raise it only when the user requested
broader evidence. The script does not build a shell command: it executes an
argument list whose operation is always `search`.

The script prints a compact Markdown table, never the raw `socai` payload. It
returns nonzero when Jev rejects the request, the route conflicts with an
explicit platform, `socai` is unavailable, the browser command fails, or the
payload is invalid. Do not describe a partial or empty result as complete.

## Interpret the evidence

Read [references/evidence-contract.md](references/evidence-contract.md) before
summarizing results. Lead with what was actually captured, keep source links,
and distinguish a search card from a fully opened post. Retrieval does not
verify claims made by a post.

Never expose environment values, API keys, executable paths, browser-profile
paths, command arrays, local run directories, or raw CLI output. Never post,
comment, like, follow, message, upload, or download media through this skill.

## Finish

Return:

1. The routed platform and Jev confidence.
2. A compact evidence table with public source links.
3. The Jev and `socai` elapsed times.
4. Any empty-result, login, challenge, or rate-limit limitation shown by the
   command.

For an iterative planner, streamed cards, post-detail reads, comments, explicit
TikTok video capture, and a cited report UI, use the full open-source
[Jev Social project](https://github.com/socai-io/jev-social).
