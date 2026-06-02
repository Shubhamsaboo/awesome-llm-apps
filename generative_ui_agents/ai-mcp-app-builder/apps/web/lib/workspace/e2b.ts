import { Sandbox } from "e2b";
import type {
  WorkspaceProvider,
  WorkspaceInfo,
  ExecOpts,
  ExecResult,
} from "./types";

const WORKSPACE_PATH = "/home/user/workspace";
// Hardcoded fallback so sandbox clone works without env; override with E2B_REPO_URL if needed
const REPO_URL =
  process.env.E2B_REPO_URL ?? "https://github.com/CopilotKit/CopilotKit";
const TEMPLATE_ID = process.env.E2B_TEMPLATE;
// Default sandbox lifetime: 60 minutes (can be extended during a session)
const SANDBOX_TIMEOUT_MS = 60 * 60 * 1000;

export class E2BWorkspaceProvider implements WorkspaceProvider {
  async provision(_name: string): Promise<WorkspaceInfo> {
    if (!TEMPLATE_ID && !REPO_URL) {
      throw new Error(
        "Set E2B_TEMPLATE (recommended) or E2B_REPO_URL in your .env.local.",
      );
    }

    // Create sandbox — use custom template if provided (pre-installed deps = faster cold start)
    const sandbox = TEMPLATE_ID
      ? await Sandbox.create(TEMPLATE_ID, { timeoutMs: SANDBOX_TIMEOUT_MS })
      : await Sandbox.create({ timeoutMs: SANDBOX_TIMEOUT_MS });

    if (TEMPLATE_ID) {
      // Template has node_modules + dist pre-built, and setStartCmd already
      // started the server on port 3109 when the sandbox booted.
      // Nothing to do — just get the endpoint below.
    } else {
      // No template — full cold start: clone + install (~60-90s)
      const clone = await sandbox.commands.run(
        `git clone --depth 1 ${REPO_URL} ${WORKSPACE_PATH}`,
        { timeoutMs: 2 * 60_000 },
      );
      if (clone.exitCode !== 0) {
        await sandbox.kill();
        throw new Error(
          `git clone failed (exit ${clone.exitCode}): ${clone.stderr}`,
        );
      }

      const install = await sandbox.commands.run(
        `cd ${WORKSPACE_PATH} && npm install --no-audit --no-fund --prefer-offline`,
        { timeoutMs: 15 * 60_000 },
      );
      if (install.exitCode !== 0) {
        await sandbox.kill();
        throw new Error(
          `npm install failed (exit ${install.exitCode}): ${install.stderr}`,
        );
      }

      // Start dev server in background and wait for it to come up
      await sandbox.commands.run(`cd ${WORKSPACE_PATH} && npm run dev`, {
        background: true,
      });
      await new Promise((r) => setTimeout(r, 10_000));
    }

    const endpoint = await this._getMcpEndpoint(sandbox);

    return {
      workspaceId: sandbox.sandboxId,
      endpoint,
      status: "running",
      path: WORKSPACE_PATH,
    };
  }

  async getInfo(workspaceId: string): Promise<WorkspaceInfo> {
    const sandbox = await Sandbox.connect(workspaceId);
    const endpoint = await this._getMcpEndpoint(sandbox);
    return { workspaceId, endpoint, status: "running", path: WORKSPACE_PATH };
  }

  async stop(workspaceId: string): Promise<void> {
    const sandbox = await Sandbox.connect(workspaceId);
    await sandbox.kill();
  }

  async readFile(workspaceId: string, path: string): Promise<string> {
    const sandbox = await Sandbox.connect(workspaceId);
    return sandbox.files.read(this._fullPath(path));
  }

  async writeFile(
    workspaceId: string,
    path: string,
    content: string,
  ): Promise<void> {
    const sandbox = await Sandbox.connect(workspaceId);
    const full = this._fullPath(path);
    // Ensure parent directory exists
    const dir = full.substring(0, full.lastIndexOf("/"));
    await sandbox.commands.run(`mkdir -p "${dir}"`);
    await sandbox.files.write(full, content);
  }

  async editFile(
    workspaceId: string,
    path: string,
    search: string,
    replace: string,
  ): Promise<void> {
    const sandbox = await Sandbox.connect(workspaceId);
    const full = this._fullPath(path);
    const content = await sandbox.files.read(full);
    if (!content.includes(search)) {
      throw new Error(
        `Search string not found in "${path}". Make sure the search string matches exactly.`,
      );
    }
    await sandbox.files.write(full, content.replace(search, replace));
  }

  async exec(
    workspaceId: string,
    cmd: string,
    opts?: ExecOpts,
  ): Promise<ExecResult> {
    const sandbox = await Sandbox.connect(workspaceId);

    if (opts?.background) {
      await sandbox.commands.run(cmd, {
        cwd: opts.cwd ?? WORKSPACE_PATH,
        background: true,
      });
      return { stdout: "", stderr: "", exitCode: 0, background: true };
    }

    const result = await sandbox.commands.run(cmd, {
      cwd: opts?.cwd ?? WORKSPACE_PATH,
      timeoutMs: opts?.timeoutMs ?? 60_000,
    });

    return {
      stdout: result.stdout ?? "",
      stderr: result.stderr ?? "",
      exitCode: result.exitCode ?? 0,
    };
  }

  async prepareDownload(workspaceId: string): Promise<{ downloadUrl: string }> {
    const sandbox = await Sandbox.connect(workspaceId);
    // Strip heavy dirs, then archive with tar (GNU zip is often missing → exit 127 on `zip`).
    const clean = await sandbox.commands.run(
      `cd ${WORKSPACE_PATH} && rm -rf node_modules dist .agent`,
      { timeoutMs: 120_000 },
    );
    if (clean.exitCode !== 0) {
      throw new Error(
        `Failed to prepare workspace for download: ${clean.stderr || clean.stdout || "unknown error"}`,
      );
    }
    const archive = await sandbox.commands.run(
      `cd /home/user && rm -f workspace.tar.gz workspace.zip && tar -czf workspace.tar.gz workspace`,
      { timeoutMs: 5 * 60_000 },
    );
    if (archive.exitCode !== 0) {
      throw new Error(
        `Archive failed (exit ${archive.exitCode}): ${archive.stderr || archive.stdout || "is tar available?"}`,
      );
    }
    const url = await sandbox.downloadUrl("/home/user/workspace.tar.gz");
    return { downloadUrl: url };
  }

  // ── helpers ────────────────────────────────────────────────────────────────

  private async _getMcpEndpoint(sandbox: Sandbox): Promise<string> {
    // Prefer the E2B-managed MCP URL (no port wrangling required).
    // betaGetMcpUrl is a beta method not yet in the public type definitions.
    try {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const url = (sandbox as any).betaGetMcpUrl?.();
      if (url) return url as string;
    } catch {
      // betaGetMcpUrl not available in this SDK version — fall through
    }
    // Fallback: map the default mcp-use port
    return `https://${sandbox.getHost(3109)}/mcp`;
  }

  private _fullPath(relativePath: string): string {
    // Strip leading slash if present, then join
    const clean = relativePath.replace(/^\//, "");
    return `${WORKSPACE_PATH}/${clean}`;
  }
}
