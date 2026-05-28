from contextlib import asynccontextmanager

from fastapi import FastAPI

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


app = FastAPI(title="EpubDoctor Worker", version="0.1.0", lifespan=lifespan)
app.include_router(artifacts_router)
app.include_router(batch_router)
app.include_router(convert_router)
app.include_router(diff_router)
app.include_router(health_router)
app.include_router(metadata_router)
app.include_router(repair_router)
app.include_router(unpack_router)
app.include_router(validate_router)
