# Running Pautograder

Anonymous autograder: FastAPI backend grades submissions inside Docker, React/Vite frontend.

## Prerequisites

- Python 3.11+
- Node.js 18+
- Docker Desktop (only needed for actual grading — the API and UI run without it)

---

## 1. Backend (API)

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API is now at `http://localhost:8000` (e.g. `GET /api/problems`).

## 2. Frontend (UI)

```bash
cd frontend
npm install
npm run dev
```

UI is at `http://localhost:5173`. Vite proxies `/api/*` to `http://localhost:8000`, so the backend must be running too.

## 3. Tests

```bash
cd backend
python -m pytest tests -v
```

All grading is mocked in tests, so Docker is **not** required here. (Also runs in CI on every push — see `.github/workflows/ci.yml`.)

---

## 4. Enable grading (required for submissions to actually run)

Without these, the UI loads and you can submit, but every submission errors — there is no sandbox to grade in. **Start Docker Desktop first**, then from the repo root:

```bash
# Build the two sandbox images
docker build -t pautograder-python-sandbox docker/python-sandbox/
docker build -t pautograder-browser-sandbox docker/browser-sandbox/   # large, takes a few minutes

# Internal (no-internet) network used by webapp grading
docker network create --internal pautograder_sandbox
```

Resource caps (`256m` RAM, `0.5` CPU, `64` PIDs, `no-new-privileges`, no network for algorithm/interactive) are applied per-container in `backend/grader/sandbox.py` — nothing to configure.

Submission methods by problem type:
- **algorithm** — paste code, or upload a single source file (not a zip)
- **interactive / webapp** — upload `index.html`, or a `.zip` containing it (zips are extracted into the sandbox)

---

## 5. Generate the interactive baseline screenshot

The interactive problem (`interactive-001`) ships with a **1×1 placeholder** baseline, so visual grading can't pass until a real one is generated. Screenshots are platform/browser specific, so the baseline **must** be produced with the same `pautograder-browser-sandbox` image that grades — otherwise it will never match.

From the repo root (after step 4):

```bash
mkdir ref-counter
```

Create `ref-counter/index.html` (a correct reference solution):

```html
<!DOCTYPE html>
<html>
  <body>
    <span data-testid="counter">0</span>
    <button onclick="document.querySelector('[data-testid=counter]').textContent =
      +document.querySelector('[data-testid=counter]').textContent + 1">Click me</button>
  </body>
</html>
```

Create `ref-counter/playwright.config.js` — must match the config the grader injects (`backend/grader/interactive.py`):

```js
module.exports = {
  snapshotPathTemplate: '{testFileDir}/__screenshots__/{arg}{ext}',
  expect: { toHaveScreenshot: { maxDiffPixelRatio: 0.05 } },
};
```

Copy in the grader's spec, then generate the snapshot inside the sandbox image:

```bash
cp backend/problems/easy/interactive-001/test.spec.js ref-counter/

docker run --rm -v "$(pwd)/ref-counter:/submission" -w /submission \
  pautograder-browser-sandbox \
  npx playwright test test.spec.js --config=/submission/playwright.config.js --update-snapshots
```

That writes `ref-counter/__screenshots__/baseline.png`. Copy it into the problem so the grader uses it (`screenshot_baseline` in `interactive-001.json` points here):

```bash
cp ref-counter/__screenshots__/baseline.png backend/problems/easy/interactive-001/baseline.png
rm -rf ref-counter
```

> Windows PowerShell: replace `$(pwd)` with `${PWD}`, `cp` with `Copy-Item`, `rm -rf` with `Remove-Item -Recurse -Force`.

---

## Known limitations / TODO

- **Chromium as root** — the Playwright image runs as root; if browser grading fails to launch Chromium ("running as root without `--no-sandbox`"), add `use: { launchOptions: { args: ['--no-sandbox'] } }` to the injected config in `backend/grader/interactive.py` and the same for the webapp spec. Verify against the running image.
- **W2 sandbox hardening (partial)** — `no-new-privileges` is applied. `cap_drop=["ALL"]`, a non-root user, and a read-only rootfs are deferred: they can break Chromium's sandbox and Playwright's writes, so enable them only after testing against `pautograder-browser-sandbox`.
- **Nested zips** — a submission zip must have `index.html` at its root; files nested under a folder won't be found at `/submission/index.html`.
