import test from "node:test";
import assert from "node:assert/strict";
import { payload } from "../jev.mjs";
test("Jev payload is classification only and validates quoted text", () => {
  const p = payload({
    source: { before: "Online.", after: "In person." },
    sentences: [{ id: "b0s0", text: "Join us via Zoom.", section: "" }],
  });
  assert.equal(p.model, "jev-latest");
  assert.equal(p.questions.b0s0.type, "choice");
  assert.equal(p.state.change.after, "In person.");
});
test("rejects oversized or malformed inputs before model use", () => {
  assert.throws(() =>
    payload({
      source: { before: "x", after: "y" },
      sentences: [{ id: "invalid", text: "test", section: "" }],
    }),
  );
  assert.throws(() =>
    payload({
      source: { before: "x".repeat(3001), after: "y" },
      sentences: [{ id: "b0s0", text: "test", section: "" }],
    }),
  );
});
test("duplicate sentence IDs cannot overwrite results", () => {
  assert.throws(() =>
    payload({
      source: { before: "x", after: "y" },
      sentences: [
        { id: "b0s0", text: "one", section: "" },
        { id: "b0s0", text: "two", section: "" },
      ],
    }),
  );
});
test("direct TypeSafe transport uses Jev model, Bearer auth, and typed answers", async () => {
  const { evaluate } = await import("../jev.mjs");
  const originalFetch = globalThis.fetch,
    originalKey = process.env.TYPESAFE_API_KEY;
  process.env.TYPESAFE_API_KEY = "synthetic-test-key";
  let calls = 0;
  globalThis.fetch = async (url, options) => {
    calls++;
    assert.equal(url, "https://api.typesafe.ai/v1/systemone");
    assert.equal(options.headers.Authorization, "Bearer synthetic-test-key");
    const body = JSON.parse(options.body);
    assert.equal(body.model, "jev-latest");
    assert.equal(body.questions.b0s0.type, "choice");
    return new Response(
      JSON.stringify({
        answers: {
          b0s0: {
            choice: "likely_conflict",
            probabilities: {
              likely_conflict: 0.95,
              worth_reviewing: 0.04,
              unaffected: 0.01,
            },
          },
        },
      }),
      { status: 200 },
    );
  };
  try {
    const result = await evaluate({
      source: { before: "Online.", after: "In person." },
      sentences: [{ id: "b0s0", text: "Join us via Zoom.", section: "" }],
    });
    assert.equal(calls, 1);
    assert.equal(result.results[0].status, "likely_conflict");
  } finally {
    globalThis.fetch = originalFetch;
    if (originalKey === undefined) delete process.env.TYPESAFE_API_KEY;
    else process.env.TYPESAFE_API_KEY = originalKey;
  }
});

test("failed Jev batches abort siblings and start no remaining work", async () => {
  const { evaluate } = await import("../jev.mjs");
  const originalFetch = globalThis.fetch,
    key = process.env.TYPESAFE_API_KEY;
  process.env.TYPESAFE_API_KEY = "synthetic";
  let calls = 0,
    aborted = false;
  globalThis.fetch = async (_url, { signal }) => {
    calls++;
    if (calls === 1) return new Response("{}", { status: 403 });
    return new Promise((_resolve, reject) =>
      signal.addEventListener(
        "abort",
        () => {
          aborted = true;
          reject(signal.reason);
        },
        { once: true },
      ),
    );
  };
  try {
    await assert.rejects(
      evaluate({
        source: { before: "Online.", after: "In person." },
        sentences: Array.from({ length: 36 }, (_, i) => ({
          id: `b0s${i}`,
          text: `Sentence ${i}.`,
          section: "",
        })),
      }),
      /cannot access/,
    );
    assert.equal(calls, 2);
    assert.equal(aborted, true);
  } finally {
    globalThis.fetch = originalFetch;
    if (key === undefined) delete process.env.TYPESAFE_API_KEY;
    else process.env.TYPESAFE_API_KEY = key;
  }
});
test("a shared deadline and caller cancellation stop all 120-sentence work", async () => {
  const { evaluate } = await import("../jev.mjs");
  const originalFetch = globalThis.fetch,
    key = process.env.TYPESAFE_API_KEY;
  process.env.TYPESAFE_API_KEY = "synthetic";
  const input = {
    source: { before: "Online.", after: "In person." },
    sentences: Array.from({ length: 120 }, (_, i) => ({
      id: `b0s${i}`,
      text: `Sentence ${i}.`,
      section: "",
    })),
  };
  const keepAlive = setInterval(() => {}, 1000);
  try {
    for (const mode of ["deadline", "disconnect"]) {
      let calls = 0,
        aborted = 0;
      const controller = new AbortController();
      globalThis.fetch = async (_url, { signal }) => {
        calls++;
        const result = new Promise((_resolve, reject) =>
          signal.addEventListener(
            "abort",
            () => {
              aborted++;
              reject(signal.reason);
            },
            { once: true },
          ),
        );
        if (mode === "disconnect" && calls === 2)
          queueMicrotask(() => controller.abort(new Error("Disconnected")));
        return result;
      };
      await assert.rejects(
        evaluate(input, { timeoutMs: 30, signal: controller.signal }),
        mode === "deadline" ? { name: "TimeoutError" } : /Disconnected/,
      );
      assert.equal(calls, 2);
      assert.equal(aborted, 2);
    }
  } finally {
    clearInterval(keepAlive);
    globalThis.fetch = originalFetch;
    if (key === undefined) delete process.env.TYPESAFE_API_KEY;
    else process.env.TYPESAFE_API_KEY = key;
  }
});

test("shared deadline also interrupts retry backoff", async () => {
  const { evaluate } = await import("../jev.mjs");
  const originalFetch = globalThis.fetch,
    key = process.env.TYPESAFE_API_KEY;
  process.env.TYPESAFE_API_KEY = "synthetic";
  let calls = 0;
  globalThis.fetch = async () => {
    calls++;
    return new Response("{}", { status: 503 });
  };
  try {
    await assert.rejects(
      evaluate(
        {
          source: { before: "Online.", after: "In person." },
          sentences: [{ id: "b0s0", text: "Join remotely.", section: "" }],
        },
        { timeoutMs: 30 },
      ),
      { name: "TimeoutError" },
    );
    assert.equal(calls, 1);
  } finally {
    globalThis.fetch = originalFetch;
    if (key === undefined) delete process.env.TYPESAFE_API_KEY;
    else process.env.TYPESAFE_API_KEY = key;
  }
});
