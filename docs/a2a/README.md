# Agent-to-Agent (A2A) Communication — Future Architecture

This document describes the *intended* future A2A architecture for
ChainPilot. **Nothing described here is implemented yet.**

## Purpose

As the number of specialized agents grows (logistics, inventory, warehouse,
supplier-risk, demand, cost-optimization, document, exception, simulation,
communication, validation), some workflows will require agents to
coordinate directly with one another rather than always routing through the
Orchestrator — for example, the Exception agent negotiating a recovery plan
jointly with Logistics and Inventory agents before presenting a single
recommendation upstream.

## Intended shape

```
Orchestrator Agent
       │
       ├── Specialized Agent A ──┐
       │                         │  A2A message bus
       ├── Specialized Agent B ──┤  (future)
       │                         │
       └── Specialized Agent C ──┘
```

Planned characteristics of the future A2A layer:

- **Message bus**: a lightweight, addressable channel (e.g. an internal
  event bus or a dedicated A2A server, configured via `A2A_SERVER_URL`)
  that agents can publish to and subscribe from.
- **Structured messages**: typed request/response/negotiation envelopes,
  independent of MCP tool schemas, so agents can propose, counter, and
  agree on joint actions.
- **Human-in-the-loop checkpoints**: any multi-agent agreement that results
  in a recommended action still passes through the existing
  recommend → validate → human approval → execute pipeline; A2A does not
  bypass human oversight.
- **Traceability**: every A2A exchange should be attributable back to the
  Orchestrator's originating user request, for audit and debugging.

## Explicitly out of scope for now

- No message bus, transport, or SDK has been chosen.
- No agent currently talks to another agent directly; all coordination
  today would go through the Orchestrator only (and even that is not yet
  implemented).
- This document exists purely to reserve the architectural seam so future
  work can slot in without restructuring the agent or MCP layers.
