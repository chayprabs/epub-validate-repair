from fastapi import FastAPI

from src.routes.artifacts import router as artifacts_router
from src.routes.health import router as health_router
from src.routes.validate import router as validate_router


app = FastAPI(title="EpubDoctor Worker", version="0.1.0")
app.include_router(artifacts_router)
app.include_router(health_router)
app.include_router(validate_router)
