const proxyPrefixPath = "/api/worker";

export function resolveWorkerOrigin(): string {
  const configuredWorker =
    process.env.EPUBDOCTOR_WORKER_URL ??
    process.env.NEXT_PUBLIC_WORKER_URL ??
    "http://127.0.0.1:8000";

  return configuredWorker.includes("://") ? configuredWorker : `http://${configuredWorker}`;
}

export function rewriteWorkerPayload<T>(payload: T, workerOrigin: string, publicOrigin: string): T {
  return rewriteValue(payload, normalizeOrigin(workerOrigin), normalizeOrigin(publicOrigin)) as T;
}

export function resolvePublicOrigin(
  fallbackOrigin: string,
  forwardedProto: string | null,
  forwardedHost: string | null,
  host: string | null
): string {
  const protocol = forwardedProto || new URL(fallbackOrigin).protocol.replace(":", "");
  const hostname = forwardedHost || host;

  if (!hostname) {
    return normalizeOrigin(fallbackOrigin);
  }

  return `${protocol}://${hostname}`;
}

function rewriteValue(value: unknown, workerOrigin: string, publicOrigin: string): unknown {
  if (Array.isArray(value)) {
    return value.map((item) => rewriteValue(item, workerOrigin, publicOrigin));
  }

  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value).map(([key, nestedValue]) => [key, rewriteValue(nestedValue, workerOrigin, publicOrigin)])
    );
  }

  if (typeof value === "string") {
    return rewriteWorkerUrl(value, workerOrigin, publicOrigin);
  }

  return value;
}

function rewriteWorkerUrl(value: string, workerOrigin: string, publicOrigin: string): string {
  const publicProxyPrefix = `${publicOrigin}${proxyPrefixPath}`;

  if (value.startsWith(publicProxyPrefix)) {
    return value;
  }

  if (value.startsWith(proxyPrefixPath)) {
    return `${publicOrigin}${value}`;
  }

  if (value.startsWith("/v1/")) {
    return `${publicProxyPrefix}${value}`;
  }

  if (value.startsWith(workerOrigin)) {
    return `${publicProxyPrefix}${value.slice(workerOrigin.length)}`;
  }

  try {
    const parsed = new URL(value);

    if (normalizeOrigin(parsed.origin) === workerOrigin && parsed.pathname.startsWith("/v1/")) {
      return `${publicProxyPrefix}${parsed.pathname}${parsed.search}`;
    }
  } catch {
    return value;
  }

  return value;
}

function normalizeOrigin(value: string): string {
  return value.replace(/\/$/, "");
}
