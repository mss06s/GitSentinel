import subprocess
import typer

git_app = typer.Typer()

@git_app.callback(invoke_without_command=True)
def get_diff(ctx: typer.Context):
    try:
        result = subprocess.run(['git', 'diff'], capture_output=True, text=True)

        if result.returncode in [0,1]:
            typer.echo(result.stdout)
            return

        typer.echo(f"Git Error: {result.stderr.strip()}")

    except FileNotFoundError:
        typer.echo("Error: Git is not installed or not found in the system PATH.")