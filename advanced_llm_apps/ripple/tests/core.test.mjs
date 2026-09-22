import test from "node:test";
import assert from "node:assert/strict";
import { diff, reconcile, sentences, uniqueSpan } from "../extension/core.js";
const before =
  "Workshop plan\nAttendance is online. Everyone can attend from anywhere.\nWe will send a Zoom link.\nLast year was online.";
const after = before.replace(
  "Attendance is online.",
  "Attendance is in person only.",
);
test("isolates a changed sentence", () => {
  const d = diff(before, after);
  assert.equal(d.before, "Attendance is online.");
  assert.equal(d.after, "Attendance is in person only.");
  assert.equal(after.slice(d.start, d.end), d.after);
});
test("unchanged document has no diff", () =>
  assert.equal(diff(before, before), null));
test("source undo clears dependencies", () => {
  const sources = reconcile(before, after, []);
  assert.equal(sources.length, 1);
  assert.deepEqual(reconcile(after, before, sources), []);
});
test("fixing a finding does not become a second governing fact", () => {
  const sources = reconcile(before, after, []);
  const fixed = after.replace(
    "Everyone can attend from anywhere.",
    "Everyone must attend at the venue.",
  );
  assert.deepEqual(
    reconcile(after, fixed, sources, [
      { text: "Everyone can attend from anywhere." },
    ]),
    sources,
  );
});
test("successive source edits preserve original before wording", () => {
  const sources = reconcile(before, after, []);
  const changed = after.replace(
    "Attendance is in person only.",
    "Attendance is hybrid.",
  );
  assert.equal(
    reconcile(after, changed, sources)[0].before,
    "Attendance is online.",
  );
  assert.equal(
    reconcile(after, changed, sources)[0].after,
    "Attendance is hybrid.",
  );
});
test("duplicate quotes do not receive guessed locations", () =>
  assert.equal(uniqueSpan("Repeat. Repeat.", "Repeat."), null));
test("paragraph and unicode offsets address exact original text", () => {
  for (const s of sentences(
    "Café workshop.\n\n  Start at 10:00. Bring a laptop.",
  ))
    assert.equal(
      "Café workshop.\n\n  Start at 10:00. Bring a laptop.".slice(
        s.start,
        s.end,
      ),
      s.text,
    );
});
test("insertions and deletion do not invent prior or new facts", () => {
  assert.deepEqual(reconcile("One.", "One.\nNew paragraph.", []), []);
});
test("deleting a tracked source retires it", () => {
  const sources = reconcile(before, after, []);
  assert.deepEqual(
    reconcile(
      after,
      after.replace("Attendance is in person only.", ""),
      sources,
    ),
    [],
  );
});
test("clearing the document retires source changes", () => {
  const sources = reconcile(before, after, []);
  assert.deepEqual(reconcile(after, "", sources), []);
});
test("deleting source and following newline leaves unrelated next sentence intact", () => {
  const original = "Attendance is online.\nJoin from home.";
  const changed = "Attendance is in person only.\nJoin from home.";
  const sources = reconcile(original, changed, []);
  assert.deepEqual(reconcile(changed, "Join from home.", sources), []);
});
test("word insertion and removal retain complete source sentence context", () => {
  assert.equal(
    diff("Attendance is online.", "Attendance is not online.").before,
    "Attendance is online.",
  );
  assert.equal(
    diff("Attendance is not online.", "Attendance is online.").after,
    "Attendance is online.",
  );
});
