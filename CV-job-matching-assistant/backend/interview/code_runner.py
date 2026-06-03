from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from backend.interview.schemas import CodeRunRequest, CodeRunResponse


MAX_OUTPUT_CHARS = 8000


def run_python_code(request: CodeRunRequest) -> CodeRunResponse:
    timeout_seconds = max(1, min(request.timeout_seconds, 10))

    with tempfile.TemporaryDirectory() as temp_dir:
        code_path = Path(temp_dir) / "solution.py"
        code_path.write_text(request.code, encoding="utf-8")

        try:
            completed = subprocess.run(
                [sys.executable, str(code_path)],
                input=request.stdin,
                capture_output=True,
                cwd=temp_dir,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            return CodeRunResponse(
                stdout=_trim(exc.stdout or ""),
                stderr=_trim(exc.stderr or "Execution timed out."),
                exit_code=None,
                timed_out=True,
            )

    return CodeRunResponse(
        stdout=_trim(completed.stdout),
        stderr=_trim(completed.stderr),
        exit_code=completed.returncode,
        timed_out=False,
    )


def _trim(value: str) -> str:
    if len(value) <= MAX_OUTPUT_CHARS:
        return value
    return value[:MAX_OUTPUT_CHARS] + "\n... output truncated ..."
