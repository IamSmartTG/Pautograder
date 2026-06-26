import json
from pathlib import Path
from unittest.mock import patch
from grader.webapp import grade_webapp

PROBLEMS_MEDIUM = Path(__file__).parent.parent / "problems" / "medium"

def test_webapp_strips_student_config_and_injects_no_sandbox():
    problem = json.loads((PROBLEMS_MEDIUM / "webapp-001.json").read_text())
    captured = {}

    def fake_run(**kwargs):
        captured.update(kwargs)
        return {"stdout": "{}", "stderr": "", "exit_code": 0, "timed_out": False}

    student_files = {"index.html": b"<html></html>", "playwright.config.ts": b"evil"}
    with patch("grader.webapp.run_in_sandbox", side_effect=fake_run):
        grade_webapp(problem, PROBLEMS_MEDIUM, student_files)

    files = captured["files"]
    assert "playwright.config.ts" not in files            # student config stripped
    assert b"--no-sandbox" in files["playwright.config.js"]  # our config injected
    assert "--config=/submission/playwright.config.js" in captured["command"]
    assert captured["shm_size"] == "512m"
