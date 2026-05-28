import { NextRequest, NextResponse } from "next/server";
import { resolvePublicOrigin, resolveWorkerOrigin, rewriteWorkerPayload } from "../../../../lib/worker-proxy";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const workerOrigin = resolveWorkerOrigin();

async function proxyRequest(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> }
) {
  const { path } = await context.params;
  const upstreamUrl = new URL(`${workerOrigin.replace(/\/$/, "")}/${path.join("/")}`);
  upstreamUrl.search = request.nextUrl.search;

  const headers = new Headers(request.headers);
  headers.delete("connection");
  headers.delete("content-length");
  headers.delete("host");

  const body =
    request.method === "GET" || request.method === "HEAD"
      ? undefined
      : await request.arrayBuffer();

  const upstreamResponse = await fetch(upstreamUrl, {
    method: request.method,
    headers,
    body,
    redirect: "manual"
  });

  const responseHeaders = new Headers(upstreamResponse.headers);
  responseHeaders.set("Cache-Control", "no-store");
  responseHeaders.delete("content-length");

  if (responseHeaders.get("content-type")?.includes("application/json")) {
    const payload = await upstreamResponse.json();
    const publicOrigin = resolvePublicOrigin(
      request.nextUrl.origin,
      request.headers.get("x-forwarded-proto"),
      request.headers.get("x-forwarded-host"),
      request.headers.get("host")
    );
    const rewrittenPayload = rewriteWorkerPayload(payload, workerOrigin, publicOrigin);
    return new NextResponse(JSON.stringify(rewrittenPayload), {
      status: upstreamResponse.status,
      headers: responseHeaders
    });
  }

  return new NextResponse(upstreamResponse.body, {
    status: upstreamResponse.status,
    headers: responseHeaders
  });
}

export async function GET(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> }
) {
  return proxyRequest(request, context);
}

export async function POST(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> }
) {
  return proxyRequest(request, context);
}
