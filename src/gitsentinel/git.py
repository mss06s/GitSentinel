from gitsentinel.diff import parse_diff

import subprocess
import typer

git_app = typer.Typer()

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


@git_app.callback(invoke_without_command=True)
def get_diff(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        try:
            raw_diff = run_git_diff()
            repo_root = get_repo_root()

            parsed_diff = parse_diff(raw_diff, repo=repo_root)

            for file in parsed_diff:
                typer.echo(f"File: {file.path}, Additions: {file.additions}, Deletions: {file.deletions}, Repo: {file.repo}")

        except RuntimeError as e:
            typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)


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