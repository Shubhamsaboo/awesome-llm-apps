# Echo Format

One reply, five sections, dense. The user should find and fix an error
in seconds. Target well under 250 words for a ten minute ramble.

Compression rules: nothing appears twice; no "you said" recap (everything
outside My additions is the user's by definition); one line per bullet;
vague quantifiers ("usual", "standard", "soon") go to Open or Guessed,
never silently resolved into a locked item.

## Template

```markdown
## Mission
<one sentence: what you are actually trying to achieve>

## Locked (your decisions and constraints)
- <one line each; mark the stated top priority with **top priority**>

## Open (needs your answer)
- <question the ramble raised but did not answer>

## Ledger
- Flipped: <position A>, then <position B>. Going with B.
- Parked: <tangent, one line>

## My additions (correct these first)
- Inferred: <implied but never stated>
- Guessed: <gap I filled>
```

Close with: "Correct anything that's off, especially My additions. Want
the interview for the Open items?"

## Worked example

**Ramble (compressed):** "ok switching to voice sorry for typos. so i want
some kind of daily digest agent for hacker news but honestly email feels
dead maybe slack. it should rank by relevance to what im building not
just points. oh and my cofounder wants it too so two profiles i guess.
actually no email is fine everyone has email. also random thought we
could sell this later but whatever. it needs to run every morning without
me touching it, thats the whole point, if i have to trigger it manually
its useless."

**Echo:**

## Mission
A zero-touch daily Hacker News digest, ranked by personal relevance,
emailed every morning.

## Locked
- Relevance ranking over raw points
- Two recipients with different interest profiles (you, cofounder)
- Email delivery
- **Top priority**: fully automatic; a manual trigger makes it useless

## Open
- What defines "relevance to what I'm building": a written interest
  profile, repo activity, something else?
- "Morning" means what time, whose timezone?

## Ledger
- Flipped: Slack (email feels dead), then email is fine. Going with email.
- Parked: possibly sellable as a product someday

## My additions (correct these first)
- Inferred: each recipient gets their own ranking, not a shared list
- Guessed: source pool is HN front page plus new stories

Correct anything that's off, especially My additions. Want the interview
for the Open items?
