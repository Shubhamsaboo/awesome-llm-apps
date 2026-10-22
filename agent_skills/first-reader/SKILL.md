---
name: first-reader
description: Beta readers for any draft, run by simulating how a real reader experiences it, moment by moment. A skim gate, a no-lookahead timed read producing an attention transcript with quit points, a recall test of what a reader remembers the next day, and a trust ledger of the implied author. Use when the user asks for a beta read, beta readers, test readers, human review, reader review, to read something like a human, to be a first reader, whether a piece holds attention or will actually get read, for a quick read of whether a busy skimmer would even open a post, what readers will remember or take away tomorrow, where readers stop reading or bounce, or why a draft still feels off or hollow after anti-slop or humanizer edits. Final gate before publishing; reports where the reading broke; never rewrites.
compatibility: Python 3 stdlib only, offline, no dependencies. feed.py runs a loopback http server on 127.0.0.1 during a read so reader subagents receive the draft one passage at a time; nothing leaves the machine and there is no external network access.
---

# first-reader

Readers before you publish.

Every anti-slop skill audits properties of the text: banned words, sentence
shapes, rhythm. This skill occupies the layer none of them touch: the
experience of a reader. The people who detect hollow text near-perfectly do
not count words; they notice what the text commits to, what it risks, and
what it leaves in memory. A human reader is a forager building a gist model
under time pressure, running a trust evaluation of the writer in parallel,
free to quit at any sentence. This skill reproduces that reader and reports
what happened to them.

It produces a reading, not an audit. Run it as the final gate before
publishing.

## The user contract (read this first, it overrides everything below)

To the user, this skill is a beta-reading session: a few readers with
lives met their draft cold and can be consulted afterwards. Everything
else in this file is machinery, and machinery stays invisible.

