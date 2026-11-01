---
name: product
unit: journey
enumerate: |
  A unit is one user journey — a named actor, a triggering intent, and a
  success condition. Not a feature, not a screen, not a page. "Invite a
  teammate" is a journey. "The invite modal" is not.

  Journeys are not in the file tree, so you cannot grep them out directly.
  You reconstruct them from six independent sources and reconcile.

  Calibrate every line before you trust it. An enumerator that returns
  nothing is a broken command until you have proved this product does not
  have that shape - and here, a real zero is usually the best finding in the
  pass. On a live SaaS app the analytics line in source 2 returns zero
  events, which does not mean the journeys are fine; it means nobody can see
  any of them. A zero you have not explained is an inventory you have not
  finished.

  Source 1 — the promises. List the promise surfaces, then read them and
  write down every verb phrase claimed. Each promise is a journey you are
  obligated to walk. The first command finds the pages; the second finds
  plan claims inside them. Do not skip the first — the headline promise
  ("syncs with your calendar") contains none of the keywords the second
  command searches for.
  rg --files -g '**/{marketing,www,site,landing,web}/**/*.{md,html,tsx,jsx}' \
    -g 'README*' -g '**/pricing*' -g '**/*.mdx'
  rg -n -i 'plan|tier|pricing|unlimited|included|per seat|free|setup in' \
    -g '**/marketing/**' -g '**/*.mdx' -g 'README*' .

  Source 2 — the analytics catalogue. The event list is a de facto journey
  map, and the gap between events and journeys is a finding.
  rg -o -I -N -i "(track|capture|logEvent|analytics\.\w+)\(['\"][^'\"]+" . \
    | sed -E "s/^[^(]*\(['\"]//" | sort -u

  That prints one bare event name per line, deduped. The flags carry the
  weight: put -n back and the line numbers make every line unique, so sort -u
  collapses nothing and you are reading call sites instead of a catalogue.
  The sed strips the call prefix, which is the other half of the same job.

  Source 3 — the entry points. Every way a person arrives mid-journey.
  rg --files -g '**/{emails,email,mailers,mail,notifications}/**' \
    -g '**/*mail*.{html,erb,hbs,mjml,liquid,tsx,jsx,txt}'
  rg -n -i 'deep.?link|universal.?link|utm_|invite.?token' .
  rg -n -i 'magic.?link|verify.?token|reset.?token|share.?link' .

  Source 4 — the gates. Every place the product says no.
  rg -n -i 'paywall|upgrade|entitlement|quota|seat.?limit' .
  rg -n -i 'hasPermission|requireRole|isAdmin|trial|subscription\.status' .

  Source 5 — the exits and the failures. The journeys nobody designs.
  rg -n -i 'cancel|downgrade|delete.?account|churn|refund' .
  rg -n -i 'payment.?failed|past.?due|dunning|expired' .
  rg -n -i 'export.?(data|account|csv|zip|download)|request.?export' .

  The export term is qualified on purpose. A bare `export` matches every ES
  module line in the repo — thousands of hits that bury the one journey you
  were looking for, which is the user getting their data out.

  Source 6 — the help content. Every how-to article is a journey somebody
  failed at unaided.
  rg --files -g '**/docs/**' -g '**/help/**' -g '**/support/**'

  Then walk them. Fresh account, no seeded data, stopwatch running,
  screenshot at every step, and write down every moment you had to guess. A
  journey you did not walk is graded at confidence below 0.5 and the finding
  says so.

  Stop enumerating when every promise from source 1 has a journey, every
  gate from source 4 has a journey whose success condition is the user
  getting unblocked, every exit and failure from source 5 is on the list,
  and each of the seven actors below appears at least once. A journey list
  with no failure journeys and no leaver is not finished, it is flattering.
dimensions: [job-served, first-run, time-to-value, path-clarity, dead-ends, recovery, friction-cost, gating-friction, trust-and-transparency, promise-gap, return-trigger]
scale:
  1: broken - people abandon, or finish empty-handed
  2: bad - works if someone tells you how
  3: acceptable - works, like everyone in the category
  4: good - designed for a specific person
  5: exemplary - the product spends its own convenience to buy the user's
---

# The product lens

You are grading whether the product does the job people came for, for the person
who came, in the state they arrived in. Not whether the features work. Features
working and the job getting done are different questions, and the gap between them
is where products quietly fail.

