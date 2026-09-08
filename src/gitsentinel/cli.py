import typer
from gitsentinel.git import run_git_diff, get_repo_root
from gitsentinel.diff import parse_diff, diff_to_json
from gitsentinel.llm import summarize_diff

app = typer.Typer()

@app.callback(invoke_without_command=True)
def default_command(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        typer.echo("GitSentinel")
        typer.echo("Local Codebase Auditing Tool")
        typer.echo("Version: 0.1.0")


@app.command()
def diff(json_output: bool = typer.Option(False, "--json", help="Output as JSON")):
    try:
        raw_diff = run_git_diff()
        repo_root = get_repo_root()

        parsed_diff = parse_diff(raw_diff, repo=repo_root)

        if json_output:
            typer.echo(diff_to_json(parsed_diff, indent=2))
        else:
            for file in parsed_diff:
                typer.echo(f"File: {file.path}, Additions: {file.additions}, Deletions: {file.deletions}, Repo: {file.repo}")

    except RuntimeError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)


@app.command()
def review():
    try:
        raw_diff = run_git_diff()
        repo_root = get_repo_root()

        parsed_diff = parse_diff(raw_diff, repo=repo_root)
        diff_json = diff_to_json(parsed_diff)

        summary = summarize_diff(diff_json)
        typer.echo(summary)

    except RuntimeError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

def main():
    app()

if __name__ == "__main__":
    main()

