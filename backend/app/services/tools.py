"""Operational tools — the only way agents touch data.

Every function here is a *tool*: a named, documented, side-effect-explicit
operation over live operational state. Agents never issue queries themselves;
they call these. The MCP server in ``mcp/`` wraps this same registry so
external agent runtimes get an identical surface.

Read tools are safe to call freely. Write tools (``execute_action``) are only
reachable after a human approves the action — see ARCHITECTURE.md §4.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable

from sqlalchemy.orm import Session

from app.models.models import (
    ActionKind,
    ActionStatus,
    AgentAction,
    CustomerOrder,
    Dock,
    DockStatus,
    EventType,
    Exception_,
    ExceptionSeverity,
    Forklift,
    InventoryItem,
    OperationalEvent,
    OrderStatus,
    Shipment,
    ShipmentStatus,
    StockStatus,
    Supplier,
    Truck,
    TruckStatus,
    Warehouse,
)


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _v(value: Any) -> Any:
    """Normalise an Enum column to its plain string value.

    SQLAlchemy hands back Enum members, and ``str(member)`` renders as
    ``"ExceptionSeverity.CRITICAL"`` rather than ``"CRITICAL"`` — which then
    fails every downstream comparison. Always pass enum-backed columns
    through here before returning them from a tool.
    """
    return value.value if isinstance(value, Enum) else value


# ── Tool registry ─────────────────────────────────────────────────────────

@dataclass
class ToolSpec:
    name: str
    description: str
    fn: Callable[..., Any]
    writes: bool = False


TOOLS: dict[str, ToolSpec] = {}


def tool(name: str, description: str, *, writes: bool = False):
    """Register a function as an agent-callable tool."""

    def wrap(fn: Callable[..., Any]) -> Callable[..., Any]:
        TOOLS[name] = ToolSpec(name=name, description=description, fn=fn, writes=writes)
        return fn

    return wrap


@dataclass
class ToolCall:
    """One tool invocation, recorded so the UI can show the agent's work."""

    tool: str
    args: dict[str, Any] = field(default_factory=dict)
    result_summary: str = ""


# ── Read tools ────────────────────────────────────────────────────────────

@tool("get_delayed_shipments", "Shipments currently delayed, worst first.")
def get_delayed_shipments(db: Session, limit: int = 10) -> list[dict]:
    rows = (
        db.query(Shipment)
        .filter(Shipment.status == ShipmentStatus.DELAYED)
        .order_by(Shipment.delay_hours.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "code": s.code,
            "supplier": s.supplier.name if s.supplier else None,
            "origin": s.origin,
            "destination": s.destination,
            "delay_hours": s.delay_hours,
            "risk": _v(s.risk),
            "direction": _v(s.direction),
            "dock_code": s.dock_code,
        }
        for s in rows
    ]


@tool("get_inventory_at_risk", "SKUs at or below reorder point, lowest coverage first.")
def get_inventory_at_risk(db: Session, limit: int = 10) -> list[dict]:
    rows = (
        db.query(InventoryItem)
        .filter(InventoryItem.stock_status.in_([StockStatus.LOW, StockStatus.CRITICAL]))
        .order_by(InventoryItem.days_of_coverage.asc())
        .limit(limit)
        .all()
    )
    return [
        {
            "sku": i.sku,
            "name": i.name,
            "on_hand": i.quantity_on_hand,
            "available": i.quantity_available,
            "reorder_point": i.reorder_point,
            "days_of_coverage": i.days_of_coverage,
            "status": _v(i.stock_status),
            "bay_code": i.bay_code,
            "supplier": i.supplier.name if i.supplier else None,
        }
        for i in rows
    ]


@tool("get_dock_utilization", "Dock occupancy, throughput and blocked doors.")
def get_dock_utilization(db: Session) -> dict:
    docks = db.query(Dock).all()
    busy = [d for d in docks if d.status in (DockStatus.OCCUPIED, DockStatus.LOADING, DockStatus.UNLOADING)]
    available = [d for d in docks if d.status == DockStatus.AVAILABLE]
    blocked = [d for d in docks if d.status == DockStatus.MAINTENANCE]
    return {
        "total": len(docks),
        "busy": len(busy),
        "available": len(available),
        "blocked": len(blocked),
        "utilization_pct": round(len(busy) / len(docks) * 100, 1) if docks else 0.0,
        "available_codes": [d.code for d in available],
        "blocked_codes": [d.code for d in blocked],
        "busy_codes": [d.code for d in busy],
    }