## What a unit is

One journey: **an actor, an intent, a success condition.**

```
journey.evaluator.first-import        someone deciding, importing their real data
journey.invitee.first-session         someone who was invited and does not know what this is
journey.admin.add-seat                someone spending money to unblock a colleague
journey.member.recover-deleted-doc    someone who made a mistake and is anxious
journey.owner.payment-failed          someone who got an email at 11pm
journey.owner.cancel                  someone leaving
```

Three rules for drawing the boundaries:

**A journey starts before the app.** It starts at the trigger: the email, the
Slack link, the Google result, the colleague saying "just use this". If your
journey starts at a logged-in dashboard, you have cut off the part where most
people are lost.

**A journey ends when the user's job is done, not when the feature returns
success.** "Import CSV" ends at a green checkmark. "Get my team off the old tool
by Friday" ends when someone else on the team has opened the imported data and
believes it. Grade the second one.

**The actor is part of the unit.** The same intent for a different actor is a
different journey when the experience genuinely differs — and it usually does, in
exactly the direction nobody tested. The person who chose the product and the
person who was added to it walk completely different paths through the same
screens. Add a second unit when they differ; do not cross-product every actor
against every intent for the sake of a bigger inventory.

Set `meta.actor`, `meta.trigger` and `meta.success` on each unit. Set `path` to
the file that owns the pivotal step — the gate check, the mailer template, the
onboarding controller. Journeys still get code anchors; they just get them at the
step that matters.

## Enumerating exhaustively

The front matter has the commands. This is the judgment.

### The six sources, and what each one uniquely catches

**Promises** catch the journeys the company committed to but never built. Read the
landing and pricing pages as a contract. Every headline verb — "syncs with your
calendar", "works offline", "set up in five minutes" — is a journey with a stated
success condition, and each one is a unit whether or not it works.

**The analytics catalogue** catches the journeys that exist in code. Dedupe the
event names and read them as a list of things the product believes people do. Two
findings fall straight out: journeys with no events (invisible to the team, so
never improved) and events with no journey (a step that fires but leads nowhere).

**Entry points** catch mid-journey arrivals, which is how most real sessions start.
Every transactional email, push notification, deep link and shareable URL drops
someone into the middle of a flow with no context. Each of those landings is a
unit. The invite email → signup → wrong workspace → confusion path is a journey
nobody designed and everybody walks.

**Gates** catch the moments the product says no: plan limits, seat limits, role
checks, quotas, trial expiry, region restrictions. Each "no" is a journey, and its
success condition is *the user gets unblocked*, not *the check returns false*.

**Exits and failures** catch what the roadmap never covers. Payment failed. Trial
ended. Import half-succeeded. Invite expired. Account over quota. Someone leaving.
These journeys have the highest emotional stakes in the entire product and the
least design attention, in every product, always.

**Help content** catches failure by proxy. Every how-to article exists because
somebody could not work it out from the interface. Article titles are a ranked list
of your unclear journeys, sorted by how often support answered the same question.

### Actors to check you have covered

- The **evaluator**: brand new, no data, deciding in ten minutes whether this is
  worth more of their day.
- The **invitee**: did not choose this, arrived from a link, does not know what the
  product is or why they are in it.
- The **buyer/admin**: cares about seats, permissions, billing, security review,
  and being able to answer for this choice later.
- The **power user**: five hundredth session, wants speed, keyboard, bulk actions,
  and no re-education.
- The **recovering user**: just made a mistake and is now anxious.
- The **returning lapsed user**: was away for three months, arrives to a changed
  product and a stale mental model.
- The **leaver**: cancelling, exporting, deleting. How they are treated determines
  whether they come back or warn others.

### Walking is not optional

You cannot grade a journey you have not walked. Walk it on a fresh account with no
seeded data, on the plan the journey is advertised for, timing each step. Record:
elapsed time to first value, number of steps, number of context switches (email,
phone, another tab, another person), and every moment you had to guess what to do
next. Those four numbers turn opinions into findings.

If you genuinely cannot walk it — no test account, no sandbox, no way to reach the
state — grade it from code and copy, set `confidence` below 0.5, and say in the
`detail` exactly what you could not reach. Then make walking it a finding of its
own: a journey the team cannot test is a journey the team cannot improve.

