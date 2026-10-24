# Team Roster

The routing target set. The agent must pick **exactly one** of these.

Edit this file to match your org — the optimizer reads it as the allowed label
space, and `optimizer/app.py` loads it into the sidebar.

| Team | Owns | Route here when |
|---|---|---|
| `auth-service` | login, session, token refresh, SSO, MFA, RBAC checks | first error is a 401/403, token validation, or the auth callback |
| `backend-infra` | DB, connection pools, caches, queues, service mesh, infra timeouts | pool exhaustion, DB timeout, broker lag, DNS/mesh failures |
| `frontend` | web UI, rendering, client-side state, bundling | blank/incorrect render with no server-side error |
| `data-platform` | ETL, warehouse, event pipelines, dbt models, reporting freshness | stale/missing data, pipeline lag, wrong aggregates |
| `devops` | CI/CD, build, deploy, env config, secrets, IaC | broken build, failed deploy, env-only config drift |
| `security` | vuln reports, dependency CVEs, exposure, audit findings | anything with an exploit path or leaked credential |
| `payments` | checkout, billing, invoices, payment-provider integrations | failures in the charge/refund path or provider webhooks |

## Routing precedence

When two teams plausibly own it, resolve in this order:

1. **`security`** wins over everything if there is an exploit path or credential exposure.
2. **First error in the trace** wins over the surface symptom. A blank dashboard
   caused by a 500 from the API routes to the API's team, not `frontend`.
3. **`devops`** owns it only when the defect is in config/pipeline itself, not
   when a deploy merely *exposed* an application bug.
4. If still tied, route to the team owning the code path where the first
   non-retryable error appears.

## Anti-patterns

- Do not route to `devops` just because the issue started after a deploy.
- Do not route to `frontend` for a rendering failure whose root cause is an
  upstream API error.
- Do not route to `backend-infra` for a slow query owned by a product team —
  that is the query owner's bug unless the pool/infra itself is at fault.
