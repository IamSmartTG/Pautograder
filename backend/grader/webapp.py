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
