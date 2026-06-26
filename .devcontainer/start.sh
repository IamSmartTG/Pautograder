#!/usr/bin/env bash
# Auto-start Pautograder servers on Codespace start/resume. Idempotent —
# only launches a server if its port isn't already responding.
set -u
ROOT=/workspaces/Pautograder
cd "$ROOT" 2>/dev/null || exit 0

if ! curl -fs -o /dev/null http://localhost:8000/api/problems 2>/dev/null; then
  ( cd "$ROOT/backend" && nohup python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload >/tmp/backend.log 2>&1 & )
fi

if ! curl -fs -o /dev/null http://localhost:5173 2>/dev/null; then
  ( cd "$ROOT/frontend" && nohup npm run dev >/tmp/frontend.log 2>&1 & )
fi

echo "Pautograder: backend :8000 and frontend :5173 starting."
