import test from "node:test";
import assert from "node:assert/strict";
import vm from "node:vm";
import { readFileSync } from "node:fs";
import { Readable } from "node:stream";
import { EventEmitter } from "node:events";
import { fileURLToPath } from "node:url";
import { createHash } from "node:crypto";
const root = fileURLToPath(new URL("../", import.meta.url));
const manifest = JSON.parse(
  readFileSync(root + "extension/manifest.json", "utf8"),
);
const id = [
  ...createHash("sha256")
    .update(Buffer.from(manifest.key, "base64"))
    .digest("hex")
    .slice(0, 32),
]
  .map((h) => String.fromCharCode(97 + parseInt(h, 16)))
  .join("");
const serverSource = readFileSync(root + "server.mjs", "utf8")
  .replace(/^import .*;\n/gm, "")
  .replace(
    'const root = fileURLToPath(new URL(".", import.meta.url));',
    "const root = testRoot;",
  );
function harness(evaluate) {
  let handler;
  vm.runInNewContext(serverSource, {
    http: {
      createServer(fn) {
        handler = fn;
        return { listen() {} };
      },
    },
    readFileSync,
    createHash,
    Buffer,
    AbortController,
    testRoot: root,
    evaluate,
    suggest: async () => ({ suggestions: [] }),
    getApiKey: () => "",
    getGeminiKey: () => "",
    SUGGESTION_MODEL: "test",
    console,
  });
  const request = (headers = {}, url = "/check") => {
    const req = Readable.from([Buffer.from("{}")]);
    Object.assign(req, {
      method: "POST",
      url,
      headers: {
        host: "127.0.0.1:4212",
        origin: "chrome-extension://" + id,
        "x-ripple-client": id,
        "content-type": "application/json",
        ...headers,
      },
    });
    const res = Object.assign(new EventEmitter(), {
      destroyed: false,
      writableEnded: false,
      setHeader() {},
      writeHead(status) {
        this.status = status;
      },
      end(body) {
        this.body = JSON.parse(body);
        this.writableEnded = true;
      },
    });
    return { req, res, done: handler(req, res) };
  };
  return { request };
}
test("HTTP rejects foreign callers before model work", async () => {
  let calls = 0;
  const h = harness(async () => {
    calls++;
    return {};
  });
  for (const headers of [
    { origin: "https://evil.example" },
    { host: "evil.example" },
    { "x-ripple-client": "wrong" },
    { "content-type": "text/plain" },
  ]) {
    const r = h.request(headers);
    await r.done;
    assert.equal(r.res.status, 403);
  }
  assert.equal(calls, 0);
});
test("HTTP busy response is retryable; disconnect cancels work before releasing slot", async () => {
  let signal,
    calls = 0;
  const h = harness(async (_input, options) => {
    calls++;
    signal = options.signal;
    if (calls > 1) return { results: [] };
    await new Promise((_resolve, reject) =>
      signal.addEventListener("abort", () => reject(signal.reason), {
        once: true,
      }),
    );
  });
  const first = h.request();
  while (!signal) await new Promise((resolve) => setImmediate(resolve));
  const second = h.request();
  await second.done;
  assert.equal(second.res.status, 429);
  assert.equal(second.res.body.retryable, true);
  assert.equal(calls, 1);
  first.res.destroyed = true;
  first.res.emit("close");
  await first.done;
  assert.equal(signal.aborted, true);
  const third = h.request();
  await third.done;
  assert.equal(third.res.status, 200);
  assert.equal(calls, 2);
});
test("extension preserves retryable busy metadata after its bounded attempts", async () => {
  let listener,
    calls = 0;
  const source = readFileSync(root + "extension/background.js", "utf8");
  vm.runInNewContext(source, {
    chrome: {
      runtime: {
        id,
        getURL: () => `chrome-extension://${id}/`,
        onMessage: {
          addListener(fn) {
            listener = fn;
          },
        },
      },
    },
    AbortSignal,
    JSON,
    setTimeout: (fn) => {
      queueMicrotask(fn);
    },
    fetch: async () => {
      calls++;
      return {
        status: 429,
        ok: false,
        json: async () => ({ error: "Busy", retryable: true }),
      };
    },
  });
  const result = await new Promise((resolve) =>
    listener(
      { type: "check", input: {} },
      { id, url: `chrome-extension://${id}/popup.html` },
      resolve,
    ),
  );
  assert.equal(calls, 3);
  assert.equal(result.ok, false);
  assert.equal(result.retryable, true);
});
