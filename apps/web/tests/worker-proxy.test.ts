import { describe, expect, it } from "vitest";

import { resolvePublicOrigin, rewriteWorkerPayload } from "../lib/worker-proxy";

describe("worker proxy rewriting", () => {
  it("rewrites worker artifact URLs to the public proxy origin", () => {
    const payload = {
      artifacts: {
        htmlUrl: "http://epubdoctor-worker:8000/v1/artifacts/job-123/report.html",
        jsonUrl: "http://epubdoctor-worker:8000/v1/artifacts/job-123/report.json"
      },
      conversion: {
        artifactUrl: "/v1/artifacts/job-456/converted.mobi"
      },
      batch: {
        csvUrl: "http://epubdoctor-worker:8000/v1/artifacts/job-789/batch-report.csv",
        repairedZipUrl: "http://epubdoctor-worker:8000/v1/artifacts/job-789/batch-repaired.zip"
      },
      externalUrl: "https://github.com/chayprabs/epub-validate-repair"
    };

    const result = rewriteWorkerPayload(payload, "http://epubdoctor-worker:8000", "https://epubdoctor.example");

    expect(result.artifacts.htmlUrl).toBe("https://epubdoctor.example/api/worker/v1/artifacts/job-123/report.html");
    expect(result.artifacts.jsonUrl).toBe("https://epubdoctor.example/api/worker/v1/artifacts/job-123/report.json");
    expect(result.conversion.artifactUrl).toBe("https://epubdoctor.example/api/worker/v1/artifacts/job-456/converted.mobi");
    expect(result.batch.csvUrl).toBe("https://epubdoctor.example/api/worker/v1/artifacts/job-789/batch-report.csv");
    expect(result.batch.repairedZipUrl).toBe(
      "https://epubdoctor.example/api/worker/v1/artifacts/job-789/batch-repaired.zip"
    );
    expect(result.externalUrl).toBe("https://github.com/chayprabs/epub-validate-repair");
  });

  it("prefers forwarded host headers for the public origin", () => {
    expect(
      resolvePublicOrigin("http://localhost:3101", "https", "books.example.com", "localhost:3101")
    ).toBe("https://books.example.com");
  });
});
