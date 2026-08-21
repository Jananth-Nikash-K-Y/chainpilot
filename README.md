# ChainPilot

**Agentic AI Supply Chain Control Tower**

## Overview

ChainPilot is a platform for operating a supply chain through a live 3D
digital twin combined with a network of specialized AI agents. It will
eventually let operators see warehouses, trucks, docks, and inventory in
real time; surface operational exceptions as they emerge; simulate
recovery options; and — with human approval — let agents take action.

## Goals

- A believable, real-time 3D digital twin of warehouse and logistics
  operations (parking lots, dock doors, aisles, bays, trucks, trailers,
  pallets, shipment routes).
- A modular agent architecture (Orchestrator → specialized agents) exposed
  through MCP tools, so agents reason over live operational data.
- Human-in-the-loop control: agents recommend and simulate; humans approve;
  actions execute and are logged as operational events.
- A clean separation between frontend, backend, agents, and MCP so each
  layer can evolve independently.

## Repository structure

```
chainpilot/
├── frontend/    React + TypeScript + Vite + Three.js digital twin UI
├── backend/     FastAPI service (API → services → domain → repositories → DB)
├── agents/      Orchestrator + specialized agent definitions
├── mcp/         MCP server exposing operational tools to agents
├── database/    Alembic migrations + seed data
├── data/        Local raw/processed/sample data
├── docs/        Architecture, API, agent, MCP, A2A, domain docs
├── scripts/     Setup, database, and dev helper scripts
├── tests/       Cross-cutting integration/e2e tests
├── infra/       Docker/deployment configuration
└── .github/     CI workflows
```

See `ARCHITECTURE.md` for the layered architecture and the AI/agent flow.

## Planned architecture (high level)

```
Frontend (Digital Twin + Control Tower)
        │
        ▼
     Backend API
        │
        ▼
  Backend Services
        │
        ▼
   Domain Layer
        │
        ▼
    Database

AI Layer:
User → Orchestrator Agent → Specialized Agents → MCP Tools → Business Data
```

## Development prerequisites

- Node.js 20+
- Python 3.11+
- PostgreSQL 16 (or Docker)
- Docker + Docker Compose (optional, for running the full stack locally)

## Setup (placeholder)

```bash
# Frontend
cd frontend && npm install && npm run dev

# Backend
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload

# Full stack via Docker
docker compose up --build
```

## Status

This repository currently contains the **architectural foundation only**:
folder structure, config, and placeholder module boundaries. No application,
agent, or MCP tool logic has been implemented yet.

## Roadmap

1. ✅ Repository foundation (this phase)
2. Backend domain models + first migrations (Warehouse, Dock, Truck, etc.)
3. First MCP tools (read-only: `get_truck_status`, `get_inventory_position`, …)
4. Orchestrator + first specialized agent (e.g. Exception agent) wired to MCP
5. Frontend Control Tower shell (layout, routing, live data binding)
6. Digital Twin scene v1 (static warehouse + trucks, no interactions)
7. Simulation + recommendation + human approval + action execution loop
8. A2A communication layer between agents
