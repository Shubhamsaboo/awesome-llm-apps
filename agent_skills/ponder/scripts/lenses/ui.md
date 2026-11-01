---
name: ui
unit: screen
enumerate: |
  A unit is one thing a person can be looking at. Not one file, not one
  component, not one route — one thing a person can be looking at, with no
  way to tell from inside it that another version of it exists.

  That means a route is usually several units. The invoices list with
  invoices, the invoices list with none, the invoices list filtered to none,
  the invoices list still loading, and the invoices list that failed to load
  are five units. A shallow pass grades one of them and calls the screen
  done. Do not do that.

  Enumeration is the phase that decides the run. Every later phase grades
  what this one found, so a screen you never enumerate is never graded and
  never shows up as missing — it leaves the denominator instead of failing
  the numerator. Coverage 1.0 over the wrong set is the exact failure this
  lens exists to prevent, and it is indistinguishable from a good result
  unless the inventory was honest.

  Work in five sweeps, in this order: 1, 1b, 2, 3, 4. Sweep 1b is the sweep
  that decides whether coverage means anything, and it is not a fallback for
  exotic stacks. It is where the screens no glob declares live: routes that
  middleware hides or redirects into, screens the app switches with a state
  variable, and hand-rolled step, tab and wizard state, which is a second
  route table nobody wrote down. On a real Next.js app a route glob returns
  thirty screens and the five sweeps return 228. Skip 1b and you report 41
  screens for an app that has 200, and every grade after that is confident
  and wrong.

  Calibrate every line before you trust it. An enumerator that returns
  nothing is a broken command until you have proved this stack does not use
  that shape. On a real Next.js app the loading/error line returns four
  files and none of them is a loading.tsx, because the app has none anywhere
  — that zero is a finding about the app. A zero you have not explained is
  an inventory you have not finished, and it is the cheapest way to fake
  coverage.

  Sweep 1 — routes. Find the router first, then enumerate mechanically.
  rg --files -g '**/app/**/page.{tsx,jsx,ts,js,mdx}'
  rg --files -g '**/app/**/{layout,template,loading,error}.{tsx,jsx,ts,js}' \
    -g '**/app/**/{global-error,not-found,default}.{tsx,jsx,ts,js}'
  rg --files -g '**/pages/**/*.{tsx,jsx,ts,js,mdx}' -g '!**/pages/api/**' \
    -g '!**/pages/_app.*' -g '!**/pages/_document.*'
  rg --files -g '**/app/routes/**/*.{tsx,jsx,ts,js,mdx}'
  rg --files -g '**/src/routes/**/+{page,layout,error}*.svelte'
  rg --files -g '**/pages/**/*.vue' -g '**/views/**/*.vue'
  rg --files -g '**/app/**/*.{tsx,jsx,ts,js}' -g '!**/app/**/_*'
  rg -n -A2 "path:\s*['\"]" -g '*.{ts,tsx,js,jsx,vue}' .
  rg -n '<Route\b|createBrowserRouter|createRoutesFromElements|loadChildren' .
  rg -n 'RouterModule\.for(Root|Child)|@NgModule' -g '*.ts' .
  rg -n 'struct \w+: View\b|NavigationStack|NavigationSplitView|TabView' \
    -g '*.swift' .
  rg -n ': UI(View|TableView|CollectionView)Controller' -g '*.swift' .
  rg -n 'composable\("|NavHost\(|: (Activity|AppCompatActivity|Fragment)\b' \
    -g '*.kt' .
  rg --files -g '**/app/views/**/*.erb' -g '**/*.html.heex' \
    -g '**/resources/views/**/*.blade.php' -g '**/templates/**/*.html'

  The path: line carries -A2 because on its own it is mostly noise: it matches
  cookie options, filesystem paths and config keys, and on a real Next.js
  app it returns five hits of which zero are routes. Read the two lines
  after each hit. It is a route table only when a component, element,
  Component, loadChildren or children sits next to it; anything else is a
  false positive and you say so rather than listing it as a screen.

  The bare app/** line is there for the file-name-as-route stacks — Expo
  Router and anything else where app/settings.tsx *is* the route. They have
  no page.tsx anywhere, so the two page.tsx lines above return nothing and
  an unwary pass concludes the app has no screens at all. If app/_layout.tsx
  exists you are in that world: trust the bare app/** line, ignore the rest.

  Sweep 1b — where routes are hidden or absent. Run all three parts.

  Middleware. In App Router, screens are hidden by middleware, never by the
  route tree. A route file that exists and is unreachable is still a unit —
  and so is whatever the redirect lands on.
  rg --files -g '**/middleware.{ts,js}' -g '**/src/middleware.{ts,js}'
  rg -n 'redirect\(|rewrite\(|NextResponse\.(redirect|rewrite)' \
    -g '**/middleware.*' -g '**/proxy.*' .
  rg -n 'getServerSideProps|\+page\.server|loader\b|beforeEnter|canActivate' .

  No router at all. Design prototypes, static sites, and apps that switch
  screens with a state variable have no router file, so every line in sweep
  1 returns zero and the repo reads as screenless. It is not. This is not an
  exotic case: a directory of standalone entry HTML files plus a src/ of
  screens-*.jsx modules is a normal shape for prototype and demo work, and
  sweep 1 finds none of it.
  rg --files -g '**/*.{html,htm}' -g '!**/node_modules/**' -g '!**/dist/**' \
    -g '!**/build/**' -g '!**/coverage/**'
  rg --files -g '**/*[Ss]creen*.{tsx,jsx,ts,js,vue,svelte}' \
    -g '**/{screens,views,Screens,Views}/**/*.{tsx,jsx,ts,js,vue,svelte}'
  rg -n -i 'setScreen\(|setView\(|activeScreen|currentScreen|currentStep' .
  rg -n -i 'location\.hash|history\.pushState|hashchange|wizard|<step' .

  Stories. Where a Storybook exists it is the only place in the repo where
  empty, loading and error variants are already written down by name. Every
  story is a unit candidate; a component with a Default story and nothing
  else is a component whose variants nobody ever drew.
  rg --files -g '**/*.stories.{tsx,jsx,ts,js,mjs,svelte,mdx}'
  rg -n -o 'export const [A-Z][A-Za-z0-9]*' -g '**/*.stories.*' .

  Sweep 2 — surfaces that are not routes. Modals, sheets, drawers,
  popovers, command palettes, toasts, context menus, alerts, onboarding
  tours, print views.
  rg -n -i 'Dialog|Modal|Sheet|Drawer|Popover|Command(Palette|Menu)' \
    -g '*.{tsx,jsx,vue,svelte,swift,kt}' .
  rg -n -i 'Toast|Snackbar|ActionSheet|BottomSheet|AlertDialog' \
    -g '*.{tsx,jsx,vue,svelte,swift,kt}' .
  rg -n '\.sheet\(|\.fullScreenCover\(|\.popover\(' -g '*.swift' .
  rg -n '\.alert\(|\.confirmationDialog\(' -g '*.swift' .

  Sweep 3 — state variants. Every screen from sweeps 1, 1b and 2 owes an
  empty, a loading, an error and a permission-denied unit. Each one is a
  separate unit with its own id and its own findings — a screen is not
  graded until its variants are graded, and grading only the populated state
  is the single most common way a UI pass ships half a review.
  rg -n -i 'isLoading|isPending|isFetching|Suspense|Skeleton|aria-busy' \
    -g '*.{tsx,jsx,ts,js,vue,svelte,astro,html}' -g '!**/node_modules/**' .
  rg -n -i 'length === 0|isEmpty|no results|nothing here|empty' \
    -g '*.{tsx,jsx,ts,js,vue,svelte,astro,html}' -g '!**/node_modules/**' .
  rg -n -i 'isError|ErrorBoundary|onError|\.catch\(|<Error|error\.tsx' \
    -g '*.{tsx,jsx,ts,js,vue,svelte,astro,html}' -g '!**/node_modules/**' .
  rg -n -i 'hasPermission|\bcan\(|requireRole|isAdmin|useFlag|featureFlag' .
  rg -n -i 'paywall|entitlement|plan ===|tier ===|quota|seatLimit' .

  Run the gate lines as a pair and read them as one answer. On a real app
  the role line returns zero and the plan line returns twenty-eight, because
  that product gates by plan and not by role. Either line alone would have
  told you the app has no gates, which was false both times.

  Sweep 4 — close the loop. Diff the route list against the navigation, and
  the navigation against the route list. Anything in the nav that is not in
  the list was missed. Anything in the list that nothing links to is an
  orphan, and an orphan is a finding.
  rg -n -i "href=|to=[\"']|router\.push|navigate\(|NavLink|<Link" \
    -g '*.{tsx,jsx,ts,js,vue,svelte,astro,html}' -g '!**/node_modules/**' .

  Then run the app and walk it. A unit you never rendered is graded at
  confidence below 0.5, and you say so in the finding.

  Stop enumerating when every sweep is closed - every router entry is
  listed, every screen sweep 1b rescued from a router-less or
  middleware-hidden stack is listed, every presented surface from sweep 2 is
  listed, every screen from sweeps 1, 1b and 2 has its empty, loading, error
  and permission-denied variants each standing as its own unit or explicitly
  ruled out as impossible with a reason, every enumerator that returned zero
  has an explanation, and the nav diff in sweep 4 comes back empty in both
  directions. Until then coverage is a number about a list you have not
  finished writing.