@tool("get_truck_status", "Trucks on site or inbound, with dock assignment.")
def get_truck_status(db: Session, status: str | None = None) -> list[dict]:
    q = db.query(Truck)
    if status:
        q = q.filter(Truck.status == status)
    return [
        {
            "code": t.code,
            "carrier": t.carrier,
            "status": _v(t.status),
            "dock_code": t.dock_code,
            "shipment_code": t.shipment.code if t.shipment else None,
            "load_pct": t.load_pct,
            "destination": t.destination,
            "risk": _v(t.risk),
        }
        for t in q.order_by(Truck.code).all()
    ]


@tool("get_supplier_risk", "Suppliers ranked by reliability, least reliable first.")
def get_supplier_risk(db: Session, limit: int = 10) -> list[dict]:
    rows = (
        db.query(Supplier)
        .order_by(Supplier.reliability_score.asc())
        .limit(limit)
        .all()
    )
    return [
        {
            "code": s.code,
            "name": s.name,
            "location": s.location,
            "reliability_score": s.reliability_score,
            "risk": _v(s.risk),
            "open_shipments": len([x for x in s.shipments if x.status != ShipmentStatus.COMPLETED]),
        }
        for s in rows
    ]


@tool("get_orders_at_risk", "Customer orders flagged at risk, highest value first.")
def get_orders_at_risk(db: Session, limit: int = 10) -> list[dict]:
    rows = (
        db.query(CustomerOrder)
        .filter(CustomerOrder.status == OrderStatus.AT_RISK)
        .order_by(CustomerOrder.total_value.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "code": o.code,
            "customer": o.customer_name,
            "value": o.total_value,
            "currency": o.currency,
            "items": o.total_items,
            "priority": o.priority,
            "promised_date": o.promised_date.isoformat() if o.promised_date else None,
            "risk": _v(o.risk),
        }
        for o in rows
    ]


@tool("get_open_exceptions", "Unresolved operational exceptions, most severe first.")
def get_open_exceptions(db: Session, category: str | None = None, limit: int = 20) -> list[dict]:
    rank = {
        ExceptionSeverity.CRITICAL.value: 0,
        ExceptionSeverity.HIGH.value: 1,
        ExceptionSeverity.MEDIUM.value: 2,
        ExceptionSeverity.LOW.value: 3,
    }
    q = db.query(Exception_).filter(Exception_.resolved == False)  # noqa: E712
    if category:
        q = q.filter(Exception_.category == category)
    rows = sorted(q.all(), key=lambda e: rank.get(_v(e.severity), 9))[:limit]
    return [
        {
            "code": e.code,
            "category": _v(e.category),
            "severity": _v(e.severity),
            "title": e.title,
            "description": e.description,
            "entity_type": e.entity_type,
            "entity_code": e.entity_code,
            "affected_sku": e.affected_sku,
            "affected_orders": e.affected_orders,
            "potential_impact": e.potential_impact,
            "currency": e.impact_currency,
            "coverage_days": e.inventory_coverage_days,
            "delay_hours": e.delay_hours,
            "recommendation": e.recommendation,
        }
        for e in rows
    ]


@tool("get_warehouse_capacity", "Warehouse-level utilisation and equipment state.")
def get_warehouse_capacity(db: Session) -> dict:
    wh = db.query(Warehouse).first()
    forklifts = db.query(Forklift).all()
    return {
        "warehouse": wh.name if wh else None,
        "utilization_pct": wh.utilization_pct if wh else 0.0,
        "forklifts_total": len(forklifts),
        "forklifts_low_battery": [f.code for f in forklifts if f.battery_pct < 25],
    }


@tool("simulate_delay", "Project the downstream effect of a shipment slipping further.")
def simulate_delay(db: Session, shipment_code: str, extra_hours: float) -> dict:
    s = db.query(Shipment).filter(Shipment.code == shipment_code).first()
    if not s:
        return {"error": f"Shipment {shipment_code} not found"}

    new_delay = s.delay_hours + extra_hours
    # Orders tied to this shipment inherit the slip.
    orders = db.query(CustomerOrder).filter(CustomerOrder.shipment_id == s.id).all()
    exposed_value = sum(o.total_value for o in orders)

    if new_delay >= 8:
        severity = ExceptionSeverity.CRITICAL.value
    elif new_delay >= 4:
        severity = ExceptionSeverity.HIGH.value
    elif new_delay >= 2:
        severity = ExceptionSeverity.MEDIUM.value
    else:
        severity = ExceptionSeverity.LOW.value

    return {
        "shipment": s.code,
        "current_delay_hours": s.delay_hours,
        "projected_delay_hours": round(new_delay, 1),
        "projected_severity": severity,
        "orders_exposed": len(orders),
        "value_exposed": round(exposed_value, 2),
        "currency": orders[0].currency if orders else "INR",
        "breaches_promise": any(o.promised_date and o.promised_date <= _now() for o in orders),
    }


