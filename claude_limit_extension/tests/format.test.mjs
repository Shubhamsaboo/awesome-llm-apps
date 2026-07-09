import { test } from "node:test";
import assert from "node:assert/strict";

import {
  formatPercent,
  accentFor,
  badgePercent,
  untilReset,
  sinceEpoch,
} from "../src/lib/format.js";

test("formatPercent rounds and handles nulls", () => {
  assert.equal(formatPercent(0), "0%");
  assert.equal(formatPercent(36.4), "36%");
  assert.equal(formatPercent(36.6), "37%");
  assert.equal(formatPercent(100), "100%");
  assert.equal(formatPercent(null), "—");
  assert.equal(formatPercent(undefined), "—");
  assert.equal(formatPercent(NaN), "—");
});

test("accentFor picks severity by threshold", () => {
  assert.equal(accentFor(null), "#9A928A"); // mist
  assert.equal(accentFor(0), "#CC785C");    // orange
  assert.equal(accentFor(69.9), "#CC785C"); // orange (just under 70)
  assert.equal(accentFor(70), "#E0A050");   // amber (inclusive)
  assert.equal(accentFor(89.9), "#E0A050"); // amber (just under 90)
  assert.equal(accentFor(90), "#C24040");   // red (inclusive)
  assert.equal(accentFor(100), "#C24040");  // red
});

test("badgePercent modes pick the right window", () => {
  const usage = {
    five_hour: { utilization: 40 },
    seven_day: { utilization: 60 },
    seven_day_opus: { utilization: 85 },
    seven_day_sonnet: { utilization: 20 },
  };
  assert.equal(badgePercent(usage, "highest"), 85);
  assert.equal(badgePercent(usage, "session"), 40);
  assert.equal(badgePercent(usage, "weekly"), 85);
});

test("badgePercent returns null when nothing usable", () => {
  assert.equal(badgePercent(null, "highest"), null);
  assert.equal(badgePercent({}, "highest"), null);
  assert.equal(badgePercent({ five_hour: null }, "session"), null);
});

test("badgePercent unknown mode falls back to highest", () => {
  const usage = {
    five_hour: { utilization: 30 },
    seven_day: { utilization: 90 },
  };
  assert.equal(badgePercent(usage, "does-not-exist"), 90);
});

test("untilReset formats future durations", () => {
  // Add a 500ms cushion so the ms drift between constructing the target and
  // reading Date.now() inside untilReset doesn't round a minute down.
  const CUSHION = 500;
  const in90m = new Date(Date.now() + 90 * 60_000 + CUSHION).toISOString();
  assert.equal(untilReset(in90m), "1h 30m");

  const in42m = new Date(Date.now() + 42 * 60_000 + CUSHION).toISOString();
  assert.equal(untilReset(in42m), "42m");

  const in3d = new Date(Date.now() + 3 * 86400_000 + 6 * 3600_000 + CUSHION).toISOString();
  assert.equal(untilReset(in3d), "3d 6h");

  const in18s = new Date(Date.now() + 18_500).toISOString();
  assert.equal(untilReset(in18s), "18s");
});

test("untilReset returns 'now' for past times and null for junk", () => {
  const past = new Date(Date.now() - 1000).toISOString();
  assert.equal(untilReset(past), "now");
  assert.equal(untilReset("not a date"), null);
  assert.equal(untilReset(null), null);
});

test("sinceEpoch renders relative times", () => {
  const now = Date.now();
  assert.equal(sinceEpoch(now - 5_000), "just now");
  assert.equal(sinceEpoch(now - 3 * 60_000), "3m ago");
  assert.equal(sinceEpoch(now - 2 * 3600_000), "2h ago");
  assert.equal(sinceEpoch(now - 5 * 86400_000), "5d ago");
  assert.equal(sinceEpoch(0), "never".slice(0, 5)); // guarded fallback
});
