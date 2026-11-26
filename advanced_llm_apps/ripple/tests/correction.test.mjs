import test from "node:test";
import assert from "node:assert/strict";
import vm from "node:vm";
import { readFileSync } from "node:fs";
const { matches } = vm.runInNewContext(
  readFileSync(new URL("../extension/correction.js", import.meta.url), "utf8") +
    "\nrippleCorrection;",
);
test("accepts only local horizontal-space normalization around a correction", () => {
  const base = "Keep  this. Remove me. Keep that.";
  assert.ok(matches(base, "Remove me.", "", "Keep  this. Keep that."));
  assert.ok(matches(base, "Remove me.", "", "Keep  this.\u00a0Keep that."));
  assert.ok(
    matches(
      base,
      "Remove me.",
      "New wording.",
      "Keep  this. New wording. Keep that.",
    ),
  );
  for (const actual of [
    "Keep this. Keep that.",
    "Keep  this.Keep that.",
    "Keep  this. Change that.",
    "Keep  this.\nKeep that.",
  ])
    assert.equal(matches(base, "Remove me.", "", actual), false, actual);
});
test("does not accept missing paragraph boundaries, wrong replacement, or ambiguous quotes", () => {
  assert.equal(
    matches("Before.\nRemove.\nAfter.", "Remove.", "", "Before.\nAfter."),
    false,
  );
  assert.equal(
    matches(
      "Before. Replace. After.",
      "Replace.",
      "Expected.",
      "Before. Wrong. After.",
    ),
    false,
  );
  assert.equal(matches("Same. Same.", "Same.", "", "Same."), false);
});
test("matches the exact smart-deletion behavior captured from the real Google Doc", () => {
  const quote =
    "Participants will not travel to a venue because the live workshop is entirely remote.";
  const before =
    "points during planning.\n\n" +
    quote +
    " The operations team should answer logistical questions.";
  const actual =
    "points during planning.\n\nThe operations team should answer logistical questions.";
  assert.ok(matches(before, quote, "", actual));
  assert.equal(matches(before, quote, "", actual.replace("\n\n", "\n")), false);
  assert.equal(
    matches(before, quote, "", actual.replace("should", "must")),
    false,
  );
  assert.ok(matches(quote + " Next sentence.", quote, "", "Next sentence."));
  assert.ok(
    matches(
      "Earlier. " + quote + "\nNext paragraph.",
      quote,
      "",
      "Earlier.\nNext paragraph.",
    ),
  );
});
