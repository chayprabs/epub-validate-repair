import { readFile } from "node:fs/promises";
import path from "node:path";

import { NextResponse } from "next/server";

const allowedSamples = new Set([
  "broken-manifest.epub",
  "drm-protected.epub",
  "kdp-ready.epub",
  "volume-1.epub",
  "volume-2.epub",
  "invalid-xhtml.epub"
]);

export async function GET(
  _request: Request,
  context: { params: Promise<{ name: string }> }
) {
  const { name } = await context.params;
  if (!allowedSamples.has(name)) {
    return NextResponse.json({ error: "Sample not found." }, { status: 404 });
  }

  const fixturePath = path.resolve(process.cwd(), "..", "..", "tests", "fixtures", name);
  const payload = await readFile(fixturePath);
  return new NextResponse(payload, {
    headers: {
      "Content-Type": "application/epub+zip",
      "Content-Disposition": `inline; filename="${name}"`,
      "Cache-Control": "no-store"
    }
  });
}
