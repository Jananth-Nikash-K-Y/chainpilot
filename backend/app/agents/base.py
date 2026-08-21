"""Agent primitives.

An agent owns one operational domain. It decides whether a goal is relevant to
it, calls tools to gather evidence, and returns findings plus proposed actions.
It never queries the database directly and never executes anything — proposals
go through the human approval gate.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from app.services.tools import ToolCall


@dataclass
class Finding:
    """One observation an agent made, with the evidence behind it."""

    headline: str
    detail: str
    severity: str = "LOW"  # LOW | MEDIUM | HIGH | CRITICAL
    entity_type: str = ""
    entity_code: str = ""
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProposedAction:
    kind: str
    title: str
    rationale: str
    entity_type: str
    entity_code: str
    exception_code: str | None = None
    projected_impact: float = 0.0
    projected_savings: float = 0.0
    confidence: float = 0.0


@dataclass
class AgentResult:
    agent: str
    relevance: float                       # 0..1 — why the orchestrator picked it
    summary: str = ""
    findings: list[Finding] = field(default_factory=list)
    actions: list[ProposedAction] = field(default_factory=list)
    tool_calls: list[ToolCall] = field(default_factory=list)


class Agent:
    """Base class for every specialized agent."""

    name: str = "agent"
    domain: str = ""
    #: Terms that make a free-text goal relevant to this agent.
    keywords: tuple[str, ...] = ()

    def relevance(self, goal: str) -> float:
        """How strongly this agent matches the goal. 0 means skip."""
        if not goal:
            return 0.0
        text = goal.lower()
        hits = sum(1 for k in self.keywords if k in text)
        return min(1.0, hits / 2) if hits else 0.0

    def run(self, db: Session, goal: str) -> AgentResult:  # pragma: no cover - interface
        raise NotImplementedError

    # -- helpers ----------------------------------------------------------

    def _call(
        self,
        result: AgentResult,
        name: str,
        fn,
        /,
        *args,
        summary: str | None = None,
        **kwargs,
    ):
        """Invoke a tool and record the call on the result's trace."""
        value = fn(*args, **kwargs)
        if summary is None:
            if isinstance(value, list):
                summary = f"{len(value)} row(s)"
            elif isinstance(value, dict):
                summary = ", ".join(f"{k}={v}" for k, v in list(value.items())[:3])
            else:
                summary = str(value)
        trace_args = {k: v for k, v in kwargs.items() if k != "db"}
        result.tool_calls.append(ToolCall(tool=name, args=trace_args, result_summary=summary))
        return value