dimensions: [information-hierarchy, empty-states, loading-states, error-states, motion, affordance-clarity, density, responsive-behaviour, accessibility, copy-tone, consistency, delight]
scale:
  1: broken - blocked, misled or excluded
  2: bad - works if you already know it
  3: acceptable - competent, nothing chosen
  4: good - designed for this screen
  5: exemplary - a taste decision you can name in one sentence
---

# The UI lens

You are grading an interface the way someone who cares about interfaces grades one.
Not an audit. Not a lint run. A judgment, per screen, per dimension, with the
evidence to back it and the specific change that would move the score.

## What a unit is

One thing a person can be looking at, in one state, with one job in front of them.

The operational test: **if the content differs, the primary action differs, or the
user's emotional context differs, it is a separate unit.** `/settings/billing`
showing three paid invoices and `/settings/billing` showing "no invoices yet" are
two different screens wearing the same URL. The second one is where products are
lost, and it is almost always the one nobody designed.

Give units stable dotted ids and hang variants off the base:

```
screen.settings.billing                  the loaded, populated state
screen.settings.billing.empty            never had an invoice
screen.settings.billing.empty-filtered   filtered to zero results
screen.settings.billing.loading          initial load
screen.settings.billing.error-network    fetch failed
screen.settings.billing.denied           user lacks billing permission
```

