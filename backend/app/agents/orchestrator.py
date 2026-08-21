"""Orchestrator — routes a goal to the relevant specialized agents.

It does no domain reasoning of its own. It scores each agent against the goal,
runs the ones that match, persists their proposed actions in PROPOSED state,
and composes a single answer from what came back.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.agents.base import AgentResult
from app.agents.specialists import ALL_AGENTS
from app.services import tools

SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}


@dataclass
class OrchestratorRun:
    goal: str
    answer: str
    agents: list[AgentResult] = field(default_factory=list)
    action_ids: list[int] = field(default_factory=list)
    followups: list[str] = field(default_factory=list)


def _compose_answer(goal: str, results: list[AgentResult]) -> str:
    """Turn agent findings into one grounded paragraph."""
    findings = [f for r in results for f in r.findings]
    if not findings:
        return (
            "I checked shipments, docks, inventory, suppliers, orders and equipment — "
            "nothing is currently breaching thresholds. The network is running clean."
        )

    findings.sort(key=lambda f: SEVERITY_ORDER.get(f.severity, 9))
    critical = [f for f in findings if f.severity == "CRITICAL"]
    high = [f for f in findings if f.severity == "HIGH"]

    lead_parts: list[str] = []
    if critical:
        lead_parts.append(f"{len(critical)} critical")
    if high:
        lead_parts.append(f"{len(high)} high-severity")
    lead = " and ".join(lead_parts) if lead_parts else f"{len(findings)}"

    agent_names = ", ".join(r.agent for r in results)
    top = findings[:3]
    bullets = " ".join(f"{f.headline} — {f.detail}" for f in top)

    return (
        f"{lead} issue(s) found across {len(results)} agent(s) ({agent_names}). {bullets}"
    ).strip()


def _followups(results: list[AgentResult]) -> list[str]:
    out: list[str] = []
    for r in results:
        for f in r.findings[:1]:
            if f.entity_type == "SHIPMENT":
                out.append(f"What happens if {f.entity_code} slips another 4 hours?")
            elif f.entity_type == "INVENTORY":
                out.append(f"Which orders depend on {f.entity_code}?")
            elif f.entity_type == "SUPPLIER":
                out.append(f"What is our exposure to {f.entity_code}?")
            elif f.entity_type == "DOCK":
                out.append("How do I clear the dock queue?")
            elif f.entity_type == "ORDER":
                out.append(f"Can we still fulfil {f.entity_code} on time?")
    if not out:
        out = ["What is at risk right now?"]
    # de-dupe, keep order
    seen: set[str] = set()
    unique = [q for q in out if not (q in seen or seen.add(q))]
    return unique[:4]


def run_goal(db: Session, goal: str, *, max_agents: int = 4) -> OrchestratorRun:
    scored = sorted(
        ((a, a.relevance(goal)) for a in ALL_AGENTS),
        key=lambda p: p[1],
        reverse=True,
    )
    selected = [a for a, score in scored if score > 0][:max_agents]

    results: list[AgentResult] = []
    action_ids: list[int] = []

    for agent in selected:
        result = agent.run(db, goal)
        results.append(result)

        for proposal in result.actions:
            created = tools.propose_action(
                db,
                kind=proposal.kind,
                title=proposal.title,
                rationale=proposal.rationale,
                entity_type=proposal.entity_type,
                entity_code=proposal.entity_code,
                exception_code=proposal.exception_code,
                projected_impact=proposal.projected_impact,
                projected_savings=proposal.projected_savings,
                confidence=proposal.confidence,
                proposed_by=agent.name,
            )
            # Validate immediately so the human sees any blocking condition
            # alongside the proposal, before deciding.
            tools.validate_action(db, created["id"])
            action_ids.append(created["id"])

    db.commit()

    return OrchestratorRun(
        goal=goal,
        answer=_compose_answer(goal, results),
        agents=results,
        action_ids=action_ids,
        followups=_followups(results),
    )
