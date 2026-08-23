# Contributing to ChainPilot

**Contributions are very welcome** — code, bug reports, or just ideas.
ChainPilot is early, and the interesting problems are still wide open.

## Getting started

Fork the repo, then get it running locally. No database server to install:
ChainPilot uses SQLite by default and creates the file on first run.

```bash
cd backend && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements-dev.txt && python -m app.seed && uvicorn app.main:app --reload
```

```bash
cd frontend && npm install && npm run dev
```

Open <http://localhost:5173> and ask it *"what is at risk right now?"*.

## Ways to help

**Have an idea rather than a patch?** Open a
[Discussion](https://github.com/Jananth-Nikash-K-Y/chainpilot/discussions) or
an issue — how agents should reason, what an operator actually needs to see,
which supply chain problems are worth modelling. Domain knowledge is as
valuable here as code.

Good places to start, roughly easiest first:

| Area | What's needed |
|---|---|
| **New agent** | Add a specialist under `backend/app/agents/specialists.py` — pricing, carrier selection, customs, sustainability |
| **New tool** | Extend `backend/app/services/tools.py`; read tools are low-risk and self-contained |
| **Digital twin** | More detail or better interaction in `frontend/src/digital-twin` |
| **LLM reasoning** | Agents currently reason deterministically; the `LLM_PROVIDER` / `LLM_API_KEY` hooks exist but are unused |
| **MCP server** | `mcp/` is scaffolded — wire the existing tool registry to it |
| **A2A** | Let agents talk to each other instead of only reporting to the orchestrator |
| **Tests** | Especially frontend — currently thin |

## Submitting a change

1. Branch off `main`.
2. Make the change, with a test where behaviour is involved.
3. Check it passes:
   ```bash
   cd backend && .venv/bin/python -m pytest tests/ -q
   ```
   ```bash
   cd frontend && npm run lint && npm run build
   ```
4. Open a PR describing *what problem it solves*, not just what changed.

Small, focused PRs get reviewed faster than large ones. If you're planning
something substantial, open an issue first so we can agree the approach before
you spend the effort.

## Two rules worth knowing before you start

These aren't style preferences — the architecture depends on them:

- **Agents never touch the database.** All access goes through named tools in
  `app/services/tools.py`, so every read and write is auditable.
- **Nothing executes without human approval.** `propose_action`,
  `validate_action` and `execute_action` are deliberately separate so a person
  sits between a recommendation and its effect. Please don't collapse them.

---

## Development conventions

### General
- Keep layers separated: no business logic in frontend components, FastAPI
  route handlers, or agent executors — put it in `services`/`domain`.
- Every new module boundary (frontend feature folder, backend package,
  agent, MCP tool) should ship with at least a short README or module
  docstring describing its purpose, even before logic is implemented.
- Prefer small, incremental PRs that match the project roadmap in
  `README.md` over large multi-phase changes.

### Frontend
- TypeScript strict mode is on — avoid `any`.
- Co-locate feature-specific components under `src/features/<feature>`;
  only truly shared UI goes in `src/components`.
- Digital Twin rendering code stays under `src/digital-twin/*`; do not put
  Three.js code directly in page components.

### Backend
- Route handlers only parse/validate input and call a service — no direct
  database access from `app/api`.
- All database access goes through `app/repositories`.
- New domain entities get a model (`app/models`), schema
  (`app/schemas`), and, once behavior exists, a repository + service.

### Agents
- Each agent keeps its `agent.py` / `executor.py` / `config.py` /
  `prompts.py` / `schemas.py` split — don't collapse an agent into a single
  file as it grows.
- Agents call MCP tools for data access; they must not query the database
  directly.

### Commits
- Use conventional-commit-style prefixes where practical: `feat:`, `fix:`,
  `chore:`, `docs:`, `refactor:`.

### Testing
- Backend: add/update a `pytest` test under `backend/tests` for any new
  service or repository behavior.
- Frontend: add/update a test under `frontend/tests` for any new hook or
  utility with non-trivial logic.
