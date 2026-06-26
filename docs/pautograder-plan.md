# Pautograder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an anonymous autograder where students upload/paste code for algorithm, interactive design, and webapp problems and receive instant Docker-sandboxed grades.

**Architecture:** Single FastAPI monolith with a `ThreadPoolExecutor(max_workers=4)` for Docker grading jobs. React frontend (Vite) proxies to the backend. File bomb checks run before any container spawns. Docker containers are hard-capped and destroyed after each run.

**Tech Stack:** Python 3.11, FastAPI, uvicorn, docker-py, pytest, httpx — React 18, Vite, React Router v6 — Docker (python:3.11-slim for algorithms, mcr.microsoft.com/playwright:v1.44.0-jammy for browser grading), Playwright (Node.js, inside browser sandbox).

## Global Constraints

- All Docker containers: `--memory 256m`, `--cpus 0.5`, `--pids-limit 64`
- Algorithm/Interactive containers: `--network none`
- Webapp containers: internal Docker bridge network `pautograder_sandbox` (no external internet)
- Algorithm timeout: 10s. Webapp/Interactive timeout: 30s.
- Max upload: 10MB raw. Max code paste: 50KB. Max decompressed: 50MB. Max compression ratio: 100:1.
- Difficulty labels: `easy`, `medium`, `hard`, `expert`, `master` (cosmetic only — no effect on scoring)
- Problem types: `algorithm`, `interactive`, `webapp`
- No user accounts, no auth, no persistence. Anonymous submissions only.
- Max 4 concurrent grading jobs (ThreadPoolExecutor limit).

---

## File Map

```
Pautograder/
├── backend/
│   ├── main.py                        # FastAPI app, CORS, route mounts
│   ├── requirements.txt
│   ├── routes/
│   │   ├── problems.py                # GET /api/problems, GET /api/problems/{id}
│   │   └── submit.py                  # POST /api/submit/{id}
│   ├── security/
│   │   └── filebomb.py               # Upload + paste guards
│   ├── grader/
│   │   ├── sandbox.py                # Docker spawn + resource caps
│   │   ├── algorithm.py              # Test case runner
│   │   ├── interactive.py            # Playwright screenshot comparison
│   │   └── webapp.py                 # Playwright UI test runner
│   ├── problems/
│   │   ├── easy/
│   │   │   ├── algo-001.json
│   │   │   ├── interactive-001.json
│   │   │   └── interactive-001/
│   │   │       ├── test.spec.js      # Playwright script
│   │   │       └── baseline.png      # Screenshot baseline
│   │   ├── medium/
│   │   │   ├── algo-002.json
│   │   │   └── webapp-001.json
│   │   │   └── webapp-001/
│   │   │       └── test.spec.js
│   │   ├── hard/
│   │   │   └── algo-003.json
│   │   ├── expert/
│   │   │   └── algo-004.json
│   │   └── master/
│   │       └── algo-005.json
│   └── tests/
│       ├── test_firebomb.py
│       ├── test_sandbox.py
│       ├── test_algorithm.py
│       └── test_routes.py
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── pages/
│       │   ├── Home.jsx
│       │   └── Submit.jsx
│       └── components/
│           ├── ProblemCard.jsx
│           └── ResultPanel.jsx
└── docker/
    ├── python-sandbox/
    │   └── Dockerfile
    └── browser-sandbox/
        └── Dockerfile
```

---

## Task 1: Project Scaffolding

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/__init__.py`
- Create: `backend/routes/__init__.py`
- Create: `backend/security/__init__.py`
- Create: `backend/grader/__init__.py`
- Create: `frontend/package.json`
- Create: `frontend/vite.config.js`
- Create: `frontend/index.html`
- Create: `.gitignore`

**Interfaces:**
- Produces: installable Python env and Node env for all subsequent tasks

- [ ] **Step 1: Create the folder tree**

```bash
cd C:\Users\ROG\Downloads\Pautograder
mkdir -p backend/routes backend/security backend/grader backend/tests
mkdir -p backend/problems/easy/interactive-001
mkdir -p backend/problems/medium/webapp-001
mkdir -p backend/problems/hard backend/problems/expert backend/problems/master
mkdir -p frontend/src/pages frontend/src/components
mkdir -p docker/python-sandbox docker/browser-sandbox
```

- [ ] **Step 2: Write `backend/requirements.txt`**

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
python-multipart==0.0.9
docker==7.1.0
pytest==8.2.1
httpx==0.27.0
pytest-asyncio==0.23.7
```

- [ ] **Step 3: Write `backend/__init__.py`, `backend/routes/__init__.py`, `backend/security/__init__.py`, `backend/grader/__init__.py`**

Each file is empty. They just make the directories Python packages.

```python
# (empty)
```

- [ ] **Step 4: Write `frontend/package.json`**

```json
{
  "name": "pautograder-frontend",
  "version": "1.0.0",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "react-router-dom": "^6.23.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.0",
    "vite": "^5.2.0"
  }
}
```

- [ ] **Step 5: Write `frontend/vite.config.js`**

```js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
})
```