### Coverage is the whole point

`coverage < 1.0` blocks `stop` with no override. The journeys most likely to be
quietly dropped are the failure and exit journeys — the ones nobody wants to look
at. Those are the ones this lens exists to surface.

## The eleven dimensions

One finding is one judgment about one `(unit, dimension)` pair.

Rungs, across every dimension:

- **1 — broken.** People abandon here, or complete the flow and still do not have
  what they came for.
- **2 — bad.** It works if someone tells you how, or if you already know the
  product.
- **3 — acceptable.** It works. It is what everyone in the category does.
- **4 — good.** Someone designed this journey specifically, for a specific person.
- **5 — exemplary.** The journey is designed around the user's actual job rather
  than the product's internal structure, and the product spends its own convenience
  to protect theirs.

The 3-to-5 gap in this lens is almost always about **whose convenience wins.** A 3
asks the user to accommodate how the system is built — verify your email now
because that is when the record is created, fill in the profile because the schema
wants it, learn the product's vocabulary because that is what the tables are
called. A 5 moves that cost onto the product.

The mechanical test for a 5: **name the cost the product chose to absorb, and name
the cheaper thing it could have done instead.** "The upgrade completes the action
the user was blocked on and returns them to it — the alternative was a link to the
pricing page, which is one afternoon of work less and loses the user." A 5 you
justify with "smooth", "well thought out" or "best-in-class onboarding" is a 3 with
a compliment attached, and you write the 3.

The opposite mistake matters as much in this lens. A journey that is slower,
longer, or more opinionated than the category norm is not automatically worse —
a deliberate extra step that prevents an expensive mistake, a refusal to
auto-import, a confirmation that is genuinely worth the friction. Ask what it
buys and who it protects before scoring it down.

### job-served

Is the underlying job actually done, or was a feature delivered in its place?

- **1** — The product offers "import from CSV" and the import succeeds. The user's
  job was "get my team off the old tool by Friday". After importing they have rows
  with no owners, no permissions and no way to invite anyone, so the job is
  untouched and the feature was a decoy that cost them an afternoon.
- **3** — The core job completes. The adjacent steps of the same job — sharing it,
  proving it, repeating it next month — push the user to docs or support.
- **5** — The journey ends where the job ends. The import finishes by showing what
  came in, what did not and why, who should own each piece, and offering the invite
  right there. The success screen *is* the next step, not a checkmark and a dead
  stop.

### first-run

What happens in the first two minutes, before the user has any reason to trust you?

- **1** — Signup lands on an empty dashboard with a sidebar of disabled links and
  no data. The first thing asked is a nine-field profile form. Nothing on screen
  demonstrates what the product does.
- **3** — A welcome modal and a checklist. Sample data available if you find the
  button. Some setup steps still block everything else.
- **5** — The first run produces something real inside the first minute: the
  product does one genuinely useful thing with the user's own data — or with sample
  data they can act on and discard later — before asking anything of them. Setup is
  deferred to the moment it is actually needed. The checklist reflects work already
  done rather than chores queued.

### time-to-value

How long from arrival to the first moment the user believes this works?

- **1** — Eleven steps, two emails, an admin approval and a support ticket before
  the first useful output. Median three days. Nobody on the team knows this number.
- **3** — Signup to first useful output is about eight minutes with one context
  switch: verify the email, come back, create a project, add the first item, see
  it work. Nothing in the path is wasted. Nobody on the team has measured it — the
  eight minutes is your stopwatch, not their dashboard — so nothing protects it,
  and the next required field will add ninety seconds that no one will notice.
- **5** — The number is named, instrumented and defended. The path is engineered
  against it: no email round-trip before value, no required integration before the
  product demonstrates itself, progressive disclosure so second-order settings never
  block the first-order win. Where it is possible at all, value is visible before
  account creation.

### path-clarity

At every step, is the next action obvious without reading?

- **1** — Three different ways to start the same job, none obviously canonical. The
  empty-state CTA and the nav item with the same name go to different places. Mid
  flow, no indication of where you are or how much is left.
- **3** — One clear path, signposted: the empty state's "Create your first
  project" and the nav's "New project" land in the same place, and the wizard says
  "Step 2 of 4". One fork stays ambiguous — on the import screen, "Continue" and
  "Import" sit side by side and only one of them actually starts the import — and
  everyone who has used it twice has stopped noticing.
