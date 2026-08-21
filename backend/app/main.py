"""ChainPilot backend entry point.

Wires together the FastAPI app. Business logic must never live in route
handlers — routes call services, services call domain/repositories, and
repositories talk to the database. See ARCHITECTURE.md at the repo root.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.database import Base, engine

# Import all models so SQLAlchemy metadata is populated
import app.models.models  # noqa: F401

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables on startup (dev convenience). Use Alembic for prod."""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="ChainPilot API",
    description="Agentic AI Supply Chain Control Tower — backend API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow the frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all API routes under /api
app.include_router(api_router, prefix="/api")


@app.get("/health")
def health_check() -> dict:
    """Basic liveness check. Expand later with dependency checks."""
    return {"status": "ok", "service": "chainpilot-backend", "env": settings.app_env}
