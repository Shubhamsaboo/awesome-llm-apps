# Examples — Golden Set

Labeled non-prod issues in the two formats you actually receive: Jira/Linear
tickets and Teams channel messages. `optimizer/app.py` loads
`golden_set.json` (the machine-readable twin of this file) as the measurement
set.

**This file is the ground truth.** The optimizer can only get as good as these
labels. Every case here was routed by a human who knew the real owner.

Cases 1–3 are straightforward. Cases 4–8 are the ones a naive agent gets wrong,
and they are why the loop is worth running.

---

## 1. Jira — token refresh fails on staging

> **DEV-4471** · staging
> Login works but users get kicked out after ~15 min. Refresh endpoint returns
> 401. Started after config push at 14:02. No prod impact.

**Team:** `auth-service` · **Severity:** P2
**Why:** First error is a 401 on the refresh path. Config push is the trigger,
not the owner.

---

## 2. Teams — connection pool exhausted in dev

> `#eng-dev-issues` · 09:14
> checkout svc is throwing `pool timeout` in dev, can't get a connection.
> nothing in prod. anyone touching the pool config?

**Team:** `backend-infra` · **Severity:** P2
**Why:** Pool exhaustion is infra-owned regardless of which service surfaces it.

---

## 3. Jira — blank chart, no server errors

> **DEV-4489** · staging
> Analytics dashboard renders an empty chart since yesterday's FE deploy.
> API returns 200 with a valid payload. Console shows a null deref in
> `ChartContainer`.

**Team:** `frontend` · **Severity:** P3
**Why:** Server is healthy, payload is valid, error is client-side. Workaround
exists (reload), so P3.

---

## 4. Teams — blank dashboard, **500 upstream** ⚠️

> `#eng-dev-issues` · 11:41
> dashboard is blank on staging again. FE team already looked, they say the
> `/metrics/rollup` call is 500ing.

**Team:** `data-platform` · **Severity:** P2
**Why:** Same *symptom* as case 3, different owner. The first error is a 500
from the rollup endpoint. Routing on symptom sends this to `frontend` — wrong.
This is the precedence rule "first error in trace beats surface symptom."

---

## 5. Jira — started after a deploy, but not a deploy bug ⚠️

> **DEV-4502** · staging
> Broke right after release 2.31 deployed. Orders with >50 line items now
> throw `IndexOutOfBounds` in the totals calculator. Rollback fixes it.

**Team:** `payments` · **Severity:** P2
**Why:** The deploy *exposed* an application bug; it did not cause it. Routing
to `devops` because "it started after a deploy" is the single most common
mis-route.

---

## 6. Teams — leaked credential in a log ⚠️

> `#eng-dev-issues` · 16:20
> heads up, staging logs are printing the full DB connection string including
> the password on startup. only staging but the creds are shared with the
> read replica.

**Team:** `security` · **Severity:** P2
**Why:** `security` takes precedence over everything when a credential is
exposed, even though the defect looks like a `devops`/logging config issue and
even though it is non-prod.

---

## 7. Jira — CI failure that *is* a pipeline bug

> **DEV-4510** · CI
> All PR builds failing at the integration-test step with
> `could not resolve host: artifacts.internal`. No code changes involved.

**Team:** `devops` · **Severity:** P2
**Why:** The defect is in the pipeline/env itself, not in application code.
Contrast with case 5.

---

## 8. Teams — stale numbers, looks like a UI bug ⚠️

> `#eng-dev-issues` · 08:55
> staging dashboard numbers are 3 days behind. UI looks fine, just old data.

**Team:** `data-platform` · **Severity:** P3
**Why:** Freshness is a pipeline concern. Nothing is broken in the render path.
Degraded with a workaround (query the warehouse directly), so P3.

---

## Coverage notes

The set deliberately includes three symptom-collision pairs, because a routing
rule that fixes one half and breaks the other will show up as a flat score
rather than an improvement:

- **3 vs 4** — identical symptom (blank chart), different first error
- **5 vs 7** — both post-deploy, only one is a pipeline defect
- **6 vs 7** — both look like config/logging, one has an exploit path

When you extend this set, add pairs, not singletons.
