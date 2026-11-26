import test from "node:test";
import assert from "node:assert/strict";
import vm from "node:vm";
import { readFileSync } from "node:fs";
const source = readFileSync(
  new URL("../extension/ui.js", import.meta.url),
  "utf8",
)
  .replace('import { logo as icon } from "./logo.js";', 'const icon = "";')
  .replace("export function createUI", "function createUI");
function harness() {
  const nodes = new Map();
  const element = () => ({
    dataset: {},
    style: {},
    hidden: false,
    disabled: false,
    value: "",
    offsetHeight: 300,
    setAttribute() {},
    focus() {},
    append() {},
    replaceChildren() {},
    querySelectorAll: () => [],
    classList: { toggle() {} },
  });
  const root = {
    getElementById(id) {
      if (!nodes.has(id)) nodes.set(id, element());
      return nodes.get(id);
    },
  };
  const host = { ...element(), attachShadow: () => root };
  let complete,
    kept = 0;
  const createUI = vm.runInNewContext(source + "\ncreateUI", {
    document: {
      createElement: () => host,
      documentElement: { append() {} },
      addEventListener() {},
    },
    innerWidth: 1200,
    innerHeight: 900,
  });
  const ui = createUI({
    navigate() {},
    keep() {
      kept++;
    },
    apply: () =>
      new Promise((r) => {
        complete = r;
      }),
  });
  const rows = ["a", "b", "c"].map((key, i) => ({
    key,
    text: key,
    source: { before: "Online", after: "In person" },
    suggestionState: "ready",
    suggestion: {
      action: i === 1 ? "delete" : "replace",
      replacement: i === 1 ? "" : "New text",
      reason: "Changed",
    },
  }));
  nodes.get("menu").hidden = true;
  nodes.get("card").hidden = true;
  ui.results(rows);
  nodes.get("chip").onclick();
  return { ui, rows, nodes, complete: (r) => complete(r), kept: () => kept };
}
test("Keep is blocked throughout a pending Apply, then enabled again", async () => {
  const h = harness();
  const pending = h.nodes.get("apply").onclick();
  assert.equal(h.nodes.get("keep").disabled, true);
  h.nodes.get("keep").onclick();
  assert.equal(h.kept(), 0);
  h.complete({ ok: false, error: "Not accepted" });
  await pending;
  assert.equal(h.nodes.get("keep").disabled, false);
  assert.equal(h.nodes.get("suggestion-status").textContent, "Not accepted");
  h.nodes.get("keep").onclick();
  assert.equal(h.kept(), 1);
});
test("navigating during Apply restores the active row button and its own action label", async () => {
  for (const ok of [true, false]) {
    const h = harness();
    const pending = h.nodes.get("apply").onclick();
    h.nodes.get("next").onclick();
    assert.equal(h.nodes.get("apply").disabled, true);
    if (ok) h.ui.results(h.rows.slice(1));
    h.complete({ ok, error: "Not accepted" });
    await pending;
    assert.equal(h.nodes.get("apply").disabled, false);
    assert.equal(h.nodes.get("apply").textContent, "Remove sentence");
    assert.equal(h.nodes.get("card").hidden, false);
  }
});