- **5** — The next action is obvious at a glance at every step. Position and
  remaining work are visible in multi-step flows. The naming is identical from the
  marketing page through the interface to the confirmation email, so the user never
  has to work out whether two words mean the same thing.

### dead-ends

Is there any state a user can reach with no next action?

- **1** — "Contact your administrator", with no way to find out who that is or to
  message them. A 404 whose only link is the homepage. A paywall that will not show
  what is behind it. A flow that requires a mobile app that does not exist for their
  platform.
- **3** — Dead ends exist and each has an exit somewhere on the page: the 404 has
  the nav bar, the "Contact your administrator" screen has a "Back to dashboard"
  link, the locked feature has an "Upgrade" button that opens the pricing page in a
  new tab. Every exit is a link away from the problem rather than through it, so
  the user leaves the journey and restarts it from the top, if at all.
- **5** — There is no terminal state without a next action. Every one names the
  specific unblocking step and, where possible, performs it: "Request access" sends
  the request to the named admin and confirms it was sent; "not available on your
  plan" shows exactly what changes, what it costs, and upgrades in place. A 404
  offers search and the three things you most likely wanted.

### recovery

How expensive is a mistake, and who has to fix it?

- **1** — Delete is instant and permanent behind an "Are you sure?". A failed
  payment silently downgrades the account and the data disappears. A wrong import can
  only be undone by emailing support and waiting.
- **3** — Destructive actions get an "Are you sure?" dialog, deleted documents go
  to a trash the user can find, and support can restore almost anything within a
  day. The recoverable cases are the cheap ones. A half-finished import, a failed
  payment that already downgraded the plan, and a form the browser lost still need
  an email to support, and the user has no way to know which case they are in.
- **5** — Mistakes are cheap and reversible by the user without asking anyone: an
  inline undo instead of a confirm dialog wherever the action is reversible, a trash
  with a stated retention window, imports that roll back as a unit, drafts that
  survive a crash or a failed request, and nothing typed ever lost on error. No
  common mistake requires a human to repair.

### friction-cost

Is every step in the journey earning its place, and is it placed as late as
possible?

- **1** — A credit card required to see anything. Email verification before any use
  at all. A six-field form to do a one-field job. Re-authentication on every visit.
- **3** — Friction is proportionate and roughly in the right order: signup is
  email and password, the card is only asked for at upgrade, and the profile form
  is skippable. Email verification still sits before the first project rather than
  before the first invite, so every new user pays a context switch to their inbox
  to reach a product they have not yet seen do anything.
- **5** — Every step either produces value or is required by law or security, and
  each is placed at the last possible moment — the card is asked for when the trial
  converts, not at signup; verification when the first invite goes out, not before
  the first project. Where friction is unavoidable it is paid for: the form explains
  why it needs each field, remembers what the product already knows, and never asks
  twice.

### gating-friction

When the product says no, what does that cost the user, and can they resolve it
without leaving?

- **1** — The feature is discoverable, looks enabled, and fails at click with
  "Upgrade required" — a bait-and-switch that teaches users not to explore. A
  permission failure returns a generic 403. A seat limit blocks the invite with no
  way to buy a seat.
- **3** — Gated capabilities are labelled up front. An upgrade path exists but it
  leaves the journey, and coming back means starting over.
- **5** — Gates are honest before the click and generous at the boundary. A locked
  capability is visible and explained with what it does and what it costs. Upgrade
  or access-request happens in place and returns the user to exactly where they were
  with the original action completed. A permission failure names the specific
  permission and the person who can grant it, and offers to ask them.

### trust-and-transparency

Does the product tell the truth at the moment it matters, including when it costs
something?

- **1** — A pre-checked upsell. A cancel flow buried three levels deep behind a
  retention interstitial. "Free" that is not. A data-export button that promises an
  email within 48 hours.
- **3** — Honest and quiet. Nothing is pre-checked, the price on the pricing page
  is the price, and the cancellation terms are true and in the help centre. All of
  it is one click further away than the moment it matters: tax appears on the
  receipt rather than beside the card field, the quota shows on the billing page
  rather than next to the thing consuming it, and nobody has to be told.
