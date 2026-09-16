import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass

from gitsentinel.models import Finding

IGNORED_DIRS = {".git", ".venv", "__pycache__", ".gitsentinel", ".pytest_cache"}


@dataclass
class VerificationResult:
    verified: bool
    message: str


def apply_fix(scratch_root: str, finding: Finding) -> bool:
    """
    Applies a finding's suggested fix (old_code -> new_code) to its file
    inside the scratch copy of the repo.

    Returns False if old_code isn't found exactly once in the file - the fix
    can't be safely applied if the model's snippet doesn't match cleanly.
    """
    full_path = os.path.join(scratch_root, finding.file_path)

    try:
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return False

    if content.count(finding.old_code) != 1:
        return False

    content = content.replace(finding.old_code, finding.new_code)

    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

    return True


def run_tests(scratch_root: str) -> bool:
    """Runs pytest in the scratch copy. Returns True if all tests pass."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=scratch_root,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def verify_fix(repo_root: str, finding: Finding) -> VerificationResult:
    """
    Copies the repo to a temporary scratch directory, applies the finding's
    suggested fix there, and runs the test suite against the scratch copy.
    Never touches the real working tree.
    """
    with tempfile.TemporaryDirectory() as scratch_root:
        shutil.copytree(
            repo_root,
            scratch_root,
            ignore=shutil.ignore_patterns(*IGNORED_DIRS),
            dirs_exist_ok=True,
        )

        if not apply_fix(scratch_root, finding):
            return VerificationResult(verified=False, message="Could not locate the exact code to replace")

        if run_tests(scratch_root):
            return VerificationResult(verified=True, message="Tests passed after applying the fix")

        return VerificationResult(verified=False, message="Tests failed after applying the fix")
