"""Warehouse-related API routes."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import Warehouse, WarehouseAisle, WarehouseBay
from app.schemas.schemas import AisleOut, BayOut, WarehouseOut

router = APIRouter(tags=["warehouse"])


@router.get("/warehouse", response_model=list[WarehouseOut])
def list_warehouses(db: Session = Depends(get_db)):
    return db.query(Warehouse).all()


@router.get("/aisles", response_model=list[AisleOut])
def list_aisles(warehouse_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(WarehouseAisle)
    if warehouse_id is not None:
        q = q.filter(WarehouseAisle.warehouse_id == warehouse_id)
    return q.order_by(WarehouseAisle.code).all()


@router.get("/bays", response_model=list[BayOut])
def list_bays(aisle_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(WarehouseBay)
    if aisle_id is not None:
        q = q.filter(WarehouseBay.aisle_id == aisle_id)
    return q.order_by(WarehouseBay.code).all()
