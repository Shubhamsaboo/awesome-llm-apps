import test from "node:test";
import assert from "node:assert/strict";
import { accessError } from "../server/http.mjs";
import handler from "../api/search.js";
test("local backend permits tokenless use, but Vercel fails closed", () => {
  assert.equal(accessError({}, {}), null);
  assert.equal(accessError({}, { VERCEL: "1" }).status, 503);
  assert.equal(
    accessError({}, { VERCEL: "1", NEEDLE_ACCESS_TOKEN: "  " }).status,
    503,
  );
  assert.equal(
    accessError({}, { NEEDLE_ACCESS_TOKEN: "app-token" }).status,
    401,
  );
  assert.equal(
    accessError(
      { "x-needle-token": "app-token" },
      { VERCEL: "1", NEEDLE_ACCESS_TOKEN: "app-token" },
    ),
    null,
  );
});
test("API rejects wrong methods before attempting inference", async () => {
  const res = {
    headers: {},
    setHeader(k, v) {
      this.headers[k] = v;
    },
    status(n) {
      this.code = n;
      return this;
    },
    json(data) {
      this.body = data;
    },
  };
  await handler({ method: "GET", headers: {} }, res);
  assert.equal(res.code, 405);
  assert.equal(res.headers.Allow, "POST");
  assert.equal(res.headers["Cache-Control"], "no-store");
});