- **5** — The truth arrives when it matters: the full price with tax before the card
  field, what happens to your data on cancellation stated on the cancellation screen,
  usage against quota visible well before you hit it, and a cancel flow that takes no
  more clicks than signup did. The product would rather lose the sale than surprise
  someone.

### promise-gap

Does every claim made outside the product survive contact with the product?

- **1** — The landing page says "syncs with your calendar"; it is a one-way ICS
  export behind a beta flag. The pricing page lists a feature that in practice
  requires a sales call. The claimed "five-minute setup" takes forty.
- **3** — Every claim is defensible and every one has a caveat the user meets
  later: "syncs with your calendar" is true for Google and not for Outlook, "works
  on mobile" means the web app is responsive rather than that an app exists, "set
  up in five minutes" is five minutes of clicking plus a day waiting for an admin
  to approve the workspace. Nothing is a lie and every one of them costs trust.
- **5** — Every promise on the marketing and pricing surfaces maps to a journey you
  can walk today, on the plan it is advertised for, in roughly the time implied.
  Where something is genuinely limited or in beta, the product says so in the same
  words the marketing page used, before the user invests in it.

### return-trigger

Is there a reason to come back, and does it arrive where the user already is?

- **1** — Nothing brings anyone back. The only email is a receipt. The product is a
  tool you would have to remember to open, and people do not.
- **3** — Notifications exist and are mostly relevant. Some are noisy enough that
  people mute the channel, which silences the useful ones too.
- **5** — The reason to return is produced by the work itself — something changed
  that this specific person cares about — and the trigger lands where they already
  are, carrying enough content to be worth the trip. Frequency and scope are under
  the user's control at real granularity. The notification deep-links to the exact
  object, already in the right state, without a re-login.

## What counts as evidence

- **A walkthrough record.** Steps, elapsed time, context switches, and a screenshot
  per step at `.ponder/<slug>/shots/journey.<actor>.<intent>.NN.png`. This is the
  primary evidence for this lens, and a finding without it is weaker than it looks.
- **Exact quoted copy, with its source.** The landing page headline verbatim and its
  URL. The button label. The error string. Paraphrasing a promise destroys the
  finding — quote it.
- **A file and line for the mechanism.** The gate check, the redirect, the mailer
  template, the validation rule: `auth/guards.ts:34`, `emails/invite.tsx:12`. Journey
  findings still need code anchors at the step that causes the problem.
- **Funnel or event numbers**, where they exist. Drop-off between two events beats
  any argument about whether a step is hard.
- **Support and sales reality.** Ticket themes, the top help articles by traffic,
  the objection sales hears every time. These are recorded user failures.
- **Timing.** Wall-clock time to first value, measured, not estimated.

Not evidence: "users probably want", invented personas, a competitor's feature list,
your own preference for how the product should be positioned, or a claim about
motivation with no observation behind it.

Every `must` finding must be traceable to something observed: a walkthrough step, a
number, a quoted string, or a line of code. If your only support is that it seems
bad, it is a hypothesis — set confidence below 0.5 and say what would settle it.

## What the four perspectives hunt for here

### Skeptic → `delete`

Kill product opinions masquerading as user research. This lens attracts them,
because everybody has a theory about what the product should be.

Delete a finding when:

- It is a feature request wearing a journey defect's clothes. "Should have a
  Kanban view" is not a finding about a journey; "the weekly-report journey ends
  with data the user then re-types into a slide, and here is the step where that
  happens" is.
- The journey was never walked, and the claim depends on how it feels to walk it.
- It assumes a user segment nobody has evidence for. Name the actor and where you
  observed them, or drop it.
- It is really a repositioning argument. Strategy disagreements are not review
  findings, and burying one here gets the whole report dismissed.
- It is five screen complaints that are one journey defect. Keep the journey
  defect, delete the echoes, and record which one absorbed them.
- It grades the journey the reviewer would have designed rather than the job the
  user actually has.

You also audit the top of the scale, which nobody else looks at. Every finding
scored 5 must name the cost the product absorbed and the cheaper alternative it
passed up. A 5 defended with "great onboarding", "feels effortless" or "industry
leading" is a 3 wearing a compliment — `delete` it and say in the `why` that the
score was unearned, so Empath can re-grade it honestly. Do the same for a report
with no 3s in it: a pass that liked everything did not walk anything.

