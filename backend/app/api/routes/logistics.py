"""Logistics-related API routes: trucks, docks, parking, shipments."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.models import Dock, ParkingSlot, Shipment, Truck
from app.schemas.schemas import DockOut, ParkingSlotOut, ShipmentOut, TruckOut

router = APIRouter(tags=["logistics"])


# ── Trucks ──────────────────────────────────────────────────────────────────

@router.get("/trucks", response_model=list[TruckOut])
def list_trucks(db: Session = Depends(get_db)):
    trucks = db.query(Truck).options(joinedload(Truck.shipment)).all()
    results = []
    for t in trucks:
        d = TruckOut.model_validate(t)
        d.shipment_code = t.shipment.code if t.shipment else None
        results.append(d)
    return results


# ── Docks ───────────────────────────────────────────────────────────────────

@router.get("/docks", response_model=list[DockOut])
def list_docks(db: Session = Depends(get_db)):
    docks = (
        db.query(Dock)
        .options(joinedload(Dock.current_truck), joinedload(Dock.current_shipment))
        .order_by(Dock.position_index)
        .all()
    )
    results = []
    for d in docks:
        out = DockOut.model_validate(d)
        out.current_truck_code = d.current_truck.code if d.current_truck else None
        out.current_shipment_code = d.current_shipment.code if d.current_shipment else None
        results.append(out)
    return results


# ── Parking ─────────────────────────────────────────────────────────────────

@router.get("/parking-slots", response_model=list[ParkingSlotOut])
def list_parking_slots(db: Session = Depends(get_db)):
    return (
        db.query(ParkingSlot)
        .order_by(ParkingSlot.position_index)
        .all()
    )


# ── Shipments ───────────────────────────────────────────────────────────────

@router.get("/shipments", response_model=list[ShipmentOut])
def list_shipments(db: Session = Depends(get_db)):
    shipments = db.query(Shipment).options(joinedload(Shipment.supplier)).all()
    results = []
    for s in shipments:
        out = ShipmentOut.model_validate(s)
        out.supplier_name = s.supplier.name if s.supplier else None
        results.append(out)
    return results
