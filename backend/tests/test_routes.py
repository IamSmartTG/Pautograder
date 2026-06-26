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
