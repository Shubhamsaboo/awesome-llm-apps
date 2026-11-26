import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import vm from "node:vm";
import { sentenceSpans } from "../server/sentences.mjs";
test("sentence spans preserve whitespace offsets, decimal numbers and Unicode", () => {
  const text =
    "  Welcome 👋. A charge of $3.50 applies.\n Keep your receipt!  ";
  const spans = sentenceSpans(text);
  assert.equal(spans.length, 3);
  assert.equal(spans[1].text, "A charge of $3.50 applies.");
  for (const span of spans)
    assert.equal(text.slice(span.start, span.end), span.text);
  assert.equal(spans[0].start, 2);
});
function rangeFixture(parts) {
  const nodes = parts.map((textContent) => ({ textContent }));
  const context = {
    NodeFilter: { SHOW_TEXT: 4 },
    document: {
      createTreeWalker() {
        let i = 0;
        return { nextNode: () => nodes[i++] || null };
      },
    },
    Range: class {
      setStart(node, offset) {
        this.start = { node, offset };
      }
      setEnd(node, offset) {
        this.end = { node, offset };
      }
    },
  };
  vm.createContext(context);
  vm.runInContext(
    readFileSync(
      new URL("../extension/text-range.js", import.meta.url),
      "utf8",
    ),
    context,
  );
  return {
    nodes,
    element: { textContent: parts.join("") },
    range: context.NeedleTextRange,
  };
}
test("sentence range crosses inline markup and accounts for trimmed leading whitespace", () => {
  const { range, element, nodes } = rangeFixture([
    "  Breakfast is included. A property ",
    "service charge of $35",
    " per night applies. Dogs welcome.  ",
  ]);
  const text = element.textContent.trim(),
    focus = sentenceSpans(text)[1],
    result = range(element, focus, text);
  assert.equal(result.start.node, nodes[0]);
  assert.equal(result.start.offset, nodes[0].textContent.indexOf("A property"));
  assert.equal(result.end.node, nodes[2]);
  assert.equal(result.end.offset, " per night applies.".length);
});
test("range handles a sentence at a text node boundary and rejects changed page text", () => {
  const { range, element, nodes } = rangeFixture(["One. ", "Two."]);
  const text = element.textContent;
  const result = range(element, { start: 5, end: 9, text: "Two." }, text);
  assert.equal(result.start.node, nodes[1]);
  assert.equal(result.start.offset, 0);
  assert.equal(result.end.offset, 4);
  assert.equal(range(element, { start: 5, end: 9, text: "Wrong" }, text), null);
  assert.equal(
    range(element, { start: 5, end: 9, text: "Two." }, "Changed"),
    null,
  );
});
