from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
def healthcheck(request: Request) -> dict[str, object]:
    runtime_status = getattr(request.app.state, "runtime_status", None)
    return {
        "status": "ok",
        "runtime": {
            "javaReady": getattr(runtime_status, "java_ready", False),
            "calibreReady": getattr(runtime_status, "calibre_ready", False),
            "epubcheckReady": getattr(runtime_status, "epubcheck_ready", False),
            "message": getattr(runtime_status, "message", "runtime warm-up not run"),
        },
    }
