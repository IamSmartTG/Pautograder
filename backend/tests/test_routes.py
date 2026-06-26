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

def test_get_problem_rejects_traversal():
    # Backslash path-traversal attempt (Windows separator) and other invalid ids
    for bad in ("..%5C..%5Cwin.ini", "bad!id", "a.b"):
        r = client.get(f"/api/problems/{bad}")
        assert r.status_code == 404, bad

def test_submit_rejects_traversal():
    r = client.post("/api/submit/bad!id", data={"code": "print(1)"})
    assert r.status_code == 404

def test_submit_no_body_rejected():
    r = client.post("/api/submit/algo-001")
    assert r.status_code == 400

def test_submit_paste_too_large():
    r = client.post("/api/submit/algo-001", data={"code": "x" * (51 * 1024)})
    assert r.status_code == 413

def test_submit_paste_rejected_for_webapp():
    # Pasted code can't satisfy a webapp problem (needs index.html)
    r = client.post("/api/submit/webapp-001", data={"code": "<html></html>"})
    assert r.status_code == 400

def test_submit_zip_rejected_for_algorithm():
    import io, zipfile
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("solution.py", "print(1)")
    r = client.post("/api/submit/algo-001",
                    files={"file": ("sol.zip", buf.getvalue(), "application/zip")})
    assert r.status_code == 400
