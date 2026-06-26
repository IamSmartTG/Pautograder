import json
from pathlib import Path
from unittest.mock import patch
from grader.interactive import grade_interactive

PROBLEMS_EASY = Path(__file__).parent.parent / "problems" / "easy"

def _passing_sandbox(**kwargs):
    return {"stdout": "", "stderr": "", "exit_code": 0, "timed_out": False}

def test_strips_student_config_and_pins_config():
    problem = json.loads((PROBLEMS_EASY / "interactive-001.json").read_text())
    captured = {}

    def fake_run(**kwargs):
        captured.update(kwargs)
        return _passing_sandbox()

    student_files = {"index.html": b"<html></html>", "playwright.config.ts": b"export default { ignoreSnapshots: true }"}
    with patch("grader.interactive.run_in_sandbox", side_effect=fake_run):
        grade_interactive(problem, PROBLEMS_EASY, student_files)

    files = captured["files"]
    # Student config must be stripped; grader config must be present
    assert "playwright.config.ts" not in files
    assert "playwright.config.js" in files
    # Auto-discovery disabled by pinning the grader config explicitly
    assert "--config=/submission/playwright.config.js" in captured["command"]
    # Chromium-in-container needs --no-sandbox and a bigger /dev/shm
    assert b"--no-sandbox" in files["playwright.config.js"]
    assert captured["shm_size"] == "512m"
