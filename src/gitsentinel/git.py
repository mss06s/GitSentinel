from gitsentinel.diff import parse_diff

import subprocess
import typer

git_app = typer.Typer()

@git_app.callback(invoke_without_command=True)
def get_diff(ctx: typer.Context):
    try:
        result = subprocess.run(
            ['git', 'diff'],
            capture_output=True,
            text=True
        )

        if result.returncode in [0, 1]:
            #return result.stdout
            parsed_diff = parse_diff(result.stdout, repo=get_repo_root())

            for file in parsed_diff:
                typer.echo(file)

            return

        return f"Git Error: {result.stderr.strip()}"

    except FileNotFoundError:
        return "Error: Git is not installed or not found in the system PATH."


def get_repo_root():
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            return result.stdout.strip()

        return f"Git Error: {result.stderr.strip()}"

    except FileNotFoundError:
        return "Error: Git is not installed or not found in the system PATH."