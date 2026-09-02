import dataclasses
import json

import typer
from gitsentinel.git import git_app, run_git_diff, get_repo_root
from gitsentinel.diff import parse_diff
from gitsentinel.llm import summarize_diff

app = typer.Typer()

app.add_typer(git_app, name="diff")

@app.callback(invoke_without_command=True)
def default_command(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        typer.echo("GitSentinel")
        typer.echo("Local Codebase Auditing Tool")
        typer.echo("Version: 0.1.0")


@app.command()
def review():
    try:
        raw_diff = run_git_diff()
        repo_root = get_repo_root()

        parsed_diff = parse_diff(raw_diff, repo=repo_root)
        as_dicts = [dataclasses.asdict(file) for file in parsed_diff]
        diff_json = json.dumps(as_dicts)

        summary = summarize_diff(diff_json)
        typer.echo(summary)

    except RuntimeError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

def main():
    app()

if __name__ == "__main__":
    main()

