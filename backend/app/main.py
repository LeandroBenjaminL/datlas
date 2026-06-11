"""
Datlas API — Entry Point

FastAPI application that powers the Datlas data analysis platform.
Includes authentication, rate limiting, and configurable CORS.
"""

from contextlib import asynccontextmanager

from alembic.config import Config as AlembicConfig
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from alembic import command as alembic_command
from app.config import settings
from app.db.database import engine, init_db
from app.logging import logger
from app.middleware.auth import AuthMiddleware
from app.middleware.logging import RequestIDMiddleware
from app.routers import clean, explore, export, pipeline, upload


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    auth_status = "enabled" if settings.API_KEY else "disabled (dev mode)"
    logger.info(
        "datlas_api_starting",
        host=settings.API_HOST,
        port=settings.API_PORT,
        auth=auth_status,
        rate_limit=settings.RATE_LIMIT,
        max_upload_mb=settings.MAX_UPLOAD_SIZE_MB,
    )

    # Initialize database tables + run pending Alembic migrations
    try:
        init_db()
        logger.info("database_tables_ready")

        # Run pending migrations automatically (so column changes apply on Render deploy)
        alembic_cfg = AlembicConfig("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url_sync)
        alembic_command.upgrade(alembic_cfg, "head")
        logger.info("database_migrations_ok")
    except Exception as e:
        logger.warning("database_migration_skipped", error=str(e))

    yield
    logger.info("datlas_api_shutting_down")


app = FastAPI(
    title="Datlas API",
    description="Cargá datasets, limpiá, explorá, transformá. Datlas se encarga.",
    version="0.2.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "upload", "description": "Upload CSV files"},
        {"name": "clean", "description": "Data quality analysis and cleaning"},
        {"name": "explore", "description": "Exploratory data analysis"},
        {"name": "pipeline", "description": "Automated upload → clean → explore"},
        {"name": "export", "description": "Download files and list datasets"},
        {"name": "health", "description": "Health check"},
    ],
)

# ── Security: API Key scheme for Swagger ──
if settings.API_KEY:
    from fastapi.openapi.utils import get_openapi

    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        schema["components"]["securitySchemes"] = {
            "ApiKeyHeader": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "API key for protected endpoints. Empty in dev mode.",
            }
        }
        schema["security"] = [{"ApiKeyHeader": []}]
        app.openapi_schema = schema
        return app.openapi_schema

    app.openapi = custom_openapi

# ── Request ID / Logging ──
app.add_middleware(RequestIDMiddleware)

# ── Rate Limiting ──
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# ── Authentication ──
app.add_middleware(AuthMiddleware, api_key=settings.API_KEY)

# ── CORS ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["health"])
async def root():
    """Health check with database connectivity verification."""
    from sqlalchemy import text

    db_ok = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    return {
        "name": "Datlas API",
        "version": "0.2.0",
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
        "auth": "enabled" if settings.API_KEY else "disabled",
        "docs": "/docs",
    }


@app.get("/health", tags=["health"])
async def health():
    """Dedicated health endpoint (same as root)."""
    return await root()


app.include_router(upload.router)
app.include_router(clean.router)
app.include_router(explore.router)
app.include_router(export.router)
app.include_router(pipeline.router)


# ── Quick test ──
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
