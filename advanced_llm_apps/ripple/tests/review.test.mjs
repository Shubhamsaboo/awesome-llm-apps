import test from "node:test";
import assert from "node:assert/strict";
import vm from "node:vm";
import { readFileSync } from "node:fs";
import * as core from "../extension/core.js";

// Run the production content controller with controlled bridge messages and RPC.
const correction = readFileSync(
  new URL("../extension/correction.js", import.meta.url),
  "utf8",
);
const source = readFileSync(
  new URL("../extension/content.js", import.meta.url),
  "utf8",
)
  .replace(
    /await\s+import\(\s*chrome\.runtime\.getURL\(['"]ui\.js['"]\)\s*\)/,
    "testUI",
  )
  .replace(
    /await\s+import\(\s*chrome\.runtime\.getURL\(['"]core\.js['"]\)\s*\)/,
    "testCore",
  );
const original =
  "Attendance is online. Zoom link follows. Join from anywhere. Bring a laptop.";
const edited = original.replace(
  "Attendance is online.",
  "Attendance is in person only.",
);
async function harness({
  deferSuggestions = false,
  baseline = original,
  busyChecks = 0,
} = {}) {
  let actions,
    listener,
    rows = [],
    id = 0,
    releaseSuggestions;
  const events = new Map();
  const timers = new Map(),
    calls = [],
    messages = [],
    states = [],
    resultHistory = [];
  const window = {
    addEventListener(type, fn) {
      if (type === "message") listener = fn;
    },
    postMessage(data) {
      messages.push(data);
    },
  };
  const location = {
    origin: "https://docs.google.com",
    pathname: "/document/d/test/edit",
  };
  const rpc = async (message) => {
    calls.push(message);
    if (message.type === "health") return { ok: true, ready: true };
    if (message.type === "check" && busyChecks-- > 0)
      return { ok: false, retryable: true, error: "Busy" };
    if (message.type === "check")
      return {
        ok: true,
        results: message.input.sentences
          .filter((s) => /Zoom|anywhere/.test(s.text))
          .map((s) => ({ id: s.id, status: "likely_conflict" })),
      };
    if (message.type === "suggest") {
      if (deferSuggestions)
        await new Promise((resolve) => {
          releaseSuggestions = resolve;
        });
      return {
        ok: true,
        suggestions: message.input.passages.map((p) => ({
          id: p.id,
          action: p.text.includes("Zoom") ? "delete" : "replace",
          replacement: p.text.includes("Zoom") ? "" : "Attend in person.",
          reason: "Attendance changed.",
        })),
      };
    }
  };
  const ui = {
    state(s) {
      states.push(s);
    },
    results(r) {
      rows = r;
      resultHistory.push([...r]);
    },
    draw() {},
    close() {},
  };
  await vm.runInNewContext(correction + "\n" + source, {
    window,
    location,
    testCore: core,
    testUI: {
      createUI(a) {
        actions = a;
        return ui;
      },
    },
    chrome: {
      runtime: { sendMessage: rpc, onMessage: { addListener() {} } },
      storage: { local: { get: async () => ({}), set() {} } },
    },
    document: {
      getElementById: () => null,
      querySelector: () => null,
      createElement: () => ({ getContext: () => ({}) }),
      addEventListener(type, fn) {
        events.set(type, fn);
      },
    },
    crypto: { randomUUID: () => String(++id) },
    MutationObserver: class {},
    requestAnimationFrame: queueMicrotask,
    setInterval() {},
    setTimeout(fn, delay) {
      const key = ++id;
      timers.set(key, { fn, delay });
      return key;
    },
    clearTimeout(key) {
      timers.delete(key);
    },
  });
  const flush = async () => {
    for (let i = 0; i < 15; i++) await Promise.resolve();
  };
  const send = (data) =>
    listener({
      source: window,
      origin: location.origin,
      data: { channel: "ripple-docs-v1", ...data },
    });
  const snapshot = (text, tab = "t.0") => send({ type: "snapshot", text, tab });
  const runTimers = async () => {
    for (const [key, timer] of [...timers]) {
      if (timer.delay === 5000) continue;
      timers.delete(key);
      await timer.fn();
    }
    await flush();
  };
  await actions.toggle(true);
  snapshot(baseline);
  snapshot(
    baseline.replace("Attendance is online.", "Attendance is in person only."),
  );
  await runTimers();
  return {
    actions,
    calls,
    messages,
    states,
    resultHistory,
    compositionEnd: () => events.get("compositionend")(),
    rows: () => rows,
    send,
    snapshot,
    runTimers,
    flush,
    releaseSuggestions: async () => {
      releaseSuggestions?.();
      await flush();
    },
    request: () => messages.findLast((m) => m.type === "apply"),
    confirm(request, ok = true) {
      const text = request.baseText.replace(request.quote, request.replacement);
      send({
        type: "apply-result",
        requestId: request.requestId,
        ok,
        text,
        tab: request.tab,
        error: ok ? "" : "Not accepted",
      });
      return text;
    },
    timeout() {
      const [key, timer] = [...timers].find(([, t]) => t.delay === 5000);
      timers.delete(key);
      timer.fn();
    },
  };
}

test("Apply preserves other drafts, removes the resolved finding, and sends no new check or generation", async () => {
  const h = await harness();
  const other = h.rows()[1],
    draft = other.suggestion;
  const checks = h.calls.length,
    history = h.resultHistory.length;
  const first = h.actions.apply(h.rows()[0], "", "delete");
  const text = h.confirm(h.request());
  assert.equal((await first).ok, true);
  h.snapshot(text);
  await h.runTimers();
  assert.equal(h.calls.length, checks);
  assert.equal(h.rows().length, 1);
  assert.equal(h.rows()[0], other);
  assert.equal(h.rows()[0].suggestion, draft);
  assert.ok(
    h.resultHistory.slice(history).every((r) => r.length === 1),
    "remaining results never disappear",
  );
  const second = h.actions.apply(other, "Attend in person.", "replace");
  const final = h.confirm(h.request());
  assert.equal((await second).ok, true);
  h.snapshot(final);
  await h.runTimers();
  assert.equal(h.rows().length, 0);
  assert.equal(h.calls.length, checks);
  assert.equal(h.states.at(-1).label, "All suggestions reviewed");
});
test("expected snapshot arriving before acknowledgement does not restart review", async () => {
  const h = await harness();
  const count = h.calls.length;
  const pending = h.actions.apply(h.rows()[0], "", "delete");
  const request = h.request();
  h.snapshot(request.baseText.replace(request.quote, ""));
  await h.runTimers();
  assert.equal(h.rows().length, 2);
  assert.equal(h.calls.length, count);
  h.confirm(request);
  assert.equal((await pending).ok, true);
  await h.runTimers();
  assert.equal(h.rows().length, 1);
  assert.equal(h.calls.length, count);
});
test("Undo and new manual edits still recheck after an accepted correction", async () => {
  for (const next of [
    edited,
    edited.replace("Bring a laptop.", "Bring a tablet."),
  ]) {
    const h = await harness();
    const pending = h.actions.apply(h.rows()[0], "", "delete");
    h.confirm(h.request());
    await pending;
    const count = h.calls.filter((c) => c.type === "check").length;
    h.snapshot(next);
    await h.runTimers();
    assert.ok(h.calls.filter((c) => c.type === "check").length > count);
  }
});
test("failure retains review, while timeout with changed text triggers normal rechecking", async () => {
  const h = await harness();
  const count = h.calls.length;
  const failed = h.actions.apply(h.rows()[0], "", "delete");
  h.confirm(h.request(), false);
  assert.equal((await failed).ok, false);
  assert.equal(h.rows().length, 2);
  await h.runTimers();
  assert.equal(h.calls.length, count);
  const late = h.actions.apply(h.rows()[0], "", "delete");
  const request = h.request();
  h.snapshot(request.baseText.replace(request.quote, ""));
  h.timeout();
  assert.equal((await late).ok, false);
  await h.runTimers();
  assert.ok(h.calls.length > count);
});
test("concurrent edits, tab switches, and pausing prevent stale confirmation from restoring a review", async () => {
  for (const change of ["edit", "tab", "pause"]) {
    const h = await harness();
    const pending = h.actions.apply(h.rows()[0], "", "delete"),
      request = h.request();
    if (change === "pause") await h.actions.toggle(false);
    else
      h.snapshot(
        edited + " Additional text.",
        change === "tab" ? "t.1" : "t.0",
      );
    h.confirm(request);
    assert.equal((await pending).ok, false, change);
    assert.equal(h.rows().length, 0, change);
  }
});
test("a pending draft for another finding completes after Apply without reviving the removed finding", async () => {
  const h = await harness({ deferSuggestions: true });
  const other = h.rows()[1];
  const pending = h.actions.apply(h.rows()[0], "", "delete");
  h.confirm(h.request());
  await pending;
  await h.releaseSuggestions();
  assert.equal(h.rows().length, 1);
  assert.equal(h.rows()[0], other);
  assert.equal(other.suggestionState, "ready");
  assert.equal(h.calls.filter((c) => c.type === "check").length, 1);
});

test("normalized Docs deletion snapshots and composition events preserve review without a new model request", async () => {
  const h = await harness(),
    count = h.calls.length;
  const pending = h.actions.apply(h.rows()[0], "", "delete"),
    request = h.request();
  const text = request.baseText.replace(request.quote, "").replace("  ", " ");
  h.snapshot(text);
  h.send({
    type: "apply-result",
    requestId: request.requestId,
    ok: true,
    text,
    tab: request.tab,
  });
  assert.equal((await pending).ok, true);
  h.snapshot(text);
  h.compositionEnd();
  await h.runTimers();
  assert.equal(h.calls.length, count);
  assert.equal(h.rows().length, 1);
  const next = h.actions.apply(h.rows()[0], "Attend in person.", "replace");
  assert.equal(h.request().baseText, text, "next Apply uses actual Docs text");
  h.confirm(h.request());
  assert.equal((await next).ok, true);
});

test("paragraph-start smart deletion advances the actual baseline without clearing remaining drafts", async () => {
  const h = await harness({
    baseline:
      "Attendance is online.\nZoom link follows. Join from anywhere. Bring a laptop.",
  });
  const other = h.rows()[1],
    count = h.calls.length;
  const pending = h.actions.apply(h.rows()[0], "", "delete"),
    request = h.request();
  const text = request.baseText.replace("Zoom link follows. ", "");
  h.snapshot(text);
  h.send({
    type: "apply-result",
    requestId: request.requestId,
    ok: true,
    text,
    tab: request.tab,
  });
  assert.equal((await pending).ok, true);
  h.snapshot(text);
  await h.runTimers();
  assert.equal(h.rows()[0], other);
  assert.equal(h.calls.length, count);
});

test("replacement Undo and Redo preserve the original governing source", async () => {
  const h = await harness();
  const row = h.rows().find((r) => r.text.includes("anywhere"));
  const pending = h.actions.apply(row, "Attend in person.");
  const applied = h.confirm(h.request());
  await pending;
  for (const text of [edited, applied, edited]) {
    const start = h.calls.length;
    h.snapshot(text);
    await h.runTimers();
    const checks = h.calls.slice(start).filter((c) => c.type === "check");
    assert.equal(checks.length, 1);
    assert.deepEqual(JSON.parse(JSON.stringify(checks[0].input.source)), {
      before: "Attendance is online.",
      after: "Attendance is in person only.",
    });
  }
});
test("invalid replacement text is rejected before sending an editor operation", async () => {
  const h = await harness();
  for (const text of ["First line.\nSecond line.", "x".repeat(2501)]) {
    const result = await h.actions.apply(h.rows()[1], text);
    assert.equal(result.ok, false);
    assert.match(result.error, /single line.*2,500/);
    assert.equal(h.request(), undefined);
  }
});
test("busy backend automatically rechecks unchanged text and respects Pause", async () => {
  const h = await harness({ busyChecks: 1 });
  assert.equal(h.rows().length, 0);
  await h.runTimers();
  assert.equal(h.rows().length, 2);
  assert.equal(h.calls.filter((c) => c.type === "check").length, 2);
  const paused = await harness({ busyChecks: 1 });
  await paused.actions.toggle(false);
  await paused.runTimers();
  assert.equal(paused.calls.filter((c) => c.type === "check").length, 1);
});
