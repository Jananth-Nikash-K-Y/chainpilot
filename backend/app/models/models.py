"""ChainPilot domain models.

Every physical or logical entity that appears in the Digital Twin is
represented here as a SQLAlchemy ORM model backed by PostgreSQL.
"""
from __future__ import annotations

import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class TruckStatus(str, enum.Enum):
    ARRIVING = "ARRIVING"
    WAITING = "WAITING"
    AT_DOCK = "AT_DOCK"
    LOADING = "LOADING"
    UNLOADING = "UNLOADING"
    READY_TO_DEPART = "READY_TO_DEPART"
    DEPARTED = "DEPARTED"
    DELAYED = "DELAYED"


class DockStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    OCCUPIED = "OCCUPIED"
    LOADING = "LOADING"
    UNLOADING = "UNLOADING"
    RESERVED = "RESERVED"
    MAINTENANCE = "MAINTENANCE"


class ParkingSlotStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    OCCUPIED = "OCCUPIED"
    RESERVED = "RESERVED"
    WAITING = "WAITING"
    MAINTENANCE = "MAINTENANCE"


class StockStatus(str, enum.Enum):
    HEALTHY = "HEALTHY"
    LOW = "LOW"
    CRITICAL = "CRITICAL"
    BLOCKED = "BLOCKED"
    RESERVED = "RESERVED"
    REPLENISHMENT_REQUIRED = "REPLENISHMENT_REQUIRED"


class ForkliftActivity(str, enum.Enum):
    IDLE = "IDLE"
    MOVING = "MOVING"
    PICKING = "PICKING"
    DROPPING = "DROPPING"
    REPLENISHING = "REPLENISHING"
    CHARGING = "CHARGING"


class ShipmentDirection(str, enum.Enum):
    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"


class ShipmentStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    IN_TRANSIT = "IN_TRANSIT"
    AT_FACILITY = "AT_FACILITY"
    LOADING = "LOADING"
    UNLOADING = "UNLOADING"
    COMPLETED = "COMPLETED"
    DELAYED = "DELAYED"
    CANCELLED = "CANCELLED"


class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    PICKING = "PICKING"
    PACKED = "PACKED"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    AT_RISK = "AT_RISK"
    CANCELLED = "CANCELLED"


class EventType(str, enum.Enum):
    TRUCK_ARRIVED = "TRUCK_ARRIVED"
    TRUCK_DELAYED = "TRUCK_DELAYED"
    DOCK_ASSIGNED = "DOCK_ASSIGNED"
    DOCK_RELEASED = "DOCK_RELEASED"
    SHIPMENT_DELAYED = "SHIPMENT_DELAYED"
    INVENTORY_LOW = "INVENTORY_LOW"
    INVENTORY_REPLENISHED = "INVENTORY_REPLENISHED"
    FORKLIFT_MOVED = "FORKLIFT_MOVED"
    ORDER_AT_RISK = "ORDER_AT_RISK"
    SUPPLIER_DELAYED = "SUPPLIER_DELAYED"


class ExceptionSeverity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ExceptionCategory(str, enum.Enum):
    SHIPMENT_DELAY = "SHIPMENT_DELAY"
    DOCK_CONGESTION = "DOCK_CONGESTION"
    INVENTORY_RISK = "INVENTORY_RISK"
    SUPPLIER_RISK = "SUPPLIER_RISK"
    ORDER_AT_RISK = "ORDER_AT_RISK"
    EQUIPMENT_ISSUE = "EQUIPMENT_ISSUE"


class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ActionStatus(str, enum.Enum):
    """Lifecycle of an agent-proposed action.

    Nothing moves from PROPOSED to EXECUTED without passing through a human
    approval — see ARCHITECTURE.md §4.
    """

    PROPOSED = "PROPOSED"
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"


class ActionKind(str, enum.Enum):
    REROUTE_SHIPMENT = "REROUTE_SHIPMENT"
    REASSIGN_DOCK = "REASSIGN_DOCK"
    EXPEDITE_SHIPMENT = "EXPEDITE_SHIPMENT"
    RAISE_REPLENISHMENT = "RAISE_REPLENISHMENT"
    SPLIT_ORDER = "SPLIT_ORDER"
    CONTACT_SUPPLIER = "CONTACT_SUPPLIER"
    SCHEDULE_MAINTENANCE = "SCHEDULE_MAINTENANCE"
    RECHARGE_FORKLIFT = "RECHARGE_FORKLIFT"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class Warehouse(Base):
    __tablename__ = "warehouses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_area_sqm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    utilization_pct: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    aisles: Mapped[List["WarehouseAisle"]] = relationship(back_populates="warehouse", cascade="all, delete-orphan")
    docks: Mapped[List["Dock"]] = relationship(back_populates="warehouse", cascade="all, delete-orphan")
    parking_slots: Mapped[List["ParkingSlot"]] = relationship(back_populates="warehouse", cascade="all, delete-orphan")
    forklifts: Mapped[List["Forklift"]] = relationship(back_populates="warehouse", cascade="all, delete-orphan")


