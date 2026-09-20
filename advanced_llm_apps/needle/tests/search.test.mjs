import test from "node:test";
import assert from "node:assert/strict";
import {
  validate,
  makePayload,
  parseAnswers,
  search,
  MODEL,
} from "../server/search.mjs";
import { splitDocument } from "../src/search.js";
const blocks = [
  { id: "b0", text: "A $25 service charge is deducted from refunds." },
  { id: "b1", text: "Breakfast is served at 8." },
];
test("validates passage boundaries and duplicate IDs", () => {
  assert.deepEqual(validate({ query: " fees ", blocks }), {
    query: "fees",
    blocks,
  });
  for (const bad of [
    [],
    [blocks[0], blocks[0]],
    [{ id: "bad", text: "abc" }],
    [{ id: "b0", text: "x".repeat(2201) }],
  ])
    assert.throws(() => validate({ query: "fees", blocks: bad }));
  assert.throws(() => validate({ query: "x".repeat(401), blocks }));
});
test("binds each relevance question to a specific passage", () => {
  const p = makePayload({ query: "fees", blocks });
  assert.equal(p.model, MODEL);
  assert.equal(p.state.passages, blocks);
  assert.match(p.questions.b1.instructions, /ONLY passage b1/);
  assert.equal(p.questions.b0.type, "boolean");
});
test("rejects incomplete, out-of-range and nonnumeric scores", () => {
  for (const p of [undefined, -1, 1.1, NaN, "0.9"])
    assert.throws(() =>
      parseAnswers(
        { answers: { b0: { probability: p }, b1: { probability: 0.1 } } },
        blocks,
      ),
    );
  assert.deepEqual(
    parseAnswers(
      {
        answers: {
          b0: { probability: 0.6 },
          b1: { probability: 0.9 },
          alien: { probability: 1 },
        },
      },
      blocks,
    ).map((x) => x.id),
    ["b1", "b0"],
  );
});
test("uses evaluation endpoint, keeps key server-side, returns ranked matching source IDs", async () => {
  const result = await search(
    { query: "fees", blocks },
    {
      key: "test-only",
      fetchImpl: async (url, options) => {
        assert.equal(url, "https://ai-gateway.vercel.sh/v1/evaluate");
        assert.equal(options.headers.Authorization, "Bearer test-only");
        return {
          ok: true,
          json: async () => ({
            answers: {
              b0: { type: "boolean", probability: 0.95 },
              b1: { type: "boolean", probability: 0.05 },
            },
          }),
        };
      },
    },
  );
  assert.deepEqual(result.matches, [
    {
      id: "b0",
      probability: 0.95,
      focus: { start: 0, end: blocks[0].text.length, text: blocks[0].text },
    },
  ]);
  assert.equal(result.model, MODEL);
  assert.ok(!JSON.stringify(result).includes("test-only"));
});
test("missing keys and upstream failures never fabricate matches", async () => {
  await assert.rejects(
    search({ query: "fees", blocks }, { key: "" }),
    /needs an AI Gateway key/,
  );
  await assert.rejects(
    search(
      { query: "fees", blocks },
      { key: "test", fetchImpl: async () => ({ ok: false, status: 429 }) },
    ),
    /Too many searches/,
  );
  await assert.rejects(
    search(
      { query: "fees", blocks },
      {
        key: "test",
        fetchImpl: async () => {
          throw new Error("secret upstream detail");
        },
      },
    ),
    /Could not reach/,
  );
});
test("splits long pasted documents into valid bounded passages", () => {
  const input =
    "A paragraph.\n\n" +
    "Long text with words. ".repeat(200) +
    "\n\n" +
    "x".repeat(5000);
  const result = splitDocument(input);
  assert.ok(result.length > 3);
  assert.ok(result.every((b) => b.text.length <= 2200));
  assert.equal(new Set(result.map((b) => b.id)).size, result.length);
  assert.doesNotThrow(() => validate({ query: "words", blocks: result }));
});
test("splitting preserves punctuation, URLs and numbers in original passages", () => {
  const text =
    "Visit https://example.com/a.b?x=3.14. " +
    "A long sentence with punctuation! ".repeat(100);
  assert.equal(
    splitDocument(text)
      .map((b) => b.text)
      .join(" ")
      .replace(/\s+/g, " ")
      .trim(),
    text.replace(/\s+/g, " ").trim(),
  );
});
test("asks Jev to select a sentence, and maps it to exact source offsets", () => {
  const blocks = [
    {
      id: "b0",
      text: "Breakfast is included. A service charge applies. Dogs are welcome.",
    },
  ];
  const payload = makePayload({ query: "hidden fees", blocks });
  assert.equal(payload.questions.focus_b0.type, "choice");
  assert.equal(
    payload.questions.focus_b0.criteria.s1,
    "A service charge applies.",
  );
  const [result] = parseAnswers(
    { answers: { b0: { probability: 0.95 }, focus_b0: { choice: "s1" } } },
    blocks,
  );
  assert.equal(result.focus.text, "A service charge applies.");
  assert.equal(
    blocks[0].text.slice(result.focus.start, result.focus.end),
    result.focus.text,
  );
  for (const choice of [undefined, "s99", "s-1", "invented text"])
    assert.throws(
      () =>
        parseAnswers(
          { answers: { b0: { probability: 0.95 }, focus_b0: { choice } } },
          blocks,
        ),
      /incomplete sentence/,
    );
});
