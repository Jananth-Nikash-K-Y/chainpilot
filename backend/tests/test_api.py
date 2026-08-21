"""Regression tests for the read API and the bugs fixed alongside it."""
import pytest

READ_ENDPOINTS = [
    "/api/warehouse", "/api/aisles", "/api/bays", "/api/trucks", "/api/docks",
    "/api/parking-slots", "/api/shipments", "/api/pallets", "/api/inventory",
    "/api/events", "/api/exceptions", "/api/orders", "/api/forklifts",
    "/api/suppliers",
]

SEVERITY_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]


@pytest.mark.parametrize("path", READ_ENDPOINTS)
def test_read_endpoints_return_rows(client, path):
    r = client.get(path)
    assert r.status_code == 200, r.text
    assert isinstance(r.json(), list)


def test_liveness_and_health_summary(client):
    assert client.get("/health").json()["status"] == "ok"
    h = client.get("/api/health").json()
    assert 0 <= h["supply_chain_health"] <= 100
    assert h["total_trucks"] > 0


def test_exceptions_sorted_most_severe_first(client):
    """Regression: ORDER BY on the severity string sorted CRITICAL last."""
    severities = [e["severity"] for e in client.get("/api/exceptions").json()]
    ranks = [SEVERITY_ORDER.index(s) for s in severities]
    assert ranks == sorted(ranks), f"not severity-ordered: {severities}"
    assert severities[0] == "CRITICAL"


def test_inventory_filter_rejects_invalid_status(client):
    """Regression: an unknown status silently returned zero rows."""
    assert client.get("/api/inventory?stock_status=CRITICAL").status_code == 200
    assert client.get("/api/inventory?stock_status=critical").status_code == 422
    assert client.get("/api/inventory?stock_status=NONSENSE").status_code == 422


def test_enum_fields_serialise_as_bare_values(client):
    """Regression: enums leaked as 'ExceptionSeverity.CRITICAL'."""
    for e in client.get("/api/exceptions").json():
        assert "." not in e["severity"]
        assert e["severity"] in SEVERITY_ORDER
    for t in client.get("/api/trucks").json():
        assert "." not in t["status"] and "." not in t["risk"]


def test_truck_and_dock_assignments_agree(client):
    """Regression: seeded trucks claimed docks that reported AVAILABLE."""
    docks = {d["code"]: d for d in client.get("/api/docks").json()}
    for t in client.get("/api/trucks").json():
        if not t["dock_code"]:
            continue
        dock = docks[t["dock_code"]]
        assert dock["current_truck_code"] == t["code"], (
            f"{t['code']} claims {t['dock_code']} but dock reports "
            f"{dock['current_truck_code']} ({dock['status']})"
        )
