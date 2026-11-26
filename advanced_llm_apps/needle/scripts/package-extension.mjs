import { readFile, writeFile, readdir, mkdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { resolve, join } from "node:path";
import { zipSync } from "fflate";
const root = fileURLToPath(new URL("../", import.meta.url));
const source = join(root, "extension");
const manifest = JSON.parse(
  await readFile(join(source, "manifest.json"), "utf8"),
);
// Explicit allowlist: credentials, local settings and unrelated files cannot enter the ZIP.
const entries = [
  "manifest.json",
  "background.js",
  "content.js",
  "text-range.js",
  "options.html",
  "options.js",
  "options.css",
];
for (const name of await readdir(join(source, "icons"))) {
  if (/^needle(?:-\d+)?\.(png|svg)$/.test(name)) entries.push(`icons/${name}`);
}
for (const asset of [
  ...Object.values(manifest.icons),
  ...Object.values(manifest.action.default_icon),
]) {
  if (!entries.includes(asset))
    throw new Error(`Missing extension icon: ${asset}`);
}
const files = {};
for (const entry of entries.sort())
  files[entry] = [
    new Uint8Array(await readFile(resolve(source, entry))),
    { mtime: new Date("2026-01-01T00:00:00Z") },
  ];
const zip = zipSync(files, { level: 9 });
await mkdir(join(root, "artifacts"), { recursive: true });
await mkdir(join(root, "public"), { recursive: true });
const filename = `needle-extension-v${manifest.version}.zip`;
await writeFile(join(root, "artifacts", filename), zip);
await writeFile(join(root, "public", "needle-extension.zip"), zip);
console.log(`Packaged artifacts/${filename} and public/needle-extension.zip`);
