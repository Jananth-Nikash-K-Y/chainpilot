"""Pydantic v2 response schemas for all ChainPilot domain entities."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Shared
# ---------------------------------------------------------------------------

class _ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Warehouse
# ---------------------------------------------------------------------------

class WarehouseOut(_ORMBase):
    id: int
    name: str
    code: str
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    total_area_sqm: Optional[float] = None
    utilization_pct: float


class AisleOut(_ORMBase):
    id: int
    warehouse_id: int
    code: str
    zone: Optional[str] = None
    capacity_pct: float
    occupied_pct: float
    active_pick_tasks: int
    replenishment_tasks: int
    risk: str
    position_x: float
    position_z: float


class BayOut(_ORMBase):
    id: int
    aisle_id: int
    code: str
    level: int
    capacity: int
    current_quantity: int
    sku: Optional[str] = None
    stock_status: str
    last_movement: Optional[datetime] = None
    replenishment_required: bool
    position_index: int


# ---------------------------------------------------------------------------
# Dock
# ---------------------------------------------------------------------------

class DockOut(_ORMBase):
    id: int
    warehouse_id: int
    code: str
    status: str
    current_truck_id: Optional[int] = None
    current_shipment_id: Optional[int] = None
    activity: Optional[str] = None
    occupancy_start: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    position_index: int
    # Denormalized for convenience
    current_truck_code: Optional[str] = None
    current_shipment_code: Optional[str] = None


# ---------------------------------------------------------------------------
# Parking
# ---------------------------------------------------------------------------

class ParkingSlotOut(_ORMBase):
    id: int
    warehouse_id: int
    code: str
    status: str
    vehicle_id: Optional[str] = None
    arrival_time: Optional[datetime] = None
    expected_departure: Optional[datetime] = None
    assigned_dock: Optional[str] = None
    position_index: int


# ---------------------------------------------------------------------------
# Supplier
# ---------------------------------------------------------------------------

class SupplierOut(_ORMBase):
    id: int
    name: str
    code: str
    location: Optional[str] = None
    reliability_score: float
    risk: str
    active: bool


# ---------------------------------------------------------------------------
# Truck
# ---------------------------------------------------------------------------

class TruckOut(_ORMBase):
    id: int
    code: str
    carrier: str
    status: str
    dock_code: Optional[str] = None
    shipment_id: Optional[int] = None
    eta: Optional[datetime] = None
    load_pct: float
    destination: Optional[str] = None
    risk: str
    position_x: float
    position_y: float
    position_z: float
    rotation_y: float
    # Denormalized
    shipment_code: Optional[str] = None


# ---------------------------------------------------------------------------
# Shipment
# ---------------------------------------------------------------------------

class ShipmentOut(_ORMBase):
    id: int
    code: str
    supplier_id: Optional[int] = None
    direction: str
    status: str
    origin: Optional[str] = None
    destination: Optional[str] = None
    eta: Optional[datetime] = None
    actual_arrival: Optional[datetime] = None
    dock_code: Optional[str] = None
    sku_count: int
    weight_kg: float
    delay_hours: float
    risk: str
    supplier_name: Optional[str] = None


# ---------------------------------------------------------------------------
# Pallet
# ---------------------------------------------------------------------------

class PalletOut(_ORMBase):
    id: int
    code: str
    bay_id: Optional[int] = None
    sku: Optional[str] = None
    quantity: int
    max_quantity: int
    stock_status: str
    condition: str
    position_x: float
    position_y: float
    position_z: float
    bay_code: Optional[str] = None


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------

class InventoryItemOut(_ORMBase):
    id: int
    sku: str
    name: str
    category: Optional[str] = None
    bay_code: Optional[str] = None
    quantity_on_hand: int
    quantity_reserved: int
    quantity_available: int
    reorder_point: int
    max_quantity: int
    stock_status: str
    days_of_coverage: float
    supplier_id: Optional[int] = None
    last_received: Optional[datetime] = None
    last_picked: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Forklift
# ---------------------------------------------------------------------------

class ForkliftOut(_ORMBase):
    id: int
    warehouse_id: int
    code: str
    activity: str
    operator: Optional[str] = None
    current_aisle: Optional[str] = None
    battery_pct: float
    position_x: float
    position_y: float
    position_z: float


# ---------------------------------------------------------------------------
# Customer Order
# ---------------------------------------------------------------------------

class CustomerOrderOut(_ORMBase):
    id: int
    code: str
    customer_name: str
    status: str
    priority: str
    total_items: int
    total_value: float
    currency: str
    promised_date: Optional[datetime] = None
    shipment_id: Optional[int] = None
    risk: str


# ---------------------------------------------------------------------------
# Operational Event
# ---------------------------------------------------------------------------

class OperationalEventOut(_ORMBase):
    id: int
    event_type: str
    entity_type: str
    entity_code: str
    message: str
    severity: str
    timestamp: datetime
    metadata_json: Optional[str] = None


# ---------------------------------------------------------------------------
# Exception
# ---------------------------------------------------------------------------

class ExceptionOut(_ORMBase):
    id: int
    code: str
    category: str
    severity: str
    title: str
    description: str
    entity_type: str
    entity_code: str
    affected_sku: Optional[str] = None
    affected_orders: int
    potential_impact: float
    impact_currency: str
    inventory_coverage_days: Optional[float] = None
    delay_hours: float
    recommendation: Optional[str] = None
    resolved: bool
    position_x: float
    position_y: float
    position_z: float
    created_at: datetime


# ---------------------------------------------------------------------------
# Health summary (derived)
# ---------------------------------------------------------------------------

class HealthSummary(BaseModel):
    supply_chain_health: int
    critical_exceptions: int
    delayed_shipments: int
    inventory_risks: int
    dock_utilization_pct: float
    warehouse_utilization_pct: float
    orders_at_risk: int
    total_trucks: int
    active_forklifts: int


# ---------------------------------------------------------------------------
# AI query
# ---------------------------------------------------------------------------

class AIQueryRequest(BaseModel):
    query: str


class AIQueryResponse(BaseModel):
    query: str
    response: str
    suggestions: list[str] = []
