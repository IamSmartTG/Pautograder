# Pautograder — Design Spec
**Date:** 2026-06-26

## Overview

An anonymous autograder where students submit solutions to programming problems and receive instant graded results. No accounts required. Submissions can be file uploads or pasted code.

---

## Problem Types & Difficulty Levels

**3 problem types:**
- **Algorithm** — graded by running against test cases
- **Interactive Design** — graded by Playwright screenshot comparison against a baseline
- **Webapp** — graded by Playwright automated UI tests

**5 difficulty labels (cosmetic only — no effect on scoring or access):**
Easy, Medium, Hard, Expert, Master

---

## Architecture

Single FastAPI (Python) monolith serving a React frontend. Grading runs in Docker containers via a `ThreadPoolExecutor` (max 4 concurrent workers).

```
Pautograder/
├── backend/
│   ├── main.py
│   ├── routes/
│   │   ├── submit.py
│   │   └── problems.py
│   ├── grader/
│   │   ├── sandbox.py
│   │   ├── algorithm.py
│   │   ├── interactive.py
│   │   └── webapp.py
│   ├── security/
│   │   └── filebomb.py
│   └── problems/
│       ├── easy/
│       ├── medium/
│       ├── hard/
│       ├── expert/
│       └── master/
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Home.jsx
│   │   │   └── Submit.jsx
│   │   └── components/
│   │       ├── ProblemCard.jsx
│   │       └── ResultPanel.jsx
│   └── package.json
└── docker/
    ├── python-sandbox/
    └── browser-sandbox/
```

---

## Security — File Bomb Protection

Three layers applied before any grading begins:

**Layer 1 — Client-side (frontend)**
- Reject files > 10MB before upload via `file.size` check

**Layer 2 — Server-side pre-extraction (`security/filebomb.py`)**
- Hard limit: 10MB raw upload size → 413 if exceeded
- Code paste limit: 50KB
- Zip/tar: stream-extract in chunks, track decompression ratio
  - Abort if uncompressed size > 50MB
  - Abort if ratio > 100:1
  - Delete partial extraction on abort

**Layer 3 — Docker container hard caps**
- `--memory 256m` (OOM killed if exceeded)
- `--cpus 0.5`
- `--network none`
- `--pids-limit 64`
- Execution timeout: 10s (algorithm), 30s (webapp/interactive)
- Container destroyed immediately after grading

---

## Problem Definition

Each problem is a JSON file under `backend/problems/<difficulty>/`.

**Algorithm problem:**
```json
{
  "id": "algo-001",
  "title": "Two Sum",
  "difficulty": "easy",
  "type": "algorithm",
  "description": "Given an array of integers...",
  "test_cases": [
    { "input": "[2,7,11,15]\n9", "expected": "[0,1]" }
  ],
  "time_limit_seconds": 10,
  "memory_limit_mb": 256
}
```

**Interactive Design problem** — replaces `test_cases` with:
```json
"playwright_script": "tests/interactive/design-001.spec.js",
"screenshot_baseline": "baselines/design-001.png",
"diff_threshold": 0.05
```

**Webapp problem** — uses only:
```json
"playwright_script": "tests/webapp/webapp-001.spec.js"
```

---

## Scoring

| Type | Formula |
|------|---------|
| Algorithm | `(passed_cases / total_cases) * 100` |
| Interactive | `100 if pixel_diff < threshold else 0` |
| Webapp | `(passed_playwright_tests / total_tests) * 100` |

---

## API

```
GET  /api/problems        → list all problems
GET  /api/problems/:id    → single problem detail
POST /api/submit/:id      → submit solution, returns grade result
```

**Submit flow:**
1. Frontend POSTs multipart file or JSON code paste
2. `filebomb.py` checks size and ratio — rejects fast if bad
3. Problem JSON loaded from disk
4. `sandbox.py` spawns Docker container with submission + test assets
5. Appropriate grader runs inside container
6. Container exits, stdout captured, container destroyed
7. Score computed, JSON response returned

**Response shape:**
```json
{
  "score": 75,
  "passed": 3,
  "total": 4,
  "results": [
    { "case": 1, "passed": true, "output": "[0,1]" },
    { "case": 2, "passed": false, "output": "timeout", "expected": "[2,3]" }
  ],
  "error": null
}
```

---

## Frontend

**Page 1 — Home (`/`)**
- Problem cards in a grid
- Filter tabs: by difficulty and by type
- Each card: title, difficulty badge, type icon, description snippet

**Page 2 — Submit (`/problem/:id`)**
- Problem description (left panel)
- Submission panel (right): tabs for file upload and code paste
- Submit button → spinner during grading
- Result panel: score, per-test-case breakdown, error output
- For webapp/interactive: screenshot comparison (expected vs submitted)

---

## Constraints & Non-Goals

- No user accounts, no authentication
- No submission history or persistence
- No leaderboard
- Difficulty labels are cosmetic only
- Max 4 concurrent grading jobs (thread pool limit)
