# Causes of death

What the scanner can read from a git history, how much to trust each verdict,
and what each one means if the user wants to resurrect. The scanner reports
every cause that matches; the first one listed is the primary. Always quote the
evidence, not just the label.

## shiny_object — killed by a newer project

**Signal:** another repo the user owns had its first commit within 14 days of
this repo's last commit. The killer is named in the evidence; when several
newer projects qualify, the nearest in time gets the blame.
**Confidence:** high that the timeline is real; medium that it's causal. Two
projects can share a death week by coincidence — but when the same user shows
this pattern three times, it's not coincidence.
**Resurrection angle:** usually the healthiest corpses. Nothing was wrong with
the project; attention just moved. Check whether the killer is also dead —
chains of three or four are common and worth showing the user.

## deploy_fear — finished but never shipped

**Signal:** README written, 20+ commits, real code — and no deploy config
anywhere. The work was done. The shipping never happened.
**Confidence:** high on the facts, but verify the intent: some projects are
libraries or scripts that were never meant to deploy. A CLI tool with no
vercel.json isn't fearful, it's a CLI tool.
**Resurrection angle:** the best candidates on the board — they score high on
pulse because the work is already done. What remains is small and boring —
deploy config, a domain, hitting publish — which is exactly what an agent is for.
This is also the death most worth naming honestly in the report: building was
never the problem.

## payments_wall / auth_wall

**Signal:** the final commits before death touch payment code (stripe, billing,
checkout) or auth code (oauth, login, sessions).
**Confidence:** high — this one is written right into where the history stops.
**Resurrection angle:** the wall that killed it in 2024 may not exist in 2026.
Managed auth and payment links have eaten most of the integration pain. If the
same wall appears on 2-3 corpses, tell the user directly: the wall isn't
moving, so the approach has to — resurrect with the managed version of
whatever they were hand-rolling.

## boilerplate_wall — died configuring

**Signal:** 60%+ of all file touches in the history were config files. The
project spent its life setting up tooling and never met its actual problem.
**Confidence:** high. The ratio doesn't lie.
**Resurrection angle:** don't resurrect the repo; resurrect the *idea* in a
fresh scaffold. The corpse contains almost nothing worth exhuming — that's the
point of the diagnosis. Ten minutes with a modern starter beats a week of
archaeology in someone's webpack config.

## rewrite_spiral

**Signal:** two or more rewrite/migrate/port commits in the history. The
project kept being rebuilt instead of finished.
**Confidence:** medium — commit messages are noisy. Read a couple before
asserting it.
**Resurrection angle:** the danger is obvious: resurrection becomes rewrite
number four. If the user wants this one back, the plan must freeze the stack
in step 1 and forbid migrations until it ships.

## scope_explosion

**Signal:** 100+ files, many top-level directories, no deploy config, and a
lifespan over a month. It grew instead of shipping.
**Confidence:** medium — monorepos and generated code inflate file counts.
Check what the files are before repeating the verdict.
**Resurrection angle:** don't resurrect the project; resurrect one feature.
Ask the user what the 20% was that they actually wanted, extract that, ship
that. The other 80 files stay in the grave.

## slow_fade

**Signal:** the gap before the final commit was 3x+ the median gap. No wall,
no killer — commits just got further apart until they stopped.
**Confidence:** high on the shape, low on the why. The history shows the fade,
not the reason.
**Resurrection angle:** interest died, and interest is the one thing an agent
can't ship. Ask the user whether they still care before planning anything.
"No" is a fine answer and worth saying out loud — closure is also a feature of
the report.

## unknown — natural causes

**Signal:** none of the above fired.
**Confidence:** n/a — it's the absence of a verdict, not a verdict.
**Resurrection angle:** the scanner can't see it, but you can: read the README
and the last few commits and form your own view. One-day burst projects land
here a lot; so do experiments that answered their question and were correctly
never reopened. Not every dead project is a failure.
