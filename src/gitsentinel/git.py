import subprocess


def run_git_diff() -> str:
    """
    Runs 'git diff' and returns the raw stdout.
    Raises RuntimeError if git fails or isn't installed.
    """
    try:
        result = subprocess.run(
            ['git', 'diff'],
            capture_output=True,
            text=True
        )
    except FileNotFoundError:
        raise RuntimeError("Git is not installed or not found in the system PATH.")

    if result.returncode not in [0, 1]:
        raise RuntimeError(f"Git Error: {result.stderr.strip()}")

    return result.stdout


def get_repo_root():
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            return result.stdout.strip()

        raise RuntimeError(f"Git Error: {result.stderr.strip()}")
    
    except FileNotFoundError as e:
        raise RuntimeError("Git is not installed or not found in the system PATH.") from e