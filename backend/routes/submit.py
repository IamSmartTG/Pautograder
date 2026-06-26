import asyncio
import json
import re
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from security.firebomb import check_paste, check_upload, safe_extract_zip
from grader.algorithm import grade_algorithm
from grader.interactive import grade_interactive
from grader.webapp import grade_webapp
from grader.sandbox import _executor

router = APIRouter()
PROBLEMS_DIR = Path(__file__).parent.parent / "problems"

def _load_problem(problem_id: str) -> tuple[dict, Path]:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", problem_id):
        raise HTTPException(404, f"Problem '{problem_id}' not found")
    for d in PROBLEMS_DIR.iterdir():
        if d.is_dir():
            p = d / f"{problem_id}.json"
            if p.exists():
                return json.loads(p.read_text()), d
    raise HTTPException(404, f"Problem '{problem_id}' not found")

@router.post("/submit/{problem_id}")
async def submit(
    problem_id: str,
    code: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    language: Optional[str] = Form("python"),
):
    if not code and not file:
        raise HTTPException(400, "Provide either 'code' or 'file'")

    problem, problem_dir = _load_problem(problem_id)
    ptype = problem["type"]

    if code:
        check_paste(code)  # raises 413 if too large
        if ptype != "algorithm":
            raise HTTPException(400, "This problem type requires a file upload, not pasted code")
        submission_files = {"solution.py": code.encode()}
        content = None
    else:
        content = await file.read()
        fname = file.filename or "upload"
        check_upload(fname, content)
        is_zip = fname.lower().endswith(".zip")
        if ptype == "algorithm" and is_zip:
            raise HTTPException(400, "Upload a single source file or paste code for algorithm problems")
        if is_zip:
            # Extract so index.html etc. land directly in the sandbox tree
            submission_files = safe_extract_zip(content)
            if not submission_files:
                raise HTTPException(400, "Zip archive contains no usable files")
        else:
            safe_name = Path(fname).name or "upload"  # strips any ../ components
            submission_files = {safe_name: content}

    loop = asyncio.get_event_loop()
    if ptype == "algorithm":
        code_str = code if code else content.decode("utf-8", errors="replace")
        return await loop.run_in_executor(_executor, grade_algorithm, problem, code_str, language)
    elif ptype == "interactive":
        return await loop.run_in_executor(_executor, grade_interactive, problem, problem_dir, submission_files)
    elif ptype == "webapp":
        return await loop.run_in_executor(_executor, grade_webapp, problem, problem_dir, submission_files)
    else:
        raise HTTPException(400, f"Unknown problem type: {ptype}")
