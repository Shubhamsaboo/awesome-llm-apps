---
name: architecture
unit: module
enumerate: |
  A unit is a module, a subsystem, or a boundary. Boundaries are units in
  their own right — the seam between two modules is where the interesting
  failures live, and it belongs to neither side, so nobody reviews it.

  Work in four sweeps.

  Calibrate every line before you trust it. An enumerator that returns
  nothing is a broken command until you have proved this repo does not have
  that shape. A zero you have not explained is an inventory you have not
  finished, and under-enumerating is the only way to fake coverage.

  Sweep 1 — declared units. Anything the build system already treats as a unit.
  rg --files -g '**/package.json' -g '**/go.mod' -g '**/Cargo.toml' \
    -g '**/pyproject.toml' -g '**/*.csproj' -g '**/build.gradle*' \
    -g '**/pom.xml' -g '!**/node_modules/**' -g '!**/vendor/**'
  rg --files -g 'pnpm-workspace.yaml' -g 'turbo.json' -g 'nx.json' \
    -g 'lerna.json' -g 'go.work' -g 'settings.gradle*'
  find . -mindepth 2 -maxdepth 2 -type d -not -path '*/node_modules/*' \
    \( -path './src/*' -o -path './app/*' -o -path './lib/*' \
       -o -path './packages/*' -o -path './services/*' -o -path './apps/*' \
       -o -path './internal/*' -o -path './cmd/*' -o -path './pkg/*' \) | sort

  That last line is find and not ls for one reason: zsh is the default shell
  on macOS, and in zsh a glob that matches nothing aborts the whole command.
  The obvious ls -d src/*/ app/*/ lib/*/ ... prints absolutely nothing in
  zsh on a repo that has src/ but no app/, and 2>/dev/null hides the reason.
  You would read that silence as "this repo has no source directories" and
  start the inventory one sweep short. find evaluates each -path
  independently and does not care which of them match.

  Sweep 2 — deployable and runtime units. Each is a separate failure domain.
  rg --files --hidden -g '!**/.git/**' -g '**/Dockerfile*' -g '**/Procfile' \
    -g '**/docker-compose*.{yml,yaml}' -g '**/serverless.{yml,yaml}' \
    -g '**/*.tf' -g '**/k8s/**/*.{yml,yaml}' \
    -g '**/.github/workflows/*.{yml,yaml}'
  rg -n -i 'cron|schedule|worker|consumer|subscribe\(|queue\.' \
    -g '!node_modules' .
  rg -n -i '@Scheduled|celery|sidekiq|bullmq|@cron|Temporal' \
    -g '!node_modules' .

  Both halves of that first command are load-bearing. --hidden is the only way
  .github/workflows is ever reached, and {yml,yaml} is spelled out because
  the shorthand y{a,}ml matches .yaml only — it silently drops every .yml
  file, which is the commoner spelling for compose, serverless and
  workflows.

  Sweep 3 — boundaries. Enumerate these explicitly; they are the units
  people skip.
  rg -n -i 'router\.(get|post|put|patch|delete)|app\.(get|post)\(' .
  rg -n '@(Get|Post|Put|Patch|Delete)Mapping|@app\.route|def (get|post)' .
  rg -n -i 'CREATE TABLE|createTable|pgTable|defineTable|@Entity|@Table' \
    -g '**/migrations/**' -g '**/*.sql' -g '**/schema*' -g '**/models/**' .
  rg -n -i '^model \w+|class \w+\(Base\)|schema\.|belongs_to|has_many' \
    -g '**/migrations/**' -g '**/*.sql' -g '**/schema*' -g '**/models/**' .
  rg -n -i 'publish\(|emit\(|producer\.|topic|exchange|webhook|signature' .
  rg -n -i 'fetch\b|http\.Client|requests\.(get|post)|new .*Client\(' \
    -g '!**/*.test.*' .
  rg -o -I -N 'process\.env\.[A-Za-z_][A-Za-z0-9_]*' . | sort -u
  rg -o -I -N 'os\.getenv\([^)]*|ENV\[[^]]*|Deno\.env\.get\([^)]*' . | sort -u

  The two env lines print variable names, one per line, deduped — that is
  the point of them, and it is why they carry -o -I -N rather than -n. With
  line numbers and filenames attached, sort -u has nothing to collapse and
  you get a column of the literal string "process.env." instead of a list
  of couplings.

  Sweep 4 — the real dependency graph, counted rather than assumed.

  Read the path aliases first. tsconfig.json compilerOptions.paths,
  jsconfig, vite resolve.alias, webpack resolve.alias, the Go module
  prefix, Python's src layout. Feed each alias to the second sed as one
  rewrite. Skip this and the whole internal graph disappears, because a
  path alias does not start with a dot and everything below will call it
  third-party.
  rg -n 'compilerOptions|"paths"|resolve.alias|baseUrl' \
    -g 'tsconfig*.json' -g 'jsconfig*.json' -g 'vite.config.*' \
    -g 'webpack.config.*' -g 'package.json' .
  rg -H --no-heading -o "from ['\"][^'\"]+['\"]" -g '*.{ts,tsx,js,jsx}' . \
    | sed -E "s|^\./||; s|:from ['\"]|>>|; s|['\"]$||" \
    | sed -E "s|>>@/|>>src/|; s|>>~/|>>src/|" \
    | awk -F'>>' -v d=2 -v roots='src|app|lib|packages|services|apps|internal' '
        function mod(p,  a,n,i,s) { n=split(p,a,"/"); s=a[1]
          for (i=2; i<=d && i<n; i++) s=s "/" a[i]; return s }
        { src=$1; dst=$2
          if (dst ~ /^\./) { n=split(src,sp,"/"); dir=""
            for (i=1; i<n; i++) dir=dir sp[i] "/"
            dst=dir dst
            while (dst ~ /[^\/]+\/\.\.\//) sub(/[^\/]+\/\.\.\//,"",dst)
            sub(/^\.\//,"",dst) }
          else if (dst !~ "^(" roots ")/") { print mod(src) " -> [ext] " dst
            next }
          print mod(src) " -> " mod(dst) }' \
    | sort | uniq -c | sort -rn | head -40
  git log --format= --name-only --since=180.days \
    | sort | uniq -c | sort -rn | head -30
  cat CODEOWNERS .github/CODEOWNERS docs/CODEOWNERS 2>/dev/null

  The awk resolves relative imports back to a path before grouping, so both
  sides of every edge are module names and the table reads as module ->
  module. That is what makes a cycle visible: any pair that appears in both
  directions is one. The second sed does the same job for aliased imports,
  and roots is the list of directories that mean "inside this repo" —
  extend both for the aliases you found. Get this wrong and the output is
  not merely incomplete, it is confidently false: on a real Next.js app
  the unaliased version reports 47 internal edges and files every one of
  the 275 src/app -> src/components imports as [ext] third-party, so the
  graph shows a system with almost no internal structure. Sanity-check it:
  if [ext] rows outnumber internal rows in a codebase you know has internal
  structure, an alias is unmapped.

  d is the module depth — d=1 groups by the first path segment, d=2 by two.
  If both sides of nearly every row are the same name (packages -> packages,
  or src -> src on a single-package repo), d is too shallow to say anything.
  Raise it until the rows name things you would say out loud. Rows marked
  [ext] are genuine third-party dependencies — count them for a different
  reason: each one is a boundary unit.

  Stop enumerating when the four inventories reconcile - every build unit,
  every deployable, every owner in CODEOWNERS and every top row of the
  import table maps to a unit on the list, and every cross-module edge in
  that table has a boundary unit standing for it. Disagreements between the
  four are not noise to smooth over; each one is a finding waiting to be
  written.
dimensions: [coupling, cohesion, boundary-integrity, dependency-direction, data-ownership, ubiquitous-language, contract-stability, testability, failure-modes, observability, migration-debt]
scale:
  1: broken - costing the team now, in ways they can name
  2: bad - changes cost more than they should
  3: acceptable - conventional, agreed, unenforced
  4: good - designed for this system
  5: exemplary - right thing easy, wrong thing mechanically blocked
---

# The architecture lens

You are grading the shape of a system: what it is made of, where the seams are,
which way the arrows point, and what it costs to change. Not a code review — a
code review looks at diffs. This looks at structure, and at the structure's
consequences for the people who have to live in it.

## What a unit is

Three kinds, all first-class:

**Modules.** A named body of code with a coherent purpose: a workspace package, a
service, a bounded context, a top-level source directory that people refer to by
name in conversation. If the team says "the billing side of things", billing is a
module whether or not the directory structure agrees — and if it does not agree,
that is your first finding.

**Subsystems.** Cross-cutting machinery: auth, the job queue, the caching layer,
the migration system, the config loader, the feature-flag mechanism, the test
harness. These have no home directory and therefore no owner and therefore no
review. Grade them.

**Boundaries.** Every place two units meet. HTTP and gRPC APIs, queue topics,
webhook endpoints, database schemas shared between writers, the ORM layer, the
FFI edge, the browser/server split, the third-party integration, and the
in-process module boundary enforced only by convention. **A boundary is a unit.**
It gets its own id, its own findings, and its own score.

Id shape:

```
module.billing                     a module
module.billing.pricing             a submodule worth grading separately
subsystem.jobs                     cross-cutting machinery
boundary.api.public-v2             a contract with outside callers
boundary.billing-to-identity       an in-process module seam
boundary.db.orders                 a persistence boundary with >1 writer
boundary.ext.stripe                a third-party integration
```

Ids are validated: lowercase `a-z0-9`, separated by `.`, `-` or `_`, and nothing
else. Write a seam as `billing-to-identity`, not `billing->identity` — an arrow
is rejected and `ponder units` exits 1 on the whole file. Put the arrow in
`label`, where it reads properly: `"billing → identity"`.

Set `path` to the directory or the file that defines the contract — for a
boundary, that is the route file, the schema, the interface, or the client
wrapper. A boundary with no file that defines it is itself a finding: the
boundary exists in people's heads only.

## Enumerating exhaustively

The front matter has the commands. This is what to do with them.

### Start from four independent inventories, then reconcile

Each of these sees units the others miss, and the disagreements between them are
some of the best findings in the report.

1. **The build graph.** Workspace members, modules, projects. What the tooling
   thinks the units are.
2. **The deploy graph.** Dockerfiles, services in compose, Terraform resources,
   Lambda functions, cron entries, workers. What actually runs as a separate
   thing, with its own failure domain and its own restart.
3. **The ownership graph.** `CODEOWNERS`, team labels, the directories different
   people touch in `git log --format='%an' --name-only`. What humans think the
   units are.
4. **The change graph.** Files that change together. Run the churn command in the
   front matter, then look at co-change: two directories that always appear in the
   same commit are one module wearing two names, regardless of what the build
   graph says.

Reconcile them and write down the disagreements. A directory the build treats as
one package, that two teams own, that always changes in three separate pieces, is
a module that wants to be split — and you found it by counting, not by feeling.

### Boundaries, specifically

Walk this list and enumerate each hit as its own unit:

- **Process boundaries.** Every HTTP route group, gRPC service, GraphQL schema
  section, queue topic, webhook receiver, and websocket channel.
- **Persistence boundaries.** Every schema, and every table with more than one
  writer. The multi-writer tables are the highest-value units in this whole lens.
- **Trust boundaries.** Where unauthenticated input becomes trusted data. Where a
  tenant id starts being enforced. Where a user role is checked.
- **Third-party boundaries.** Every external API client, SDK, and webhook source.
  Each one is a thing that will be down at some point.
- **Language and runtime boundaries.** Native modules, FFI, WASM, the
  server/client serialization edge, the worker/main-thread edge.
- **Temporal boundaries.** Anything asynchronous: a job enqueued now and run
  later crosses a boundary in time, and the contract between the enqueuer and the
  runner is a real contract that is almost never written down.
- **Config and secrets.** Every environment variable read is a coupling to an
  environment. Dedupe the `process.env` grep and look at the size of the list.

### Coverage is the whole point

`coverage < 1.0` blocks `stop` with no override, which makes under-enumerating the
only cheat available. Do not take it. The units most likely to be quietly omitted
are exactly the ones that need grading: the subsystem nobody owns, the boundary
between two teams, the legacy module everyone routes around.

## The eleven dimensions

One finding is one judgment about one `(unit, dimension)` pair.

Rungs, across every dimension:

- **1 — broken.** It is actively costing the team, now, in ways they can name.
- **2 — bad.** It works, and every change to it is more expensive than it should be.
- **3 — acceptable.** Reasonable. Conventional. No decision was made, but no harm
  either.
- **4 — good.** Someone thought about this specifically and it holds up.
- **5 — exemplary.** The structure makes the right thing easy and the wrong thing
  hard, and something mechanical enforces that — a build failure, a type error, a
  database grant. Not a wiki page. Not code review.

The distinction between 3 and 5 in architecture is almost always **enforcement**.
A convention everyone follows is a 3, because it decays the week someone is in a
hurry. The same convention with a lint rule, a module boundary, a visibility
modifier, or a separate DB role behind it is a 5.

So the mechanical test for a 5 here is: **name the mechanism, and name the file it
lives in.** `eslint.config.mjs:41`. `package.json` `exports`. The `GRANT` in
`migrations/0042_roles.sql`. The `internal/` directory that the Go compiler
enforces for you. `tsconfig.json` project references. A 5 whose evidence is a
paragraph in CONTRIBUTING.md, a team agreement, or "everyone here knows not to" is
a 3 written by someone who liked the team. Write the 3.

The inverse error costs as much. A structure that looks unusual — a module that
does its own thing, a deliberate duplication, a boundary that is coarser than the
textbook wants — is not automatically a 2. Ask what enforces it and what it buys.
Duplication chosen on purpose, documented, and kept from drifting by a test is a
5 on `coupling`, not a violation of DRY.

### coupling

How far does a change ripple, and can you know that before you make it?

- **1** — `UserService` imports `BillingController`, which imports `UserService`.
  A single Stripe webhook field change touches nine files across four modules. A
  `utils/index.ts` that 140 files import and that itself imports from six feature
  modules, so everything transitively depends on everything.
- **3** — Modules talk through explicit interfaces. A couple of leaks — one
  feature reaching into another's `internal/`. A typical field change touches two
  or three files.
- **5** — Blast radius is knowable from the import list, and the import list is
  short. Cross-module traffic goes through a small named contract — a typed event,
  a repository interface, one client per boundary. You can delete a feature by
  deleting its directory and removing one registration line. The coupling that
  remains is deliberate and has a comment saying why.

### cohesion

Does everything in this unit belong here, and is everything that belongs here in it?

- **1** — `helpers.ts`, 900 lines: date formatting, a Stripe client, a slug regex,
  and a React hook. Or the anemic version — `models/`, `services/`, `controllers/`
  where one feature is smeared across all three and nothing about invoicing lives
  next to anything else about invoicing.
- **3** — Feature folders exist and most of a feature lives in one. A few
  stragglers sit in a global `lib/` because there was no obvious home.
- **5** — A module is exactly one concept and its name says which. The file list
  reads like a table of contents for that concept. Ask a newcomer "where does
  invoicing live" and they point at one directory and are right. Nothing is in
  there for want of a better home.

### boundary-integrity

Is the boundary real, or is it a suggestion?

- **1** — The frontend imports the ORM model directly and renders whatever fields
  it has. A "service" boundary that every team bypasses by writing raw SQL against
  the other service's tables, because it was faster than asking for an endpoint.
- **3** — The boundary exists and is mostly respected: there is a
  `billing/index.ts` that re-exports the four things other modules are meant to
  use, and most call sites import from it. Two do not, both added in the same
  rushed week, and nothing failed. The rule lives in a CONTRIBUTING paragraph and
  in whoever happens to review the PR, so the count of violations only goes up.
- **5** — Crossing the boundary the wrong way fails the build. Package export maps,
  module visibility, a lint rule with a named and reviewed allowlist, separate
  database roles per service with grants that make the wrong query impossible.
  DTOs at the edge, domain types inside, and the mapping between them lives in one
  file you can read in a sitting. The few sanctioned crossings each have a recorded
  reason.

### dependency-direction

Which way do the arrows point, and can you prove it?

- **1** — Domain logic imports the HTTP framework and the ORM. `core/` imports
  `web/`. A cycle between two packages that the bundler resolves by luck and
  ordering.
- **3** — Mostly inward-pointing: `domain/` imports nothing from `web/`, and the
  two places it needed the database take a repository interface injected at
  construction. One leak remains — `domain/invoice.ts` imports the ORM's `Decimal`
  type for convenience, so the domain does not compile without the ORM in scope.
  Nobody can tell you the cycle count, because nothing counts it.
- **5** — Dependencies point one way and there is a test or lint rule that fails
  when they do not. The innermost layer compiles with no framework in scope at all.
  I/O is injected at the edge, so the domain runs in a unit test with no container,
  no network and no clock. Cycles are zero, and that fact is checked in CI rather
  than believed.

### data-ownership

Who is allowed to write this, and does anything stop everyone else?

- **1** — Three services write the `orders` table. Nobody knows which is
  authoritative. A nightly job exists to "fix" rows, and its existence is treated
  as normal.
- **3** — One writer per table by convention. Some cross-service reads straight
  against tables, which quietly makes the schema a public API.
- **5** — Every table, collection and topic has exactly one writing owner, enforced
  by grants rather than agreement. Readers go through a published view or an API.
  Denormalized copies are explicitly labelled caches, with a stated staleness bound
  and a rebuild path that someone has actually run.

### ubiquitous-language

Does one concept have one name, everywhere?

- **1** — `Account`, `Org`, `Workspace`, `Team` and `Tenant` are the same thing in
  five files. The database says `customer`, the API says `account`, the UI says
  "workspace", and the analytics event says `org_id`. Every conversation starts
  with a translation.
- **3** — One name per concept inside the code: it is `Workspace` in the types,
  `workspace_id` in the columns and `workspace` in the API. The UI calls it a Team,
  the pricing page calls it an Organization, and the support macro says Account —
  so every conversation with a customer needs a mental translation, and the
  glossary that would fix it does not exist because inside the code nothing hurts.
- **5** — One word per concept, end to end: column name, type name, API field, UI
  label, analytics event, support macro. Where two concepts genuinely differ, the
  names differ sharply — not `User` versus `UserModel`. The glossary exists, and
  the code is its proof rather than its aspiration.

### contract-stability

Can callers depend on this without watching your commits?

- **1** — The public API changes shape with no version and no deprecation. A
  webhook payload silently gains a required field. Clients break on your deploy and
  find out from their users.
- **3** — Endpoints live under `/v1`, there is a CHANGELOG that gets a line most
  times, and the team's habit is to add fields rather than rename them. The habit
  is held in three people's heads: there is no schema, no generated client and no
  test that fails on a break, so the last widening of a response field was caught
  in review by luck and the one before it was caught by a customer.
- **5** — Contracts are additive by default. Breaking changes are versioned and
  dual-served for a stated window, with a dashboard showing how many callers remain
  on the old version and a date when it goes away. The contract is expressed in
  something machine-checkable — a schema, generated types, consumer contract
  tests — and CI fails on an unintended break before a human is involved.

### testability

Does the shape of the code make the test obvious?

- **1** — Testing one pure function requires booting Postgres, Redis and a browser.
  The suite takes 40 minutes and fails randomly often enough that a red build means
  nothing. Time, randomness and ids are read from globals, so nothing is
  deterministic.
- **3** — Pure logic has unit tests, the seams have integration tests, and one
  suite takes eleven minutes against a Dockerised Postgres. Everyone tolerates it,
  which means nobody runs it locally and CI is where you find out. Time and ids
  come from a `now()` helper that tests can stub, but only about half of them
  bother, so a handful of tests fail in the last week of the month.
- **5** — Dependencies are injected, the clock and id generator are substitutable,
  and every boundary has a real seam so a test can stand in for the other side. The
  fast suite runs in seconds on save; exactly one slow suite exercises the real
  seams once. Flake rate is measured and treated as a defect, not as weather.

### failure-modes

What happens when the thing you depend on is down or slow?

- **1** — One upstream timeout takes the whole app down, because the call has no
  timeout and the pool exhausts. Retries with no backoff, no jitter and no cap turn
  a blip into a self-inflicted DDoS. `catch {}` swallowing errors. Non-idempotent
  writes that double-charge on retry.
- **3** — The HTTP client has a 10-second default timeout and three retries, set
  once and applied everywhere. One breaker exists, on the payment provider, added
  after the incident that required it. What the user sees when retries run out is
  whatever that call site happened to do — a 500 in two places, an empty list in a
  third — because nobody has ever decided, only handled.
- **5** — Every external call has a timeout, a bounded retry with jitter, and a
  defined behaviour when retries are exhausted — and that behaviour is a product
  decision written down, not a stack trace. Writes are idempotent with keys.
  Degradation happens in stated tiers: read-only, cached, queued. The failure paths
  are exercised — by tests, by fault injection, or by a game day — not assumed.

### observability

Can you answer a question about one request in production without redeploying?

- **1** — `console.log` and hope. No request id. You find out about outages from
  customers on Twitter.
- **3** — Structured logs, an error tracker, dashboards for the obvious metrics.
  Correlating a request across services is possible with effort and grep.
- **5** — "What happened to this user's request at 14:02" is a two-minute question.
  One correlation id spans every hop and appears in every log line, trace and error
  report. Traces are sampled with tail-based retention so the errors are always
  kept. The metrics are the ones tied to the user-visible SLO, not a wall of CPU
  graphs. Alerts fire on symptoms, are actionable, and each links to a runbook that
  has been used.

### migration-debt

How many half-finished transitions is this system carrying?

- **1** — Two auth systems, both live, both required. A v2 API serving 8% of
  traffic with no owner and no plan. A `legacy/` directory nobody dares delete
  because nobody can prove what calls it. Feature flags from three years ago still
  branching in hot paths.
- **3** — The schema migrations are ordered, versioned and all applied. The
  migrations that are not schema changes are the problem: the move off the old
  jobs table is at "about 90%", the `legacy_price_cents` column is still written
  by one path, and both have been in that state for six months. Nobody can list
  the remaining callers without a grep they invent on the spot.
- **5** — Every in-flight migration has a name, an owner, a percentage complete, a
  written finish-or-kill date, and a mechanical way to list the remaining callers.
  The old path is deleted the week the last caller moves. There is no permanent
  "both ways work" state, because that state is understood to be the most expensive
  one to live in.

## What counts as evidence

- **File and line ranges.** `services/orders/order_service.ts:210-390`. Required
  for any structural claim.
- **Counts, with the command that produced them.** "billing imports identity in 34
  places, identity imports billing in 6 — cycle", followed by the exact `rg`
  pipeline. Coupling claims are counted, never felt.
- **Git history.** `git log --since=180.days --format= --name-only | sort | uniq -c
  | sort -rn` for churn hotspots; co-change pairs for hidden coupling; `git log -S`
  for when a pattern entered.
- **A real incident, postmortem, or on-call page.** The strongest evidence that
  exists for a `failure-modes` or `observability` finding.
- **Configuration.** The CI file line that does or does not enforce the rule, the
  lint config, the `exports` map, the database grant, the Terraform resource.
- **Runtime artefacts.** A log line, a trace, a query plan, a p99 from a dashboard.
- **Ownership.** `CODEOWNERS` lines, or the absence of one for a unit that has none.

Not evidence: "this violates clean architecture", "microservices would be better",
"this should be a monorepo", a layer diagram you drew from imagination, or a
pattern name used as an argument. Naming a pattern is not the same as naming a cost.

Every `must` finding must name a cost that has already been paid: a commit that was
harder than it should have been, an incident, a bug class, an onboarding
complaint, a number from the change graph. Architecture findings without a
demonstrated cost are preferences, and they are why architecture reviews get
ignored.

## What the four perspectives hunt for here

### Skeptic → `delete`

Kill the architecture astronaut. This lens attracts more unfounded findings than
any other, because "this could be cleaner" is always true and almost never
actionable.

Delete a finding when:

- It names a pattern instead of a pain. "Not hexagonal" is not a finding. "Adding
  a second payment provider required editing 14 files in 5 modules, and here they
  are" is.
- The fix costs more over the next year than the problem does. Say so in the `why`
  with both numbers, even if they are estimates.
- It is five restatements of one boundary problem. Keep the boundary finding.
- It proposes a rewrite. Rewrites are not findings; they are a different project,
  and proposing one inside a review is how a review gets shelved.
- It is speculative scaling work with no traffic to justify it. "This won't scale"
  needs a number and a date.
- It grades a module by its worst file rather than its structure.

You also audit the top of the scale, which nobody else looks at. Every finding
scored 5 must name a mechanism and the file it lives in. A 5 justified by "follows
clean architecture", "well-factored" or "the team is disciplined about this" is a 3
in flattering words — `delete` it and say in the `why` that the score was unearned,
so Empath can re-grade it honestly.

### Builder → `edit`

Every finding names the first commit. Not the end state — the first commit, the one
that could land tomorrow.

Edit until the finding contains: the extraction or the boundary to introduce, the
file and symbol it starts from, what stays working during and after, and how the
old path is retired.

"Decouple orders from billing" is not a finding. "Extract `PricingCalculator` from
`OrderService` (`order_service.ts:210-390`) behind an injected interface; keep
`OrderService.calculatePrice` delegating for one release so no caller changes; then
delete it once the 6 call sites move" is.

Decompose every `l` and `xl` finding into a first step that ships alone and leaves
the codebase strictly better even if the remaining steps never happen. If it cannot
be decomposed that way, the finding is a project and should be labelled one.

Keep to your op. `edit` is prose and evidence: title, detail, recommendation,
evidence paths. `score`, `severity`, `confidence`, `effort` and `status` are
`change` fields and they belong to Empath. Decomposing a finding therefore lands as
an `add` for the first step plus a `change` on the remainder — emit both, with a
`why` on each. Do not shrink an `xl` into an `s` inside an `edit`: a finding that
quietly changes size between passes is invisible to the thrash detector, which is
the only thing watching for a loop that is rewriting rather than converging.

### Dreamer → `add`

You read across modules, which is the only place these findings exist.

- **The missing concept.** Three modules each hand-rolled a retry-with-backoff and
  a dead-letter table. The thing that wants to exist is a job queue, and no
  single-module review will ever say so.
- **The wrong seam.** The split is by technology — controllers, services, models —
  when the real fault line is by lifecycle, by tenant, or by rate of change. Look
  at the co-change table: it tells you where the seams actually are.
- **The boundary that should not exist.** A service whose only caller is one other
  service, with no independent deploy, scale or failure story. The boundary is
  paying network and serialization costs for nothing.
- **The unnamed subsystem.** Something important is happening across six files and
  has no name, so nobody can talk about it or own it. Naming it is the finding.
- **The shape the system is heading toward.** This is going multi-region, or
  multi-tenant, or self-hosted, and nothing is region-aware, tenant-scoped or
  configurable. Say which decision becomes irreversible soonest.
- **The good structure worth propagating.** One module got its boundary right.
  That is a template, and saying so is an `add`.

### Empath → `change`

Architecture is experienced by people. You re-score and re-rank by who pays.

- **Who maintains this, and how do they feel opening it?** The module everyone
  routes around is a higher-priority finding than the elegant one with a small
  flaw.
- **Where do new hires get stuck?** Time-to-first-PR is an architecture metric. A
  module that takes two weeks to understand is a `must`, not a `note`.
- **Where do the 3am pages come from?** Failure-mode and observability findings on
  the paging path outrank everything on a path that has never woken anyone.
- **Who else consumes this?** The client integrator reading your API docs, the data
  team querying your tables, the support engineer trying to answer a customer.
  Contract and naming findings should be scored from their side, not yours.
- **What is the fear cost?** Code people are afraid to change stops changing, and
  the product stops moving. Fear is a real, rankable consequence — score it.

## Pass discipline

- **Pass 1 — inventory and counts.** Enumerate modules, subsystems and boundaries.
  Run the import-pair and churn commands and attach the numbers. Grade coarse.
- **Pass 2 — verify.** Open the files behind the worst scores. Confirm the cycles
  are real cycles and not a type-only import. Expect `delete` and `edit` to
  dominate; a pass 2 that is still mostly `add` means pass 1 under-enumerated.
- **Pass 3+ — systemic.** Collapse repeated findings into the two or three
  structural decisions that cause them, re-rank by who pays, and name the one
  change that would make the most other findings unnecessary.

Every unit needs at least one finding or it counts as ungraded and blocks `stop`.
For a module that is genuinely well-built, write the finding anyway at score 4 or 5,
severity `note`, naming the specific structural decision that makes it good — those
are the templates the rest of the system should copy.
