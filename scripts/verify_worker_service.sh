#!/usr/bin/env bash
set -euo pipefail

container_name="${1:-epubdoctor-worker-smoke}"
host_port="${2:-18000}"

cleanup() {
  docker rm -f "${container_name}" >/dev/null 2>&1 || true
}

trap cleanup EXIT

docker run -d --name "${container_name}" -p "${host_port}:8000" epubdoctor-worker:ci >/dev/null

deadline=$((SECONDS + 45))
health_json=""
while [ "${SECONDS}" -lt "${deadline}" ]; do
  if health_json=$(curl -fsS "http://127.0.0.1:${host_port}/health"); then
    break
  fi
  sleep 1
done

if [ -z "${health_json}" ]; then
  echo "worker service smoke: /health did not become ready"
  docker logs "${container_name}" || true
  exit 1
fi

python - <<'PY' "${health_json}"
import json
import sys

payload = json.loads(sys.argv[1])
runtime = payload.get("runtime", {})
assert payload.get("status") == "ok", payload
assert runtime.get("javaReady") is True, payload
assert runtime.get("calibreReady") is True, payload
assert runtime.get("epubcheckReady") is True, payload
assert "runtime warm-up" in runtime.get("message", ""), payload
print("worker health smoke:", json.dumps(payload))
PY

docker logs "${container_name}" 2>&1 | tail -n 20