- [ ] **Step 6: Write `frontend/index.html`**

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Pautograder</title>
    <style>
      *, *::before, *::after { box-sizing: border-box; }
      body { margin: 0; font-family: system-ui, sans-serif; background: #f9fafb; }
    </style>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

- [ ] **Step 7: Write `.gitignore`**

```
__pycache__/
*.pyc
.pytest_cache/
venv/
node_modules/
dist/
.env
```

- [ ] **Step 8: Initialize git and install deps**

```bash
git init
cd backend && python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt
cd ../frontend && npm install
```

- [ ] **Step 9: Commit**

```bash
git add .
git commit -m "feat: project scaffolding"
```

---

## Task 2: File Bomb Guard

**Files:**
- Create: `backend/security/filebomb.py`
- Create: `backend/tests/test_firebomb.py`

**Interfaces:**
- Produces:
  - `check_paste(code: str) -> None` — raises `HTTPException(413)` if code > 50KB
  - `check_upload(filename: str, content: bytes) -> None` — raises `HTTPException(413)` if unsafe

- [ ] **Step 1: Write the failing tests**

```python
# backend/tests/test_firebomb.py
import io, zipfile, pytest
from fastapi import HTTPException
from security.firebomb import check_paste, check_upload

def test_paste_ok():
    check_paste("x" * 100)  # should not raise

def test_paste_too_large():
    with pytest.raises(HTTPException) as exc:
        check_paste("x" * (51 * 1024))
    assert exc.value.status_code == 413

def test_upload_ok():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("hello.py", "print('hello')")
    check_upload("sub.zip", buf.getvalue())

def test_upload_too_large_raw():
    with pytest.raises(HTTPException) as exc:
        check_upload("big.py", b"x" * (11 * 1024 * 1024))
    assert exc.value.status_code == 413

def test_zip_bomb_detected():
    # Build a zip where a single file is 51MB of zeros (compressed well)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("bomb.txt", b"\x00" * (51 * 1024 * 1024))
    with pytest.raises(HTTPException) as exc:
        check_upload("bomb.zip", buf.getvalue())
    assert exc.value.status_code == 413
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd backend
pytest tests/test_firebomb.py -v
```

Expected: `ImportError` or `ModuleNotFoundError` (module doesn't exist yet)

- [ ] **Step 3: Implement `backend/security/firebomb.py`**

```python
import io, zipfile, tarfile
from fastapi import HTTPException

MAX_UPLOAD_BYTES = 10 * 1024 * 1024   # 10MB
MAX_PASTE_BYTES = 50 * 1024            # 50KB
MAX_DECOMPRESSED_BYTES = 50 * 1024 * 1024  # 50MB
MAX_RATIO = 100

def check_paste(code: str) -> None:
    if len(code.encode()) > MAX_PASTE_BYTES:
        raise HTTPException(413, "Code paste exceeds 50KB limit")

def check_upload(filename: str, content: bytes) -> None:
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "File exceeds 10MB limit")
    name = filename.lower()
    if name.endswith(".zip"):
        _check_zip(content)
    elif name.endswith((".tar", ".tar.gz", ".tgz", ".tar.bz2")):
        _check_tar(content)

def _check_zip(content: bytes) -> None:
    compressed = len(content)
    decompressed = 0
    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        for info in zf.infolist():
            decompressed += info.file_size
            _assert_limits(compressed, decompressed)

def _check_tar(content: bytes) -> None:
    compressed = len(content)
    decompressed = 0
    with tarfile.open(fileobj=io.BytesIO(content)) as tf:
        for member in tf.getmembers():
            decompressed += member.size
            _assert_limits(compressed, decompressed)

def _assert_limits(compressed: int, decompressed: int) -> None:
    if decompressed > MAX_DECOMPRESSED_BYTES:
        raise HTTPException(413, "Archive expands beyond 50MB limit")
    if compressed > 0 and decompressed / compressed > MAX_RATIO:
        raise HTTPException(413, "Suspicious compression ratio — possible zip bomb")
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
cd backend
pytest tests/test_firebomb.py -v
```

Expected: 5 tests PASSED

- [ ] **Step 5: Commit**

```bash
git add backend/security/firebomb.py backend/tests/test_firebomb.py
git commit -m "feat: file bomb guard with zip/tar ratio checks"
```

---

## Task 3: Docker Sandbox Runner

**Files:**
- Create: `docker/python-sandbox/Dockerfile`
- Create: `backend/grader/sandbox.py`
- Create: `backend/tests/test_sandbox.py`

**Interfaces:**
- Produces:
  - `run_in_sandbox(image: str, command: list[str], files: dict[str, bytes], timeout: int, network: str = "none") -> dict`
  - Returns `{"stdout": str, "stderr": str, "exit_code": int, "timed_out": bool}`

- [ ] **Step 1: Write the failing test (mocked Docker)**

```python
# backend/tests/test_sandbox.py
from unittest.mock import MagicMock, patch
from grader.sandbox import run_in_sandbox

def test_run_returns_stdout():
    mock_container = MagicMock()
    mock_container.wait.return_value = {"StatusCode": 0}
    mock_container.logs.side_effect = [b"hello\n", b""]

    with patch("grader.sandbox._client") as mock_client:
        mock_client.containers.run.return_value = mock_container
        result = run_in_sandbox(
            image="pautograder-python-sandbox",
            command=["python", "-c", "print('hello')"],
            files={"solution.py": b"print('hello')"},
            timeout=5
        )

    assert result["stdout"] == "hello\n"
    assert result["exit_code"] == 0
    assert result["timed_out"] is False

def test_run_timeout():
    mock_container = MagicMock()
    mock_container.wait.side_effect = Exception("timeout")

    with patch("grader.sandbox._client") as mock_client:
        mock_client.containers.run.return_value = mock_container
        result = run_in_sandbox(
            image="pautograder-python-sandbox",
            command=["python", "infinite.py"],
            files={"infinite.py": b"while True: pass"},
            timeout=1
        )

    assert result["timed_out"] is True
    assert result["exit_code"] == -1
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd backend && pytest tests/test_sandbox.py -v
```

Expected: `ImportError` (module not written yet)

- [ ] **Step 3: Write `backend/grader/sandbox.py`**

```python
import os, tempfile, docker
from concurrent.futures import ThreadPoolExecutor

_client = docker.from_env()
_executor = ThreadPoolExecutor(max_workers=4)

def run_in_sandbox(
    image: str,
    command: list[str],
    files: dict[str, bytes],
    timeout: int,
    network: str = "none"
) -> dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        for name, content in files.items():
            dest = os.path.join(tmpdir, name)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "wb") as f:
                f.write(content)

        try:
            container = _client.containers.run(
                image=image,
                command=command,
                volumes={tmpdir: {"bind": "/submission", "mode": "rw"}},
                mem_limit="256m",
                cpu_period=100000,
                cpu_quota=50000,
                network_mode=network,
                pids_limit=64,
                detach=True,
                remove=False,
            )
            try:
                result = container.wait(timeout=timeout)
                stdout = container.logs(stdout=True, stderr=False).decode("utf-8", errors="replace")
                stderr = container.logs(stdout=False, stderr=True).decode("utf-8", errors="replace")
                return {"stdout": stdout, "stderr": stderr, "exit_code": result["StatusCode"], "timed_out": False}
            except Exception:
                try:
                    container.kill()
                except Exception:
                    pass
                return {"stdout": "", "stderr": "Execution timed out", "exit_code": -1, "timed_out": True}
            finally:
                try:
                    container.remove(force=True)
                except Exception:
                    pass
        except Exception as e:
            return {"stdout": "", "stderr": str(e), "exit_code": -1, "timed_out": False}
```

- [ ] **Step 4: Write `docker/python-sandbox/Dockerfile`**

```dockerfile
FROM python:3.11-slim
WORKDIR /submission
```

- [ ] **Step 5: Build the python sandbox image**

```bash
docker build -t pautograder-python-sandbox docker/python-sandbox/
```

Expected: Successfully built and tagged `pautograder-python-sandbox`

- [ ] **Step 6: Run tests — verify they pass**

```bash
cd backend && pytest tests/test_sandbox.py -v
```

Expected: 2 tests PASSED

- [ ] **Step 7: Commit**

```bash
git add docker/python-sandbox/Dockerfile backend/grader/sandbox.py backend/tests/test_sandbox.py
git commit -m "feat: Docker sandbox runner with resource caps"
```

---

## Task 4: Algorithm Grader

**Files:**
- Create: `backend/grader/algorithm.py`
- Create: `backend/tests/test_algorithm.py`

**Interfaces:**
- Consumes: `run_in_sandbox(image, command, files, timeout) -> dict`
- Produces: `grade_algorithm(problem: dict, code: str) -> dict`
  - Returns `{"score": int, "passed": int, "total": int, "results": list, "error": str|None}`

- [ ] **Step 1: Write the failing tests**

```python
# backend/tests/test_algorithm.py
from unittest.mock import patch
from grader.algorithm import grade_algorithm

PROBLEM = {
    "test_cases": [
        {"input": "hello", "expected": "hello"},
        {"input": "world", "expected": "world"},
    ],
    "time_limit_seconds": 5,
}

def _mock_sandbox(stdout="", exit_code=0, timed_out=False):
    return {"stdout": stdout, "stderr": "", "exit_code": exit_code, "timed_out": timed_out}

def test_all_pass():
    with patch("grader.algorithm.run_in_sandbox", side_effect=[
        _mock_sandbox("hello\n"), _mock_sandbox("world\n")
    ]):
        result = grade_algorithm(PROBLEM, "print(input())")
    assert result["score"] == 100
    assert result["passed"] == 2
    assert result["total"] == 2
    assert all(r["passed"] for r in result["results"])

def test_partial_pass():
    with patch("grader.algorithm.run_in_sandbox", side_effect=[
        _mock_sandbox("hello\n"), _mock_sandbox("wrong\n")
    ]):
        result = grade_algorithm(PROBLEM, "print(input())")
    assert result["score"] == 50
    assert result["passed"] == 1

def test_timeout_case():
    with patch("grader.algorithm.run_in_sandbox", side_effect=[
        _mock_sandbox("hello\n"), _mock_sandbox(timed_out=True, exit_code=-1)
    ]):
        result = grade_algorithm(PROBLEM, "print(input())")
    assert result["passed"] == 1
    assert result["results"][1]["output"] == "timeout"
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd backend && pytest tests/test_algorithm.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Implement `backend/grader/algorithm.py`**

```python
from .sandbox import run_in_sandbox

PYTHON_IMAGE = "pautograder-python-sandbox"

# ponytail: runner.py redirects stdin so the student's script uses input() normally
_RUNNER = """\
import sys
sys.stdin = open('/submission/input.txt', 'r')
exec(open('/submission/solution.py').read())
"""

def grade_algorithm(problem: dict, code: str) -> dict:
    test_cases = problem["test_cases"]
    timeout = problem.get("time_limit_seconds", 10)
    results = []

    for i, case in enumerate(test_cases):
        output = run_in_sandbox(
            image=PYTHON_IMAGE,
            command=["python", "/submission/runner.py"],
            files={
                "runner.py": _RUNNER.encode(),
                "solution.py": code.encode(),
                "input.txt": case["input"].encode(),
            },
            timeout=timeout,
        )
        actual = output["stdout"].strip()
        expected = case["expected"].strip()
        passed = (
            actual == expected
            and not output["timed_out"]
            and output["exit_code"] == 0
        )
        results.append({
            "case": i + 1,
            "passed": passed,
            "output": "timeout" if output["timed_out"] else actual,
            "expected": expected,
        })

    passed_count = sum(1 for r in results if r["passed"])
    total = len(test_cases)
    return {
        "score": round(passed_count / total * 100) if total else 0,
        "passed": passed_count,
        "total": total,
        "results": results,
        "error": None,
    }
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
cd backend && pytest tests/test_algorithm.py -v
```

Expected: 3 tests PASSED

- [ ] **Step 5: Smoke test against real Docker**

```bash
cd backend
python -c "
from grader.algorithm import grade_algorithm
p = {'test_cases': [{'input': '5', 'expected': '5'}], 'time_limit_seconds': 5}
print(grade_algorithm(p, 'print(input())'))
"
```

Expected: `{'score': 100, 'passed': 1, 'total': 1, ...}`

- [ ] **Step 6: Commit**

```bash
git add backend/grader/algorithm.py backend/tests/test_algorithm.py
git commit -m "feat: algorithm grader with per-test-case Docker execution"
```

---

## Task 5: Browser Graders (Interactive + Webapp)

**Files:**
- Create: `docker/browser-sandbox/Dockerfile`
- Create: `backend/grader/interactive.py`
- Create: `backend/grader/webapp.py`

**Interfaces:**
- Consumes: `run_in_sandbox(image, command, files, timeout, network) -> dict`
- Produces:
  - `grade_interactive(problem: dict, problem_dir: Path, files: dict[str, bytes]) -> dict`
  - `grade_webapp(problem: dict, problem_dir: Path, files: dict[str, bytes]) -> dict`
  - Both return same shape: `{"score": int, "passed": int, "total": int, "results": list, "error": str|None}`

- [ ] **Step 1: Write `docker/browser-sandbox/Dockerfile`**

```dockerfile
FROM mcr.microsoft.com/playwright:v1.44.0-jammy
WORKDIR /submission
RUN npm init -y && npm install @playwright/test
```

- [ ] **Step 2: Build the browser sandbox image**

```bash
docker build -t pautograder-browser-sandbox docker/browser-sandbox/
```

Expected: Successfully tagged `pautograder-browser-sandbox` (this may take a few minutes — Playwright image is large)

- [ ] **Step 3: Create the internal Docker network for webapp grading**

```bash
docker network create --internal pautograder_sandbox
```

Expected: network ID printed, no error

- [ ] **Step 4: Write `backend/grader/interactive.py`**

```python
from pathlib import Path
from .sandbox import run_in_sandbox

BROWSER_IMAGE = "pautograder-browser-sandbox"

def grade_interactive(problem: dict, problem_dir: Path, files: dict[str, bytes]) -> dict:
    """
    Mounts student files + the problem's Playwright spec into the container.
    The spec compares student's page against the baseline screenshot via
    Playwright's built-in toHaveScreenshot() which reads from __screenshots__/.
    """
    script_name = Path(problem["playwright_script"]).name
    baseline_name = Path(problem["screenshot_baseline"]).name

    submission = dict(files)
    submission[script_name] = (problem_dir / problem["playwright_script"]).read_bytes()
    submission[f"__screenshots__/{script_name}/{baseline_name}"] = (
        problem_dir / problem["screenshot_baseline"]
    ).read_bytes()

    output = run_in_sandbox(
        image=BROWSER_IMAGE,
        command=["npx", "playwright", "test", f"/submission/{script_name}", "--reporter=json"],
        files=submission,
        timeout=problem.get("time_limit_seconds", 30),
        network="none",
    )

    passed = output["exit_code"] == 0 and not output["timed_out"]
    return {
        "score": 100 if passed else 0,
        "passed": 1 if passed else 0,
        "total": 1,
        "results": [{"case": 1, "passed": passed, "output": output["stdout"][:500], "expected": "matches baseline"}],
        "error": output["stderr"][:300] if output["stderr"] else None,
    }
```

- [ ] **Step 5: Write `backend/grader/webapp.py`**

```python
import json
from pathlib import Path
from .sandbox import run_in_sandbox

BROWSER_IMAGE = "pautograder-browser-sandbox"

def grade_webapp(problem: dict, problem_dir: Path, files: dict[str, bytes]) -> dict:
    script_name = Path(problem["playwright_script"]).name

    submission = dict(files)
    submission[script_name] = (problem_dir / problem["playwright_script"]).read_bytes()

    output = run_in_sandbox(
        image=BROWSER_IMAGE,
        command=["npx", "playwright", "test", f"/submission/{script_name}", "--reporter=json"],
        files=submission,
        timeout=problem.get("time_limit_seconds", 30),
        network="pautograder_sandbox",
    )

    try:
        data = json.loads(output["stdout"])
        all_specs = [s for suite in data.get("suites", []) for s in suite.get("specs", [])]
        total = len(all_specs)
        passed_count = sum(1 for s in all_specs if s.get("ok", False))
        results = [
            {"case": i + 1, "passed": s.get("ok", False), "output": s.get("title", ""), "expected": "pass"}
            for i, s in enumerate(all_specs)
        ]
    except (json.JSONDecodeError, KeyError):
        total = 1
        passed_count = 1 if (output["exit_code"] == 0 and not output["timed_out"]) else 0
        results = [{"case": 1, "passed": bool(passed_count), "output": output["stdout"][:300], "expected": "all tests pass"}]

    return {
        "score": round(passed_count / total * 100) if total else 0,
        "passed": passed_count,
        "total": total,
        "results": results,
        "error": output["stderr"][:300] if output["stderr"] else None,
    }
```

- [ ] **Step 6: Commit**

```bash
git add docker/browser-sandbox/Dockerfile backend/grader/interactive.py backend/grader/webapp.py
git commit -m "feat: Playwright browser graders for interactive and webapp problems"
```

---

## Task 6: Problem Definitions (JSON + Playwright Scripts)

**Files:**
- Create: `backend/problems/easy/algo-001.json` — Two Sum (algorithm, easy)
- Create: `backend/problems/medium/algo-002.json` — Valid Parentheses (algorithm, medium)
- Create: `backend/problems/hard/algo-003.json` — Longest Substring Without Repeating (algorithm, hard)
- Create: `backend/problems/expert/algo-004.json` — Median of Two Sorted Arrays (algorithm, expert)
- Create: `backend/problems/master/algo-005.json` — Regular Expression Matching (algorithm, master)
- Create: `backend/problems/easy/interactive-001.json` — Click Counter (interactive, easy)
- Create: `backend/problems/easy/interactive-001/test.spec.js` — Playwright script
- Create: `backend/problems/medium/webapp-001.json` — Todo List App (webapp, medium)
- Create: `backend/problems/medium/webapp-001/test.spec.js` — Playwright script

**Interfaces:**
- Produces: loadable problem JSON files consumed by routes/problems.py and routes/submit.py

- [ ] **Step 1: Write algorithm problem JSONs**

`backend/problems/easy/algo-001.json`:
```json
{
  "id": "algo-001",
  "title": "Echo Input",
  "difficulty": "easy",
  "type": "algorithm",
  "description": "Read a line from stdin and print it back exactly as-is.",
  "test_cases": [
    { "input": "hello world", "expected": "hello world" },
    { "input": "42", "expected": "42" },
    { "input": "Python is fun", "expected": "Python is fun" }
  ],
  "time_limit_seconds": 5
}
```

`backend/problems/medium/algo-002.json`:
```json
{
  "id": "algo-002",
  "title": "Valid Parentheses",
  "difficulty": "medium",
  "type": "algorithm",
  "description": "Given a string of brackets '(', ')', '{', '}', '[', ']', determine if it is valid. A valid string has every open bracket closed in correct order. Print 'true' or 'false'.",
  "test_cases": [
    { "input": "()", "expected": "true" },
    { "input": "()[]{}", "expected": "true" },
    { "input": "(]", "expected": "false" },
    { "input": "([)]", "expected": "false" },
    { "input": "{[]}", "expected": "true" }
  ],
  "time_limit_seconds": 10
}
```

`backend/problems/hard/algo-003.json`:
```json
{
  "id": "algo-003",
  "title": "Longest Unique Substring",
  "difficulty": "hard",
  "type": "algorithm",
  "description": "Given a string, find the length of the longest substring without repeating characters. Print the length as an integer.",
  "test_cases": [
    { "input": "abcabcbb", "expected": "3" },
    { "input": "bbbbb", "expected": "1" },
    { "input": "pwwkew", "expected": "3" },
    { "input": "", "expected": "0" },
    { "input": "dvdf", "expected": "3" }
  ],
  "time_limit_seconds": 10
}
```

`backend/problems/expert/algo-004.json`:
```json
{
  "id": "algo-004",
  "title": "Two Sum Indices",
  "difficulty": "expert",
  "type": "algorithm",
  "description": "Given a list of integers (space-separated on line 1) and a target integer on line 2, print the two 0-based indices that add up to the target, space-separated. Assume exactly one solution exists.",
  "test_cases": [
    { "input": "2 7 11 15\n9", "expected": "0 1" },
    { "input": "3 2 4\n6", "expected": "1 2" },
    { "input": "3 3\n6", "expected": "0 1" }
  ],
  "time_limit_seconds": 10
}
```

`backend/problems/master/algo-005.json`:
```json
{
  "id": "algo-005",
  "title": "FizzBuzz",
  "difficulty": "master",
  "type": "algorithm",
  "description": "Read an integer N from stdin. Print FizzBuzz for numbers 1 to N: 'Fizz' if divisible by 3, 'Buzz' if by 5, 'FizzBuzz' if both, else the number itself. One number per line.",
  "test_cases": [
    { "input": "5", "expected": "1\n2\nFizz\n4\nBuzz" },
    { "input": "15", "expected": "1\n2\nFizz\n4\nBuzz\nFizz\n7\n8\nFizz\nBuzz\n11\nFizz\n13\n14\nFizzBuzz" }
  ],
  "time_limit_seconds": 5
}
```

- [ ] **Step 2: Write interactive problem JSON and Playwright script**

`backend/problems/easy/interactive-001.json`:
```json
{
  "id": "interactive-001",
  "title": "Click Counter",
  "difficulty": "easy",
  "type": "interactive",
  "description": "Build an HTML page with a button labeled 'Click me' and a counter that starts at 0. Each click increments the counter by 1. The counter value must be visible on the page.",
  "playwright_script": "interactive-001/test.spec.js",
  "screenshot_baseline": "interactive-001/baseline.png",
  "diff_threshold": 0.05,
  "time_limit_seconds": 20
}
```

`backend/problems/easy/interactive-001/test.spec.js`:
```js
const { test, expect } = require('@playwright/test');
const path = require('path');

test('click counter works correctly', async ({ page }) => {
  // Student must submit an index.html in their zip
  await page.goto('file:///submission/index.html');

  // Counter starts at 0
  const counter = page.locator('[data-testid="counter"], #counter, .counter');
  await expect(counter).toHaveText('0');

  // Click increments counter
  await page.click('button:has-text("Click me")');
  await expect(counter).toHaveText('1');

  await page.click('button:has-text("Click me")');
  await expect(counter).toHaveText('2');

  // Screenshot comparison
  await expect(page).toHaveScreenshot('baseline.png', { threshold: 0.05 });
});
```

- [ ] **Step 3: Generate the interactive baseline screenshot**

Run this once to create the reference screenshot. Requires a working `index.html` solution to exist temporarily:

```bash
# Create a reference solution temporarily
mkdir -p /tmp/ref-counter
cat > /tmp/ref-counter/index.html << 'EOF'
<!DOCTYPE html>
<html>
<body>
  <span data-testid="counter">0</span>
  <button onclick="document.querySelector('[data-testid=counter]').textContent = +document.querySelector('[data-testid=counter]').textContent + 1">Click me</button>
</body>
</html>
EOF

# Copy test spec next to it and run playwright to generate baseline
cp backend/problems/easy/interactive-001/test.spec.js /tmp/ref-counter/
cd /tmp/ref-counter && npx playwright test test.spec.js --update-snapshots
cp /tmp/ref-counter/test-results/*/baseline.png \
   C:/Users/ROG/Downloads/Pautograder/backend/problems/easy/interactive-001/baseline.png
```

- [ ] **Step 4: Write webapp problem JSON and Playwright script**

`backend/problems/medium/webapp-001.json`:
```json
{
  "id": "webapp-001",
  "title": "Todo List App",
  "difficulty": "medium",
  "type": "webapp",
  "description": "Build a static HTML/CSS/JS todo list. Must have: an input field, an 'Add' button that appends the typed text as a list item, and each item must have a 'Delete' button that removes it. Submit as a zip containing index.html.",
  "playwright_script": "webapp-001/test.spec.js",
  "time_limit_seconds": 30
}
```

`backend/problems/medium/webapp-001/test.spec.js`:
```js
const { test, expect } = require('@playwright/test');

test('can add a todo item', async ({ page }) => {
  await page.goto('file:///submission/index.html');
  await page.fill('input', 'Buy milk');
  await page.click('button:has-text("Add")');
  await expect(page.locator('text=Buy milk')).toBeVisible();
});

test('can add multiple items', async ({ page }) => {
  await page.goto('file:///submission/index.html');
  await page.fill('input', 'Task one');
  await page.click('button:has-text("Add")');
  await page.fill('input', 'Task two');
  await page.click('button:has-text("Add")');
  await expect(page.locator('text=Task one')).toBeVisible();
  await expect(page.locator('text=Task two')).toBeVisible();
});

test('can delete a todo item', async ({ page }) => {
  await page.goto('file:///submission/index.html');
  await page.fill('input', 'Delete me');
  await page.click('button:has-text("Add")');
  await page.click('button:has-text("Delete")');
  await expect(page.locator('text=Delete me')).not.toBeVisible();
});
```

- [ ] **Step 5: Commit**

```bash
git add backend/problems/
git commit -m "feat: add 5 algorithm problems + interactive and webapp sample problems"
```

---

## Task 7: API Routes

**Files:**
- Create: `backend/routes/problems.py`
- Create: `backend/routes/submit.py`
- Create: `backend/tests/test_routes.py`

**Interfaces:**
- Consumes: `check_paste`, `check_upload`, `grade_algorithm`, `grade_interactive`, `grade_webapp`
- Produces: FastAPI routers mounted at `/api`

- [ ] **Step 1: Write failing route tests**

```python
# backend/tests/test_routes.py
from fastapi.testclient import TestClient
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from main import app

client = TestClient(app)

def test_list_problems_returns_list():
    r = client.get("/api/problems")
    assert r.status_code == 200
    problems = r.json()
    assert isinstance(problems, list)
    assert len(problems) >= 1

def test_get_problem_ok():
    r = client.get("/api/problems/algo-001")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == "algo-001"
    assert "test_cases" not in data  # internal grading detail must be hidden

def test_get_problem_not_found():
    r = client.get("/api/problems/does-not-exist")
    assert r.status_code == 404

def test_submit_no_body_rejected():
    r = client.post("/api/submit/algo-001")
    assert r.status_code == 400

def test_submit_paste_too_large():
    r = client.post("/api/submit/algo-001", data={"code": "x" * (51 * 1024)})
    assert r.status_code == 413
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd backend && pytest tests/test_routes.py -v
```

Expected: `ImportError` (main.py doesn't exist yet)

- [ ] **Step 3: Write `backend/routes/problems.py`**

```python
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException

router = APIRouter()
PROBLEMS_DIR = Path(__file__).parent.parent / "problems"
_DIFFICULTY_ORDER = ["easy", "medium", "hard", "expert", "master"]

def _load_summary(path: Path) -> dict:
    data = json.loads(path.read_text())
    return {k: data[k] for k in ("id", "title", "difficulty", "type", "description")}

def _load_full(path: Path) -> dict:
    return json.loads(path.read_text())

def _find_problem_file(problem_id: str) -> Path | None:
    for d in PROBLEMS_DIR.iterdir():
        if d.is_dir():
            p = d / f"{problem_id}.json"
            if p.exists():
                return p
    return None

@router.get("/problems")
def list_problems():
    problems = []
    for d in PROBLEMS_DIR.iterdir():
        if d.is_dir():
            for f in d.glob("*.json"):
                problems.append(_load_summary(f))
    problems.sort(key=lambda p: _DIFFICULTY_ORDER.index(p["difficulty"]))
    return problems

@router.get("/problems/{problem_id}")
def get_problem(problem_id: str):
    path = _find_problem_file(problem_id)
    if not path:
        raise HTTPException(404, f"Problem '{problem_id}' not found")
    data = _load_full(path)
    # Strip internal grading details
    return {k: data[k] for k in ("id", "title", "difficulty", "type", "description", "time_limit_seconds") if k in data}
```

- [ ] **Step 4: Write `backend/routes/submit.py`**

```python
import json
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from security.firebomb import check_paste, check_upload
from grader.algorithm import grade_algorithm
from grader.interactive import grade_interactive
from grader.webapp import grade_webapp

router = APIRouter()
PROBLEMS_DIR = Path(__file__).parent.parent / "problems"

def _load_problem(problem_id: str) -> tuple[dict, Path]:
    for d in PROBLEMS_DIR.iterdir():
        if d.is_dir():
            p = d / f"{problem_id}.json"
            if p.exists():
                return json.loads(p.read_text()), d / problem_id
    raise HTTPException(404, f"Problem '{problem_id}' not found")

@router.post("/submit/{problem_id}")
async def submit(
    problem_id: str,
    code: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
):
    if not code and not file:
        raise HTTPException(400, "Provide either 'code' or 'file'")

    problem, problem_dir = _load_problem(problem_id)

    if code:
        check_paste(code)
        submission_files = {"solution.py": code.encode()}
    else:
        content = await file.read()
        check_upload(file.filename, content)
        submission_files = {file.filename: content}

    ptype = problem["type"]
    if ptype == "algorithm":
        code_str = code if code else content.decode("utf-8", errors="replace")
        return grade_algorithm(problem, code_str)
    elif ptype == "interactive":
        return grade_interactive(problem, problem_dir, submission_files)
    elif ptype == "webapp":
        return grade_webapp(problem, problem_dir, submission_files)
    else:
        raise HTTPException(400, f"Unknown problem type: {ptype}")
```

- [ ] **Step 5: Write `backend/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.problems import router as problems_router
from routes.submit import router as submit_router

app = FastAPI(title="Pautograder")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(problems_router, prefix="/api")
app.include_router(submit_router, prefix="/api")
```

- [ ] **Step 6: Run tests — verify they pass**

```bash
cd backend && pytest tests/test_routes.py -v
```

Expected: 5 tests PASSED

- [ ] **Step 7: Commit**

```bash
git add backend/routes/ backend/main.py backend/tests/test_routes.py
git commit -m "feat: FastAPI routes for problems listing and submission"
```

---

## Task 8: Frontend Scaffold

**Files:**
- Create: `frontend/src/main.jsx`
- Create: `frontend/src/App.jsx`

**Interfaces:**
- Produces: running React dev server at `http://localhost:5173` with routing

- [ ] **Step 1: Write `frontend/src/main.jsx`**

```jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'

ReactDOM.createRoot(document.getElementById('root')).render(<App />)
```

- [ ] **Step 2: Write `frontend/src/App.jsx`**

```jsx
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import Submit from './pages/Submit'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/problem/:id" element={<Submit />} />
      </Routes>
    </BrowserRouter>
  )
}
```

- [ ] **Step 3: Start the dev server and verify it loads**

```bash
cd frontend && npm run dev
```

Open `http://localhost:5173` — expect a blank page with no console errors (Home component doesn't exist yet, React will show an error, that's fine for now).

- [ ] **Step 4: Commit**

```bash
git add frontend/src/main.jsx frontend/src/App.jsx
git commit -m "feat: React app scaffold with routing"
```

---

## Task 9: Home Page

**Files:**
- Create: `frontend/src/components/ProblemCard.jsx`
- Create: `frontend/src/pages/Home.jsx`

**Interfaces:**
- Consumes: `GET /api/problems` → `[{id, title, difficulty, type, description}]`
- Produces: filterable problem grid at `/`

- [ ] **Step 1: Write `frontend/src/components/ProblemCard.jsx`**

```jsx
import { useNavigate } from 'react-router-dom'

const BADGE_COLOR = {
  easy: '#22c55e', medium: '#f59e0b', hard: '#ef4444',
  expert: '#8b5cf6', master: '#ec4899'
}
const TYPE_ICON = { algorithm: '⚡', interactive: '🎨', webapp: '🌐' }

export default function ProblemCard({ problem }) {
  const nav = useNavigate()
  return (
    <div
      onClick={() => nav(`/problem/${problem.id}`)}
      style={{
        border: '1px solid #e5e7eb', borderRadius: 8, padding: 16,
        cursor: 'pointer', background: '#fff',
        transition: 'box-shadow .15s'
      }}
      onMouseEnter={e => e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,.12)'}
      onMouseLeave={e => e.currentTarget.style.boxShadow = ''}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
        <span style={{
          background: BADGE_COLOR[problem.difficulty], color: '#fff',
          padding: '2px 8px', borderRadius: 4, fontSize: 12, fontWeight: 600
        }}>
          {problem.difficulty[0].toUpperCase() + problem.difficulty.slice(1)}
        </span>
        <span style={{ color: '#6b7280', fontSize: 13 }}>
          {TYPE_ICON[problem.type]} {problem.type}
        </span>
      </div>
      <h3 style={{ margin: '0 0 6px', fontSize: 16 }}>{problem.title}</h3>
      <p style={{ color: '#6b7280', fontSize: 13, margin: 0, lineHeight: 1.4 }}>
        {problem.description.slice(0, 100)}{problem.description.length > 100 ? '…' : ''}
      </p>
    </div>
  )
}
```

- [ ] **Step 2: Write `frontend/src/pages/Home.jsx`**

```jsx
import { useState, useEffect } from 'react'
import ProblemCard from '../components/ProblemCard'

const DIFFICULTIES = ['all', 'easy', 'medium', 'hard', 'expert', 'master']
const TYPES = ['all', 'algorithm', 'interactive', 'webapp']

function FilterBtn({ label, active, onClick }) {
  return (
    <button onClick={onClick} style={{
      padding: '4px 12px', border: 'none', borderRadius: 4, cursor: 'pointer',
      background: active ? '#3b82f6' : '#e5e7eb',
      color: active ? '#fff' : '#374151', fontWeight: active ? 600 : 400
    }}>
      {label[0].toUpperCase() + label.slice(1)}
    </button>
  )
}

export default function Home() {
  const [problems, setProblems] = useState([])
  const [diff, setDiff] = useState('all')
  const [type, setType] = useState('all')

  useEffect(() => {
    fetch('/api/problems').then(r => r.json()).then(setProblems)
  }, [])

  const visible = problems.filter(p =>
    (diff === 'all' || p.difficulty === diff) &&
    (type === 'all' || p.type === type)
  )

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: 24 }}>
      <h1 style={{ marginBottom: 4 }}>Pautograder</h1>
      <p style={{ color: '#6b7280', marginBottom: 20 }}>Submit your solution and get instant feedback.</p>

      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 20 }}>
        {DIFFICULTIES.map(d => <FilterBtn key={d} label={d} active={diff === d} onClick={() => setDiff(d)} />)}
        <span style={{ color: '#d1d5db', margin: '0 4px' }}>|</span>
        {TYPES.map(t => <FilterBtn key={t} label={t} active={type === t} onClick={() => setType(t)} />)}
      </div>

      {visible.length === 0 && (
        <p style={{ color: '#9ca3af' }}>No problems match these filters.</p>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
        {visible.map(p => <ProblemCard key={p.id} problem={p} />)}
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Start backend and frontend, verify the home page renders problems**

Terminal 1:
```bash
cd backend && uvicorn main:app --reload --port 8000
```

Terminal 2:
```bash
cd frontend && npm run dev
```

Open `http://localhost:5173` — expect a grid of problem cards. Verify filters work by clicking difficulty and type buttons.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/ProblemCard.jsx frontend/src/pages/Home.jsx
git commit -m "feat: home page with filterable problem grid"
```

---

## Task 10: Submit Page

**Files:**
- Create: `frontend/src/components/ResultPanel.jsx`
- Create: `frontend/src/pages/Submit.jsx`

**Interfaces:**
- Consumes:
  - `GET /api/problems/:id` → `{id, title, difficulty, type, description, time_limit_seconds}`
  - `POST /api/submit/:id` → `{score, passed, total, results, error}`
- Produces: submission form + result display at `/problem/:id`

- [ ] **Step 1: Write `frontend/src/components/ResultPanel.jsx`**

```jsx
export default function ResultPanel({ result }) {
  if (!result) return null
  const { score, passed, total, results, error } = result
  return (
    <div style={{ marginTop: 24, padding: 16, border: '1px solid #e5e7eb', borderRadius: 8, background: '#fff' }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, marginBottom: 8 }}>
        <h2 style={{ margin: 0, fontSize: 28, color: score === 100 ? '#16a34a' : score >= 50 ? '#d97706' : '#dc2626' }}>
          {score}/100
        </h2>
        <span style={{ color: '#6b7280' }}>{passed}/{total} tests passed</span>
      </div>

      {error && (
        <pre style={{
          background: '#fee2e2', color: '#dc2626', padding: 12,
          borderRadius: 4, fontSize: 12, overflowX: 'auto', marginBottom: 12
        }}>
          {error}
        </pre>
      )}

      <div>
        {results.map(r => (
          <div key={r.case} style={{
            display: 'flex', alignItems: 'flex-start', gap: 8,
            padding: '8px 12px', marginBottom: 4, borderRadius: 4,
            background: r.passed ? '#dcfce7' : '#fee2e2'
          }}>
            <span style={{ fontWeight: 700, color: r.passed ? '#16a34a' : '#dc2626' }}>
              {r.passed ? '✓' : '✗'}
            </span>
            <span style={{ color: '#374151' }}>Case {r.case}</span>
            {!r.passed && (
              <span style={{ color: '#6b7280', fontSize: 12, marginLeft: 4 }}>
                got: <code>{r.output}</code> · expected: <code>{r.expected}</code>
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Write `frontend/src/pages/Submit.jsx`**

```jsx
import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import ResultPanel from '../components/ResultPanel'

export default function Submit() {
  const { id } = useParams()
  const nav = useNavigate()
  const [problem, setProblem] = useState(null)
  const [tab, setTab] = useState('paste')
  const [code, setCode] = useState('')
  const [file, setFile] = useState(null)
  const [fileError, setFileError] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const fileRef = useRef()

  useEffect(() => {
    fetch(`/api/problems/${id}`).then(r => r.json()).then(data => {
      if (data.detail) { nav('/'); return; }
      setProblem(data)
    })
  }, [id])

  function handleFileChange(e) {
    const f = e.target.files[0]
    if (!f) return
    if (f.size > 10 * 1024 * 1024) {
      setFileError('File exceeds 10MB limit')
      setFile(null)
      return
    }
    setFileError(null)
    setFile(f)
  }

  async function handleSubmit() {
    setLoading(true)
    setResult(null)
    const form = new FormData()
    if (tab === 'paste') form.append('code', code)
    else form.append('file', file)

    try {
      const res = await fetch(`/api/submit/${id}`, { method: 'POST', body: form })
      setResult(await res.json())
    } finally {
      setLoading(false)
    }
  }

  if (!problem) return <div style={{ padding: 24 }}>Loading…</div>

  const canSubmit = !loading && (tab === 'paste' ? code.trim() : !!file)
  const TabBtn = ({ t, label }) => (
    <button onClick={() => setTab(t)} style={{
      padding: '6px 16px', border: 'none', borderRadius: 4, cursor: 'pointer',
      background: tab === t ? '#3b82f6' : '#e5e7eb',
      color: tab === t ? '#fff' : '#374151'
    }}>{label}</button>
  )

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: 24 }}>
      <button onClick={() => nav('/')} style={{
        background: 'none', border: 'none', cursor: 'pointer', color: '#3b82f6', marginBottom: 12
      }}>← Back</button>

      <h1 style={{ marginBottom: 4 }}>{problem.title}</h1>
      <p style={{ color: '#6b7280', marginBottom: 12 }}>
        {problem.difficulty} · {problem.type} · {problem.time_limit_seconds}s limit
      </p>
      <p style={{ lineHeight: 1.6, marginBottom: 24 }}>{problem.description}</p>

      <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
        <TabBtn t="paste" label="Paste Code" />
        <TabBtn t="upload" label="Upload File" />
      </div>

      {tab === 'paste' ? (
        <textarea
          value={code} onChange={e => setCode(e.target.value)}
          rows={14} placeholder="Paste your solution here…"
          style={{
            width: '100%', fontFamily: 'monospace', fontSize: 13,
            padding: 12, border: '1px solid #d1d5db', borderRadius: 6
          }}
        />
      ) : (
        <div>
          <div
            onClick={() => fileRef.current.click()}
            style={{
              border: '2px dashed #d1d5db', borderRadius: 8, padding: 40,
              textAlign: 'center', cursor: 'pointer', color: '#6b7280'
            }}
          >
            {file ? `📄 ${file.name}` : 'Click to select a file (max 10MB)'}
          </div>
          <input ref={fileRef} type="file" onChange={handleFileChange} style={{ display: 'none' }} />
          {fileError && <p style={{ color: '#dc2626', marginTop: 6, fontSize: 13 }}>{fileError}</p>}
        </div>
      )}

      <button
        onClick={handleSubmit} disabled={!canSubmit}
        style={{
          marginTop: 14, padding: '10px 28px', background: canSubmit ? '#3b82f6' : '#9ca3af',
          color: '#fff', border: 'none', borderRadius: 6, cursor: canSubmit ? 'pointer' : 'default',
          fontSize: 15, fontWeight: 600
        }}
      >
        {loading ? 'Grading…' : 'Submit'}
      </button>
      {loading && <p style={{ color: '#6b7280', marginTop: 6, fontSize: 13 }}>Running in sandbox…</p>}

      <ResultPanel result={result} />
    </div>
  )
}
```

- [ ] **Step 3: Test the full flow manually**

With backend and frontend running:
1. Go to `http://localhost:5173`
2. Click an algorithm problem (e.g., "Echo Input")
3. Paste `print(input())` and click Submit
4. Expect score: 100/100 with green checkmarks
5. Paste `print("wrong")` and submit
6. Expect score: 0/100 with red X marks and diff shown

- [ ] **Step 4: Test file upload with a zip bomb (security check)**

```bash
python -c "
import io, zipfile
buf = io.BytesIO()
with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
    zf.writestr('bomb.txt', b'\x00' * (51*1024*1024))
open('/tmp/bomb.zip', 'wb').write(buf.getvalue())
"
```

Try uploading `/tmp/bomb.zip` — expect a 413 error shown in the UI.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/ResultPanel.jsx frontend/src/pages/Submit.jsx
git commit -m "feat: submit page with code paste, file upload, and result panel"
```

---

## Self-Review Checklist

- [x] **Spec coverage:**
  - File bomb protection (3 layers) → Task 2 + Task 10 step 3
  - Algorithm grading → Tasks 4, 6, 7
  - Interactive grading (Playwright screenshot) → Tasks 5, 6, 7
  - Webapp grading (Playwright UI tests) → Tasks 5, 6, 7
  - 5 difficulty labels → Task 6 (all 5 difficulties have at least one problem)
  - File upload + code paste → Tasks 2, 7, 10
  - Anonymous, no accounts → routes never ask for identity
  - Docker resource caps → Task 3 (`sandbox.py`)
  - Internal network for webapp → Task 5 step 3
  - React frontend with filters → Tasks 9, 10
  - All problems defined as JSON → Task 6

- [x] **No placeholders:** all steps have exact code

- [x] **Type consistency:**
  - `run_in_sandbox` signature consistent across Tasks 3, 4, 5
  - `grade_*` functions all return `{score, passed, total, results, error}` — consistent with `ResultPanel` expectations
  - `problem_dir: Path` param added to `grade_interactive` and `grade_webapp` — consistent with `submit.py` caller
