import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.runtime import prewarm_runtime
from src.routes.artifacts import router as artifacts_router
from src.routes.batch import router as batch_router
from src.routes.convert import router as convert_router
from src.routes.diff import router as diff_router
from src.routes.health import router as health_router
from src.routes.metadata import router as metadata_router
from src.routes.repair import router as repair_router
from src.routes.unpack import router as unpack_router
from src.routes.validate import router as validate_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.runtime_status = prewarm_runtime()
    yield


def _load_cors_origins() -> list[str]:
    configured = os.getenv("EPUBDOCTOR_CORS_ORIGINS")
    if configured:
        return [origin.strip() for origin in configured.split(",") if origin.strip()]

    return [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3100",
        "http://127.0.0.1:3100",
        "http://localhost:3101",
        "http://127.0.0.1:3101",
    ]


app = FastAPI(title="EpubDoctor Worker", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_load_cors_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(artifacts_router)
app.include_router(batch_router)
app.include_router(convert_router)
app.include_router(diff_router)
app.include_router(health_router)
app.include_router(metadata_router)
app.include_router(repair_router)
app.include_router(unpack_router)
app.include_router(validate_router)