Set `meta.route` to the real path and `meta.variant` to the variant name. `path`
points at the file that owns the state — for a variant, that is often a different
file than the base (`app/settings/billing/loading.tsx`, not `page.tsx`), and
pointing at the right one is half the value of the finding.

## Enumerating exhaustively

The front matter has the commands. This is the judgment that goes with them.

### Routers, by stack

**Next.js App Router.** Every `page.*` is a unit. So is every `loading.*`,
`error.*`, `global-error.*`, `not-found.*` and `default.*` — those files *are*
state variants that someone already made a file for, which means they exist and
have almost certainly never been looked at. Route groups `(marketing)` do not
create URL segments but do create separate layouts, so a screen can inherit a
completely different chrome than you assume. Parallel routes `@modal` and
intercepting routes `(.)photo/[id]` produce screens that only exist on a soft
navigation — the same URL renders a modal from inside the feed and a full page on
reload. Both are units. Dynamic segments `[id]` and `[...slug]` are one unit
unless the rendered result genuinely differs by param (a `[type]` segment that
switches between three layouts is three units).

The route tree is not the whole answer, because App Router hides screens in
`middleware.ts`, which is invisible to every glob in sweep 1. Read it first. A
middleware that redirects unauthenticated traffic to `/login` and authenticated
traffic away from `/login` has just defined two units nothing in `app/` declares:
the logged-out landing on a protected deep link, and the bounce a logged-in user
gets from a bookmarked signup URL. Any `page.tsx` that middleware makes
unreachable is still a unit — an unreachable screen scores 1 and is a finding on
its own.

Read the absence of files too. An App Router repo with 41 `page.tsx` files, one
`not-found.tsx`, three `layout.tsx` and **no `loading.tsx` and no `error.tsx`
anywhere** is a real and common shape. That is not four units to grade; it is 41
screens with no designed loading state and no designed error state, which is one
systemic finding plus 82 variant units that all resolve to the framework default.
Enumerate them anyway — a variant that falls through to a default is still a thing
a person looks at, and "the default" is what you are grading.

**Next.js Pages Router.** Everything under `pages/` except `_app`, `_document`,
`_error` (which is a unit — grade it), and `api/`. Check `getServerSideProps` for
redirects that hide a screen behind a condition.

**Remix / React Router v7.** Flat route files use dots for nesting:
`app/routes/settings.billing.invoices.$id.tsx`. Every exported `ErrorBoundary` is
an error-state unit; a route with no `ErrorBoundary` inherits the nearest parent's,
which is itself worth a finding if that parent is the root.

**SvelteKit.** `+page.svelte` per route, `+error.svelte` per error boundary,
`+layout.svelte` for chrome. `+page.server.ts` redirects hide screens.

**Expo Router / React Native.** Directory-shaped like Next.js, named nothing like
it: the *file name* is the route, so screens are `app/settings.tsx`,
`app/(tabs)/index.tsx`, `app/+not-found.tsx`. There is no `page.tsx` anywhere, so
the Next.js lines in sweep 1 return zero and the app looks screenless. Use the
`-g '**/app/**/*.{tsx,jsx,ts,js}' -g '!**/app/**/_*'` line instead. `_layout.tsx`
files declare stacks, tabs and native modals — a screen presented with
`presentation: 'modal'` looks and behaves differently enough to be its own unit.
Also enumerate the OS surfaces the app owns: permission prompts, share sheets,
push notification presentation, and the app's own splash/launch state.

**Explicit route tables.** react-router `createBrowserRouter`, vue-router's
`routes` array, Angular's `RouterModule.forRoot`. Read the whole array, including
lazy `loadChildren` / `component: () => import(...)` entries, which is where
half-finished sections hide. Watch for catch-all `path: '*'` — that is your 404
and it is a unit.

**SwiftUI.** Every `struct X: View` is a candidate, but most are components.
Units are the things pushed onto a `NavigationStack`, presented by `.sheet`,
`.fullScreenCover`, `.popover`, `.alert`, `.confirmationDialog`, or hung off a
`TabView` tab. Grep for the presentation modifiers, not the struct declarations —
presentation is what makes something a screen.

**UIKit.** `UIViewController` subclasses plus every scene in every `.storyboard`
and `.xib`. Interface files hide screens from a code grep, so enumerate them
directly — `find . -name '*.storyboard' -o -name '*.xib'` — and then read the
scenes inside, since one storyboard commonly holds a dozen:
`rg -n '<viewController ' --glob '*.storyboard' .`.

**Android.** `Activity` and `Fragment` subclasses; in Compose, every
`composable("route")` registered in a `NavHost`, plus `ModalBottomSheet` and
`AlertDialog` call sites.

**Server-rendered.** Rails `app/views/**/*.erb`, Django `templates/`, Laravel
`resources/views/**/*.blade.php`, Phoenix `*.html.heex`. Partials are components;
templates rendered by a controller action are screens. Read `routes.rb` /
`urls.py` / `web.php` / `router.ex` as the authoritative list and map each route
to its template.

**No router at all.** Design prototypes, static sites, internal demos and
kiosk-style apps often have no router of any kind, and every line in sweep 1
returns zero on them. Do not conclude the repo has no screens — check the shape
before you conclude anything. A prototype repo of 52 standalone `.html` files, a
`prototypes/<name>/entries/*.html` set of entry points, and a `src/screens-*.jsx`
module per screen is an ordinary shape for this kind of work, and sweep 1 finds
none of it while sweep 1b finds all of it.

