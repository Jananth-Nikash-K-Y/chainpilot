# Contributing to ChainPilot

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
