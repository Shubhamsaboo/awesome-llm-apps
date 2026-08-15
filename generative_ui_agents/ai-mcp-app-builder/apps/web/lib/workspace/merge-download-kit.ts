import { createReadStream, existsSync } from "fs";
import fs from "fs/promises";
import os from "os";
import path from "path";
import type { Readable } from "stream";
import * as tar from "tar";

/** E2B prepareDownload produces a tarball whose top-level directory is `workspace`. */
const E2B_WORKSPACE_DIR = "workspace";
export const KIT_FOLDER_NAME = "mcp-apps-starter";

export function getBaseKitPath(): string | null {
  const p = path.join(process.cwd(), ".download-kit", "base.tar.gz");
  return existsSync(p) ? p : null;
}

/**
 * Unpacks the prebuilt base kit and the E2B workspace archive, replaces
 * `apps/mcp-use-server` with the sandbox tree, and returns a gzip tarball stream.
 * Caller should destroy the stream or wait for `close` so temp dirs can be removed.
 */
export async function mergeE2bWorkspaceIntoBaseKit(
  workspaceTarGz: Buffer,
  baseTarGzPath: string,
): Promise<Readable> {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), "mcp-kit-"));
  const workspaceArchive = path.join(tmp, "workspace.tar.gz");
  const baseExtract = path.join(tmp, "base");
  const wsExtract = path.join(tmp, "e2b");

  try {
    await fs.writeFile(workspaceArchive, workspaceTarGz);

    await fs.mkdir(baseExtract, { recursive: true });
    await tar.x({ file: baseTarGzPath, cwd: baseExtract });

    const kitPath = path.join(baseExtract, KIT_FOLDER_NAME);
    const stat = await fs.stat(kitPath).catch(() => null);
    if (!stat?.isDirectory()) {
      throw new Error(`Base kit missing ${KIT_FOLDER_NAME}/ at tarball root`);
    }

    await fs.mkdir(wsExtract, { recursive: true });
    await tar.x({ file: workspaceArchive, cwd: wsExtract });

    const wsPath = path.join(wsExtract, E2B_WORKSPACE_DIR);
    const wsStat = await fs.stat(wsPath).catch(() => null);
    if (!wsStat?.isDirectory()) {
      throw new Error(
        `E2B archive missing ${E2B_WORKSPACE_DIR}/ at tarball root`,
      );
    }

    const mcpDest = path.join(kitPath, "apps", "mcp-use-server");
    await fs.rm(mcpDest, { recursive: true, force: true });
    await fs.rename(wsPath, mcpDest);

    const outFile = path.join(tmp, "merged.tar.gz");
    await tar.c(
      { gzip: true, file: outFile, cwd: baseExtract, portable: true },
      [KIT_FOLDER_NAME],
    );

    const rs = createReadStream(outFile);
    rs.on("close", () => {
      void fs.rm(tmp, { recursive: true, force: true }).catch(() => {});
    });
    rs.on("error", () => {
      void fs.rm(tmp, { recursive: true, force: true }).catch(() => {});
    });

    return rs;
  } catch (e) {
    await fs.rm(tmp, { recursive: true, force: true }).catch(() => {});
    throw e;
  }
}
