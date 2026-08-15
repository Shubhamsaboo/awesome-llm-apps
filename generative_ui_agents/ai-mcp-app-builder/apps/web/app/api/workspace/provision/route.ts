import { NextRequest, NextResponse } from "next/server";
import { getProvider } from "@/lib/workspace";

export const maxDuration = 300;

export async function POST(req: NextRequest) {
  try {
    const { name } = (await req.json()) as { name?: string };
    if (!name) {
      return NextResponse.json({ error: "name is required" }, { status: 400 });
    }

    const provider = getProvider();
    const workspace = await provider.provision(name);
    return NextResponse.json(workspace);
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    console.error("[workspace/provision]", message);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
