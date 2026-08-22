"""Seed the database with realistic synthetic supply-chain data.

Run with:
    cd backend
    source .venv/bin/activate
    python -m app.seed
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

from app.core.database import Base, SessionLocal, engine
from app.models.models import (
    CustomerOrder,
    Dock,
    DockStatus,
    EventType,
    Exception_,
    ExceptionCategory,
    ExceptionSeverity,
    Forklift,
    ForkliftActivity,
    InventoryItem,
    OperationalEvent,
    OrderStatus,
    Pallet,
    ParkingSlot,
    ParkingSlotStatus,
    RiskLevel,
    Shipment,
    ShipmentDirection,
    ShipmentStatus,
    StockStatus,
    Supplier,
    Truck,
    TruckStatus,
    Warehouse,
    WarehouseAisle,
    WarehouseBay,
)

random.seed(42)
# Naive UTC — the DateTime columns are timezone-naive, so strip tzinfo to
# keep seeded values consistent with what server_default=func.now() writes.
NOW = datetime.now(timezone.utc).replace(tzinfo=None, second=0, microsecond=0)

CARRIERS = [
    "Maersk Logistics", "DHL Supply Chain", "Blue Dart Express",
    "Delhivery", "GATI KWE", "Rivigo", "TCI Freight",
    "Safexpress", "Allcargo Logistics", "VRL Logistics",
]
CITIES = [
    "Chennai DC", "Mumbai Hub", "Delhi NCR", "Bangalore Depot",
    "Hyderabad WH", "Pune Center", "Kolkata Yard", "Ahmedabad Port",
    "Jaipur Terminal", "Kochi Facility",
]
SUPPLIERS_DATA = [
    ("Tata Steel", "SUP-01", "Jamshedpur"),
    ("Reliance Industries", "SUP-02", "Mumbai"),
    ("Hindustan Unilever", "SUP-03", "Mumbai"),
    ("Asian Paints", "SUP-04", "Mumbai"),
    ("Godrej Consumer", "SUP-05", "Mumbai"),
    ("Bosch India", "SUP-06", "Bangalore"),
    ("Amul Dairy", "SUP-07", "Anand"),
    ("Larsen & Toubro", "SUP-08", "Chennai"),
    ("Mahindra Parts", "SUP-09", "Pune"),
    ("Bajaj Auto", "SUP-10", "Pune"),
]
SKU_NAMES = {
    "SKU-1001": "Steel Coil 250mm",
    "SKU-1002": "Polymer Resin Bag",
    "SKU-1003": "Detergent Bulk Pack",
    "SKU-1004": "Enamel Paint 20L",
    "SKU-1005": "Hair Care Kit",
    "SKU-1006": "Spark Plug Set",
    "SKU-1007": "Butter Carton 10kg",
    "SKU-1008": "Bearing Assembly",
    "SKU-1009": "Tractor Gear Box",
    "SKU-1010": "Brake Pad Set",
    "SKU-2001": "Lubricant Drum 20L",
    "SKU-2002": "Packaging Film Roll",
    "SKU-2003": "Conveyor Belt 5m",
    "SKU-2004": "Safety Helmet Box",
    "SKU-2005": "LED Panel Light",
    "SKU-2006": "Motor Assembly",
    "SKU-2007": "Valve Fitting Kit",
    "SKU-2008": "Cable Spool 100m",
    "SKU-2009": "Industrial Gloves Box",
    "SKU-2010": "Fastener Assortment",
}
CATEGORIES = [
    "Raw Materials", "Finished Goods", "Packaging",
    "Consumables", "Equipment", "Spare Parts",
]
CUSTOMER_NAMES = [
    "FlipMart", "Amazon India", "BigBasket", "Reliance Retail",
    "Tata CLiQ", "Myntra", "Udaan", "IndiaMART", "Moglix",
    "Nykaa", "Snapdeal", "Meesho", "1mg", "PharmEasy",
    "Swiggy Instamart", "Blinkit", "Zepto", "JioMart", "Croma",
    "DMart Online",
]

# --- Site layout ---------------------------------------------------------
# These mirror SITE in frontend/src/constants/index.ts. The two must agree or
# entities render outside the structures they belong to.
GATE_X = -40            # site entrance
APRON_X = 4             # where trucks berth, nose pointing east
APRON_Z_START = -20     # dock berth 0
APRON_SLOT_DEPTH = 4.5
AISLE_X_START = 14      # first racking run, inside the building
AISLE_SPACING = 8
AISLE_Z = -20           # aisles start here; bays extend along +z
BAY_DEPTH = 4           # spacing between bays along an aisle

# The truck model runs ~10 units along its local X with the nose at +x, and is
# only ~2.6 wide. A berthed truck therefore points straight at the wall
# (rotation 0) so its LENGTH sits perpendicular to the dock face and only its
# width occupies the berth. Rotating it 90° would lay 10 units of truck across
# berths spaced 4.5 apart — which is what used to pile them on top of
# each other.
FACING_DOCK = 0.0       # nose east, toward the dock wall
HEADING_WEST = 3.1416   # nose west, for departing traffic

# The model is ~10.1 long; 15 leaves a clear gap between vehicles in a queue.
TRUCK_LEN = 15.0

# Traffic lanes, as z bands. Nothing stands inside the road corridor
# (z -6..6) except vehicles actually moving through it, and the parking yard
# starts well south of it.
LANE_INBOUND_Z = -3.0     # north half of the road, heading east
LANE_OUTBOUND_Z = 3.0     # south half of the road, heading west
LANE_HOLDING_Z = -14.0    # queued, waiting for a berth
LANE_SHOULDER_Z = -22.0   # held / delayed, off the running lanes


def _seed() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # ---------- Warehouse ----------
        wh = Warehouse(
            name="ChainPilot Central Warehouse",
            code="WH-01",
            address="Plot 42, Industrial Area, Chennai 600032",
            latitude=13.0827,
            longitude=80.2707,
            total_area_sqm=25000.0,
            utilization_pct=84.0,
        )
        db.add(wh)
        db.flush()

        # ---------- Suppliers ----------
        suppliers = []
        for name, code, loc in SUPPLIERS_DATA:
            s = Supplier(
                name=name,
                code=code,
                location=loc,
                reliability_score=round(random.uniform(72, 99), 1),
                risk=random.choice([RiskLevel.LOW, RiskLevel.LOW, RiskLevel.MEDIUM]),
                active=True,
            )
            # Make two suppliers risky
            if code in ("SUP-03", "SUP-09"):
                s.reliability_score = round(random.uniform(55, 70), 1)
                s.risk = RiskLevel.HIGH
            db.add(s)
            suppliers.append(s)
        db.flush()

        # ---------- Aisles ----------
        aisle_zones = ["RECEIVING", "STORAGE", "STORAGE", "PICKING", "DISPATCH"]
        aisles = []
        for i, zone in enumerate(aisle_zones):
            code = f"A{i+1:02d}"
            a = WarehouseAisle(
                warehouse_id=wh.id,
                code=code,
                zone=zone,
                capacity_pct=round(random.uniform(70, 98), 1),
                occupied_pct=round(random.uniform(50, 95), 1),
                active_pick_tasks=random.randint(0, 20),
                replenishment_tasks=random.randint(0, 8),
                risk=random.choice([RiskLevel.LOW, RiskLevel.LOW, RiskLevel.MEDIUM]),
                position_x=AISLE_X_START + i * AISLE_SPACING,
                position_z=AISLE_Z,
            )
            if i == 2:
                a.occupied_pct = 94.0
                a.risk = RiskLevel.HIGH
                a.replenishment_tasks = 7
            db.add(a)
            aisles.append(a)
        db.flush()

        # ---------- Bays ----------
        skus = list(SKU_NAMES.keys())
        bays = []
        for aisle in aisles:
            for j in range(10):
                code = f"{aisle.code}-B{j+1:02d}"
                sku = skus[(aisles.index(aisle) * 10 + j) % len(skus)]
                cap = random.randint(300, 600)
                qty = random.randint(20, cap)
                stock = StockStatus.HEALTHY
                replenish = False
                if qty < cap * 0.2:
                    stock = StockStatus.LOW
                    replenish = True
                elif qty > cap * 0.95:
                    stock = StockStatus.BLOCKED
                bay = WarehouseBay(
                    aisle_id=aisle.id,
                    code=code,
                    level=random.randint(1, 3),
                    capacity=cap,
                    current_quantity=qty,
                    sku=sku,
                    stock_status=stock,
                    last_movement=NOW - timedelta(minutes=random.randint(5, 600)),
                    replenishment_required=replenish,
                    position_index=j,
                )
                db.add(bay)
                bays.append(bay)
        db.flush()

        # ---------- Docks ----------
        dock_statuses = [
            DockStatus.OCCUPIED, DockStatus.LOADING, DockStatus.UNLOADING,
            DockStatus.AVAILABLE, DockStatus.OCCUPIED, DockStatus.LOADING,
            DockStatus.AVAILABLE, DockStatus.RESERVED, DockStatus.MAINTENANCE,
            DockStatus.UNLOADING,
        ]
        docks = []
        for i in range(10):
            d = Dock(
                warehouse_id=wh.id,
                code=f"D-{i+1:02d}",
                status=dock_statuses[i],
                activity="Active" if dock_statuses[i] not in (DockStatus.AVAILABLE, DockStatus.MAINTENANCE) else None,
                position_index=i,
            )
            if dock_statuses[i] not in (DockStatus.AVAILABLE, DockStatus.MAINTENANCE):
                d.occupancy_start = NOW - timedelta(minutes=random.randint(10, 120))
                d.estimated_completion = NOW + timedelta(minutes=random.randint(10, 90))
            db.add(d)
            docks.append(d)
        db.flush()

        # ---------- Parking Slots ----------
        parking_statuses = (
            [ParkingSlotStatus.OCCUPIED] * 8
            + [ParkingSlotStatus.AVAILABLE] * 6
            + [ParkingSlotStatus.RESERVED] * 3
            + [ParkingSlotStatus.WAITING] * 2
            + [ParkingSlotStatus.MAINTENANCE] * 1
        )
        parking_slots = []
        for i in range(20):
            ps = ParkingSlot(
                warehouse_id=wh.id,
                code=f"P{i+1:02d}",
                status=parking_statuses[i],
                position_index=i,
            )
            if parking_statuses[i] == ParkingSlotStatus.OCCUPIED:
                ps.vehicle_id = f"TR-{1001 + i}"
                ps.arrival_time = NOW - timedelta(minutes=random.randint(10, 180))
                ps.expected_departure = NOW + timedelta(minutes=random.randint(30, 240))
                ps.assigned_dock = f"D-{random.randint(1, 10):02d}"
            elif parking_statuses[i] == ParkingSlotStatus.RESERVED:
                ps.vehicle_id = f"TR-{1021 + i}"
                ps.assigned_dock = f"D-{random.randint(1, 10):02d}"
            db.add(ps)
            parking_slots.append(ps)
        db.flush()

        # ---------- Shipments ----------
        shipments = []
        for i in range(30):
            direction = ShipmentDirection.INBOUND if i < 18 else ShipmentDirection.OUTBOUND
            status = random.choice([
                ShipmentStatus.SCHEDULED, ShipmentStatus.IN_TRANSIT,
                ShipmentStatus.AT_FACILITY, ShipmentStatus.LOADING,
                ShipmentStatus.UNLOADING, ShipmentStatus.COMPLETED,
            ])
            delay = 0.0
            risk = RiskLevel.LOW
            if i in (2, 7, 14, 22):
                status = ShipmentStatus.DELAYED
                delay = random.uniform(2, 8)
                risk = RiskLevel.HIGH
            if i in (5, 11):
                delay = random.uniform(1, 3)
                risk = RiskLevel.MEDIUM

            s = Shipment(
                code=f"SHP-{88200 + i}",
                supplier_id=suppliers[i % len(suppliers)].id,
                direction=direction,
                status=status,
                origin=random.choice(CITIES),
                destination=random.choice(CITIES),
                eta=NOW + timedelta(hours=random.randint(-12, 48)),
                dock_code=f"D-{(i % 10) + 1:02d}" if status in (ShipmentStatus.AT_FACILITY, ShipmentStatus.LOADING, ShipmentStatus.UNLOADING) else None,
                sku_count=random.randint(3, 25),
                weight_kg=round(random.uniform(500, 15000), 1),
                delay_hours=round(delay, 1),
                risk=risk,
            )
            db.add(s)
            shipments.append(s)
        db.flush()

        # ---------- Trucks ----------
        truck_statuses = [
            TruckStatus.ARRIVING, TruckStatus.ARRIVING,
            TruckStatus.WAITING, TruckStatus.WAITING,
            TruckStatus.AT_DOCK, TruckStatus.AT_DOCK,
            TruckStatus.LOADING, TruckStatus.UNLOADING,
            TruckStatus.DELAYED, TruckStatus.READY_TO_DEPART,
        ]
        # Docks that are actually busy — trucks at a dock must be assigned to
        # one of these, otherwise the twin renders a truck parked at a dock
        # that reports itself AVAILABLE.
        busy_docks = [
            d for d in docks
            if d.status in (DockStatus.OCCUPIED, DockStatus.LOADING, DockStatus.UNLOADING)
        ]
        docked_truck_cursor = 0
        lane_counts = {"arriving": 0, "waiting": 0, "delayed": 0, "departing": 0}

        trucks = []
        for i in range(10):
            status = truck_statuses[i]

            # Assign a dock first — position depends on which dock it is.
            dock_code = None
            dock_slot = None
            if status in (TruckStatus.AT_DOCK, TruckStatus.LOADING, TruckStatus.UNLOADING):
                if docked_truck_cursor < len(busy_docks):
                    assigned = busy_docks[docked_truck_cursor]
                    dock_code = assigned.code
                    dock_slot = assigned.position_index
                    docked_truck_cursor += 1
                else:
                    # No busy dock left to occupy — keep the truck waiting
                    # rather than inventing an inconsistent assignment.
                    status = TruckStatus.WAITING

            # Position by status. Each status owns a lane, and vehicles are
            # spaced by TRUCK_LEN along that lane so nothing overlaps.
            if dock_slot is not None:
                # Nose up to the wall; length runs perpendicular to the face.
                px, py, pz = APRON_X, 0, APRON_Z_START + dock_slot * APRON_SLOT_DEPTH
                ry = FACING_DOCK
            elif status == TruckStatus.ARRIVING:
                # Inbound half of the road, nose-to-tail toward the apron.
                px = GATE_X + 8 + lane_counts["arriving"] * TRUCK_LEN
                py, pz = 0, LANE_INBOUND_Z
                ry = FACING_DOCK
                lane_counts["arriving"] += 1
            elif status == TruckStatus.WAITING:
                # Holding lane, parallel to the road and clear of it.
                px = GATE_X + 8 + lane_counts["waiting"] * TRUCK_LEN
                py, pz = 0, LANE_HOLDING_Z
                ry = FACING_DOCK
                lane_counts["waiting"] += 1
            elif status == TruckStatus.DELAYED:
                # Pulled onto the shoulder, off the running lanes.
                px = GATE_X + 8 + lane_counts["delayed"] * TRUCK_LEN
                py, pz = 0, LANE_SHOULDER_Z
                ry = FACING_DOCK
                lane_counts["delayed"] += 1
            else:
                # Departing: outbound half of the road, already turned around.
                px = -12 - lane_counts["departing"] * TRUCK_LEN
                py, pz = 0, LANE_OUTBOUND_Z
                ry = HEADING_WEST
                lane_counts["departing"] += 1

            t = Truck(
                code=f"TR-{1020 + i}",
                carrier=CARRIERS[i % len(CARRIERS)],
                status=status,
                dock_code=dock_code,
                shipment_id=shipments[i].id if i < len(shipments) else None,
                eta=NOW + timedelta(minutes=random.randint(-60, 120)),
                load_pct=round(random.uniform(20, 95), 1),
                destination=random.choice(CITIES),
                risk=RiskLevel.HIGH if status == TruckStatus.DELAYED else RiskLevel.LOW,
                position_x=px,
                position_y=py,
                position_z=pz,
                rotation_y=ry,
            )
            db.add(t)
            trucks.append(t)
        db.flush()

        # Link docks to trucks
        for i, dock in enumerate(docks):
            if dock.status in (DockStatus.OCCUPIED, DockStatus.LOADING, DockStatus.UNLOADING):
                matching = [t for t in trucks if t.dock_code == dock.code]
                if matching:
                    dock.current_truck_id = matching[0].id
                    dock.current_shipment_id = matching[0].shipment_id

        # ---------- Pallets ----------
        pallets = []
        for i in range(30):
            bay = bays[i % len(bays)]
            sku = bay.sku or skus[i % len(skus)]
            qty = random.randint(10, 100)
            stock = StockStatus.HEALTHY
            if qty < 20:
                stock = StockStatus.LOW
            elif i in (5, 18, 25):
                stock = StockStatus.RESERVED
            p = Pallet(
                code=f"PLT-{3000 + i}",
                bay_id=bay.id,
                sku=sku,
                quantity=qty,
                max_quantity=100,
                stock_status=stock,
                condition=random.choice(["GOOD", "GOOD", "GOOD", "FAIR", "DAMAGED"]),
                position_x=bay.aisle.position_x + (i % 5) * 1.2,
                position_y=0.3,
                position_z=bay.aisle.position_z + bay.position_index * BAY_DEPTH,
            )
            db.add(p)
            pallets.append(p)
        db.flush()

        # ---------- Inventory Items ----------
        inv_items = []
        for i, (sku, name) in enumerate(SKU_NAMES.items()):
            qty_on_hand = random.randint(30, 500)
            qty_reserved = random.randint(0, int(qty_on_hand * 0.3))
            reorder = random.randint(40, 80)
            max_q = random.randint(400, 600)
            stock = StockStatus.HEALTHY
            coverage = round(random.uniform(10, 45), 1)
            if qty_on_hand < reorder:
                stock = StockStatus.LOW
                coverage = round(random.uniform(2, 8), 1)
            if i in (3, 11, 17):
                stock = StockStatus.CRITICAL
                qty_on_hand = random.randint(5, 25)
                coverage = round(random.uniform(0.5, 3), 1)

            inv = InventoryItem(
                sku=sku,
                name=name,
                category=random.choice(CATEGORIES),
                bay_code=bays[i % len(bays)].code,
                quantity_on_hand=qty_on_hand,
                quantity_reserved=qty_reserved,
                quantity_available=qty_on_hand - qty_reserved,
                reorder_point=reorder,
                max_quantity=max_q,
                stock_status=stock,
                days_of_coverage=coverage,
                supplier_id=suppliers[i % len(suppliers)].id,
                last_received=NOW - timedelta(days=random.randint(1, 30)),
                last_picked=NOW - timedelta(hours=random.randint(1, 72)),
            )
            db.add(inv)
            inv_items.append(inv)

        # Pad to 100
        for i in range(len(SKU_NAMES), 100):
            sku_key = skus[i % len(skus)]
            qty_on_hand = random.randint(30, 500)
            qty_reserved = random.randint(0, int(qty_on_hand * 0.3))
            inv = InventoryItem(
                sku=f"{sku_key}-{i:03d}",
                name=f"{SKU_NAMES[sku_key]} (Variant {i})",
                category=random.choice(CATEGORIES),
                bay_code=bays[i % len(bays)].code,
                quantity_on_hand=qty_on_hand,
                quantity_reserved=qty_reserved,
                quantity_available=qty_on_hand - qty_reserved,
                reorder_point=random.randint(40, 80),
                max_quantity=random.randint(400, 600),
                stock_status=StockStatus.HEALTHY,
                days_of_coverage=round(random.uniform(10, 45), 1),
                supplier_id=suppliers[i % len(suppliers)].id,
                last_received=NOW - timedelta(days=random.randint(1, 30)),
                last_picked=NOW - timedelta(hours=random.randint(1, 72)),
            )
            db.add(inv)
        db.flush()

        # ---------- Forklifts ----------
        forklift_activities = [
            ForkliftActivity.MOVING, ForkliftActivity.PICKING,
            ForkliftActivity.IDLE, ForkliftActivity.REPLENISHING,
            ForkliftActivity.CHARGING,
        ]
        operators = ["Ravi K.", "Suresh M.", "Priya S.", "Arun T.", "Deepa R."]
        for i in range(5):
            fl = Forklift(
                warehouse_id=wh.id,
                code=f"FL-{i+1:02d}",
                activity=forklift_activities[i],
                operator=operators[i],
                current_aisle=aisles[i].code,
                battery_pct=round(random.uniform(30, 100), 1),
                position_x=aisles[i].position_x + 2,
                position_y=0,
                position_z=aisles[i].position_z + random.uniform(-3, 3),
            )
            if forklift_activities[i] == ForkliftActivity.CHARGING:
                fl.battery_pct = round(random.uniform(5, 25), 1)
                fl.current_aisle = None
                # Charging bay sits in the building's north-east corner.
                fl.position_x = 48
                fl.position_z = 20
            db.add(fl)
        db.flush()

        # ---------- Customer Orders ----------
        for i in range(20):
            status = random.choice([
                OrderStatus.PENDING, OrderStatus.PROCESSING,
                OrderStatus.PICKING, OrderStatus.PACKED,
                OrderStatus.SHIPPED,
            ])
            risk = RiskLevel.LOW
            if i in (2, 8, 15):
                status = OrderStatus.AT_RISK
                risk = RiskLevel.HIGH
            co = CustomerOrder(
                code=f"ORD-{7000 + i}",
                customer_name=CUSTOMER_NAMES[i],
                status=status,
                priority=random.choice(["LOW", "NORMAL", "NORMAL", "HIGH", "URGENT"]),
                total_items=random.randint(3, 50),
                total_value=round(random.uniform(15000, 850000), 2),
                currency="INR",
                promised_date=NOW + timedelta(days=random.randint(1, 14)),
                shipment_id=shipments[i % len(shipments)].id,
                risk=risk,
            )
            db.add(co)
        db.flush()

        # ---------- Operational Events ----------
        event_defs = [
            (EventType.TRUCK_ARRIVED, "TRUCK", "TR-1020", "Truck TR-1020 arrived at gate"),
            (EventType.TRUCK_ARRIVED, "TRUCK", "TR-1021", "Truck TR-1021 arrived at gate"),
            (EventType.TRUCK_DELAYED, "TRUCK", "TR-1028", "Truck TR-1028 delayed by 3 hours — traffic on NH-48"),
            (EventType.DOCK_ASSIGNED, "DOCK", "D-01", "Dock D-01 assigned to TR-1024"),
            (EventType.DOCK_ASSIGNED, "DOCK", "D-02", "Dock D-02 assigned to TR-1025"),
            (EventType.DOCK_RELEASED, "DOCK", "D-04", "Dock D-04 released — loading complete"),
            (EventType.SHIPMENT_DELAYED, "SHIPMENT", "SHP-88202", "Shipment SHP-88202 delayed +4h — supplier dispatch late"),
            (EventType.SHIPMENT_DELAYED, "SHIPMENT", "SHP-88207", "Shipment SHP-88207 delayed +2.5h — port congestion"),
            (EventType.INVENTORY_LOW, "INVENTORY", "SKU-1004", "SKU-1004 (Enamel Paint 20L) below reorder point"),
            (EventType.INVENTORY_LOW, "INVENTORY", "SKU-2002", "SKU-2002 (Packaging Film Roll) critical stock level"),
            (EventType.INVENTORY_REPLENISHED, "INVENTORY", "SKU-1001", "SKU-1001 (Steel Coil 250mm) replenished to safe level"),
            (EventType.FORKLIFT_MOVED, "FORKLIFT", "FL-01", "Forklift FL-01 picking from A03-B07"),
            (EventType.FORKLIFT_MOVED, "FORKLIFT", "FL-02", "Forklift FL-02 replenishing A02-B04"),
            (EventType.ORDER_AT_RISK, "ORDER", "ORD-7002", "Order ORD-7002 at risk — dependent shipment delayed"),
            (EventType.ORDER_AT_RISK, "ORDER", "ORD-7008", "Order ORD-7008 at risk — inventory shortage"),
            (EventType.SUPPLIER_DELAYED, "SUPPLIER", "SUP-03", "Supplier SUP-03 (Hindustan Unilever) delayed dispatch"),
            (EventType.SUPPLIER_DELAYED, "SUPPLIER", "SUP-09", "Supplier SUP-09 (Mahindra Parts) factory shutdown"),
            (EventType.TRUCK_ARRIVED, "TRUCK", "TR-1023", "Truck TR-1023 arrived — queued for parking"),
            (EventType.DOCK_ASSIGNED, "DOCK", "D-06", "Dock D-06 assigned to TR-1026"),
            (EventType.SHIPMENT_DELAYED, "SHIPMENT", "SHP-88214", "Shipment SHP-88214 delayed +5h — customs hold"),
        ]
        severities = [
            ExceptionSeverity.LOW, ExceptionSeverity.LOW,
            ExceptionSeverity.HIGH,
            ExceptionSeverity.LOW, ExceptionSeverity.LOW,
            ExceptionSeverity.LOW,
            ExceptionSeverity.HIGH, ExceptionSeverity.MEDIUM,
            ExceptionSeverity.MEDIUM, ExceptionSeverity.CRITICAL,
            ExceptionSeverity.LOW,
            ExceptionSeverity.LOW, ExceptionSeverity.LOW,
            ExceptionSeverity.HIGH, ExceptionSeverity.MEDIUM,
            ExceptionSeverity.HIGH, ExceptionSeverity.CRITICAL,
            ExceptionSeverity.LOW,
            ExceptionSeverity.LOW,
            ExceptionSeverity.HIGH,
        ]
        for i, (etype, ent_type, ent_code, msg) in enumerate(event_defs):
            ev = OperationalEvent(
                event_type=etype,
                entity_type=ent_type,
                entity_code=ent_code,
                message=msg,
                severity=severities[i],
                timestamp=NOW - timedelta(minutes=random.randint(1, 240)),
            )
            db.add(ev)
        db.flush()

        # ---------- Exceptions ----------
        exception_defs = [
            # Shipment delays
            ("EXC-001", ExceptionCategory.SHIPMENT_DELAY, ExceptionSeverity.CRITICAL,
             "Critical Shipment Delay", "Shipment SHP-88202 delayed +4 hours due to late supplier dispatch",
             "SHIPMENT", "SHP-88202", "SKU-1003", 2, 520000, 7.0, 4.0,
             "Expedite alternate transport from Pune depot", -24, 2, -6),
            ("EXC-002", ExceptionCategory.SHIPMENT_DELAY, ExceptionSeverity.HIGH,
             "Port Congestion Delay", "Shipment SHP-88207 delayed +2.5h due to port congestion",
             "SHIPMENT", "SHP-88207", "SKU-1008", 1, 180000, 12.0, 2.5,
             "Re-route through alternate port terminal", -24, 2, 4),
            ("EXC-003", ExceptionCategory.SHIPMENT_DELAY, ExceptionSeverity.HIGH,
             "Customs Hold", "Shipment SHP-88214 held at customs — documentation issue",
             "SHIPMENT", "SHP-88214", "SKU-2005", 3, 340000, 5.0, 5.0,
             "Contact customs broker for expedited clearance", -24, 2, 14),
            # Dock congestion
            ("EXC-004", ExceptionCategory.DOCK_CONGESTION, ExceptionSeverity.MEDIUM,
             "Dock Congestion", "76% dock utilization — approaching capacity threshold",
             "DOCK", "D-05", None, 0, 0, None, 0,
             "Prioritize fast-turnaround shipments", 5, 2, -12),
            ("EXC-005", ExceptionCategory.DOCK_CONGESTION, ExceptionSeverity.HIGH,
             "Dock Maintenance Overlap", "D-09 under maintenance while utilization is high",
             "DOCK", "D-09", None, 0, 50000, None, 0,
             "Reschedule maintenance to off-peak hours", 5, 2, 14),
            # Inventory risk
            ("EXC-006", ExceptionCategory.INVENTORY_RISK, ExceptionSeverity.CRITICAL,
             "Critical Inventory — Enamel Paint", "SKU-1004 below safety stock, 2 days coverage remaining",
             "INVENTORY", "SKU-1004", "SKU-1004", 4, 380000, 2.0, 0,
             "Place emergency order with Asian Paints or source from alternate supplier", 22, 2, -10),
            ("EXC-007", ExceptionCategory.INVENTORY_RISK, ExceptionSeverity.MEDIUM,
             "Low Stock — Packaging Film", "SKU-2002 approaching reorder point",
             "INVENTORY", "SKU-2002", "SKU-2002", 1, 95000, 8.0, 0,
             "Trigger standard replenishment order", 30, 2, 0),
            ("EXC-008", ExceptionCategory.INVENTORY_RISK, ExceptionSeverity.HIGH,
             "Critical Inventory — Motor Assembly", "SKU-2006 at critically low level",
             "INVENTORY", "SKU-2006", "SKU-2006", 2, 250000, 1.5, 0,
             "Source from alternate supplier immediately", 38, 2, -14),
            # Supplier risk
            ("EXC-009", ExceptionCategory.SUPPLIER_RISK, ExceptionSeverity.HIGH,
             "Supplier Reliability Drop", "SUP-03 reliability dropped to 62% — 3 delayed shipments in 7 days",
             "SUPPLIER", "SUP-03", None, 3, 420000, None, 0,
             "Initiate supplier review and identify backup suppliers", -38, 2, -12),
            ("EXC-010", ExceptionCategory.SUPPLIER_RISK, ExceptionSeverity.CRITICAL,
             "Supplier Factory Shutdown", "SUP-09 (Mahindra Parts) factory shutdown — indefinite",
             "SUPPLIER", "SUP-09", "SKU-1009", 5, 780000, 4.0, 0,
             "Activate contingency supply from Bajaj Auto", -38, 2, 12),
            # Order at risk
            ("EXC-011", ExceptionCategory.ORDER_AT_RISK, ExceptionSeverity.HIGH,
             "Order At Risk — FlipMart", "ORD-7002 depends on delayed shipment SHP-88202",
             "ORDER", "ORD-7002", "SKU-1003", 1, 520000, 7.0, 4.0,
             "Partial fulfillment from available stock + expedite remaining", 46, 2, 18),
            ("EXC-012", ExceptionCategory.ORDER_AT_RISK, ExceptionSeverity.MEDIUM,
             "Order At Risk — Reliance Retail", "ORD-7008 impacted by SKU-1004 shortage",
             "ORDER", "ORD-7008", "SKU-1004", 1, 210000, 2.0, 0,
             "Substitute with compatible SKU or negotiate delivery extension", 46, 2, 8),
            # Equipment
            ("EXC-013", ExceptionCategory.EQUIPMENT_ISSUE, ExceptionSeverity.LOW,
             "Forklift Low Battery", "FL-05 battery at 12% — needs charging",
             "FORKLIFT", "FL-05", None, 0, 0, None, 0,
             "Route to charging station", 48, 1, 20),
            ("EXC-014", ExceptionCategory.EQUIPMENT_ISSUE, ExceptionSeverity.MEDIUM,
             "Forklift Maintenance Due", "FL-03 overdue for scheduled maintenance",
             "FORKLIFT", "FL-03", None, 0, 15000, None, 0,
             "Schedule maintenance during next shift change", 30, 1, -18),
            ("EXC-015", ExceptionCategory.SHIPMENT_DELAY, ExceptionSeverity.MEDIUM,
             "Inbound Shipment Delay", "Shipment SHP-88222 minor delay — traffic",
             "SHIPMENT", "SHP-88222", "SKU-2010", 0, 45000, 20.0, 1.5,
             "Monitor — no action required yet", -24, 2, -18),
        ]
        for (code, cat, sev, title, desc, ent_type, ent_code,
             sku, orders, impact, coverage, delay, rec, px, py, pz) in exception_defs:
            exc = Exception_(
                code=code,
                category=cat,
                severity=sev,
                title=title,
                description=desc,
                entity_type=ent_type,
                entity_code=ent_code,
                affected_sku=sku,
                affected_orders=orders,
                potential_impact=impact,
                impact_currency="INR",
                inventory_coverage_days=coverage,
                delay_hours=delay,
                recommendation=rec,
                resolved=False,
                position_x=px,
                position_y=py,
                position_z=pz,
            )
            db.add(exc)

        db.commit()
        print("✅  Seed data created successfully.")
        print(f"    Warehouse:  1")
        print(f"    Aisles:     {len(aisles)}")
        print(f"    Bays:       {len(bays)}")
        print(f"    Docks:      {len(docks)}")
        print(f"    Parking:    {len(parking_slots)}")
        print(f"    Trucks:     {len(trucks)}")
        print(f"    Pallets:    {len(pallets)}")
        print(f"    Shipments:  {len(shipments)}")
        print(f"    Suppliers:  {len(suppliers)}")
        print(f"    Inventory:  100")
        print(f"    Forklifts:  5")
        print(f"    Orders:     20")
        print(f"    Events:     {len(event_defs)}")
        print(f"    Exceptions: {len(exception_defs)}")

    except Exception as e:
        db.rollback()
        print(f"❌  Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    _seed()
