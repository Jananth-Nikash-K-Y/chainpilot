"""Health endpoint — derived supply-chain health summary."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import (
    CustomerOrder,
    Dock,
    DockStatus,
    Exception_,
    ExceptionSeverity,
    Forklift,
    ForkliftActivity,
    InventoryItem,
    OrderStatus,
    Shipment,
    ShipmentStatus,
    StockStatus,
    Truck,
    Warehouse,
)
from app.schemas.schemas import HealthSummary

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthSummary)
def supply_chain_health(db: Session = Depends(get_db)):
    critical_exc = (
        db.query(Exception_)
        .filter(
            Exception_.resolved == False,  # noqa: E712
            Exception_.severity.in_([ExceptionSeverity.CRITICAL, ExceptionSeverity.HIGH]),
        )
        .count()
    )
    delayed_shipments = (
        db.query(Shipment).filter(Shipment.status == ShipmentStatus.DELAYED).count()
    )
    inv_risks = (
        db.query(InventoryItem)
        .filter(InventoryItem.stock_status.in_([StockStatus.LOW, StockStatus.CRITICAL]))
        .count()
    )
    total_docks = db.query(Dock).count()
    occupied_docks = (
        db.query(Dock)
        .filter(Dock.status.in_([DockStatus.OCCUPIED, DockStatus.LOADING, DockStatus.UNLOADING]))
        .count()
    )
    dock_util = round((occupied_docks / total_docks * 100) if total_docks else 0, 1)

    wh = db.query(Warehouse).first()
    wh_util = wh.utilization_pct if wh else 0

    orders_at_risk = (
        db.query(CustomerOrder)
        .filter(CustomerOrder.status == OrderStatus.AT_RISK)
        .count()
    )
    total_trucks = db.query(Truck).count()
    active_forklifts = (
        db.query(Forklift)
        .filter(Forklift.activity.in_([ForkliftActivity.MOVING, ForkliftActivity.PICKING, ForkliftActivity.REPLENISHING]))
        .count()
    )

    # Simple health score: 100 minus penalty for each problem
    health = max(0, min(100, 100 - critical_exc * 5 - delayed_shipments * 3 - inv_risks * 2 - orders_at_risk * 4))

    return HealthSummary(
        supply_chain_health=health,
        critical_exceptions=critical_exc,
        delayed_shipments=delayed_shipments,
        inventory_risks=inv_risks,
        dock_utilization_pct=dock_util,
        warehouse_utilization_pct=wh_util,
        orders_at_risk=orders_at_risk,
        total_trucks=total_trucks,
        active_forklifts=active_forklifts,
    )
