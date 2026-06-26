from .sandbox import run_in_sandbox

PYTHON_IMAGE = "pautograder-python-sandbox"
C_IMAGE = "pautograder-c-sandbox"

# ponytail: runner.py redirects stdin so the student's script uses input() normally
_RUNNER = """\
import sys
sys.stdin = open('/submission/input.txt', 'r')
exec(open('/submission/solution.py').read())
"""

# Per-language config. Compiled languages provide a shell 'compile' command that
# produces /submission/sol; the binary is then run with stdin from input.txt.
_LANGS = {
    "python": {"image": PYTHON_IMAGE, "src": "solution.py"},
    "c":   {"image": C_IMAGE, "src": "solution.c",
            "compile": "gcc -O2 -std=c11 -o /submission/sol /submission/solution.c -lm"},
    "cpp": {"image": C_IMAGE, "src": "solution.cpp",
            "compile": "g++ -O2 -std=c++17 -o /submission/sol /submission/solution.cpp"},
}


def grade_algorithm(problem: dict, code: str, language: str = "python") -> dict:
    language = language if language in _LANGS else "python"
    cfg = _LANGS[language]
    test_cases = problem["test_cases"]
    timeout = problem.get("time_limit_seconds", 10)

    # Compiled languages: one compile-check up front so compile errors surface
    # cleanly instead of every test case showing blank output.
    if "compile" in cfg:
        chk = run_in_sandbox(
            image=cfg["image"],
            command=["sh", "-c", cfg["compile"]],
            files={cfg["src"]: code.encode()},
            timeout=timeout,
        )
        if chk["timed_out"] or chk["exit_code"] != 0:
            err = (chk["stderr"] or "Compilation failed").strip()[:1000]
            return {
                "score": 0, "passed": 0, "total": len(test_cases),
                "results": [
                    {"case": i + 1, "passed": False, "output": "compile error",
                     "expected": c["expected"].strip()}
                    for i, c in enumerate(test_cases)
                ],
                "error": err,
            }

    results = []
    for i, case in enumerate(test_cases):
        if language == "python":
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
        else:
            output = run_in_sandbox(
                image=cfg["image"],
                command=["sh", "-c", f'{cfg["compile"]} && /submission/sol < /submission/input.txt'],
                files={cfg["src"]: code.encode(), "input.txt": case["input"].encode()},
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
