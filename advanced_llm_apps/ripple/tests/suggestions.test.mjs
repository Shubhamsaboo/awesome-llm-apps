import test from "node:test";
import assert from "node:assert/strict";
import {
  parseSuggestions,
  validateSuggestionInput,
  suggest,
} from "../suggestions.mjs";
const input = {
  source: {
    before: "Attendance is online.",
    after: "Attendance is in person only.",
  },
  passages: [{ id: "one", text: "Join from anywhere." }],
};
const response = (rows) => ({
  candidates: [
    {
      finishReason: "STOP",
      content: { parts: [{ text: JSON.stringify({ suggestions: rows }) }] },
    },
  ],
});
test("accepts explicit missing-information response without an invented rewrite", () => {
  const rows = parseSuggestions(
    response([
      {
        id: "one",
        action: "needs_info",
        replacement: "",
        reason: "Please supply the new venue.",
      },
    ]),
    input,
  );
  assert.equal(rows[0].replacement, "");
});
test("rejects incomplete, unknown, multiline, and truncated suggestions", () => {
  assert.throws(() => parseSuggestions(response([]), input));
  assert.throws(() =>
    parseSuggestions(
      response([
        {
          id: "other",
          action: "replace",
          replacement: "Go there.",
          reason: "Changed.",
        },
      ]),
      input,
    ),
  );
  assert.throws(() =>
    parseSuggestions(
      response([
        {
          id: "one",
          action: "replace",
          replacement: "First\nSecond",
          reason: "Changed.",
        },
      ]),
      input,
    ),
  );
  assert.throws(() =>
    parseSuggestions({ candidates: [{ finishReason: "MAX_TOKENS" }] }, input),
  );
});
test("bounds model input and rejects duplicate passage IDs", () => {
  assert.throws(() =>
    validateSuggestionInput({
      ...input,
      passages: [input.passages[0], input.passages[0]],
    }),
  );
  assert.throws(() =>
    validateSuggestionInput({
      ...input,
      passages: [{ id: "one", text: "x", context: "x".repeat(4001) }],
    }),
  );
});
test("Gemini direct request uses requested model and server-side key header", async () => {
  const originalFetch = globalThis.fetch,
    originalKey = process.env.GEMINI_API_KEY;
  process.env.GEMINI_API_KEY = "synthetic-gemini-key";
  globalThis.fetch = async (url, options) => {
    assert.equal(
      url,
      "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent",
    );
    assert.equal(options.headers["x-goog-api-key"], "synthetic-gemini-key");
    assert.equal(
      JSON.parse(options.body).generationConfig.responseMimeType,
      "application/json",
    );
    return new Response(
      JSON.stringify(
        response([
          {
            id: "one",
            action: "replace",
            replacement: "Attend in person.",
            reason: "Attendance changed.",
          },
        ]),
      ),
    );
  };
  try {
    assert.equal(
      (await suggest(input)).suggestions[0].replacement,
      "Attend in person.",
    );
  } finally {
    globalThis.fetch = originalFetch;
    if (originalKey === undefined) delete process.env.GEMINI_API_KEY;
    else process.env.GEMINI_API_KEY = originalKey;
  }
});

test("deletion, keeping and asking are explicit and never inferred from empty text", () => {
  for (const action of ["delete", "keep", "needs_info"])
    assert.equal(
      parseSuggestions(
        response([
          { id: "one", action, replacement: "", reason: "Editorial decision." },
        ]),
        input,
      )[0].action,
      action,
    );
  for (const row of [
    { action: "replace", replacement: "" },
    { action: "delete", replacement: "Something else." },
    { action: "keep", replacement: "Changed." },
    { action: "needs_info", replacement: "Unknown address" },
    { replacement: "" },
    { action: "replace", replacement: "Join from anywhere." },
  ])
    assert.throws(() =>
      parseSuggestions(
        response([{ id: "one", reason: "A reason.", ...row }]),
        input,
      ),
    );
});
