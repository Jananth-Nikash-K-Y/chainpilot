# ChainPilot Architecture

This document describes ChainPilot's intended layered architecture. It
reflects the target design; large parts are not implemented yet — see each
directory's README for current status.

## 1. Application layering

```
Frontend
   │
   ▼
   API
   │
   ▼
Backend Services
   │
   ▼
Domain Layer
   │
   ▼
Database
```

- **Frontend** — React/TypeScript UI, including the Control Tower shell and
  the Three.js-based Digital Twin scene. Talks to the backend only through
  the API layer (`services/` in `frontend/src`).
- **API** — FastAPI route handlers (`backend/app/api`). Routes translate
  HTTP requests into service calls and responses back into HTTP. Routes
  contain **no business logic**.
- **Backend Services** — (`backend/app/services`) orchestrate use cases,
  calling into the domain layer and repositories. This is where application
  logic (as opposed to route or DB plumbing) lives.
- **Domain Layer** — (`backend/app/domain`) core business rules and
  entities, framework-independent.
- **Repositories** — (`backend/app/repositories`) the only layer allowed to
  issue SQLAlchemy queries against the database.
- **Database** — PostgreSQL, accessed exclusively through repositories.

## 2. AI / agent layering

```
AI Layer
   │
   ▼
Orchestrator
   │
   ▼
Specialized Agents
   │
   ▼
MCP Tools
```

- **Orchestrator** (`agents/orchestrator`) — receives a user or system
  goal, decides which specialized agent(s) are relevant, and coordinates
  their responses into a single outcome.
- **Specialized Agents** (`agents/logistics`, `agents/inventory`,
  `agents/warehouse`, `agents/supplier-risk`, `agents/demand`,
  `agents/cost-optimization`, `agents/document`, `agents/exception`,
  `agents/simulation`, `agents/communication`, `agents/validation`) — each
  owns one operational domain and exposes it to the Orchestrator.
- **MCP Tools** (`mcp/tools`) — the only way agents read or act on
  operational data (trucks, shipments, inventory, warehouse capacity, docks,
  suppliers, orders, exceptions, simulations, recommendations, actions).
  Agents never talk to the database directly.
- **Business Data** — ultimately the same PostgreSQL database the backend
  uses, accessed via MCP tools that call backend services/repositories.

## 3. Digital Twin → Agent → Data relationship (future)

```
Digital Twin (frontend)
   │  renders live state of:
   │  warehouse, aisles, bays, docks, parking slots,
   │  trucks, trailers, forklifts, pallets, shipment routes
   ▼
Backend API (real-time state + operational events)
   ▲
   │  same underlying data, read via MCP tools
   │
Specialized Agents (reason about exceptions, risk, recovery options)
   │
   ▼
Recommendations → Human Approval → Actions → Operational Events
   │
   └──> fed back into the Digital Twin and Backend API, closing the loop
```

The Digital Twin is a *view* of the same operational data the agents
reason over — never a separate source of truth. Actions agents take (once
approved by a human) are expected to flow back through the backend as
`OperationalEvent`s, which both the Digital Twin and the Control Tower UI
subscribe to.

## 4. Human-in-the-loop principle

No agent-recommended action executes automatically. The intended pipeline
is always:

```
recommend_action → validate_action → human approval → execute_action
```

This is a hard architectural constraint, not just a UI affordance — the
`validation` agent and `execute_action` MCP tool are separate from
`recommend_action` specifically so an approval gate can sit between them.

## 5. Future extensions (not built yet)

- **A2A communication** between specialized agents — see
  `docs/a2a/README.md` for the intended design.
- **Simulation engine** for delay/disruption scenarios (`agents/simulation`,
  `simulate_delay` / `calculate_recovery_options` MCP tools).
- **Real-time event streaming** from backend to frontend for live Digital
  Twin updates (transport not yet chosen).
