# ChainPilot — Backend

FastAPI backend for ChainPilot's supply-chain control tower.

## Stack
- Python 3.11+
- FastAPI + Pydantic v2
- SQLAlchemy 2.0
- PostgreSQL
- Alembic (migrations, see /database)

## Layering
```
API (routes) -> Services -> Domain -> Repositories -> Database
```
Business logic must never live directly in route handlers.

## Status
Foundation scaffold only. Only a `/health` endpoint exists.

## Local development
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```