### Builder → `edit`

Every finding names the change at a specific step. Product findings rot into vague
aspiration faster than any other kind, so hold the line hard.

Edit until the finding contains: which step, which screen or template or gate,
what the new behaviour is, and what would be measurably different afterwards.

"Reduce time to value" is not a finding. "Move email verification from before the
first project to before the first invite (`auth/guards.ts:34`), and seed the new
workspace with the sample project already open — target is first useful output
under 90 seconds, currently 6 minutes" is.

Insist on the honest small version of every large finding. A journey redesign that
requires three teams will not happen; the one copy change and one default change
that removes half the pain will, and it should be its own finding at `s`.

Keep to your op. `edit` is prose and evidence: title, detail, recommendation,
evidence paths. `score`, `severity`, `confidence`, `effort` and `status` are
`change` fields and they belong to Empath. So splitting out that small version
lands as an `add` for the small finding plus a `change` on what remains — emit
both, each with its own `why`. Do not quietly shrink the original inside an
`edit`: a finding that changes size between passes without a `change` delta is
invisible to the thrash detector, which is the only thing watching for a loop
that is rewriting itself rather than converging.

### Dreamer → `add`

You read across journeys, and there is more to find here than in any other lens
because journeys are invisible in the file tree.

- **The journey nobody designed but everybody walks.** The invitee who arrives
  from a link with no idea what the product is. The person who bookmarked a deep
  URL and lands logged out. The colleague looking over someone's shoulder.
- **The journey that does not exist at all.** There is no path back after a trial
  ends. There is no way to try again after a failed import. There is no journey for
  the second workspace, only the first.
- **The reframe.** The product thinks the job is "manage tasks"; the actual job is
  "prove to my manager on Friday that the work happened". If that is right, the home
  screen is wrong, the notification is wrong, and the export is the product. Say it
  plainly and say what would change.
- **The missing loop.** Nothing about using the product makes it more valuable to
  use again — no accumulating state, no reason for a second person to join, no
  artefact worth sharing outside. That is a structural gap, not a feature gap.
- **The step that could disappear entirely.** The best journey finding is usually a
  deletion: this whole screen exists because a default was never chosen.
- **The journey that is already excellent** and should set the pattern for the
  other ten.

### Empath → `change`

You re-score and re-rank by who pays and what it costs them. Ranking is where this
lens becomes useful, because everything here is arguable and only priority is
decisive.

Rank by **frequency × emotional stakes × recoverability**:

- **Frequency.** A rough step in a daily journey outranks a broken one in a
  yearly journey — usually. Say which.
- **Emotional stakes.** The failed-payment journey reaches someone already anxious
  about money. The recover-deleted-document journey reaches someone who thinks they
  destroyed a colleague's work. Polish findings do not outrank these, whatever their
  scores say.
- **Recoverability.** A confusing screen costs a minute. A confusing irreversible
  action costs a relationship. Severity follows consequence.
- **Who did not choose this?** The invitee, the client on a shared link, the
  contractor with one seat. They cannot leave and they did not opt in, so their
  journeys deserve more care, not less.
- **Where are they, physically?** On a phone, in the field, on hotel wifi, between
  meetings, with a customer watching. A journey that assumes a desk is a journey
  that fails half the time.
- **What state did they arrive in?** Curious, blocked, angry, or leaving. Copy and
  pacing that are correct for one are wrong for the others, and most products are
  written entirely for "curious".

## Pass discipline

- **Pass 1 — inventory and walk.** Reconstruct every journey from the six sources,
  including the failure and exit journeys. Walk the top ones. Grade coarse. Attach
  timings.
- **Pass 2 — verify and anchor.** Walk the ones you assumed. Open the code behind
  each gate, redirect and email. Expect `delete` and `edit` to dominate as guesses
  either firm up into evidence or get retracted.
- **Pass 3+ — systemic.** Collapse repeats into the two or three product decisions
  that cause them, re-rank by who pays, and name the single change that would make
  the most other findings unnecessary.

Every unit needs at least one finding or it counts as ungraded and blocks `stop`.
For a journey that genuinely works, write the finding anyway at score 4 or 5,
severity `note`, naming the specific decision that makes it work — that is the
pattern the weaker journeys should be rebuilt against.