Three shapes to look for, and how each carries units:

- **Entry-point HTML.** One file per screen. Each file is a unit, but so is each
  distinct state inside it, since a prototype usually fakes states with a query
  param or a toggle rather than with data.
- **Screen modules.** `screens-dashboard.jsx`, `views/Settings.vue`,
  `Screens/Onboarding.swift`. The exported components in these are units even
  though nothing routes to them by URL.
- **Hand-rolled view state.** `setScreen('review')`, `currentStep`, a `switch` on
  a string, `location.hash`. Read the switch: **every arm of it is a unit**, and
  the arms are the closest thing to a route table this app has. Grep the state
  setter for its full set of argument values and you have the inventory.

The screen that only exists as a story counts too. Where a Storybook exists, read
it as an inventory rather than as a test fixture — it is the one place in most
repos where `Empty`, `Loading` and `Error` variants are already named and drawn,
which makes it both a source of units and the fastest way to see which screens
have no variants written down at all.

### The screens that hide

This is the section that separates a real pass from a shallow one. Every item
here is a unit somebody forgot to design.

- **Empty states.** Two kinds, and they are different units: *never had data*
  (needs onboarding: what this is, why it's empty, how to fill it) and *filtered
  to nothing* (needs an escape: clear the filter). A single "No results" string
  serving both is a finding on its own.
- **Loading states.** Initial load, refetch-with-stale-data, pagination/infinite
  scroll append, optimistic pending, and the >5-second case. The last one almost
  never exists.
- **Error states.** Network offline, request timeout, 401 expired session, 403
  permission denied, 404 object missing, 422 validation, 500 server, and the
  client-side render crash. Each has a different correct response. A single red
  box for all eight is a finding on every screen that shares it.
- **Permission and plan gates.** Admin-only screens, role-gated tabs, plan-gated
  features, feature-flagged screens. Find them with the gate greps in sweep 3,
  then find what a user without the entitlement actually sees. If the answer is a
  blank page or a raw 403, that is a unit and it scores 1.
- **Auth boundary screens.** Signed out, session expired mid-action, email not
  verified, invite acceptance, SSO handoff, magic-link landing, password reset,
  2FA challenge, account locked. These are almost never in the design file.
- **Onboarding-only screens.** Anything that renders once and never again. You
  will not see them by clicking around a seeded dev account. Find them in code.
- **Data-shape extremes.** One item vs ten thousand. A 90-character workspace
  name. A user with no avatar. A number with no upper bound in a fixed-width
  column. Zero, one, and many are three different layouts and the middle one is
  usually the only one drawn.
- **States that need seeded data.** Trial expiring in 2 days. Payment failed.
  Storage 97% full. Import partially succeeded. If you cannot reach it by
  clicking, seed it or read the code — do not skip it.
- **Non-app surfaces the product owns.** Transactional emails, the OG/share card,
  the print stylesheet, the exported PDF, the CSV a user opens in Excel, the
  marketing pages if they are in this repo.

### Coverage is the whole point

`coverage < 1.0` blocks `stop` and has no override. That makes under-enumerating
the only available cheat: a unit you never listed is a unit you never had to
grade. Do not take it. Enumerate wide on pass 1 even if it costs you a pass —
a broad inventory with coarse grades converges; a narrow inventory with fine
grades is a lie that terminates early.

If a unit turns out not to exist, `unit-delete` it with a `why`. That is honest.
Never omitting it in the first place is not.

**The variant rule, stated as a rule because it is the one that gets skipped.**
For every screen you list, its empty, loading, error and permission-denied states
are each a separate unit, with their own id, their own findings and their own
score. Not a dimension of the base screen — a unit. `empty-states`,
`loading-states` and `error-states` are dimensions *of each variant unit*, which
is how a loading state gets graded on hierarchy, motion and copy-tone rather than
only on being present.

A screen is not graded until its variants are graded. The three legal outcomes for
each variant are:

1. It exists — grade it.
2. It does not exist but the state is reachable — grade what the user actually
   sees, which is the framework default, a blank region, or a crash. This is where
   most of the 1s in a real UI report come from.
3. It is genuinely impossible — `unit-delete` it and put the mechanism in the
   `why`. "This list is seeded at account creation and cannot be empty" is a
   reason. "Unlikely" is not.

If your unit count is roughly equal to your route count, you did option 4, which
is not on the list.

## The twelve dimensions

Each finding is one judgment about one `(unit, dimension)` pair. Score the pair,
not the screen. A screen can be a 5 on hierarchy and a 1 on error states, and
saying so is more useful than an average.

### The 5 rung, before the specifics

Across all twelve dimensions, the rungs mean:

- **1 — broken.** A user is blocked, misled, or excluded.
- **2 — bad.** It works if you already know how it works.
- **3 — acceptable.** Competent. Nothing wrong. Nothing chosen either. This is
  what a component library plus a careful engineer produces by default.
- **4 — good.** Someone thought about this screen specifically.
- **5 — exemplary.** Someone with taste made a decision here — and you can name
  the decision, say what the obvious alternative was, and say why this is better.

**5 is not "follows best practices."** Best practices get you a 3. A 5 has a point
of view: a choice that a careful, opinionated person made on purpose, that a
generic implementation would not have arrived at, and that makes the screen feel
like it was built by someone rather than assembled. Motion that means something.
Copy that sounds like a person who knows the product. A default that is right
often enough that nobody changes it. If you cannot name the decision in one
sentence, it is not a 5.

The mechanical test, and it is not optional: a score of 5 is only valid if the
finding's `detail` contains all three of these sentences.

1. **The decision.** "The skeleton is generated from the same layout primitive as
   the resolved row, so the two cannot drift apart."
2. **The obvious alternative** — what a competent engineer with the same component
   library and no strong opinion would have shipped instead. "Three grey bars at a
   guessed height."
3. **Why this one is better, in terms of what the user experiences.** "Nothing
   moves when data lands, so you can start reading before it finishes loading."

If any of the three is missing, the score is a 4 and you write the 4. A 5 without a
nameable decision is not praise, it is a reviewer who ran out of vocabulary — and
it is worse than a wrong 2, because it teaches the team that taste is unfalsifiable
and therefore not worth arguing about.

Two failure modes to watch in yourself, in both directions:

- **Competence read as taste.** AA contrast, a focus ring, a skeleton, a
  `prefers-reduced-motion` guard and an 8pt grid are all a 3. They are the floor.
  A screen can do every one of them and still be a 3 on every dimension, because
  nobody chose anything — a library did.
- **Taste read as noise.** A deliberate deviation from the design system, an
  unusual density, an animation that is slower than the guideline, a button that
  is not where the convention puts it: check whether it is load-bearing before you
  mark it down. If the screen earns it and does it consistently, that is a 5 on
  `consistency`, not a violation. Ask what the alternative would have cost.

Be honest that most screens are 3s. Inflating everything to 4 destroys the signal
that makes the report worth reading.

### information-hierarchy

Does the screen answer "what is this and what do I do" in under a second, by
visual weight rather than by reading?

- **1** — A settings page: fourteen controls in one flat column, identical weight,
  no grouping, "Delete account" styled exactly like "Theme". Nothing is first
  because everything is.
- **3** — Grouped into titled cards, one filled primary button top-right. You can
  find things. Three elements still compete for first glance: a promo banner, the
  tab bar, and the page title.
- **5** — On an invoice detail, the amount and status are the largest things on the
  page and everything else is demoted to a metadata rail in one step-down of size,
  weight *and* colour. The type scale is chosen, not inherited from `h1`/`h2`
  defaults. The destructive action is present but recessive until you go looking
  for it. One glance tells you whether you owe money.

### empty-states

Does the absence of content do a job, or is it a hole?

- **1** — `No invoices` in 14px grey, centred, on an otherwise blank panel.
- **3** — Icon, "No invoices yet", a sentence explaining invoices appear after the
  first billing cycle. No action.
- **5** — The two empties are distinct and correct. *Never had any* explains the
  cause, sets a specific expectation ("Your first invoice will be generated on
  1 March"), and offers the one action that resolves it. *Filtered to none* says
  what filter is hiding what, and the primary action is "Clear filters". The
  never-had-any state hints at the shape of the filled state, so the user learns
  what they are working toward instead of staring at a void.

### loading-states

Does waiting feel like the system is working, and does content arrive without
throwing the layout around?

- **1** — Full-page spinner replaces all content on every navigation; when data
  lands the layout jumps; a slow request spins forever with no escalation.
- **3** — Skeletons roughly match the content shape, action buttons show an inline
  spinner and go disabled, and nothing white-flashes on navigation. The skeleton
  renders on the first frame, so a 40ms cached response flashes it and is gone —
  and a 12-second export shows the same skeleton at second 1 and second 12, with
  nothing to tell you which one you are in.
- **5** — Skeletons are the exact geometry of the resolved content, so nothing
  moves at all when data arrives. No loader renders before ~300ms, so fast
  responses never flash. Actions that almost always succeed are optimistic, with a
  quiet, non-destructive rollback. Content streams in a stable order — header and
  first rows before the rest. Past five seconds the UI says something true
  ("Still working — this export is large") instead of spinning in silence.

### error-states

When something fails, does the user know what happened, what it cost them, and
what to do?

- **1** — `Error: Request failed with status code 500` in a red box. No retry. The
  form the user just spent four minutes filling in is gone.
- **3** — One shared `<ErrorState>` on every failure: "Something went wrong. Please
  try again." with a Retry button that refetches, inside an error boundary that
  keeps the sidebar and the rest of the app alive. It is readable and it does not
  white-screen. It says that same sentence for an expired session, a 403 and a 500,
  so a user who cannot fix any of them retries three times against a wall — and the
  boundary remounts the subtree, which takes the half-filled form with it.
- **5** — The message is specific to the failure class: offline says offline and
  retries itself when connectivity returns; permission names the permission and who
  can grant it; validation points at the field; server failure offers retry plus a
  copyable incident id. **Nothing the user typed is ever lost.** Retry happens in
  place, not by resetting the page. The tone neither grovels nor blames — it states
  the situation and the next move.

### motion

Does movement carry meaning, or is it decoration and delay?

- **1** — No motion at all, so state changes are teleports; or motion that fights
  you — a 600ms modal fade, every transition on the same generic ease, list items
  re-animating on every keystroke of a filter.
- **3** — One `transition: all 150ms ease` in the shared styles, applied to hover,
  open and close alike, and a `prefers-reduced-motion` block that switches every
  duration to `0.01ms`. Nothing jars. The modal, the tooltip and the row hover all
  move at the same speed with the same curve, so movement tells you that something
  happened but never which thing or where it came from.
- **5** — Motion has a vocabulary and it is used consistently: things enter from
  where they came from (the popover grows out of the button that opened it, the
  detail expands from the row you clicked), durations form a scale with jobs
  attached (~120ms feedback, ~220ms surfaces, ~400ms only when spatial context
  actually changes), and transitions are interruptible and reversible mid-flight
  rather than locking you out until they finish. Reduced-motion gets a designed
  crossfade, not motion deleted.

### affordance-clarity

Can you tell what is interactive, and what will happen, before you touch it?

- **1** — A `div` with an `onClick`: no cursor change, no hover, no focus ring, not
  reachable by keyboard. Text styled like a link that is not one. A card that is
  clickable except for the 40px that is not.
- **3** — Everything clickable is a real `<button>` or `<a>` from the component
  library, with a hover state and the library's default focus ring. Disabled
  controls sit at 50% opacity and do nothing. The row in the table is clickable
  and looks exactly like the rows in the read-only table two screens over, and a
  user who cannot work out why the Invite button is dead has nowhere on the screen
  to find out.
- **5** — Interactivity is legible without moving the pointer. Hit targets exceed
  their visual bounds. Disabled controls say *why* they are disabled instead of
  dead-ending. Primary, secondary and destructive are distinguishable by shape and
  position, not by colour alone. Keyboard focus order matches visual order, and the
  focus ring is designed for the surface it lands on rather than being the browser
  default over a dark card.

### density

Is the amount of information per screen chosen for the task?

- **1** — A data table with 24px cell padding so six rows fit on a laptop; or the
  inverse, 11px text with 2px gutters and nothing breathing.
- **3** — One spacing scale used everywhere: 24px card padding, 16px between
  fields, 12px row padding, on an 8pt grid with no strays. The four-field
  workspace-name form and the 400-row audit log are spaced identically, so the
  form floats in a half-empty card and the log fits fourteen rows on a laptop.
  Nothing is inconsistent and nothing is wrong enough to point at, which is
  exactly why nobody has.
- **5** — Density is a decision per surface. The scan-400-rows view is dense, with
  tight leading and tabular figures so columns align. The make-one-decision view is
  generous. The same component adapts — a compact row in a sidebar preview, a roomy
  one in the full page — instead of one size shipped everywhere. Whitespace is used
  to group, not to fill.

### responsive-behaviour

Does the layout change what it *is*, or only how wide it is?

- **1** — The whole page scrolls horizontally at 375px. A table with a 1024px
  min-width. A modal taller than the viewport with no internal scroll, so the
  confirm button is unreachable.
- **3** — The sidebar collapses to a hamburger under 768px, the three-column card
  grid becomes one column, and the wide table scrolls inside its own `overflow-x`
  container. Nothing overlaps, nothing is cut off, nothing is unreachable. The
  mobile screen is the desktop screen stacked: same order, same components, same
  filter panel that now costs four taps to open because it was a sidebar.
- **5** — Structure changes with the context: a three-pane desktop layout becomes a
  stack with a real back affordance on mobile. Touch targets grow on coarse
  pointers. Every hover-only affordance has a tap equivalent. It survives 200%
  browser zoom, the iOS keyboard eating half the viewport, and a 1440px window —
  where the reading column stays at a readable measure instead of stretching to
  the edges.

### accessibility

Does it work for someone not using it the way you are?

- **1** — Icon-only buttons with no accessible name. A modal that neither traps
  focus nor returns it on close. Placeholder-as-label at 2.4:1 contrast.
- **3** — axe reports zero violations here. Landmarks, `alt` text and `<label for>`
  are all present, contrast passes AA, the focus ring is visible, and the dialog
  traps focus and returns it on close. Nobody has driven the screen with a keyboard
  or a screen reader, so tab order runs sidebar → footer → main content because
  that is the DOM order, the toast that confirms the save is never announced, and
  the three icon buttons in the row read as "button, button, button".
- **5** — You ran it. Keyboard only, start to finish, and again with a screen
  reader on. Async results announce through a live region. Form errors are
  associated to their fields and focus moves to the first one. The loading state
  announces. Icon button names read well in sequence, not just individually.
  Reduced-motion, high-contrast and forced-colors are all handled. The evidence is
  a transcript of that run, not an automated score.

### copy-tone

Do the words do work that no visual can?

- **1** — "An error occurred." "Are you sure?" "Item." "Submit." Title Case and
  sentence case mixed on one screen.
- **3** — Sentence case throughout, one voice, and every button is the verb from
  its heading — "Create project" under "Create project". Nothing is wrong and
  nothing is memorable. The confirm dialog still says "This action cannot be
  undone" without naming the action; the empty state still says "No items yet"
  about invoices; the toast still says "Saved" when the user wants to know what
  was saved and where it went.
- **5** — The confirm dialog names the exact consequence with real numbers —
  "Delete 3 workspaces and the 412 documents inside them. This can't be undone." —
  and the button says "Delete workspaces", not "OK". Empty-state copy sounds like a
  person who knows the product and respects the reader. Nothing hedges, nothing
  apologises twice, no filler. Microcopy answers the question the user was about to
  ask, one beat before they ask it.

### consistency

Does the same thing look and behave the same way everywhere — and where it does
not, was that a choice?

- **1** — Three button heights, four greys that are nearly the same grey, two date
  formats, and a modal implemented twice by two people.
- **3** — The screen is assembled from the shared library — same `Button`, same
  `Card`, same `Input` — with three or four local escapes where the design wanted
  something the system does not have: an `mt-[13px]`, a one-off `#F7F7F8` border,
  a card with its own radius. Each escape is defensible on its own, none of them
  went back into the system, and the next screen will invent its own four.
- **5** — Consistency where it aids recognition, deliberate deviation where the
  screen earns it — and the deviation is absorbed back into the system as a named
  variant rather than left as a local hack. No raw hex, no magic pixel values. The
  same concept carries the same name in the UI, the code and the analytics event.

### delight

Is there anything here that a careful person made on purpose?

- **1** — Nothing memorable; it is a form. Or worse, delight bolted on: confetti
  for a routine save.
- **3** — Pleasant touches, all of them bought rather than made: the checkmark
  animation that ships with the toast library, a purchased empty-state
  illustration, a subtle gradient on the primary button. Take any one of them out
  and nothing about the product is lost, because none of them knows anything about
  what this screen is for.
- **5** — One decision on this screen that no component library would have handed
  you: the drag handle that shows the row's final resting position instead of a
  ghost line; the search field that keeps your last query as a dimmed suggestion;
  a haptic used exactly once, at the moment it means something; a transition that
  makes a hierarchy legible for the first time. The test: crop the logo out of a
  screenshot — could someone still tell this product from its competitor?

## What counts as evidence

Every finding carries `evidence: []`. An entry is one of:

- **A file and line range.** `src/routes/settings/billing.tsx:88-94`. Required for
  any claim about code. A file with no line range is weak evidence; a line range
  you did not open is not evidence.
- **A route or unit path.** `/settings/billing?status=paid` — the exact URL, with
  the query and the state needed to reproduce it.
- **A screenshot path.** `.ponder/<slug>/shots/screen.settings.billing.empty.png`.
  Name the file after the unit id. A screenshot with no note about what in it you
  are pointing at is decoration.
- **A measured value, quoted exactly.** `#8A8A8E on #F2F2F7 = 2.9:1 (AA needs 4.5)`.
  `Modal fade: 600ms, transitions.ts:12`. `CLS 0.31 on first paint`.
- **A transcript.** For keyboard and screen-reader findings, the sequence you
  pressed and what was announced.
- **A token or component name.** `Button size="sm" is 28px here and 32px in
  ui/button.tsx:44`.

Not evidence: "feels cluttered", "this is bad UX", "best practice says", a link to
an article, an appeal to another product's screenshot without saying what the
mechanism is.

**Rules.** Every `must` needs at least one anchor. If you could not open the file
or render the screen, set `confidence` below 0.5 and say in `detail` what you were
unable to see — a hypothesis flagged as one is useful; a hypothesis dressed as a
conclusion poisons the report.

## What the four perspectives hunt for here

The four perspectives are the four delta operations. In a UI review they have
sharply different jobs.

### Skeptic → `delete`

Your job is killing personal taste dressed as principle. In UI work that is the
dominant failure mode, because everyone has opinions about interfaces and almost
none of them are load-bearing.

Delete a finding when:

- It cites an adjective instead of a measurement. "Feels cramped" with no spacing
  value, no comparison, no task that got harder.
- You would not write the same sentence about a screen you happen to like. If the
  rule only fires on screens you find ugly, it is taste, not a rule.
- The user harm is theoretical. Name the person and what it costs them, or drop it.
- It is one of five restatements of a single systemic problem. Keep the systemic
  one, delete the four echoes, and say in the `why` which one absorbed them.
- It grades a variant nobody actually rendered and the code does not support the
  claim.
- It prescribes a solution ("should use a design system") without evidence that the
  problem exists or that the system does.
- It is a style preference in a codebase that made the opposite choice
  consistently and deliberately. Consistency with a defensible local convention
  beats your preferred convention.

Do not delete a finding merely because it is uncomfortable, hard, or about
something the team is attached to.

You also own the honesty of the top of the scale, and nobody else is looking at
it. Walk every finding scored 5 and check it names a decision, an alternative and
a reason. A 5 that says the screen "follows the design system", "handles all
states" or "feels polished" is describing a 3 in warm words: `delete` it and say
in the `why` that the score was unearned, so Empath can re-grade it honestly. Do
the same for a wall of 4s — if a pass produced no 3s, the pass was flattering the
product, and that is a defect in the review rather than a fact about the UI.

### Builder → `edit`

Your job is that every finding names the actual change. A finding a reader cannot
act on without another meeting is not finished.

Edit a finding until it contains:

- **Where.** File and line, or the component and the prop.
- **What.** The concrete change: the token, the value, the copy string, the
  component to swap, the state to add.
- **What "done" looks like.** One sentence a reviewer could check against.

"Improve the hierarchy on billing" is not a finding. "Promote the amount to
32px/600 and demote the metadata into a right-hand rail; the destructive action
moves out of the card header into the overflow menu — `billing.tsx:41-77`" is.

Split every `xl` finding nobody will ever do. Emit the `s` version that ships this
week and stands on its own as a new finding, and leave the remainder behind it.
That split is an `add` plus a `change`, not an `edit` — say so in each `why`, and
do not disguise it as a rewrite of the original, because a finding that quietly
changes size between passes is invisible to the thrash detector.

Keep to your op. `edit` is prose and evidence: title, detail, recommendation,
evidence paths. `score`, `severity`, `confidence`, `effort` and `status` are
`change` fields and they belong to Empath. When you notice that an estimate is
wrong — and you will, because effort estimates that are all `m` mean nobody
estimated — emit a `change` for it as its own delta with its own `why`, rather
than smuggling a re-grade inside an `edit` where nothing can see it.

### Dreamer → `add`

Your job is what no single-screen review can see. You are the only perspective
that reads the finding set as a set. Hunt for:

- **Motion vocabulary drift.** Three durations doing the same job across four
  screens, or one duration doing four different jobs. That is one finding about the
  system, not four about screens.
- **The missing system-level concept.** Five screens each invented their own way
  to say "saved" because there is no toast primitive. Nobody reviewing one screen
  can see that.
- **Rhythm.** Every screen opens with a page title and a filled button on the
  right. The product has exactly one shape, and moving through it feels like
  nothing is happening. Or the opposite: no two screens share a spine.
- **The screen that does not exist.** The code can produce "your trial ended", and
  there is no design for it. Enumerate the states the *system* can be in and diff
  against the states the *interface* has.
- **A wrong frame.** These three tabs are pretending to be one page and should be
  one page. This wizard is a form. This modal is a route and is unlinkable, so
  nobody can send it to a colleague.
- **The variant read across the product.** You are the only perspective holding
  every `.empty`, `.loading` and `.error` unit at once. Read them as three
  columns. Forty screens sharing one skeleton that matches none of them is one
  finding, not forty. Forty error variants all rendering the same
  "Something went wrong" is one finding about a missing error taxonomy. And a
  column with holes in it — nineteen screens with an empty state and twenty-one
  with nothing — tells you which half of the product was designed and which half
  was implemented.
- **The good thing worth propagating.** A 5 on one screen that should be the
  pattern on nine others is an `add`, not a compliment.

And then the one output that matters more than any of them: **the through-line.**
Before you finish, name what is wrong with this interface *as a whole*, in one
paragraph, as a single `add` titled `Through-line`. Not a summary of the findings
— a judgement no per-screen grade can reach, saying what kind of problem this
product has.

It has to be specific to this product and it has to be arguable. "The design is
inconsistent" is not a through-line; it is what you write when you have not found
one. "This product is not badly designed, it is under-decided — every serious
finding is a seam where the paint stops" is: it names the shape of the problem,
explains why the 3s outnumber the 1s, and tells the team that the thing to fix is
a decision rather than a screen.

Write it on every pass from 3 onward, and rewrite it rather than restating it when
the finding set moves under you — a through-line that survives a pass unchanged is
either right or unexamined, and the `why` has to say which. Write it even when the
findings are mostly small: a product with no through-line is itself the finding,
and saying that plainly is worth more than a fifteenth motion-drift `add`.

### Empath → `change`

Your job is who is on this screen, in what state, and whether the design meets
them. You emit `change` — re-scoring and re-ranking, because ranking is where
empathy becomes actionable. You are the only perspective that may move `score`,
`severity`, `confidence` and `effort`; the other three hand you the argument and
you make the call.

Rank by **reach × stakes × recoverability**, and write the three factors into the
`why` so the re-rank can be argued with:

- **Reach.** How many people see this unit, how often. The empty state of the
  first screen after signup has 100% reach exactly once, which is more than the
  dashboard's daily 40%.
- **Stakes.** What the person is feeling when they arrive. Browsing, blocked,
  billed, or afraid they destroyed a colleague's work.
- **Recoverability.** What one wrong move costs. A misread setting costs a minute;
  a misread delete confirmation costs an afternoon and a relationship.

Ask, per unit:

- **Who is here?** The billing screen's real audience is someone who got a
  failed-payment email at 11pm and is worried they lost their data. Is the copy
  calibrated to that person, or to a happy user browsing invoices?
- **First time or five hundredth?** A screen tuned for the expert is hostile on day
  one; a screen tuned for onboarding is condescending by week two. Say which one
  this is tuned for and whether that is right.
- **How did they get here?** Someone who clicked into this screen from the nav
  arrives with context. Someone dropped here by a notification, a shared link or a
  redirect after login does not, and that is usually most of the traffic. A screen
  graded only from the inside of the app is graded for the minority.
- **Who is excluded?** Low vision, slow network, small phone, non-native reader,
  someone in a shared office who does not want this on screen, someone whose data
  looks nothing like the seed data.
- **Is the ranking honest?** A `could` on a screen 90% of users see every day
  outranks a `must` on an admin screen three people have ever opened. Re-score it
  and say so in the `why`.

## Pass discipline

- **Pass 1 — breadth.** Enumerate everything, including all the variants. Grade
  coarse. Coverage before precision. It is normal for pass 1 to be almost entirely
  `add`; that is the one pass where that is allowed.
- **Pass 2 — depth.** Open the files behind the worst scores. Confirm or retract.
  Expect `delete` and `edit` to dominate. If pass 2 is still mostly `add`, your
  pass 1 enumeration was incomplete — fix that with `unit-add` deltas and say so.
- **Pass 3+ — systemic.** Stop looking at screens and look at the finding set.
  Collapse repeats into system-level findings. Re-rank against real usage. Dreamer
  writes the through-line here. This is where Dreamer and Empath earn their keep,
  and where the report stops being a list and starts being an argument.

Every unit needs at least one finding or it counts as ungraded and blocks `stop`.
For a genuinely good screen, write the finding anyway: score 4 or 5, severity
`note`, and state what is right and why — those findings are how the rest of the
product learns from its best screen.
