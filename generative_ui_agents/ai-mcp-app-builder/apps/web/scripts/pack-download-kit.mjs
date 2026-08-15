/**
 * Builds apps/web/.download-kit/base.tar.gz — monorepo shell (no node_modules / .next / dist)
 * for merging with the E2B workspace on download. Run via prebuild before next build.
 */
import fs from "fs/promises";
import os from "os";
import path from "path";
import { fileURLToPath } from "url";
import { createWriteStream } from "fs";
import { pipeline } from "stream/promises";
import * as tar from "tar";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const WEB_ROOT = path.resolve(__dirname, "..");
const REPO_ROOT = path.resolve(WEB_ROOT, "..", "..");
const OUT_DIR = path.join(WEB_ROOT, ".download-kit");
const OUT_FILE = path.join(OUT_DIR, "base.tar.gz");
const KIT_ROOT = "mcp-apps-starter";

const SKIP_DIR_NAMES = new Set([
  "node_modules",
  ".next",
  ".turbo",
  "dist",
  ".vercel",
  ".git",
  "coverage",
  ".agent",
  ".download-kit",
]);

function shouldSkipDir(name) {
  return SKIP_DIR_NAMES.has(name);
}

const KIT_README = `# ${KIT_ROOT}

This archive was produced by **MCP App builder** (download with **full app kit**). It matches this starter layout: root workspace, \`apps/web\`, \`apps/mcp-use-server\` (your sandbox code), and \`apps/threejs-server\`.

## Setup

1. Copy environment: \`cp .env.example .env\` (PowerShell: \`Copy-Item .env.example .env\`) and set \`OPENAI_API_KEY\` and any E2B vars you need.
2. Install: \`pnpm i\`
3. Run everything from the repo root: \`pnpm dev\` (Turbo starts web + configured apps — see root \`package.json\` / \`turbo.json\`).

Your downloaded MCP server lives in \`apps/mcp-use-server\`. See root \`README.md\` and \`docs/DEPLOY.md\` for deployment notes.

`;

async function pathExists(p) {
  try {
    await fs.access(p);
    return true;
  } catch {
    return false;
  }
}

async function copyFiltered(src, dest) {
  const stat = await fs.stat(src);
  if (stat.isDirectory()) {
    const base = path.basename(src);
    if (shouldSkipDir(base)) return;
    await fs.mkdir(dest, { recursive: true });
    const entries = await fs.readdir(src, { withFileTypes: true });
    for (const e of entries) {
      if (shouldSkipDir(e.name)) continue;
      await copyFiltered(path.join(src, e.name), path.join(dest, e.name));
    }
  } else {
    await fs.copyFile(src, dest);
  }
}

async function main() {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), "pack-kit-"));
  const stage = path.join(tmp, KIT_ROOT);
  try {
    await fs.mkdir(stage, { recursive: true });
    await fs.writeFile(path.join(stage, "README.md"), KIT_README, "utf8");

    const rootFiles = [
      "package.json",
      "pnpm-workspace.yaml",
      "turbo.json",
      ".env.example",
    ];
    for (const f of rootFiles) {
      const from = path.join(REPO_ROOT, f);
      if (await pathExists(from)) {
        await fs.copyFile(from, path.join(stage, f));
      }
    }

    const appsSrc = path.join(REPO_ROOT, "apps");
    if (!(await pathExists(appsSrc))) {
      throw new Error(`Expected ${appsSrc} — run from monorepo with apps/web`);
    }
    const appsDest = path.join(stage, "apps");
    await fs.mkdir(appsDest, { recursive: true });
    const appDirs = await fs.readdir(appsSrc, { withFileTypes: true });
    for (const d of appDirs) {
      if (!d.isDirectory()) continue;
      await copyFiltered(
        path.join(appsSrc, d.name),
        path.join(appsDest, d.name),
      );
    }

    await fs.mkdir(OUT_DIR, { recursive: true });
    const ws = createWriteStream(OUT_FILE);
    await pipeline(
      tar.c({ gzip: true, cwd: tmp, portable: true }, [KIT_ROOT]),
      ws,
    );
    const st = await fs.stat(OUT_FILE);
    console.log(
      `[pack-download-kit] wrote ${OUT_FILE} (${(st.size / 1024 / 1024).toFixed(2)} MiB)`,
    );
  } finally {
    await fs.rm(tmp, { recursive: true, force: true });
  }
}

main().catch((err) => {
  console.error("[pack-download-kit]", err);
  process.exit(1);
});