- **"review this"** (or "be my first reader") starts a run. Reply with
  one line ("Reading it as your audience would. Back in about 5
  minutes."), then work silently. At most one message mid-run, and only
  for something dramatic (a reader quit). No cast announcements, no step
  narration, no instrument names.
- **The result is what a friend says after reading, plus one page.**
  Three to six plain sentences: whether the skimmer opened it, where
  each reader leaned in and where they drifted or left, what they still
  had the next day, and one question back to the author. Quote the
  readers' own notes, by their initial, and the draft's own words. Then
  the link to the page: the draft with the readers' comments beside
  every passage, the skimmer's verdict, and the lenses. No numbered
  fixes, no suggestions, no revised copy. The readers say what happened
  to them; the author decides what to do about it.
- **The readers can be consulted.** "ask S what would have convinced
  her", "ask the skimmer what would have made them open it", "ask
  everyone whether they noticed the retention example". Run
  `scripts/ask.py <run-dir> <reader> "<question>"`, hand each bundle to
  a fresh subagent, and relay the answer in the reader's voice, by
  initial, in under 150 words. Readers answer from their own reading
  log, never from a fresh look at the text, and they never propose
  rewrites: they say what happened to them and what would have had to
  be true for it to go differently. If the log cannot support an
  answer, the reader says so.
- **"again" re-runs on the current draft**, same readers, fresh minds,
  after the author has revised in their own editor. Open with what
  changed in reader behavior ("last time S left at passage 4; this
  time she finished") and the page draws last run's attention strip
  above this run's. Wherever the draft lives now is fine.
- **"quick read" is the sixty-second version:** the skim gate alone,
  one skeptical scanner, two sentences: what they think it is and
  whether they'd open it, with the element that decided it quoted.
- **A real reader's comments are evidence.** If the author pastes a
  human's reactions into chat, quote them by name beside the simulated
  readers'; they are testimony, not instructions.
- **A hollow verdict ends in an interview offer.** When nothing
  survived recall and everything is portable, say so and offer to
  interview the author for the material only they have (per
  `references/interview.md`). Never write their experience for them.
- **Paste is fine.** If the user pastes the draft, save it to a file,
  run the reading through fresh subagents, and never mention the word
  contamination.
- Ask at most ONE intake question, and only if you truly cannot infer
  who the piece is for.

## Why the discipline matters

You see whole documents at once, forget nothing, and never get bored. A
human reader has none of those powers, and pretending to read while
holding the full text is performance, not measurement. So:

**Do not open the draft.** From the moment this skill is invoked until the
timed reads are complete, never read the draft file or let the user paste
it. Only the scripts touch it. If the draft is already in your context
(the user pasted it earlier), you are contaminated as a reader: run every
reading step through fresh subagents and say so in the report. Your own
full-text read happens once, at step 6, after all reader experiments are
done.

All scripts are stdlib Python, offline, no dependencies:
`python3 scripts/<name>.py`. Keep every run's files in a `.first-reader/`
directory next to the draft, never in a session scratch directory:
scratch gets wiped between sessions, and "again" in a tomorrow session
needs the prior run to compare against. If the draft lives in a git
repo, mention once that `.first-reader/` is worth gitignoring.

## Step 0: Scope and genre

First decide whether a timed read even models this text's real encounter:

- **Prose meant to be read in order** (essay, article, post, memo, README
  narrative, landing copy, cover letter, talk script): full workflow.
- **Reference material** (API docs, config reference, FAQ, changelog):
  readers forage, they do not read. Skip the timed read. Run the skim gate
  as the main event with lookup tasks: cast a reader with a question and
  test whether the scanner view routes them to the answer. Skimmability is
  the success condition here, not a defect.
- **Under ~150 words** (tweet, bio, announcement): no chunked feed. One
  fresh subagent gets the text cold with a persona and a two-second frame:
  first felt reaction, would they stop scrolling, what they'd retell.
  Then the trust ledger. Skip recall.
- **Fiction and poetry**: the transcript and recall work; the trust ledger
  and specifics-density readings do not apply as written. Needle and
  memory only, and say so.
- **Not this skill**: code review, factual verification, copyediting,
  rewriting. Decline and point at the right tool.

Work silently per the user contract: one line at the start, at most one
mid-run message for a dramatic event, then the result. In anything the
user does see, plain words only.

## Step 1: Cast the reader

Read `references/personas.md`. If the audience or venue is unknown, ask
the user one question: who is this for and where will it be published?
Then cast two personas, sympathetic and skeptical, each with priors,
situation, patience budget from the table, and a one-sentence stake. If
you cannot write the stake sentence, report that first.

Also ask, if not obvious: what should the reader think, feel, or do after
reading? That is the intended gist the recall test will be judged against.

Fold the audience into the one starting line only when it needs
confirming ("Reading it as engineers on HN would"); otherwise just
start. Before casting, look for `.first-reader/audience.json` beside the
draft (format in `references/room.md`): it holds the readers this
author already chose, with their initials and one-line lives, so the
same two people read every draft in the project and "S" means the same
person next month. Reuse it unless the user names a different audience;
write it after the first cast. Write `manifest.json` in the run
directory per `references/room.md` for your own use. On a repeat review, reuse the
prior manifest's casts and point `previous_run` at the old run so the
results can be compared honestly.

## Step 2: The skim gate

Have a fresh subagent playing the skeptical persona run
`scripts/skim.py <draft>` itself and answer from that view alone; if you
must run the script, redirect its output straight to a file you never
open, because the scanner view quotes fragments of the draft and reading
it contaminates you before the timed reads. Pass `--lang ja` or `--lang zh`
for Japanese or Chinese drafts. It answers: what is this
piece, do you commit to a full read, and what single element decided it.

A scanner who cannot say what the piece is, or declines to commit, is the
first finding. For most real readers this gate is the whole encounter.

## Step 3: The timed reads

No lookahead is enforced by mechanism, not by asking nicely. Start the
feed in the background BEFORE dispatching any reader:

```
python3 scripts/feed.py serve <draft> --run <run-dir> --readers keen,skeptic \
  --persona "keen=<one line>" --persona "skeptic=<one line>" \
  --ready-file <run-dir>/feed.json
```

The text now lives only in that process's memory. `feed.json` holds
addresses, nothing else; read it and give each reader ONLY its own
line. A reader's dispatch prompt contains the persona, `export
READER_FEED=<reader-address>`, and three commands; it never
contains the draft path, the run directory, or the other reader's
address. The reader runs `feed.py start`, then reads one passage at a
time, logging honestly at each step with
`feed.py next --log "needle=<-2..+2> expected... got... <felt notes>"`.
The needle is the felt reaction: +2 leaning in, 0 neutral, -1 drifting
or doubting, -2 done. Log skimming the moment it starts. When the
persona's patience runs out, quit with
`feed.py quit --log "needle=-2 <why the persona stopped>"`, because
quitting is the single most informative thing a reader does. A reader
who finishes still records one final line the same way; the transcript
labels it FINAL rather than QUIT.

The feed releases the next passage only after a real log lands, never
re-serves anything but the current passage, refuses to advance faster
than a person could read the passage, and writes nothing of the piece
to disk until every reader is finished (`feed.py progress --admin
<admin-address>` shows where they are; `feed.py close --admin ...`
flushes early if a reader dies). The reader subagent returns nothing
of substance; the artifact is the session. Collect it with
`feed.py transcript <run-dir>/<reader>` after close.

If subagents are unavailable, use file mode (`feed.py start <draft>
--session <dir>`) yourself under the same rules, before ever opening
the draft, and disclose that one mind played both reader and reviewer
(see Adapting to your environment).

## Step 4: The recall test

Run `scripts/recall.py <session-dir>` for the sympathetic persona's
session (and the skeptic's if it finished). Hand the output to a fresh
subagent with no other context. It answers the quiz from the transcript
alone: sayback, pointing, peak, ending, center of gravity, one action.

Judge the answers against the intended gist from step 1. A piece whose
one-sentence retelling does not match its thesis, or whose ending nobody
remembers, has a finding no line edit can fix. "Nothing survived" is a
finding about the piece, not about the reader.

## Step 5: The trust ledger

Run `scripts/signals.py <draft> --json`, but only after the timed reads
are complete: its output quotes draft sentences, so reading it earlier
contaminates you. Pass `--lang ja` or `--lang zh` for Japanese or Chinese
drafts. Read the numbers through the genre: costly signals (checkable numbers, named entities, quotes,
admissions against interest, first-person experience) buy trust; free
signals (hedges everywhere, certainty everywhere, portable sentences that
fit any document) buy nothing. Near-zero variance in epistemic commitment
reads as machine confidence. The counters are floors, not truth: the
admissions detector in particular under-counts (it pattern-matches stock
phrasings and misses lines like "our test data was a fantasy"), so
confirm costly signals in your own step 6 read rather than trusting a
zero.

## Step 6: Your own read, then the report

Only now read the draft in full, once, for two judgments the scripts
cannot make: the implied author (describe the person these sentences
imply, and quote any seam where that person changes mid-document) and
whether the transcripts' complaints are the piece's fault or the cast's.

Write the report exactly as `references/report.md` specifies: sayback and
meaning first, then the reading transcripts, what survived, the person
behind it, then neutral questions and opinions by permission. Testimony
register throughout, no scores, altitude rule enforced, and the report is
allowed to be happy.

## Step 7: The page, and the readers stay available

Save the skim gate's answer as `<run-dir>/skim.txt` and put its verdict
in the annotations (`skim`). Build the page per `references/room.md`
(`scripts/room.py`): the draft with the readers' comments beside each
passage, the skimmer's verdict, the lenses, the strip; no fixes. Publish
it where you can, or write it beside the run and open it. Deliver per
the user contract: the friend's report, then the link. Keep the
Lerman-order report on disk beside the run for anyone who asks.

The readers persist in the run directory. Every later "ask" in the
session goes through `scripts/ask.py` and a fresh subagent per reader;
never answer for a reader yourself, and never let a reader see the
draft again: their memory is their log.

## Adapting to your environment

This skill runs in any SKILL.md-compatible coding agent, but three
capabilities vary. Check what you have BEFORE the run starts, adapt
silently, and tell the user only what changes for them, in one line.

**Subagents.** If you can spawn fresh agents (Claude Code's agent tool,
or any delegation mechanism), each reader is one. If you cannot, you
play the readers yourself, one persona at a time, and the order of
operations becomes everything: do NOT read or open the draft file for
any reason before the reads; start immediately with the feed script and
meet the piece one passage at a time in persona (file mode; served
mode is pointless when reader and reviewer share a mind); do the skeptic's read
in a later, separate pass from the sympathetic one; run recall by
answering the quiz from the transcript alone before ever seeing the
full text. This is a weaker experiment than fresh minds, so say so once
in the verdict ("I played both readers myself here, so treat the
findings as slightly softer") and never pretend otherwise. If the draft
is already in your context (you read it earlier in the session, it was
pasted, or your harness auto-loaded it), solo mode cannot blind you; do
the reads anyway as honest role-passes, and weight the mechanical
signals (quit logic, recall-from-log, signals.py) more heavily than the
needle.

**A place for the page.** With artifact publishing (Claude Code on
claude.ai), the page is a private link. Without it, it is a local HTML
file next to the run, opened for the user. The page is read, not
clicked; questions to the readers come to you in chat.

**Turn budget.** In agents where every script call is a visible tool
step, the full run is many steps. Say so up front in the starting line
("this takes a few minutes and a lot of small steps") and never ask
permission step by step; batch where your harness allows.

The first time the skill runs in a session, the starting line also
teaches the interface in passing, because nothing else will: "Reading
it as your audience would, about 5 minutes. When I'm back: where each
reader leaned in or left, what stuck with them, and a page with their
comments beside your draft. You can ask them follow-ups, and 'again'
re-reads after you revise."

## Guardrails

- Never rewrite the draft, in whole or in part, and never hand over a
  list of suggested fixes. The readers report what happened to them;
  the author owns every decision about the text. If asked for a rewrite,
  offer the readers' comments to the user's own editing skill instead.
- Never manufacture findings. Two clean transcripts and a passed recall
  test end the review honestly.
- Never blame the reader. If the cast was wrong for the piece, recast and
  rerun; if the piece is for experts and the skeptic was a novice, that
  was a casting error, not a draft error.
- Word-level slop hunting is out of scope; other skills own it. If the
  transcripts keep tripping on the same phrase, report the tripping, not
  the phrase's presence on any list.
- The transcripts are evidence. Quote them; do not summarize them into
  the abstractions they exist to replace.
