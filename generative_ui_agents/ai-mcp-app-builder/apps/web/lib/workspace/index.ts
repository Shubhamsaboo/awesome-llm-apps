import { E2BWorkspaceProvider } from "./e2b";
import type { WorkspaceProvider } from "./types";

let _provider: WorkspaceProvider | null = null;

/** Returns a singleton WorkspaceProvider for the current process. */
export function getProvider(): WorkspaceProvider {
  if (!_provider) {
    _provider = new E2BWorkspaceProvider();
  }
  return _provider;
}

export type {
  WorkspaceProvider,
  WorkspaceInfo,
  ExecOpts,
  ExecResult,
} from "./types";
