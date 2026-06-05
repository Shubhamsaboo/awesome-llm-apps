import { NextRequest, NextResponse } from "next/server";
import { writeFile, mkdir } from "fs/promises";
import { join } from "path";
import { tmpdir } from "os";

// NOTE: Python agent reads from the same tmpdir — only works when both processes run on the same host.
const UPLOAD_DIR = join(tmpdir(), "knowledge-explorer-uploads");

export async function POST(req: NextRequest) {
  const { files } = await req.json();
  await mkdir(UPLOAD_DIR, { recursive: true });

  const saved: { name: string; path: string }[] = [];
  for (const file of files) {
    const safeName = file.name.replace(/[^a-zA-Z0-9._-]/g, "_");
    const path = join(UPLOAD_DIR, `${Date.now()}-${safeName}`);
    await writeFile(path, file.content, "utf-8");
    saved.push({ name: file.name, path });
  }

  return NextResponse.json({ files: saved });
}
