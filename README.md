# Pautograder

![CI](https://github.com/IamSmartTG/Pautograder/actions/workflows/ci.yml/badge.svg)

An anonymous autograder where students submit solutions and get instant, sandboxed feedback — no accounts, no login. Submissions run in disposable Docker containers, so untrusted code never touches the host.

## Features

- **3 problem types**
  - **Algorithm** — graded by running the submission against test cases (score = % passed)
  - **Interactive design** — graded by Playwright screenshot comparison against a baseline
  - **Webapp** — graded by Playwright UI tests (clicks, DOM assertions)
- **5 difficulty labels** — Easy · Medium · Hard · Expert · Master
- **Two submission methods** — paste code, or upload a file / `.zip`
- **File-bomb resistant** — uploads are size-capped and decompression-ratio checked *before* anything runs; archives are extracted with zip-slip and bomb guards
- **Sandboxed grading** — each submission runs in a fresh container: `256m` RAM, `0.5` CPU, `64` PIDs, `no-new-privileges`, no network for algorithm/interactive
- **Instant results** — no accounts, no queue; the grade comes back in the same request

## Tech stack

FastAPI (Python 3.11) · React 18 + Vite · Docker (python:3.11-slim and Playwright image) · pytest

## Quick start

```bash
# Backend
cd backend && pip install -r requirements.txt && uvicorn main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend && npm install && npm run dev   # http://localhost:5173
```

For Docker grading setup and generating the interactive baseline, see **[docs/RUNNING.md](docs/RUNNING.md)**.

## Project structure

```
backend/
  main.py            FastAPI app + CORS
  routes/            problems listing + submission endpoints
  security/          file-bomb guard + safe zip extraction
  grader/            sandbox runner + per-type graders
  problems/          problem definitions (JSON) grouped by difficulty
  tests/             pytest suite (mocked grading — no Docker needed)
frontend/            React UI (problem grid + submit/results)
docker/              sandbox image Dockerfiles
docs/                design doc, plan, RUNNING.md
```

## Tests

```bash
cd backend && python -m pytest tests -v
```

Runs in CI on every push (`.github/workflows/ci.yml`).

## Security model

The core threat is *running untrusted student code*. Defense is layered:

1. **Before grading** — 10 MB upload cap, 50 KB paste cap, 50 MB decompressed cap, 100:1 ratio limit; problem ids validated against path traversal
2. **In the sandbox** — fresh container per run, hard resource caps, network isolation, `no-new-privileges`, container destroyed after grading
3. **Grade integrity** — student-supplied Playwright config is stripped so it can't loosen or skip the checks

See **[docs/pautograder-design.md](docs/pautograder-design.md)** for the full design.

## Status

Functional. Two steps need a local Docker run to finish (documented in [docs/RUNNING.md](docs/RUNNING.md)): generating a real interactive baseline screenshot, and completing the optional sandbox hardening (`cap_drop` / non-root / read-only rootfs).
