export interface WorkspaceInfo {
  workspaceId: string; // e2b: sandboxId
  endpoint: string; // MCP URL from sandbox.betaGetMcpUrl()
  status: "provisioning" | "running" | "stopped";
  path: string; // /home/user/workspace inside the sandbox
}

export interface ExecOpts {
  cwd?: string;
  background?: boolean;
  timeoutMs?: number;
}

export interface ExecResult {
  stdout: string;
  stderr: string;
  exitCode: number;
  background?: boolean; // true if the process was started in background (no exit code yet)
}

export interface WorkspaceProvider {
  provision(name: string): Promise<WorkspaceInfo>;
  getInfo(workspaceId: string): Promise<WorkspaceInfo>;
  stop(workspaceId: string): Promise<void>;

  readFile(workspaceId: string, path: string): Promise<string>;
  writeFile(workspaceId: string, path: string, content: string): Promise<void>;
  editFile(
    workspaceId: string,
    path: string,
    search: string,
    replace: string,
  ): Promise<void>;

  exec(workspaceId: string, cmd: string, opts?: ExecOpts): Promise<ExecResult>;
  prepareDownload(workspaceId: string): Promise<{ downloadUrl: string }>;
}
