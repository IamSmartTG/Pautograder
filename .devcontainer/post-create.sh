#!/usr/bin/env bash
# One-time Codespace setup: deps + grading sandbox images + network.
set -euo pipefail

echo "==> Installing backend dependencies"
pip install -r backend/requirements.txt

echo "==> Installing frontend dependencies"
( cd frontend && npm ci )

echo "==> Building grading sandbox images (the browser image is large; a few minutes)"
docker build -t pautograder-python-sandbox  docker/python-sandbox/
docker build -t pautograder-c-sandbox       docker/c-sandbox/
docker build -t pautograder-browser-sandbox docker/browser-sandbox/

echo "==> Creating internal grading network"
docker network create --internal pautograder_sandbox 2>/dev/null || true

cat <<'MSG'

==> Setup complete. Start the app in two terminals:
      Terminal 1:  cd backend  && python -m uvicorn main:app --port 8000
      Terminal 2:  cd frontend && npm run dev
    Then open the forwarded port 5173 ("Pautograder UI").
MSG
