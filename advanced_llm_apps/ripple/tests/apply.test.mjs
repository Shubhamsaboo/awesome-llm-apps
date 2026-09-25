import test from "node:test";
import assert from "node:assert/strict";
import vm from "node:vm";
import { readFileSync } from "node:fs";
const correction = readFileSync(
  new URL("../extension/correction.js", import.meta.url),
  "utf8",
);
const source = readFileSync(
  new URL("../extension/bootstrap.js", import.meta.url),
  "utf8",
);
function harness(
  initial,
  {
    acceptEdit = true,
    deferApply = false,
    loseFocus = false,
    wrongSelection = false,
    concurrentEdit = false,
    collapseEditSpaces = false,
  } = {},
) {
  let raw = "\u0003" + initial + "\n",
    listener,
    selection,
    commands = [],
    focused = false;
  let reads = 0,
    release;
  const messages = [];
  const body = { isContentEditable: false };
  class KeyboardEvent {
    constructor(type, options) {
      this.type = type;
      Object.assign(this, options);
    }
  }
  class ClipboardEvent {
    constructor(type, options) {
      this.type = type;
      Object.assign(this, options);
    }
  }
  class DataTransfer {
    setData(type, value) {
      this[type] = value;
    }
    getData(type) {
      return this[type] || "";
    }
  }
  const realm = { KeyboardEvent, ClipboardEvent, DataTransfer };
  const target = {
    isContentEditable: true,
    focus() {
      focused = true;
      selection = [0, 0];
      targetDocument.activeElement = this;
    },
    dispatchEvent(event) {
      assert.equal(
        targetDocument.activeElement,
        this,
        "input must target actual editor",
      );
      assert.ok(focused);
      if (event.type === "keyup") return;
      if (event.type === "keydown") {
        assert.ok(event instanceof realm.KeyboardEvent);
        assert.equal(event.key, "Backspace");
        assert.equal(event.keyCode, 8);
        assert.equal(event.bubbles, true);
        assert.equal(event.composed, true);
      }
      if (event.type === "paste")
        assert.ok(event instanceof realm.ClipboardEvent);
      const command = event.type === "keydown" ? "Backspace" : "paste",
        value =
          command === "paste"
            ? event.clipboardData.getData("text/plain")
            : undefined;
      commands.push({ command, value });
      if (acceptEdit) {
        raw =
          raw.slice(0, selection[0]) +
          (command === "Backspace" ? "" : value) +
          raw.slice(selection[1]);
        if (collapseEditSpaces) raw = raw.replace("  ", " ");
      }
    },
  };
  const targetDocument = {
    activeElement: body,
    defaultView: realm,
    querySelector: () => target,
    execCommand() {
      throw new Error("Must not edit the Docs proxy DOM");
    },
  };
  const api = {
    getText: () => raw,
    setSelection: (a, b) => {
      assert.ok(focused, "focus before selection");
      selection = [a, b];
    },
    getSelection: () => [{ start: selection?.[0], end: selection?.[1] }],
  };
  const window = {
    _docs_annotate_getAnnotatedText: async () => {
      reads++;
      if (deferApply && reads === 2)
        await new Promise((resolve) => {
          release = resolve;
        });
      if (reads === 3) {
        if (loseFocus) targetDocument.activeElement = body;
        if (wrongSelection) selection = [0, 0];
        if (concurrentEdit) raw += "collaborator";
      }
      return api;
    },
    addEventListener: (type, fn) => {
      if (type === "message") listener = fn;
    },
    postMessage: (data) => messages.push(data),
  };
  const location = {
    origin: "https://docs.google.com",
    href: "https://docs.google.com/document/d/test/edit?tab=t.0",
  };
  vm.runInNewContext(correction + "\n" + source, {
    window,
    location,
    document: {
      hidden: false,
      querySelector: () => ({
        contentDocument: targetDocument,
        contentWindow: { focus() {} },
      }),
    },
    URL,
    setInterval() {},
    setTimeout(fn) {
      queueMicrotask(fn);
    },
  });
  const send = async (data) =>
    listener({
      source: window,
      origin: location.origin,
      data: { channel: "ripple-docs-v1", ...data },
    });
  return {
    send,
    messages,
    release: () => release?.(),
    setTab: (t) => {
      location.href = "https://docs.google.com/document/d/test/edit?tab=" + t;
    },
    text: () => raw.slice(1, -1),
    commands: () => commands,
  };
}
const original = "Attendance is in person only. Join from anywhere.";
const change = {
  type: "apply",
  requestId: "test-1",
  baseText: original,
  quote: "Join from anywhere.",
  action: "replace",
  replacement: "Attend in person.",
  tab: "t.0",
};
test("restores editor focus before selection and confirms one Docs paste operation", async () => {
  const h = harness(original);
  await h.send({ type: "enabled", enabled: true });
  await h.send(change);
  assert.equal(h.text(), "Attendance is in person only. Attend in person.");
  assert.deepEqual(h.commands(), [
    { command: "paste", value: "Attend in person." },
  ]);
  assert.equal(h.messages.find((m) => m.type === "apply-result").ok, true);
  assert.equal(
    h.messages.find((m) => m.type === "apply-result").text,
    h.text(),
  );
  assert.equal(h.messages.find((m) => m.type === "apply-result").tab, "t.0");
});
test("explicit deletion removes only the reviewed sentence and preserves adjacent text", async () => {
  const text = "Keep this. Zoom link follows. Bring a laptop.";
  const h = harness(text);
  await h.send({ type: "enabled", enabled: true });
  await h.send({
    ...change,
    baseText: text,
    quote: "Zoom link follows.",
    action: "delete",
    replacement: "",
  });
  assert.equal(h.text(), "Keep this.  Bring a laptop.");
  assert.deepEqual(h.commands(), [{ command: "Backspace", value: undefined }]);
  assert.equal(h.messages.find((m) => m.type === "apply-result").ok, true);
  assert.equal(
    h.messages.find((m) => m.type === "apply-result").text,
    h.text(),
  );
  assert.equal(h.messages.find((m) => m.type === "apply-result").tab, "t.0");
});
test("empty replacement never silently becomes a deletion", async () => {
  for (const request of [
    { ...change, replacement: "" },
    { ...change, action: "delete" },
    { ...change, action: "keep", replacement: "" },
    { ...change, replacement: 42 },
  ]) {
    const h = harness(original);
    await h.send({ type: "enabled", enabled: true });
    await h.send(request);
    assert.equal(h.commands().length, 0);
    assert.equal(h.messages.find((m) => m.type === "apply-result").ok, false);
  }
});
test("stale document and wrong tab prevent any edit", async () => {
  for (const input of [
    { ...change, baseText: "Old text." },
    { ...change, tab: "t.1" },
  ]) {
    const h = harness(original);
    await h.send({ type: "enabled", enabled: true });
    await h.send(input);
    assert.equal(h.commands().length, 0);
    assert.equal(h.messages.find((m) => m.type === "apply-result").ok, false);
  }
});
test("duplicate quote never changes a guessed occurrence", async () => {
  const text = original + " Join from anywhere.";
  const h = harness(text);
  await h.send({ type: "enabled", enabled: true });
  await h.send({ ...change, baseText: text });
  assert.equal(h.commands().length, 0);
});
test("ignored input is attempted once without a second operation or success claim", async () => {
  const h = harness(original, { acceptEdit: false });
  await h.send({ type: "enabled", enabled: true });
  await h.send(change);
  assert.equal(h.commands().length, 1);
  assert.equal(h.messages.find((m) => m.type === "apply-result").ok, false);
  assert.equal(h.text(), original);
});
test("lost focus, changed selection, and concurrent document edits cancel the write", async () => {
  for (const options of [
    { loseFocus: true },
    { wrongSelection: true },
    { concurrentEdit: true },
  ]) {
    const h = harness(original, options);
    await h.send({ type: "enabled", enabled: true });
    await h.send(change);
    assert.equal(h.commands().length, 0);
    assert.equal(h.messages.find((m) => m.type === "apply-result").ok, false);
  }
});
test("paused extension does not apply a queued correction", async () => {
  const h = harness(original);
  await h.send(change);
  assert.equal(h.commands().length, 0);
});
test("pause, pause-resume, or tab switch during adapter read cancels pending Apply", async () => {
  for (const action of ["pause", "resume", "tab"]) {
    const h = harness(original, { deferApply: true });
    await h.send({ type: "enabled", enabled: true });
    const pending = h.send(change);
    if (action === "tab") h.setTab("t.1");
    else {
      await h.send({ type: "enabled", enabled: false });
      if (action === "resume") await h.send({ type: "enabled", enabled: true });
    }
    h.release();
    await pending;
    assert.equal(h.commands().length, 0, action);
    assert.equal(h.messages.find((m) => m.type === "apply-result").ok, false);
  }
});

test("Docs collapsing the deletion boundary is confirmed with its actual text", async () => {
  const text = "Keep this. Zoom link follows. Bring a laptop.";
  const h = harness(text, { collapseEditSpaces: true });
  await h.send({ type: "enabled", enabled: true });
  await h.send({
    ...change,
    baseText: text,
    quote: "Zoom link follows.",
    action: "delete",
    replacement: "",
  });
  const result = h.messages.find((m) => m.type === "apply-result");
  assert.equal(result.ok, true);
  assert.equal(result.text, "Keep this. Bring a laptop.");
});
