import { NextRequest, NextResponse } from "next/server";
import { getProvider } from "@/lib/workspace";

export async function POST(req: NextRequest) {
  try {
    const { workspaceId, path, content } = (await req.json()) as {
      workspaceId?: string;
      path?: string;
      content?: string;
    };
    if (!workspaceId || !path || content === undefined) {
      return NextResponse.json(
        { error: "workspaceId, path, and content are required" },
        { status: 400 },
      );
    }

    const provider = getProvider();
    await provider.writeFile(workspaceId, path, content);
    return NextResponse.json({ ok: true });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    console.error("[workspace/write-file]", message);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
