import http from "node:http";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { createHash } from "node:crypto";
import { evaluate } from "./jev.mjs";
import { getApiKey, getGeminiKey } from "./config.mjs";
import { suggest, SUGGESTION_MODEL } from "./suggestions.mjs";
const root = fileURLToPath(new URL(".", import.meta.url));
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
const origin = "chrome-extension://" + id;
const active = { check: 0, suggest: 0 };
const server = http.createServer(async (req, res) => {
  const json = (code, value) => {
    res.writeHead(code, {
      "Content-Type": "application/json",
      "Cache-Control": "no-store",
    });
    res.end(JSON.stringify(value));
  };
  if (!["127.0.0.1:4212", "localhost:4212"].includes(req.headers.host))
    return json(403, { error: "Invalid host." });
  if (req.headers.origin && req.headers.origin !== origin)
    return json(403, {
      error: "Only the Ripple extension can use this service.",
    });
  if (req.headers.origin === origin)
    res.setHeader("Access-Control-Allow-Origin", origin);
  res.setHeader("Vary", "Origin");
  if (req.method === "OPTIONS") {
    res.writeHead(204, {
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, X-Ripple-Client",
    });
    return res.end();
  }
  if (req.url === "/health" && req.method === "GET")
    return json(200, {
      ready: !!getApiKey(),
      model: "jev-latest",
      provider: "typesafe",
      suggestionsReady: !!getGeminiKey(),
      suggestionModel: SUGGESTION_MODEL,
      extensionId: id,
    });
  if (!["/check", "/suggest"].includes(req.url) || req.method !== "POST")
    return json(404, { error: "Not found." });
  if (
    req.headers["x-ripple-client"] !== id ||
    req.headers["content-type"] !== "application/json"
  )
    return json(403, { error: "Use the Ripple extension." });
  const route = req.url === "/check" ? "check" : "suggest";
  if (active[route] >= (route === "check" ? 1 : 2))
    return json(429, {
      error: "Another request is running. Retrying shortly.",
    });
  active[route]++;
  try {
    let bytes = 0,
      parts = [];
    for await (const chunk of req) {
      bytes += chunk.length;
      if (bytes > 50000)
        throw new Error("Document exceeds the prototype limit.");
      parts.push(chunk);
    }
    const input = JSON.parse(Buffer.concat(parts).toString());
    const result = await (route === "check" ? evaluate(input) : suggest(input));
    json(200, result);
  } catch (error) {
    json(400, {
      error:
        error.name === "TimeoutError"
          ? route === "check"
            ? "Jev timed out. Retry in a moment."
            : "Gemini timed out. Your highlights are still available."
          : error.message,
    });
  } finally {
    active[route]--;
  }
});
server.requestTimeout = 90000;
server.listen(4212, "127.0.0.1", () =>
  console.log(
    "Ripple is running on http://127.0.0.1:4212. Load the extension folder in Chrome or Brave.",
  ),
);
