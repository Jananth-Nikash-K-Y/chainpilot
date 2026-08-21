"""Top-level API router aggregation point.

Includes all domain sub-routers under the /api prefix.
"""
from fastapi import APIRouter

from app.api.routes import ai, health, inventory, logistics, operations, warehouse

api_router = APIRouter()
api_router.include_router(warehouse.router)
api_router.include_router(logistics.router)
api_router.include_router(inventory.router)
api_router.include_router(operations.router)
api_router.include_router(health.router)
api_router.include_router(ai.router)
