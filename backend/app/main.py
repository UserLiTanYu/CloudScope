from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.metrics import router as metrics_router
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title="CloudScope API", version="0.1.0")
    app.include_router(health_router, prefix="/api")
    app.include_router(metrics_router, prefix="/api")
    return app


app = create_app()
