from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from uuid import uuid4

import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

from config import DEFAULT_AUTH_SECRET, get_settings
from db import init_db
from routers import auth, cars, ops, web


logger = logging.getLogger("carsharing")


def configure_logging() -> None:
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def validate_runtime_settings() -> None:
    settings = get_settings()
    if settings.environment == "production" and settings.auth_secret == DEFAULT_AUTH_SECRET:
        raise RuntimeError("AUTH_SECRET must be set before starting in production.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    validate_runtime_settings()
    init_db()
    logger.info("Application startup complete.")
    yield
    logger.info("Application shutdown complete.")


def create_application() -> FastAPI:
    settings = get_settings()
    docs_url = "/docs" if settings.docs_enabled else None
    redoc_url = "/redoc" if settings.docs_enabled else None
    openapi_url = "/openapi.json" if settings.docs_enabled else None

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
    )

    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=list(settings.trusted_hosts),
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.allowed_origins),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1024)

    app.include_router(cars.router)
    app.include_router(web.router)
    app.include_router(auth.router)
    app.include_router(ops.router)

    @app.middleware("http")
    async def add_request_context(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        request.state.request_id = request_id
        started_at = time.perf_counter()

        response = await call_next(request)

        process_time = time.perf_counter() - started_at
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.6f}"
        logger.info(
            "%s %s -> %s in %.4fs",
            request.method,
            request.url.path,
            response.status_code,
            process_time,
        )
        return response

    @app.exception_handler(Exception)
    async def unexpected_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception on %s", request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Internal server error",
                "request_id": getattr(request.state, "request_id", None),
            },
        )

    return app


app = create_application()


if __name__ == "__main__":
    uvicorn.run(
        "carsharing:app",
        host="0.0.0.0",
        port=8000,
        reload=get_settings().debug,
    )
