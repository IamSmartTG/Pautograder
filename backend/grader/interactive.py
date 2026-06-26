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
