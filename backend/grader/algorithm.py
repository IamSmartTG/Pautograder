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
