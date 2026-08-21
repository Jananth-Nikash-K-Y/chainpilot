"""Top-level API router aggregation point.

Future versioned routers (e.g. api/v1/*) will be included here.
Intentionally empty — no endpoints beyond /health exist yet.
"""
from fastapi import APIRouter

api_router = APIRouter()
