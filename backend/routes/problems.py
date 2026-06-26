import json
import re
from pathlib import Path
from fastapi import APIRouter, HTTPException

router = APIRouter()
PROBLEMS_DIR = Path(__file__).parent.parent / "problems"
_DIFFICULTY_ORDER = ["easy", "medium", "hard", "expert", "master", "challenger"]
# Problem ids are filesystem path segments — reject anything that could traverse
_VALID_ID = re.compile(r"[A-Za-z0-9_-]+")

def _load_summary(path: Path) -> dict:
    data = json.loads(path.read_text())
    return {k: data[k] for k in ("id", "title", "difficulty", "type", "description")}

def _load_full(path: Path) -> dict:
    return json.loads(path.read_text())

def _find_problem_file(problem_id: str) -> Path | None:
    if not _VALID_ID.fullmatch(problem_id):
        return None
    for d in PROBLEMS_DIR.iterdir():
        if d.is_dir():
            p = d / f"{problem_id}.json"
            if p.exists():
                return p
    return None

@router.get("/problems")
def list_problems():
    problems = []
    for d in PROBLEMS_DIR.iterdir():
        if d.is_dir():
            for f in d.glob("*.json"):
                problems.append(_load_summary(f))
    problems.sort(key=lambda p: _DIFFICULTY_ORDER.index(p["difficulty"])
                  if p["difficulty"] in _DIFFICULTY_ORDER else len(_DIFFICULTY_ORDER))
    return problems

@router.get("/problems/{problem_id}")
def get_problem(problem_id: str):
    path = _find_problem_file(problem_id)
    if not path:
        raise HTTPException(404, f"Problem '{problem_id}' not found")
    data = _load_full(path)
    # Strip internal grading details (test_cases, etc.)
    return {k: data[k] for k in ("id", "title", "difficulty", "type", "description", "time_limit_seconds") if k in data}
