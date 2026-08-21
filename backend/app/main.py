"""ChainPilot backend entry point.

Wires together the FastAPI app. Business logic must never live in route
handlers — routes call services, services call domain/repositories, and
repositories talk to the database. See ARCHITECTURE.md at the repo root.
"""
from fastapi import FastAPI

from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="ChainPilot API",
    description="Agentic AI Supply Chain Control Tower — backend API",
    version="0.1.0",
)


@app.get("/health")
def health_check() -> dict:
    """Basic liveness check. Expand later with dependency checks."""
    return {"status": "ok", "service": "chainpilot-backend", "env": settings.app_env}
