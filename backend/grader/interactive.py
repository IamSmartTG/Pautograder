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
    threshold = problem.get("diff_threshold", 0.05)

    # Drop any student-supplied Playwright config so it can't shadow ours and
    # disable the screenshot comparison (e.g. ignoreSnapshots / loose threshold).
    submission = {k: v for k, v in files.items()
                  if not Path(k).name.lower().startswith("playwright.config.")}
    submission[script_name] = (problem_dir / problem["playwright_script"]).read_bytes()
    # Pin a deterministic, platform-independent snapshot path so the shipped
    # baseline is found — Playwright's default appends a platform suffix we
    # can't predict from here.
    submission["playwright.config.js"] = (
        "module.exports = {\n"
        "  snapshotPathTemplate: '{testFileDir}/__screenshots__/{arg}{ext}',\n"
        f"  expect: {{ toHaveScreenshot: {{ maxDiffPixelRatio: {threshold} }} }},\n"
        "  use: { launchOptions: { args: ['--no-sandbox'] } },\n"
        "};\n"
    ).encode()
    submission[f"__screenshots__/{baseline_name}"] = (
        problem_dir / problem["screenshot_baseline"]
    ).read_bytes()

    output = run_in_sandbox(
        image=BROWSER_IMAGE,
        command=["playwright", "test", f"/submission/{script_name}",
                 "--config=/submission/playwright.config.js", "--reporter=json"],
        files=submission,
        timeout=problem.get("time_limit_seconds", 30),
        network="none",
        shm_size="512m",  # Chromium crashes on the default 64m /dev/shm
    )

    passed = output["exit_code"] == 0 and not output["timed_out"]
    return {
        "score": 100 if passed else 0,
        "passed": 1 if passed else 0,
        "total": 1,
        "results": [{"case": 1, "passed": passed, "output": output["stdout"][:500], "expected": "matches baseline"}],
        "error": output["stderr"][:300] if output["stderr"] else None,
    }