@tool("calculate_recovery_options", "Rank recovery options for an open exception.")
def calculate_recovery_options(db: Session, exception_code: str) -> list[dict]:
    e = db.query(Exception_).filter(Exception_.code == exception_code).first()
    if not e:
        return []

    dock = get_dock_utilization(db)
    options: list[dict] = []

    category = _v(e.category)
    if category == "SHIPMENT_DELAY":
        options = [
            {
                "kind": ActionKind.EXPEDITE_SHIPMENT.value,
                "title": f"Expedite {e.entity_code} via premium carrier",
                "rationale": f"Recovers ~{min(e.delay_hours, 4):.1f}h of the {e.delay_hours:.1f}h slip; "
                             f"protects {e.affected_orders} order(s).",
                "projected_savings": round(e.potential_impact * 0.7, 2),
                "projected_impact": round(e.potential_impact * 0.12, 2),
                "confidence": 0.78,
            },
            {
                "kind": ActionKind.REASSIGN_DOCK.value,
                "title": f"Pre-assign {dock['available_codes'][0] if dock['available_codes'] else 'next free dock'} "
                         f"for immediate turnaround",
                "rationale": f"{dock['available']} of {dock['total']} docks free — berthing on arrival "
                             f"removes queue time.",
                "projected_savings": round(e.potential_impact * 0.25, 2),
                "projected_impact": 0.0,
                "confidence": 0.86 if dock["available"] else 0.35,
            },
        ]
    elif category == "INVENTORY_RISK":
        options = [
            {
                "kind": ActionKind.RAISE_REPLENISHMENT.value,
                "title": f"Raise emergency replenishment for {e.affected_sku or e.entity_code}",
                "rationale": f"Only {e.inventory_coverage_days or 0:.1f} days of cover left; "
                             f"lead time will not be met without an expedited PO.",
                "projected_savings": round(e.potential_impact * 0.8, 2),
                "projected_impact": round(e.potential_impact * 0.15, 2),
                "confidence": 0.82,
            },
            {
                "kind": ActionKind.SPLIT_ORDER.value,
                "title": "Partially fulfil from on-hand stock, backorder remainder",
                "rationale": f"Protects revenue on {e.affected_orders} order(s) while the PO lands.",
                "projected_savings": round(e.potential_impact * 0.45, 2),
                "projected_impact": 0.0,
                "confidence": 0.7,
            },
        ]
    elif category == "SUPPLIER_RISK":
        options = [
            {
                "kind": ActionKind.CONTACT_SUPPLIER.value,
                "title": f"Escalate with {e.entity_code} and confirm recovery plan",
                "rationale": "Reliability has dropped below tolerance; a committed date is needed "
                             "before re-planning downstream.",
                "projected_savings": round(e.potential_impact * 0.3, 2),
                "projected_impact": 0.0,
                "confidence": 0.6,
            },
            {
                "kind": ActionKind.EXPEDITE_SHIPMENT.value,
                "title": "Activate contingency supplier for affected SKUs",
                "rationale": f"Removes single-source exposure on {e.affected_orders} order(s).",
                "projected_savings": round(e.potential_impact * 0.65, 2),
                "projected_impact": round(e.potential_impact * 0.2, 2),
                "confidence": 0.68,
            },
        ]
    elif category == "DOCK_CONGESTION":
        options = [
            {
                "kind": ActionKind.REASSIGN_DOCK.value,
                "title": "Re-sequence berths to prioritise fast turnarounds",
                "rationale": f"Utilisation at {dock['utilization_pct']}% with "
                             f"{len(dock['blocked_codes'])} door(s) blocked.",
                "projected_savings": round(max(e.potential_impact, 40000) * 0.4, 2),
                "projected_impact": 0.0,
                "confidence": 0.74,
            },
            {
                "kind": ActionKind.SCHEDULE_MAINTENANCE.value,
                "title": "Move blocked-door maintenance to off-peak window",
                "rationale": "Returns a door to service during the arrival peak.",
                "projected_savings": round(max(e.potential_impact, 40000) * 0.3, 2),
                "projected_impact": 12000.0,
                "confidence": 0.8,
            },
        ]
    elif category == "ORDER_AT_RISK":
        options = [
            {
                "kind": ActionKind.SPLIT_ORDER.value,
                "title": f"Split {e.entity_code} — ship available lines now",
                "rationale": "Protects the majority of order value against the upstream delay.",
                "projected_savings": round(e.potential_impact * 0.6, 2),
                "projected_impact": round(e.potential_impact * 0.05, 2),
                "confidence": 0.75,
            },
            {
                "kind": ActionKind.EXPEDITE_SHIPMENT.value,
                "title": "Expedite the blocking shipment",
                "rationale": "Keeps the order whole if the slip can be recovered in time.",
                "projected_savings": round(e.potential_impact * 0.85, 2),
                "projected_impact": round(e.potential_impact * 0.18, 2),
                "confidence": 0.62,
            },
        ]
    elif category == "EQUIPMENT_ISSUE":
        options = [
            {
                "kind": ActionKind.RECHARGE_FORKLIFT.value
                if "battery" in e.description.lower()
                else ActionKind.SCHEDULE_MAINTENANCE.value,
                "title": f"Service {e.entity_code} at next shift change",
                "rationale": "Avoids an unplanned stoppage during the picking peak.",
                "projected_savings": round(max(e.potential_impact, 15000) * 0.6, 2),
                "projected_impact": 4000.0,
                "confidence": 0.88,
            },
        ]

    return sorted(options, key=lambda o: o["projected_savings"] * o["confidence"], reverse=True)


