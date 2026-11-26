import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { execFileSync } from "node:child_process";
import { unzipSync, strFromU8 } from "fflate";
test("extension package contains all runtime files and icons but no backend or secrets", async () => {
  execFileSync(process.execPath, ["scripts/package-extension.mjs"]);
  const zip = unzipSync(
    new Uint8Array(await readFile("public/needle-extension.zip")),
  );
  const manifest = JSON.parse(strFromU8(zip["manifest.json"]));
  assert.equal(manifest.manifest_version, 3);
  for (const file of [
    manifest.background.service_worker,
    manifest.options_page,
    "content.js",
    "text-range.js",
    ...Object.values(manifest.icons),
    ...Object.values(manifest.action.default_icon),
  ])
    assert.ok(zip[file], `Missing ${file}`);
  for (const name of Object.keys(zip))
    assert.match(
      name,
      /^(?:[\w-]+\.(?:js|html|css|json)|icons\/needle(?:-\d+)?\.(?:png|svg))$/,
    );
  assert.ok(
    !Object.keys(zip).some((name) =>
      /env|server|node_modules|test/i.test(name),
    ),
  );
});
