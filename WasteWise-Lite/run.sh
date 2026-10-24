#!/usr/bin/env bash
cd "$(dirname "$0")"
[ -d .venv ] || { python3 -m venv .venv && . .venv/bin/activate && pip install -r backend/requirements.txt; }
. .venv/bin/activate
[ -d frontend/node_modules ] || (cd frontend && npm install)
(cd backend && uvicorn app.main:app --port 8000) &
(cd frontend && npm run dev)
