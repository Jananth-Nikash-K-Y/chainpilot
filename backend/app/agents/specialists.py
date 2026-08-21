"""The specialized agents. Each owns exactly one operational domain."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.agents.base import Agent, AgentResult, Finding, ProposedAction
from app.models.models import ActionKind
from app.services import tools


def _sev_from_delay(hours: float) -> str:
    if hours >= 8:
        return "CRITICAL"
    if hours >= 4:
        return "HIGH"
    if hours >= 2:
        return "MEDIUM"
    return "LOW"


class LogisticsAgent(Agent):
    name = "logistics"
    domain = "Trucks, docks, yard flow and shipment movement"
    keywords = (
        "truck", "trucks", "dock", "docks", "yard", "delay", "delayed", "shipment",
        "shipments", "transit", "carrier", "congestion", "utilisation", "utilization",
        "berth", "arrival", "gate",
    )

    def run(self, db: Session, goal: str) -> AgentResult:
        r = AgentResult(agent=self.name, relevance=self.relevance(goal))

        delayed = self._call(r, "get_delayed_shipments", tools.get_delayed_shipments, db)
        dock = self._call(r, "get_dock_utilization", tools.get_dock_utilization, db)
        trucks = self._call(r, "get_truck_status", tools.get_truck_status, db)

        for s in delayed[:3]:
            r.findings.append(
                Finding(
                    headline=f"{s['code']} running {s['delay_hours']:.1f}h late",
                    detail=f"{s['direction'].title()} from {s['supplier'] or s['origin'] or 'unknown origin'} "
                           f"to {s['destination'] or 'site'}.",
                    severity=_sev_from_delay(s["delay_hours"]),
                    entity_type="SHIPMENT",
                    entity_code=s["code"],
                    metrics={"delay_hours": s["delay_hours"], "risk": s["risk"]},
                )
            )
            r.actions.append(
                ProposedAction(
                    kind=ActionKind.EXPEDITE_SHIPMENT.value,
                    title=f"Expedite {s['code']}",
                    rationale=f"Recovers up to 4h of the {s['delay_hours']:.1f}h slip before it "
                              f"cascades into dock and order plans.",
                    entity_type="SHIPMENT",
                    entity_code=s["code"],
                    projected_savings=round(s["delay_hours"] * 45000, 2),
                    projected_impact=round(s["delay_hours"] * 6000, 2),
                    confidence=0.74,
                )
            )

        if dock["utilization_pct"] >= 70 or dock["blocked"]:
            sev = "HIGH" if dock["utilization_pct"] >= 80 or dock["blocked"] else "MEDIUM"
            r.findings.append(
                Finding(
                    headline=f"Dock utilisation at {dock['utilization_pct']}%",
                    detail=f"{dock['busy']} of {dock['total']} doors busy, {dock['available']} free"
                           + (f", {dock['blocked']} blocked ({', '.join(dock['blocked_codes'])})"
                              if dock["blocked"] else ""),
                    severity=sev,
                    entity_type="DOCK",
                    entity_code=dock["blocked_codes"][0] if dock["blocked_codes"] else "ALL",
                    metrics=dock,
                )
            )
            if dock["blocked_codes"]:
                r.actions.append(
                    ProposedAction(
                        kind=ActionKind.SCHEDULE_MAINTENANCE.value,
                        title=f"Return {dock['blocked_codes'][0]} to service",
                        rationale="Moving maintenance out of the arrival peak frees a door while "
                                  "utilisation is high.",
                        entity_type="DOCK",
                        entity_code=dock["blocked_codes"][0],
                        projected_savings=68000.0,
                        projected_impact=12000.0,
                        confidence=0.8,
                    )
                )

        waiting = [t for t in trucks if t["status"] == "WAITING"]
        if waiting and dock["available_codes"]:
            r.findings.append(
                Finding(
                    headline=f"{len(waiting)} truck(s) waiting with {dock['available']} dock(s) free",
                    detail="Yard queue can be cleared immediately by berthing waiting vehicles.",
                    severity="MEDIUM",
                    entity_type="TRUCK",
                    entity_code=waiting[0]["code"],
                )
            )
            r.actions.append(
                ProposedAction(
                    kind=ActionKind.REASSIGN_DOCK.value,
                    title=f"Berth {waiting[0]['code']} at {dock['available_codes'][0]}",
                    rationale=f"{waiting[0]['carrier']} is idle in the yard while "
                              f"{dock['available_codes'][0]} sits empty.",
                    entity_type="TRUCK",
                    entity_code=waiting[0]["code"],
                    projected_savings=32000.0,
                    confidence=0.88,
                )
            )

        r.summary = (
            f"{len(delayed)} delayed shipment(s), dock utilisation {dock['utilization_pct']}%, "
            f"{len(waiting)} truck(s) waiting."
        )
        return r


class InventoryAgent(Agent):
    name = "inventory"
    domain = "Stock cover, replenishment and SKU risk"
    keywords = (
        "inventory", "stock", "sku", "replenish", "replenishment", "reorder",
        "shortage", "coverage", "low", "critical", "bay", "pallet", "out of stock",
    )

    def run(self, db: Session, goal: str) -> AgentResult:
        r = AgentResult(agent=self.name, relevance=self.relevance(goal))
        at_risk = self._call(r, "get_inventory_at_risk", tools.get_inventory_at_risk, db)

        for i in at_risk[:4]:
            sev = "CRITICAL" if i["days_of_coverage"] < 3 else "HIGH" if i["days_of_coverage"] < 8 else "MEDIUM"
            r.findings.append(
                Finding(
                    headline=f"{i['sku']} — {i['days_of_coverage']:.1f} days of cover",
                    detail=f"{i['name']}: {i['on_hand']} on hand against a reorder point of "
                           f"{i['reorder_point']}"
                           + (f", supplied by {i['supplier']}" if i["supplier"] else ""),
                    severity=sev,
                    entity_type="INVENTORY",
                    entity_code=i["sku"],
                    metrics={
                        "days_of_coverage": i["days_of_coverage"],
                        "on_hand": i["on_hand"],
                        "reorder_point": i["reorder_point"],
                    },
                )
            )
            if sev in ("CRITICAL", "HIGH"):
                r.actions.append(
                    ProposedAction(
                        kind=ActionKind.RAISE_REPLENISHMENT.value,
                        title=f"Emergency replenishment for {i['sku']}",
                        rationale=f"Cover falls below lead time in {i['days_of_coverage']:.1f} days; "
                                  f"a standard PO will not land in time.",
                        entity_type="INVENTORY",
                        entity_code=i["sku"],
                        projected_savings=round(max(0.0, (10 - i["days_of_coverage"])) * 48000, 2),
                        projected_impact=round(i["reorder_point"] * 120, 2),
                        confidence=0.83,
                    )
                )

        r.summary = (
            f"{len(at_risk)} SKU(s) at or below reorder point"
            + (f"; lowest cover {at_risk[0]['days_of_coverage']:.1f}d on {at_risk[0]['sku']}."
               if at_risk else ".")
        )
        return r


class SupplierRiskAgent(Agent):
    name = "supplier-risk"
    domain = "Supplier reliability and single-source exposure"
    keywords = ("supplier", "suppliers", "vendor", "reliability", "sourcing", "source", "factory")

    def run(self, db: Session, goal: str) -> AgentResult:
        r = AgentResult(agent=self.name, relevance=self.relevance(goal))
        suppliers = self._call(r, "get_supplier_risk", tools.get_supplier_risk, db)

        risky = [s for s in suppliers if s["reliability_score"] < 75]
        for s in risky[:3]:
            r.findings.append(
                Finding(
                    headline=f"{s['name']} reliability at {s['reliability_score']:.0f}%",
                    detail=f"{s['code']} in {s['location'] or 'unknown location'} with "
                           f"{s['open_shipments']} open shipment(s).",
                    severity="CRITICAL" if s["reliability_score"] < 62 else "HIGH",
                    entity_type="SUPPLIER",
                    entity_code=s["code"],
                    metrics={"reliability": s["reliability_score"], "open": s["open_shipments"]},
                )
            )
            r.actions.append(
                ProposedAction(
                    kind=ActionKind.CONTACT_SUPPLIER.value,
                    title=f"Escalate with {s['code']} for a committed recovery date",
                    rationale=f"Reliability {s['reliability_score']:.0f}% is below tolerance across "
                              f"{s['open_shipments']} open shipment(s).",
                    entity_type="SUPPLIER",
                    entity_code=s["code"],
                    projected_savings=round(s["open_shipments"] * 65000, 2),
                    confidence=0.64,
                )
            )

        r.summary = (
            f"{len(risky)} supplier(s) below 75% reliability out of {len(suppliers)} reviewed."
        )
        return r


class WarehouseAgent(Agent):
    name = "warehouse"
    domain = "Aisle capacity, equipment and internal throughput"
    keywords = (
        "warehouse", "aisle", "aisles", "capacity", "forklift", "forklifts",
        "equipment", "picking", "throughput", "battery", "utilisation", "utilization",
    )

    def run(self, db: Session, goal: str) -> AgentResult:
        r = AgentResult(agent=self.name, relevance=self.relevance(goal))
        cap = self._call(r, "get_warehouse_capacity", tools.get_warehouse_capacity, db)

        if cap["utilization_pct"] >= 80:
            r.findings.append(
                Finding(
                    headline=f"Warehouse {cap['utilization_pct']:.0f}% utilised",
                    detail="Approaching the point where put-away starts blocking picking lanes.",
                    severity="HIGH" if cap["utilization_pct"] >= 90 else "MEDIUM",
                    entity_type="WAREHOUSE",
                    entity_code=cap["warehouse"] or "WH-01",
                    metrics={"utilization_pct": cap["utilization_pct"]},
                )
            )

        for code in cap["forklifts_low_battery"]:
            r.findings.append(
                Finding(
                    headline=f"{code} below 25% battery",
                    detail="Risks stalling mid-aisle during the picking peak.",
                    severity="MEDIUM",
                    entity_type="FORKLIFT",
                    entity_code=code,
                )
            )
            r.actions.append(
                ProposedAction(
                    kind=ActionKind.RECHARGE_FORKLIFT.value,
                    title=f"Route {code} to the charging station",
                    rationale="Pre-empts an unplanned stoppage in an active aisle.",
                    entity_type="FORKLIFT",
                    entity_code=code,
                    projected_savings=18000.0,
                    projected_impact=3000.0,
                    confidence=0.9,
                )
            )

        r.summary = (
            f"Warehouse {cap['utilization_pct']:.0f}% utilised, "
            f"{len(cap['forklifts_low_battery'])} forklift(s) low on charge."
        )
        return r


class DemandAgent(Agent):
    name = "demand"
    domain = "Customer orders, promises and revenue exposure"
    keywords = (
        "order", "orders", "customer", "demand", "promise", "promised", "sla",
        "revenue", "fulfil", "fulfill", "tomorrow", "at risk",
    )

    def run(self, db: Session, goal: str) -> AgentResult:
        r = AgentResult(agent=self.name, relevance=self.relevance(goal))
        orders = self._call(r, "get_orders_at_risk", tools.get_orders_at_risk, db)

        exposed = sum(o["value"] for o in orders)
        for o in orders[:3]:
            r.findings.append(
                Finding(
                    headline=f"{o['code']} at risk — {o['currency']} {o['value']:,.0f}",
                    detail=f"{o['customer']}, {o['items']} line(s), {o['priority']} priority.",
                    severity="CRITICAL" if o["value"] > 500000 else "HIGH",
                    entity_type="ORDER",
                    entity_code=o["code"],
                    metrics={"value": o["value"], "items": o["items"]},
                )
            )
            r.actions.append(
                ProposedAction(
                    kind=ActionKind.SPLIT_ORDER.value,
                    title=f"Split {o['code']} — release available lines",
                    rationale=f"Protects the bulk of {o['currency']} {o['value']:,.0f} while the "
                              f"blocking supply is recovered.",
                    entity_type="ORDER",
                    entity_code=o["code"],
                    projected_savings=round(o["value"] * 0.6, 2),
                    confidence=0.72,
                )
            )

        r.summary = f"{len(orders)} order(s) at risk, ₹{exposed:,.0f} exposed."
        return r


class ExceptionAgent(Agent):
    name = "exception"
    domain = "Cross-domain triage of open exceptions"
    keywords = (
        "exception", "exceptions", "issue", "issues", "problem", "problems", "wrong",
        "risk", "risks", "alert", "alerts", "why", "what", "status", "summary",
        "overview", "brief", "happening",
    )

    def relevance(self, goal: str) -> float:
        # The triage agent is the fallback: always at least mildly relevant so a
        # vague question ("what's going on?") still gets a grounded answer.
        return max(0.35, super().relevance(goal))

    def run(self, db: Session, goal: str) -> AgentResult:
        r = AgentResult(agent=self.name, relevance=self.relevance(goal))
        open_exc = self._call(r, "get_open_exceptions", tools.get_open_exceptions, db)

        for e in open_exc[:4]:
            options = self._call(
                r,
                "calculate_recovery_options",
                tools.calculate_recovery_options,
                db,
                exception_code=e["code"],
                summary=f"{e['code']}: ranked options",
            )
            r.findings.append(
                Finding(
                    headline=f"{e['code']} · {e['title']}",
                    detail=e["description"],
                    severity=str(e["severity"]),
                    entity_type=e["entity_type"],
                    entity_code=e["entity_code"],
                    metrics={
                        "impact": e["potential_impact"],
                        "currency": e["currency"],
                        "affected_orders": e["affected_orders"],
                    },
                )
            )
            if options:
                best = options[0]
                r.actions.append(
                    ProposedAction(
                        kind=best["kind"],
                        title=best["title"],
                        rationale=best["rationale"],
                        entity_type=e["entity_type"],
                        entity_code=e["entity_code"],
                        exception_code=e["code"],
                        projected_savings=best["projected_savings"],
                        projected_impact=best["projected_impact"],
                        confidence=best["confidence"],
                    )
                )

        crit = len([e for e in open_exc if str(e["severity"]) == "CRITICAL"])
        total_impact = sum(e["potential_impact"] for e in open_exc)
        r.summary = (
            f"{len(open_exc)} open exception(s), {crit} critical, "
            f"₹{total_impact:,.0f} of exposure."
        )
        return r


class SimulationAgent(Agent):
    name = "simulation"
    domain = "What-if projection of delays and disruptions"
    keywords = ("simulate", "what if", "what-if", "scenario", "project", "forecast", "impact if")

    def run(self, db: Session, goal: str) -> AgentResult:
        r = AgentResult(agent=self.name, relevance=self.relevance(goal))
        delayed = self._call(r, "get_delayed_shipments", tools.get_delayed_shipments, db, limit=3)

        for s in delayed[:2]:
            sim = self._call(
                r,
                "simulate_delay",
                tools.simulate_delay,
                db,
                shipment_code=s["code"],
                extra_hours=4.0,
                summary=f"{s['code']} +4h",
            )
            if "error" in sim:
                continue
            r.findings.append(
                Finding(
                    headline=f"If {s['code']} slips another 4h → {sim['projected_severity']}",
                    detail=f"Delay would reach {sim['projected_delay_hours']}h, exposing "
                           f"{sim['orders_exposed']} order(s) worth "
                           f"{sim['currency']} {sim['value_exposed']:,.0f}.",
                    severity=str(sim["projected_severity"]),
                    entity_type="SHIPMENT",
                    entity_code=s["code"],
                    metrics=sim,
                )
            )

        r.summary = f"Projected {len(delayed)} delay scenario(s) forward by 4h."
        return r


ALL_AGENTS: list[Agent] = [
    ExceptionAgent(),
    LogisticsAgent(),
    InventoryAgent(),
    SupplierRiskAgent(),
    WarehouseAgent(),
    DemandAgent(),
    SimulationAgent(),
]
