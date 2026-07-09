import { test } from "node:test";
import assert from "node:assert/strict";

import { pickPrimaryOrg, mergeExtraUsage, ApiError } from "../src/lib/api.js";

test("pickPrimaryOrg picks Max over Pro over Free", () => {
  const orgs = [
    { uuid: "free-1", capabilities: ["claude_free"] },
    { uuid: "pro-1", capabilities: ["claude_pro"] },
    { uuid: "max-1", capabilities: ["claude_max_5x"] },
  ];
  assert.equal(pickPrimaryOrg(orgs).uuid, "max-1");
});

test("pickPrimaryOrg tolerates missing capabilities", () => {
  assert.equal(pickPrimaryOrg([{ uuid: "a" }]).uuid, "a");
  assert.equal(pickPrimaryOrg([]), null);
  assert.equal(pickPrimaryOrg(null), null);
  assert.equal(pickPrimaryOrg(undefined), null);
});

test("pickPrimaryOrg picks team over free when no pro/max", () => {
  const orgs = [
    { uuid: "free-1", capabilities: ["claude_free"] },
    { uuid: "team-1", capabilities: ["claude_team"] },
  ];
  assert.equal(pickPrimaryOrg(orgs).uuid, "team-1");
});

test("mergeExtraUsage prefers usage.extra_usage when present", () => {
  const usage = {
    five_hour: { utilization: 10 },
    extra_usage: { is_enabled: true, utilization: 42 },
  };
  const overage = { is_enabled: false };
  const merged = mergeExtraUsage(usage, overage);
  assert.deepEqual(merged.extra_usage, { is_enabled: true, utilization: 42 });
});

test("mergeExtraUsage falls back to overage_spend_limit shape", () => {
  const usage = { five_hour: { utilization: 10 } };
  const overage = {
    is_enabled: true,
    monthly_limit_usd: 40,
    used_credits_usd: 12.5,
    utilization: 31.25,
  };
  const merged = mergeExtraUsage(usage, overage);
  assert.deepEqual(merged.extra_usage, {
    is_enabled: true,
    monthly_limit: 40,
    used_credits: 12.5,
    utilization: 31.25,
  });
});

test("mergeExtraUsage sets null when neither source has data", () => {
  const merged = mergeExtraUsage({ five_hour: {} }, null);
  assert.equal(merged.extra_usage, null);
});

test("ApiError carries the kind tag", () => {
  const err = new ApiError("LOGGED_OUT", "nope");
  assert.equal(err.kind, "LOGGED_OUT");
  assert.equal(err.message, "nope");
  assert.ok(err instanceof Error);
});
