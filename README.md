# ChainPilot

**Agentic AI Supply Chain Control Tower**

Operate a supply chain through a live 3D digital twin driven by a network of
specialized AI agents. Agents reason over real operational data, propose
recovery actions, and — only after a human approves — execute them.

---

## What it does

Ask a question in plain language. An orchestrator routes it to the relevant
specialized agents, each of which calls tools against live data, returns
findings, and proposes actions. Nothing is applied until you approve it.

```mermaid
flowchart LR
    U["Operator asks<br/>'what inventory is at risk?'"] --> O[Orchestrator]
    O -->|routes by relevance| A1[Inventory agent]
    O --> A2[Exception agent]
    O --> A3[Demand agent]
    A1 & A2 & A3 -->|call tools| T[(Operational data)]
    A1 & A2 & A3 --> F["Findings +<br/>proposed actions"]
    F --> V{validate_action}
    V --> H["👤 Human approval"]
    H -->|approve| X[execute_action]
    H -->|reject| R[Recorded, not run]
    X --> E[OperationalEvent]
    E --> D[Digital twin updates]

    style H fill:#fff4e1,stroke:#b8720b,stroke-width:2px,color:#000
    style X fill:#e9f7ef,stroke:#1f7a4d,color:#000
    style R fill:#f4f4f6,stroke:#6b7488,color:#000
```

The approval gate is a hard architectural constraint, not a UI affordance:
`validate_action` and `execute_action` are separate tools from
`propose_action` precisely so a human can sit between them.

---

## Architecture

Two stacks that meet at one database. The twin and the agents are two views
of the same operational truth — never separate systems.

```mermaid
flowchart TB
    subgraph APP["Application stack"]
        direction TB
        FE["Frontend<br/><i>React + Three.js</i>"] --> API["API<br/><i>FastAPI routes, no business logic</i>"]
        API --> SVC["Services<br/><i>use-case orchestration</i>"]
        SVC --> DOM["Domain<br/><i>business rules</i>"]
        DOM --> REPO["Repositories<br/><i>only layer issuing SQL</i>"]
    end

    subgraph AI["Agent stack"]
        direction TB
        GOAL["Goal / question"] --> ORCH["Orchestrator<br/><i>routes by relevance</i>"]
        ORCH --> AG["Specialized agents<br/><i>one domain each</i>"]
        AG --> TOOLS["Tools<br/><i>the only data access agents get</i>"]
    end

    REPO --> DB[("SQLite<br/>chainpilot.db")]
    TOOLS --> DB

    style DB fill:#0f1b3c,stroke:#1e4fd8,color:#fff
    style AI fill:#edebfb,stroke:#5b3fd1,color:#000
    style APP fill:#eaf0ff,stroke:#1e4fd8,color:#000
```

**Rules this enforces**

| Rule | Why |
|---|---|
| Routes contain no business logic | Keeps HTTP concerns swappable |
| Only repositories issue SQL | One place to reason about queries |
| Agents never touch the database | All access goes through named, auditable tools |
| Every tool call is recorded | The trace is the evidence behind an answer |
| Write tools are flagged `writes: true` | Read/write separation is explicit |

---

## The digital twin

The 3D scene is a *view* of the same data the agents reason over. Site layout
is defined once in `frontend/src/constants/index.ts` and mirrored by
`backend/app/seed.py` — change both together or entities render outside the
structures they belong to.

```
   x: -40        -34 … -16        2       8 ──────────────── 52
      GATE        PARKING       APRON  DOCK WALL         WAREHOUSE
       │             │            │        │                  │
       │   20 bays   │  trucks    │  10 doors,      5 aisles × 10 bays
       │             │  berth     │  status-lit     racking, 3 levels
```

Clicking any object — truck, dock, bay, forklift, exception marker — opens an
inspector bound to live backend state.

---

## Quick start

Two terminals. No database server to install: ChainPilot uses SQLite by
default, created automatically on first run.

**Backend**

```bash
cd backend && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements-dev.txt && python -m app.seed && uvicorn app.main:app --reload
```

**Frontend**

```bash
cd frontend && npm install && npm run dev
```

Open <http://localhost:5173>. The Vite dev server proxies `/api` to the
backend, so there is no CORS setup and no origin to configure.

Try asking:

- *what is at risk right now?*
- *which trucks are delayed?*
- *what inventory is at risk?*
- *which suppliers are risky?*

---

## Repository layout

| Path | Contents |
|---|---|
| `frontend/` | React + TypeScript + Vite + Three.js digital twin and control tower |
| `backend/app/api/` | FastAPI routes — thin HTTP translation only |
| `backend/app/agents/` | Orchestrator, agent base classes, specialized agents |
| `backend/app/services/tools.py` | The tool registry agents call |
| `backend/app/models/` | SQLAlchemy ORM models |
| `backend/app/seed.py` | Realistic synthetic operational data |
| `mcp/` | MCP server that will expose the same tool registry externally |
| `docs/` | Architecture, API, agent, MCP, A2A and domain docs |
| `tests/`, `backend/tests/` | Integration and API/agent tests |

---

## API surface

**Operational reads** — `/api/warehouse`, `/aisles`, `/bays`, `/trucks`,
`/docks`, `/parking-slots`, `/shipments`, `/pallets`, `/inventory`, `/events`,
`/exceptions`, `/orders`, `/forklifts`, `/suppliers`, `/health`

**Agent layer**

| Endpoint | Purpose |
|---|---|
| `POST /api/ai/query` | Run a goal through the orchestrator |
| `GET /api/actions` | List proposed / decided actions |
| `POST /api/actions/{id}/approve` | Re-validate, then execute |
| `POST /api/actions/{id}/reject` | Decline an action |
| `POST /api/simulate` | Project a shipment delay forward |
| `GET /api/agents` | Agent roster and domains |
| `GET /api/tools` | Tool catalogue, with write flags |

Interactive docs at <http://localhost:8000/docs>.

---

## Development

```bash
cd backend && .venv/bin/python -m pytest tests/ -q
```

```bash
cd frontend && npm run lint && npm run build
```

**Switching to PostgreSQL** — nothing above the repository layer changes:

```bash
pip install "psycopg[binary]>=3.1"
```

Then set `DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/chainpilot`.

**Plugging in an LLM** — the agents currently reason deterministically over
live data, which keeps them testable and offline-capable. Set `LLM_PROVIDER`
and `LLM_API_KEY` in `.env` to route the reasoning step through a model; the
tool layer and approval gate are unchanged either way.

---

## Status

Working end to end: digital twin, operational API, agent orchestration, tool
layer, and the propose → validate → approve → execute loop with operational
event logging.

Not built yet:

1. MCP server exposing the tool registry to external agent runtimes
2. A2A communication between specialized agents
3. Real-time event streaming (twin currently refreshes on action)
4. LLM-backed reasoning behind the existing agent interface
5. Alembic migrations (schema is currently created on startup)

See [ARCHITECTURE.md](ARCHITECTURE.md) for the layering in detail.
