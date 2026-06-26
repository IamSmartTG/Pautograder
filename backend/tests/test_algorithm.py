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

def test_c_all_pass():
    # compile-check (ok) then one run per test case
    with patch("grader.algorithm.run_in_sandbox", side_effect=[
        _mock_sandbox(exit_code=0),        # compile-check
        _mock_sandbox("hello\n"),          # case 1
        _mock_sandbox("world\n"),          # case 2
    ]):
        result = grade_algorithm(PROBLEM, "int main(){}", "c")
    assert result["score"] == 100
    assert result["passed"] == 2

def test_c_compile_error():
    with patch("grader.algorithm.run_in_sandbox", side_effect=[
        {"stdout": "", "stderr": "solution.c:1:1: error: expected ';'",
         "exit_code": 1, "timed_out": False},
    ]):
        result = grade_algorithm(PROBLEM, "int main(){ bad }", "c")
    assert result["score"] == 0
    assert result["passed"] == 0
    assert "error" in result["error"]
    assert result["results"][0]["output"] == "compile error"
