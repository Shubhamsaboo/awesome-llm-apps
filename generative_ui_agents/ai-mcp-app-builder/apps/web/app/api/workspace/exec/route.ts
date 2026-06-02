import { NextRequest, NextResponse } from "next/server";
import { getProvider } from "@/lib/workspace";

export async function POST(req: NextRequest) {
  try {
    const { workspaceId, cmd, background, cwd, timeoutMs } =
      (await req.json()) as {
        workspaceId?: string;
        cmd?: string;
        background?: boolean;
        cwd?: string;
        timeoutMs?: number;
      };
    if (!workspaceId || !cmd) {
      return NextResponse.json(
        { error: "workspaceId and cmd are required" },
        { status: 400 },
      );
    }

    const provider = getProvider();
    const result = await provider.exec(workspaceId, cmd, {
      background,
      cwd,
      timeoutMs,
    });
    return NextResponse.json(result);
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    console.error("[workspace/exec]", message);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
