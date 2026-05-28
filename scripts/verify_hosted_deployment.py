from __future__ import annotations

import argparse
import json
import mimetypes
import ssl
import time
import uuid
from pathlib import Path
from urllib import error, parse, request

REPO_URL = "https://github.com/chayprabs/epub-validate-repair"
SEO_ROUTES = [
    "/epub-validator-online",
    "/epub-to-mobi",
    "/mobi-to-epub",
    "/epub-metadata-editor",
    "/epub-cover-replace",
    "/kdp-epub-check",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify a hosted EpubDoctor deployment.")
    parser.add_argument("--base-url", required=True, help="Public base URL for the deployed app.")
    parser.add_argument(
        "--fixtures-root",
        default=str(Path("tests/fixtures")),
        help="Fixture directory used for hosted validation checks.",
    )
    parser.add_argument(
        "--allow-http",
        action="store_true",
        help="Allow a non-HTTPS base URL for local dry runs.",
    )
    parser.add_argument(
        "--allow-degraded-health",
        action="store_true",
        help="Allow /api/worker/health to report missing runtime dependencies during local dry runs.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=60.0,
        help="Request timeout used for all hosted checks.",
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=4,
        help="Retry count for transient network errors.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base_url = args.base_url.rstrip("/")

    if not args.allow_http and not base_url.startswith("https://"):
        raise SystemExit("Hosted verification requires an https:// base URL.")

    fixtures_root = Path(args.fixtures_root)
    broken_fixture = fixtures_root / "broken-manifest.epub"
    clean_fixture = fixtures_root / "kdp-ready.epub"

    require(broken_fixture.exists(), f"Missing fixture: {broken_fixture}")
    require(clean_fixture.exists(), f"Missing fixture: {clean_fixture}")

    context = ssl.create_default_context()
    timeout = args.timeout_seconds

    homepage = fetch_text(f"{base_url}/", timeout, context, args.max_attempts)
    require("EpubDoctor" in homepage["body"], "Homepage should mention EpubDoctor.")
    require(REPO_URL in homepage["body"], "Homepage should include a direct source link.")

    robots = fetch_text(f"{base_url}/robots.txt", timeout, context, args.max_attempts)
    require("Sitemap:" in robots["body"], "robots.txt should publish the sitemap.")

    sitemap = fetch_text(f"{base_url}/sitemap.xml", timeout, context, args.max_attempts)
    require("<urlset" in sitemap["body"], "sitemap.xml should be XML.")

    checked_routes: dict[str, int] = {}
    for route in SEO_ROUTES:
        response = fetch_text(f"{base_url}{route}", timeout, context, args.max_attempts)
        require("EpubDoctor" in response["body"], f"{route} should render the product page.")
        checked_routes[route] = response["status"]

    health = fetch_json(f"{base_url}/api/worker/health", timeout, context, args.max_attempts)
    require(health["status"] == 200, "/api/worker/health should return 200.")
    require(health["body"].get("status") == "ok", "Worker proxy health payload should be ok.")
    runtime = health["body"].get("runtime") or {}
    if not args.allow_degraded_health:
        require(runtime.get("javaReady") is True, "Worker runtime should report javaReady=true.")
        require(runtime.get("calibreReady") is True, "Worker runtime should report calibreReady=true.")
        require(runtime.get("epubcheckReady") is True, "Worker runtime should report epubcheckReady=true.")

    broken_validation = post_fixture(
        f"{base_url}/api/worker/v1/validate",
        broken_fixture,
        timeout,
        context,
        args.max_attempts,
    )
    require(broken_validation["status"] == 200, "Hosted validation should accept broken-manifest.epub.")
    require(broken_validation["body"].get("counts", {}).get("error") == 4, "broken-manifest should report 4 errors.")
    require(broken_validation["body"].get("pass") is False, "broken-manifest should not pass validation.")

    artifacts = broken_validation["body"].get("artifacts") or {}
    html_url = artifacts.get("htmlUrl", "")
    json_url = artifacts.get("jsonUrl", "")
    require(
        is_public_proxy_artifact_url(html_url, base_url),
        "Hosted validation should emit public HTML artifact URLs.",
    )
    require(
        is_public_proxy_artifact_url(json_url, base_url),
        "Hosted validation should emit public JSON artifact URLs.",
    )
    report_html = fetch_text(html_url, timeout, context, args.max_attempts)
    require("EpubDoctor Validation Report" in report_html["body"], "HTML report should render the validation report.")

    clean_validation = post_fixture(
        f"{base_url}/api/worker/v1/validate",
        clean_fixture,
        timeout,
        context,
        args.max_attempts,
    )
    require(clean_validation["status"] == 200, "Hosted validation should accept kdp-ready.epub.")
    require(clean_validation["body"].get("counts", {}).get("error") == 0, "kdp-ready should report 0 errors.")
    require(clean_validation["body"].get("pass") is True, "kdp-ready should pass validation.")

    summary = {
        "baseUrl": base_url,
        "homepage": homepage["status"],
        "seoRoutes": checked_routes,
        "workerHealth": runtime,
        "brokenManifest": {
            "errors": broken_validation["body"]["counts"]["error"],
            "htmlUrl": html_url,
            "jsonUrl": json_url,
        },
        "kdpReady": {
            "errors": clean_validation["body"]["counts"]["error"],
            "pass": clean_validation["body"]["pass"],
        },
    }
    print(f"hosted verification: {json.dumps(summary, ensure_ascii=True)}")


def fetch_text(url: str, timeout: float, context: ssl.SSLContext, max_attempts: int) -> dict[str, object]:
    response = send_request(request.Request(url), timeout, context, max_attempts)
    body = response["body_bytes"].decode("utf-8")
    return {"status": response["status"], "body": body, "headers": response["headers"]}


def fetch_json(url: str, timeout: float, context: ssl.SSLContext, max_attempts: int) -> dict[str, object]:
    response = send_request(
        request.Request(
            url,
            headers={
                "Accept": "application/json",
            },
        ),
        timeout,
        context,
        max_attempts,
    )
    body = json.loads(response["body_bytes"].decode("utf-8"))
    return {"status": response["status"], "body": body, "headers": response["headers"]}


def post_fixture(
    url: str,
    fixture_path: Path,
    timeout: float,
    context: ssl.SSLContext,
    max_attempts: int,
) -> dict[str, object]:
    boundary = f"----EpubDoctorBoundary{uuid.uuid4().hex}"
    content_type = mimetypes.guess_type(str(fixture_path))[0] or "application/octet-stream"
    body = build_multipart_body(
        boundary=boundary,
        field_name="file",
        filename=fixture_path.name,
        content_type=content_type,
        payload=fixture_path.read_bytes(),
    )
    response = send_request(
        request.Request(
            url,
            method="POST",
            data=body,
            headers={
                "Accept": "application/json",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
        ),
        timeout,
        context,
        max_attempts,
    )
    payload = json.loads(response["body_bytes"].decode("utf-8"))
    return {"status": response["status"], "body": payload, "headers": response["headers"]}


def build_multipart_body(
    *,
    boundary: str,
    field_name: str,
    filename: str,
    content_type: str,
    payload: bytes,
) -> bytes:
    lines = [
        f"--{boundary}".encode("ascii"),
        f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"'.encode("utf-8"),
        f"Content-Type: {content_type}".encode("ascii"),
        b"",
        payload,
        f"--{boundary}--".encode("ascii"),
        b"",
    ]
    return b"\r\n".join(lines)


def send_request(
    req: request.Request,
    timeout: float,
    context: ssl.SSLContext,
    max_attempts: int,
) -> dict[str, object]:
    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            with request.urlopen(req, timeout=timeout, context=context) as response:
                return {
                    "status": response.status,
                    "headers": dict(response.headers.items()),
                    "body_bytes": response.read(),
                }
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise SystemExit(f"Request failed with HTTP {exc.code} for {req.full_url}: {body}") from exc
        except (ConnectionResetError, error.URLError) as exc:
            last_error = exc
            if attempt == max_attempts:
                break
            time.sleep(min(attempt, 5))

    raise SystemExit(f"Request failed for {req.full_url}: {last_error}")


def is_public_proxy_artifact_url(url: str, base_url: str) -> bool:
    parsed_url = parse.urlparse(url)
    parsed_base = parse.urlparse(base_url)
    return (
        parsed_url.scheme == parsed_base.scheme
        and bool(parsed_url.netloc)
        and parsed_url.path.startswith("/api/worker/v1/artifacts/")
    )


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


if __name__ == "__main__":
    main()