# ── Write tools (gated behind human approval) ─────────────────────────────

@tool("propose_action", "Record a proposed action for human review.", writes=True)
def propose_action(
    db: Session,
    *,
    kind: str,
    title: str,
    rationale: str,
    entity_type: str,
    entity_code: str,
    proposed_by: str,
    exception_code: str | None = None,
    projected_impact: float = 0.0,
    projected_savings: float = 0.0,
    confidence: float = 0.0,
) -> dict:
    action = AgentAction(
        kind=kind,
        status=ActionStatus.PROPOSED,
        proposed_by=proposed_by,
        title=title,
        rationale=rationale,
        entity_type=entity_type,
        entity_code=entity_code,
        exception_code=exception_code,
        projected_impact=projected_impact,
        projected_savings=projected_savings,
        confidence=confidence,
    )
    db.add(action)
    db.flush()
    return {"id": action.id, "status": _v(action.status), "title": action.title}


@tool("validate_action", "Check a proposed action is still safe to run.", writes=True)
def validate_action(db: Session, action_id: int) -> dict:
    a = db.query(AgentAction).filter(AgentAction.id == action_id).first()
    if not a:
        return {"ok": False, "reason": "Action not found"}
    if a.status not in (ActionStatus.PROPOSED, ActionStatus.VALIDATED):
        return {"ok": False, "reason": f"Action already {_v(a.status)}"}

    notes: list[str] = []
    ok = True

    # Re-check the world hasn't moved on since the action was proposed.
    if _v(a.kind) == ActionKind.REASSIGN_DOCK.value:
        dock = get_dock_utilization(db)
        if not dock["available_codes"]:
            ok = False
            notes.append("No dock is currently free — reassignment would queue.")
        else:
            notes.append(f"{dock['available']} dock(s) free: {', '.join(dock['available_codes'][:3])}.")

    if a.exception_code:
        exc = db.query(Exception_).filter(Exception_.code == a.exception_code).first()
        if exc is None:
            ok = False
            notes.append(f"Exception {a.exception_code} no longer exists.")
        elif exc.resolved:
            ok = False
            notes.append(f"Exception {a.exception_code} was already resolved.")
        else:
            notes.append(f"Exception {a.exception_code} still open at {_v(exc.severity)}.")

    if a.confidence < 0.5:
        notes.append(f"Low confidence ({a.confidence:.0%}) — review carefully before approving.")

    a.validation_notes = " ".join(notes) if notes else "No blocking conditions found."
    if ok:
        a.status = ActionStatus.VALIDATED
    db.flush()
    return {"ok": ok, "notes": a.validation_notes, "status": _v(a.status)}