class WarehouseAisle(Base):
    __tablename__ = "warehouse_aisles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    zone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # RECEIVING, STORAGE, PICKING, DISPATCH
    capacity_pct: Mapped[float] = mapped_column(Float, default=0.0)
    occupied_pct: Mapped[float] = mapped_column(Float, default=0.0)
    active_pick_tasks: Mapped[int] = mapped_column(Integer, default=0)
    replenishment_tasks: Mapped[int] = mapped_column(Integer, default=0)
    risk: Mapped[str] = mapped_column(Enum(RiskLevel), default=RiskLevel.LOW)
    position_x: Mapped[float] = mapped_column(Float, default=0.0)
    position_z: Mapped[float] = mapped_column(Float, default=0.0)

    warehouse: Mapped["Warehouse"] = relationship(back_populates="aisles")
    bays: Mapped[List["WarehouseBay"]] = relationship(back_populates="aisle", cascade="all, delete-orphan")


class WarehouseBay(Base):
    __tablename__ = "warehouse_bays"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    aisle_id: Mapped[int] = mapped_column(ForeignKey("warehouse_aisles.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=1)  # rack level
    capacity: Mapped[int] = mapped_column(Integer, default=500)
    current_quantity: Mapped[int] = mapped_column(Integer, default=0)
    sku: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    stock_status: Mapped[str] = mapped_column(Enum(StockStatus), default=StockStatus.HEALTHY)
    last_movement: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    replenishment_required: Mapped[bool] = mapped_column(Boolean, default=False)
    position_index: Mapped[int] = mapped_column(Integer, default=0)  # position within aisle

    aisle: Mapped["WarehouseAisle"] = relationship(back_populates="bays")
    pallets: Mapped[List["Pallet"]] = relationship(back_populates="bay", cascade="all, delete-orphan")


class Dock(Base):
    __tablename__ = "docks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(Enum(DockStatus), default=DockStatus.AVAILABLE)
    current_truck_id: Mapped[Optional[int]] = mapped_column(ForeignKey("trucks.id"), nullable=True)
    current_shipment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("shipments.id"), nullable=True)
    activity: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    occupancy_start: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    estimated_completion: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    position_index: Mapped[int] = mapped_column(Integer, default=0)

    warehouse: Mapped["Warehouse"] = relationship(back_populates="docks")
    current_truck: Mapped[Optional["Truck"]] = relationship(foreign_keys=[current_truck_id])
    current_shipment: Mapped[Optional["Shipment"]] = relationship(foreign_keys=[current_shipment_id])


class ParkingSlot(Base):
    __tablename__ = "parking_slots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(Enum(ParkingSlotStatus), default=ParkingSlotStatus.AVAILABLE)
    vehicle_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    arrival_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expected_departure: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    assigned_dock: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    position_index: Mapped[int] = mapped_column(Integer, default=0)

    warehouse: Mapped["Warehouse"] = relationship(back_populates="parking_slots")


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    reliability_score: Mapped[float] = mapped_column(Float, default=95.0)
    risk: Mapped[str] = mapped_column(Enum(RiskLevel), default=RiskLevel.LOW)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    shipments: Mapped[List["Shipment"]] = relationship(back_populates="supplier")


class Truck(Base):
    __tablename__ = "trucks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    carrier: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(Enum(TruckStatus), default=TruckStatus.ARRIVING)
    dock_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    shipment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("shipments.id"), nullable=True)
    eta: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    load_pct: Mapped[float] = mapped_column(Float, default=0.0)
    destination: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    risk: Mapped[str] = mapped_column(Enum(RiskLevel), default=RiskLevel.LOW)
    position_x: Mapped[float] = mapped_column(Float, default=0.0)
    position_y: Mapped[float] = mapped_column(Float, default=0.0)
    position_z: Mapped[float] = mapped_column(Float, default=0.0)
    rotation_y: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    shipment: Mapped[Optional["Shipment"]] = relationship(foreign_keys=[shipment_id], back_populates="truck")


class Shipment(Base):
    __tablename__ = "shipments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    supplier_id: Mapped[Optional[int]] = mapped_column(ForeignKey("suppliers.id"), nullable=True)
    direction: Mapped[str] = mapped_column(Enum(ShipmentDirection), default=ShipmentDirection.INBOUND)
    status: Mapped[str] = mapped_column(Enum(ShipmentStatus), default=ShipmentStatus.SCHEDULED)
    origin: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    destination: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    eta: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    actual_arrival: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    dock_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    sku_count: Mapped[int] = mapped_column(Integer, default=0)
    weight_kg: Mapped[float] = mapped_column(Float, default=0.0)
    delay_hours: Mapped[float] = mapped_column(Float, default=0.0)
    risk: Mapped[str] = mapped_column(Enum(RiskLevel), default=RiskLevel.LOW)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    supplier: Mapped[Optional["Supplier"]] = relationship(back_populates="shipments")
    truck: Mapped[Optional["Truck"]] = relationship(foreign_keys=[Truck.shipment_id], back_populates="shipment")


