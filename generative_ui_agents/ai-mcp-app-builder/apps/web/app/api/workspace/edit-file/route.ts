import { NextRequest, NextResponse } from "next/server";
import { getProvider } from "@/lib/workspace";

export async function POST(req: NextRequest) {
  try {
    const { workspaceId, path, search, replace } = (await req.json()) as {
      workspaceId?: string;
      path?: string;
      search?: string;
      replace?: string;
    };
    if (
      !workspaceId ||
      !path ||
      search === undefined ||
      replace === undefined
    ) {
      return NextResponse.json(
        { error: "workspaceId, path, search, and replace are required" },
        { status: 400 },
      );
    }

    const provider = getProvider();
    await provider.editFile(workspaceId, path, search, replace);
    return NextResponse.json({ ok: true });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    console.error("[workspace/edit-file]", message);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