@tool("execute_action", "Apply an approved action and log an operational event.", writes=True)
def execute_action(db: Session, action_id: int) -> dict:
    """Only call after a human has approved. Mutates operational state."""
    a = db.query(AgentAction).filter(AgentAction.id == action_id).first()
    if not a:
        return {"ok": False, "message": "Action not found"}
    if a.status == ActionStatus.EXECUTED:
        return {"ok": False, "message": "Action already executed"}

    message = f"{a.title} — applied"
    event_type = EventType.DOCK_ASSIGNED

    if a.kind == ActionKind.REASSIGN_DOCK:
        dock = (
            db.query(Dock)
            .filter(Dock.status == DockStatus.AVAILABLE)
            .order_by(Dock.position_index)
            .first()
        )
        truck = db.query(Truck).filter(Truck.code == a.entity_code).first()
        if dock and truck:
            dock.status = DockStatus.RESERVED
            dock.current_truck_id = truck.id
            truck.dock_code = dock.code
            message = f"{truck.code} assigned to {dock.code}"
        else:
            message = "Dock reassignment recorded; no free dock to bind yet"
        event_type = EventType.DOCK_ASSIGNED

    elif a.kind in (ActionKind.EXPEDITE_SHIPMENT, ActionKind.REROUTE_SHIPMENT):
        s = db.query(Shipment).filter(Shipment.code == a.entity_code).first()
        if s:
            recovered = min(s.delay_hours, 4.0)
            s.delay_hours = round(max(0.0, s.delay_hours - recovered), 1)
            if s.delay_hours == 0 and s.status == ShipmentStatus.DELAYED:
                s.status = ShipmentStatus.IN_TRANSIT
            message = f"{s.code} expedited — {recovered:.1f}h recovered, {s.delay_hours:.1f}h remaining"
        event_type = EventType.SHIPMENT_DELAYED

    elif a.kind == ActionKind.RAISE_REPLENISHMENT:
        item = (
            db.query(InventoryItem)
            .filter(InventoryItem.sku == a.entity_code)
            .order_by(InventoryItem.days_of_coverage.asc())
            .first()
        )
        if item:
            topup = max(item.reorder_point * 2 - item.quantity_on_hand, item.reorder_point)
            item.quantity_on_hand += topup
            item.quantity_available = item.quantity_on_hand - item.quantity_reserved
            item.stock_status = StockStatus.HEALTHY
            item.days_of_coverage = round(item.days_of_coverage + 21, 1)
            item.last_received = _now()
            message = f"Replenishment raised for {item.sku} — +{topup} units inbound"
        event_type = EventType.INVENTORY_REPLENISHED

    elif a.kind == ActionKind.SPLIT_ORDER:
        o = db.query(CustomerOrder).filter(CustomerOrder.code == a.entity_code).first()
        if o:
            o.status = OrderStatus.PROCESSING
            o.risk = "MEDIUM"
            message = f"{o.code} split — available lines released for picking"
        event_type = EventType.ORDER_AT_RISK

    elif a.kind == ActionKind.CONTACT_SUPPLIER:
        sup = db.query(Supplier).filter(Supplier.code == a.entity_code).first()
        if sup:
            message = f"Escalation raised with {sup.name} ({sup.code})"
        event_type = EventType.SUPPLIER_DELAYED

    elif a.kind == ActionKind.SCHEDULE_MAINTENANCE:
        d = db.query(Dock).filter(Dock.code == a.entity_code).first()
        if d and d.status == DockStatus.MAINTENANCE:
            d.status = DockStatus.AVAILABLE
            d.activity = None
            message = f"{d.code} maintenance rescheduled — door returned to service"
        else:
            message = f"Maintenance window booked for {a.entity_code}"
        event_type = EventType.DOCK_RELEASED

    elif a.kind == ActionKind.RECHARGE_FORKLIFT:
        f = db.query(Forklift).filter(Forklift.code == a.entity_code).first()
        if f:
            f.activity = "CHARGING"
            message = f"{f.code} routed to charging station"
        event_type = EventType.FORKLIFT_MOVED

    # Close the originating exception, if any.
    if a.exception_code:
        exc = db.query(Exception_).filter(Exception_.code == a.exception_code).first()
        if exc and not exc.resolved:
            exc.resolved = True
            exc.resolved_at = _now()

    db.add(
        OperationalEvent(
            event_type=event_type,
            entity_type=a.entity_type,
            entity_code=a.entity_code,
            message=f"[agent] {message}",
            severity=ExceptionSeverity.LOW,
            timestamp=_now(),
        )
    )

    a.status = ActionStatus.EXECUTED
    a.result_message = message
    a.decided_at = _now()
    db.flush()
    return {"ok": True, "message": message}


def tool_catalog() -> list[dict]:
    """Machine-readable list of tools, for the UI and future MCP export."""
    return [
        {"name": t.name, "description": t.description, "writes": t.writes}
        for t in TOOLS.values()
    ]
