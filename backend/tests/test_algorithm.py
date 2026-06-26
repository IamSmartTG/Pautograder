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
