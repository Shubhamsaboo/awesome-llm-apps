import { NextRequest, NextResponse } from "next/server";
import { getProvider } from "@/lib/workspace";

export async function POST(req: NextRequest) {
  try {
    const { workspaceId, path } = (await req.json()) as {
      workspaceId?: string;
      path?: string;
    };
    if (!workspaceId || !path) {
      return NextResponse.json(
        { error: "workspaceId and path are required" },
        { status: 400 },
      );
    }

    const provider = getProvider();
    const content = await provider.readFile(workspaceId, path);
    return NextResponse.json({ content });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    console.error("[workspace/read-file]", message);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
