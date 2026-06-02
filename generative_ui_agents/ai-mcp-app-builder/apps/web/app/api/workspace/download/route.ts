import { NextRequest, NextResponse } from "next/server";
import { Readable } from "stream";
import { getProvider } from "@/lib/workspace";
import {
  getBaseKitPath,
  mergeE2bWorkspaceIntoBaseKit,
} from "@/lib/workspace/merge-download-kit";

/** E2B archive + signed URL can be slow; allow up to 5 min. */
export const maxDuration = 300;

type DownloadBody = {
  workspaceId?: string;
  /** When true, response is the .tar.gz bytes with Content-Disposition (no pop-up on client). */
  stream?: boolean;
  /**
   * When true (default), merge E2B `workspace/` into prebuilt `mcp-apps-starter` if
   * `.download-kit/base.tar.gz` exists (from `prebuild`). Set false for MCP-only tarball.
   */
  fullKit?: boolean;
};

export async function POST(req: NextRequest) {
  try {
    const body = (await req.json()) as DownloadBody;
    const { workspaceId, stream, fullKit = true } = body;
    if (!workspaceId) {
      return NextResponse.json(
        { error: "workspaceId is required" },
        { status: 400 },
      );
    }

    const provider = getProvider();
    const { downloadUrl } = await provider.prepareDownload(workspaceId);

    if (!stream) {
      return NextResponse.json({ downloadUrl });
    }

    const upstream = await fetch(downloadUrl, { redirect: "follow" });
    if (!upstream.ok) {
      const snippet = (await upstream.text().catch(() => "")).slice(0, 200);
      console.error(
        "[workspace/download] upstream fetch failed",
        upstream.status,
        snippet,
      );
      return NextResponse.json(
        { error: `Failed to fetch archive from storage (${upstream.status})` },
        { status: 502 },
      );
    }

    const safeId =
      workspaceId.replace(/[^\w-]/g, "").slice(0, 16) || "workspace";
    const basePath = getBaseKitPath();
    const archive = Buffer.from(await upstream.arrayBuffer());

    if (fullKit && basePath) {
      try {
        const nodeStream = await mergeE2bWorkspaceIntoBaseKit(
          archive,
          basePath,
        );
        const webStream = Readable.toWeb(nodeStream);
        return new NextResponse(webStream as unknown as BodyInit, {
          status: 200,
          headers: {
            "Content-Type": "application/gzip",
            "Content-Disposition": `attachment; filename="mcp-app-kit-${safeId}.tar.gz"`,
          },
        });
      } catch (mergeErr) {
        const msg =
          mergeErr instanceof Error ? mergeErr.message : String(mergeErr);
        console.error(
          "[workspace/download] full-kit merge failed, falling back to MCP-only",
          msg,
        );
      }
    } else if (fullKit && !basePath) {
      console.warn(
        "[workspace/download] fullKit requested but .download-kit/base.tar.gz missing — MCP-only",
      );
    }

    return new NextResponse(archive, {
      status: 200,
      headers: {
        "Content-Type": "application/gzip",
        "Content-Disposition": `attachment; filename="workspace-${safeId}.tar.gz"`,
      },
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    console.error("[workspace/download]", message);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
