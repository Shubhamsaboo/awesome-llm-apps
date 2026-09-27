import { mkdirSync, cpSync, rmSync } from "node:fs";
import { execFileSync } from "node:child_process";
const root = new URL(".", import.meta.url);
const dist = new URL("dist/", root);
mkdirSync(dist, { recursive: true });
const target = new URL("ripple-extension/", dist);
rmSync(target, { recursive: true, force: true });
cpSync(new URL("extension/", root), target, { recursive: true });
rmSync(new URL("ripple-extension.zip", dist), { force: true });
execFileSync("zip", ["-qr", "ripple-extension.zip", "ripple-extension"], {
  cwd: dist,
});
console.log(
  "Extension folder: " +
    target.pathname +
    "\nZIP: " +
    new URL("ripple-extension.zip", dist).pathname,
);