class Pallet(Base):
    __tablename__ = "pallets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(30), nullable=False)
    bay_id: Mapped[Optional[int]] = mapped_column(ForeignKey("warehouse_bays.id"), nullable=True)
    sku: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    max_quantity: Mapped[int] = mapped_column(Integer, default=100)
    stock_status: Mapped[str] = mapped_column(Enum(StockStatus), default=StockStatus.HEALTHY)
    condition: Mapped[str] = mapped_column(String(50), default="GOOD")
    position_x: Mapped[float] = mapped_column(Float, default=0.0)
    position_y: Mapped[float] = mapped_column(Float, default=0.0)
    position_z: Mapped[float] = mapped_column(Float, default=0.0)

    bay: Mapped[Optional["WarehouseBay"]] = relationship(back_populates="pallets")


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sku: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bay_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    quantity_on_hand: Mapped[int] = mapped_column(Integer, default=0)
    quantity_reserved: Mapped[int] = mapped_column(Integer, default=0)
    quantity_available: Mapped[int] = mapped_column(Integer, default=0)
    reorder_point: Mapped[int] = mapped_column(Integer, default=50)
    max_quantity: Mapped[int] = mapped_column(Integer, default=500)
    stock_status: Mapped[str] = mapped_column(Enum(StockStatus), default=StockStatus.HEALTHY)
    days_of_coverage: Mapped[float] = mapped_column(Float, default=30.0)
    supplier_id: Mapped[Optional[int]] = mapped_column(ForeignKey("suppliers.id"), nullable=True)
    last_received: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_picked: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    supplier: Mapped[Optional["Supplier"]] = relationship()


class Forklift(Base):
    __tablename__ = "forklifts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    activity: Mapped[str] = mapped_column(Enum(ForkliftActivity), default=ForkliftActivity.IDLE)
    operator: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    current_aisle: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    battery_pct: Mapped[float] = mapped_column(Float, default=100.0)
    position_x: Mapped[float] = mapped_column(Float, default=0.0)
    position_y: Mapped[float] = mapped_column(Float, default=0.0)
    position_z: Mapped[float] = mapped_column(Float, default=0.0)

    warehouse: Mapped["Warehouse"] = relationship(back_populates="forklifts")


class CustomerOrder(Base):
    __tablename__ = "customer_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    customer_name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(Enum(OrderStatus), default=OrderStatus.PENDING)
    priority: Mapped[str] = mapped_column(String(20), default="NORMAL")
    total_items: Mapped[int] = mapped_column(Integer, default=0)
    total_value: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(10), default="INR")
    promised_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    shipment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("shipments.id"), nullable=True)
    risk: Mapped[str] = mapped_column(Enum(RiskLevel), default=RiskLevel.LOW)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    shipment: Mapped[Optional["Shipment"]] = relationship()


class OperationalEvent(Base):
    __tablename__ = "operational_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(Enum(EventType), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # TRUCK, DOCK, SHIPMENT, etc.
    entity_code: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(Enum(ExceptionSeverity), default=ExceptionSeverity.LOW)
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class AgentAction(Base):
    """An action an agent proposed, awaiting (or past) human approval."""

    __tablename__ = "agent_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    kind: Mapped[str] = mapped_column(Enum(ActionKind), nullable=False)
    status: Mapped[str] = mapped_column(Enum(ActionStatus), default=ActionStatus.PROPOSED)

    proposed_by: Mapped[str] = mapped_column(String(50), nullable=False)  # agent name
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)

    # What this action operates on
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_code: Mapped[str] = mapped_column(String(50), nullable=False)
    exception_code: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    # Projected effect, used by the UI to show the trade-off before approving
    projected_impact: Mapped[float] = mapped_column(Float, default=0.0)
    projected_savings: Mapped[float] = mapped_column(Float, default=0.0)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)  # 0..1

    validation_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    result_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class Exception_(Base):
    """Operational exception — named Exception_ to avoid shadowing builtins."""
    __tablename__ = "exceptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    category: Mapped[str] = mapped_column(Enum(ExceptionCategory), nullable=False)
    severity: Mapped[str] = mapped_column(Enum(ExceptionSeverity), default=ExceptionSeverity.MEDIUM)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_code: Mapped[str] = mapped_column(String(50), nullable=False)
    affected_sku: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    affected_orders: Mapped[int] = mapped_column(Integer, default=0)
    potential_impact: Mapped[float] = mapped_column(Float, default=0.0)
    impact_currency: Mapped[str] = mapped_column(String(10), default="INR")
    inventory_coverage_days: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    delay_hours: Mapped[float] = mapped_column(Float, default=0.0)
    recommendation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    position_x: Mapped[float] = mapped_column(Float, default=0.0)
    position_y: Mapped[float] = mapped_column(Float, default=2.0)
    position_z: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
