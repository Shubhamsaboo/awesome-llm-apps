// Talks to claude.ai's internal endpoints on behalf of the currently-logged-in
// browser session. All requests use `credentials: "include"` so the browser
// automatically attaches the sessionKey cookie the user set when they signed in.
//
// If the user isn't logged in, /api/organizations returns 401 and we surface
// LOGGED_OUT so the popup can prompt them to open claude.ai.

const BASE = "https://claude.ai";

/**
 * @typedef {Object} UsageWindow
 * @property {number} utilization  // 0..100
 * @property {string} resets_at    // ISO 8601 UTC
 */

/**
 * @typedef {Object} UsageResponse
 * @property {UsageWindow|null} five_hour
 * @property {UsageWindow|null} seven_day
 * @property {UsageWindow|null} seven_day_opus
 * @property {UsageWindow|null} seven_day_sonnet
 * @property {Object|null} extra_usage
 */

/**
 * @typedef {Object} AccountInfo
 * @property {string} email
 * @property {string} plan
 * @property {string} orgId
 */

/**
 * @typedef {Object} Snapshot
 * @property {UsageResponse} usage
 * @property {AccountInfo} account
 * @property {number} fetchedAtEpochMs
 */

export class ApiError extends Error {
  /** @param {"LOGGED_OUT"|"NETWORK"|"HTTP"|"NO_ORG"} kind */
  constructor(kind, message, cause) {
    super(message);
    this.kind = kind;
    this.cause = cause;
  }
}

async function getJson(path) {
  let res;
  try {
    res = await fetch(BASE + path, {
      method: "GET",
      credentials: "include",
      headers: { "Accept": "application/json" },
    });
  } catch (e) {
    throw new ApiError("NETWORK", `Network error on ${path}: ${e.message}`, e);
  }
  if (res.status === 401 || res.status === 403) {
    throw new ApiError("LOGGED_OUT", `Not signed in to claude.ai (HTTP ${res.status})`);
  }
  if (!res.ok) {
    throw new ApiError("HTTP", `HTTP ${res.status} on ${path}`);
  }
  return res.json();
}

/**
 * Reads the whole snapshot in the fewest possible round-trips.
 * @returns {Promise<Snapshot>}
 */
export async function fetchSnapshot() {
  const orgs = await getJson("/api/organizations");
  const org = pickPrimaryOrg(orgs);
  if (!org) throw new ApiError("NO_ORG", "No organizations on this account");

  const [usage, overage, account] = await Promise.all([
    getJson(`/api/organizations/${org.uuid}/usage`).catch(handleOptional),
    getJson(`/api/organizations/${org.uuid}/overage_spend_limit`).catch(handleOptional),
    getJson(`/api/account`).catch(handleOptional),
  ]);

  const merged = mergeExtraUsage(usage ?? {}, overage);
  return {
    usage: merged,
    account: {
      email: account?.email ?? "",
      plan: account?.plan ?? org?.capabilities ?? "",
      orgId: org.uuid,
    },
    fetchedAtEpochMs: Date.now(),
  };
}

function pickPrimaryOrg(orgs) {
  if (!Array.isArray(orgs) || orgs.length === 0) return null;
  // Prefer a "claude_pro" / "claude_max" / "claude_team" org over the free one.
  const scored = orgs.map((o) => ({
    o,
    score: (o.capabilities || []).reduce(
      (s, c) => s + (c.includes("max") ? 3 : c.includes("pro") ? 2 : c.includes("team") ? 2 : 0),
      0,
    ),
  }));
  scored.sort((a, b) => b.score - a.score);
  return scored[0].o;
}

function mergeExtraUsage(usage, overage) {
  // Some accounts return extra_usage inside /usage, others in /overage_spend_limit.
  // Normalise so callers see one shape.
  const extra = usage.extra_usage
    ?? (overage
      ? {
          is_enabled: overage.is_enabled ?? false,
          monthly_limit: overage.monthly_limit_usd ?? overage.monthly_limit ?? null,
          used_credits: overage.used_credits_usd ?? overage.used_credits ?? null,
          utilization: overage.utilization ?? null,
        }
      : null);
  return { ...usage, extra_usage: extra };
}

function handleOptional(err) {
  if (err instanceof ApiError && err.kind === "LOGGED_OUT") throw err;
  return null; // treat other misses as "endpoint missing on this plan"
}
