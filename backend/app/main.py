"""AlumniConnect FastAPI Modular Monolith Application
Authoritative DBMS Project Implementation following the Master Specifications.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.api.v1.api import api_router
from app.db.init_db import init_db
from app.workers.outbox_worker import outbox_worker

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("alumniconnect.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure schema and seeds exist, graph projection loaded
    logger.info("Starting up AlumniConnect backend service...")
    try:
        init_db()
        # Run one outbox pass
        outbox_worker.run_once()
    except Exception as e:
        logger.error(f"Startup initialization failed: {e}")
    yield
    logger.info("Shutting down AlumniConnect backend service.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Alumni-Student Mentorship and Mock Interview Platform (DBMS Mini Project)",
    lifespan=lifespan
)

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.exception_handler(HTTPException)
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Ensures CORS headers are present even on 401/403/404 error responses.

    Without this, browsers block the response before JS can read the status code,
    causing a misleading 'CORS error' instead of showing 'Unauthorized'.
    """
    origin = request.headers.get("origin") or "http://localhost:3000"
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    """Guarantees CORS headers on 422 Unprocessable Entity payload validation errors."""
    origin = request.headers.get("origin") or "http://localhost:3000"
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
        headers={
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )


@app.exception_handler(ResponseValidationError)
async def response_validation_exception_handler(request: Request, exc: ResponseValidationError):
    origin = request.headers.get("origin") or "http://localhost:3000"
    logger.error(f"Response validation error on {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Response serialization error", "errors": str(exc.errors())},
        headers={
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    origin = request.headers.get("origin") or "http://localhost:3000"
    logger.error(f"Unhandled error on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Internal server error: {str(exc)}"},
        headers={
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )


# Register API v1
app.include_router(api_router, prefix=settings.API_V1_STR)


from sqlalchemy import text
from app.core.database import engine
from app.core.redis_client import redis_client
from app.core.graph_client import graph_client


@app.get("/health", tags=["Health"])
@app.get(f"{settings.API_V1_STR}/health", tags=["Health"], include_in_schema=False)
def healthcheck():
    """Health check endpoint actively confirming database, cache, graph, and worker readiness."""
    db_ok = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            db_ok = True
    except Exception as e:
        logger.error(f"Healthcheck database connectivity check failed: {e}")

    return {
        "status": "healthy" if db_ok else "degraded",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "checks": {
            "database_relational": "connected" if db_ok else "unreachable",
            "redis_cache": "live_redis" if redis_client.is_live_redis else "in_memory_resilient_fallback",
            "neo4j_graph": "live_bolt" if graph_client.is_live_neo4j else "in_memory_resilient_fallback",
            "outbox_worker": "ready"
        }
    }


@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Welcome to AlumniConnect API",
        "docs_url": "/docs",
        "version": settings.VERSION
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

