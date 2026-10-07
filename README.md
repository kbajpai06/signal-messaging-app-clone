# Signal Clone

Secure messaging platform (Signal clone): Next.js + FastAPI + SQLite + WebSockets.

## Structure
- `frontend/`: Next.js (App Router, TypeScript)
- `backend/`: FastAPI, SQLAlchemy 2.0 async, SQLite (WAL)

## Quick start
See `backend/.env.example` and `frontend/.env.example`.

Backend:  `cd backend && python3.12 -m venv .venv && source .venv/bin/activate && pip install -r requirements-dev.txt && uvicorn app.main:app --reload --workers 1`
Frontend: `cd frontend && npm install && npm run dev`

_Full architecture, schema, and API docs: TBD (final phase)._