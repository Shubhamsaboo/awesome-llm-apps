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
