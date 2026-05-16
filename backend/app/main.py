"""
Datlas API — Entry Point

FastAPI application that powers the Datlas data analysis platform.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import clean, explore, export, pipeline, upload


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    print(f"🚀 Datlas API starting on http://{settings.API_HOST}:{settings.API_PORT}")
    print(f"📚 Docs at http://{settings.API_HOST}:{settings.API_PORT}/docs")
    yield
    print("👋 Datlas API shutting down")


app = FastAPI(
    title="Datlas API",
    description="Cargá datasets, limpiá, explorá, transformá. Datlas se encarga.",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS: permitir requests desde cualquier origen (desarrollo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check."""
    return {
        "name": "Datlas API",
        "version": "0.1.0",
        "status": "online",
        "docs": "/docs",
    }


app.include_router(upload.router)
app.include_router(clean.router)
app.include_router(explore.router)
app.include_router(export.router)
app.include_router(pipeline.router)


# ── Quick test ──
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
