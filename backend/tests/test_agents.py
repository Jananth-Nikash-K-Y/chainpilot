"""Tests for the agent layer and the human-in-the-loop approval gate."""


def test_query_engages_agents_and_records_tool_calls(client):
    r = client.post("/api/ai/query", json={"query": "what inventory is at risk?"})
    assert r.status_code == 200, r.text
    d = r.json()

    assert d["response"]
    assert d["agents"], "no agent engaged"
    assert any(a["agent"] == "inventory" for a in d["agents"])

    # Every agent must show the tools it actually called — that trace is the
    # evidence behind the answer.
    assert all(a["tool_calls"] for a in d["agents"])


def test_query_routes_to_the_relevant_domain(client):
    supplier = client.post("/api/ai/query", json={"query": "which suppliers are risky?"}).json()
    assert any(a["agent"] == "supplier-risk" for a in supplier["agents"])

    logistics = client.post("/api/ai/query", json={"query": "dock congestion and waiting trucks"}).json()
    assert any(a["agent"] == "logistics" for a in logistics["agents"])


def test_empty_query_rejected(client):
    assert client.post("/api/ai/query", json={"query": "   "}).status_code == 422


def test_proposed_actions_are_validated_before_the_human_sees_them(client):
    d = client.post("/api/ai/query", json={"query": "what is at risk right now?"}).json()
    assert d["actions"], "agents proposed nothing"
    for a in d["actions"]:
        assert a["status"] in ("PROPOSED", "VALIDATED")
        assert a["validation_notes"], "action reached the operator unvalidated"
        assert 0.0 <= a["confidence"] <= 1.0


def test_approve_executes_and_changes_operational_state(fresh_client):
    c = fresh_client
    before = c.get("/api/inventory?stock_status=CRITICAL").json()
    assert before, "expected seeded critical stock"

    d = c.post("/api/ai/query", json={"query": "inventory at risk"}).json()
    action = next(a for a in d["actions"] if a["kind"] == "RAISE_REPLENISHMENT")

    res = c.post(f"/api/actions/{action['id']}/approve").json()
    assert res["ok"], res["message"]
    assert res["action"]["status"] == "EXECUTED"

    # The replenished SKU should no longer be critical...
    after = {i["sku"] for i in c.get("/api/inventory?stock_status=CRITICAL").json()}
    assert action["entity_code"] not in after

    # ...and the change must be recorded as an operational event.
    messages = [e["message"] for e in c.get("/api/events?limit=5").json()]
    assert any("[agent]" in m for m in messages)


def test_executed_action_cannot_be_approved_twice(fresh_client):
    c = fresh_client
    d = c.post("/api/ai/query", json={"query": "inventory at risk"}).json()
    action_id = d["actions"][0]["id"]

    assert c.post(f"/api/actions/{action_id}/approve").json()["ok"]
    assert c.post(f"/api/actions/{action_id}/approve").status_code == 409


def test_rejected_action_does_not_execute(fresh_client):
    c = fresh_client
    d = c.post("/api/ai/query", json={"query": "inventory at risk"}).json()
    action_id = d["actions"][0]["id"]

    res = c.post(f"/api/actions/{action_id}/reject").json()
    assert res["action"]["status"] == "REJECTED"
    # Rejection is terminal — approving afterwards must not run it.
    assert c.post(f"/api/actions/{action_id}/approve").status_code == 409


def test_unknown_action_returns_404(client):
    assert client.post("/api/actions/999999/approve").status_code == 404


def test_simulate_projects_impact(client):
    delayed = [s for s in client.get("/api/shipments").json() if s["status"] == "DELAYED"]
    assert delayed
    r = client.post(
        "/api/simulate",
        json={"shipment_code": delayed[0]["code"], "extra_hours": 4},
    )
    assert r.status_code == 200
    sim = r.json()
    assert sim["projected_delay_hours"] > sim["current_delay_hours"]
    assert sim["projected_severity"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")

    assert client.post(
        "/api/simulate", json={"shipment_code": "NOPE-000", "extra_hours": 1}
    ).status_code == 404


def test_agent_and_tool_catalogues_exposed(client):
    agents = client.get("/api/agents").json()
    assert {a["name"] for a in agents} >= {"logistics", "inventory", "exception"}
    assert all(a["domain"] for a in agents)

    tools = client.get("/api/tools").json()
    names = {t["name"] for t in tools}
    assert "get_delayed_shipments" in names
    # Write tools must be explicitly flagged as such.
    assert next(t for t in tools if t["name"] == "execute_action")["writes"] is True
    assert next(t for t in tools if t["name"] == "get_delayed_shipments")["writes"] is False
