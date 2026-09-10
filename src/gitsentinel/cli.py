import questionary
import typer
from rich.console import Console
from rich.table import Table

from gitsentinel.git import run_git_diff, get_repo_root
from gitsentinel.diff import parse_diff, diff_to_json
from gitsentinel.llm import summarize_diff, find_issues

app = typer.Typer()

@app.callback(invoke_without_command=True)
def default_command(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        typer.echo("GitSentinel")
        typer.echo("Local Codebase Auditing Tool")
        typer.echo("Version: 0.1.0")
        typer.echo("")

        choice = questionary.select(
            "What do you want to do?",
            choices=[
                "Review changes (plain-English summary)",
                "Find issues (structured findings table)",
                "Show diff stats",
                "Show diff as JSON",
                "Exit",
            ],
        ).ask()

        if choice == "Review changes (plain-English summary)":
            review()
        elif choice == "Find issues (structured findings table)":
            findings()
        elif choice == "Show diff stats":
            diff(json_output=False)
        elif choice == "Show diff as JSON":
            diff(json_output=True)


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


@app.command()
def findings():
    try:
        raw_diff = run_git_diff()
        repo_root = get_repo_root()

        parsed_diff = parse_diff(raw_diff, repo=repo_root)
        diff_json = diff_to_json(parsed_diff)

        results = find_issues(diff_json)

        table = Table(title="GitSentinel Findings")
        table.add_column("Severity")
        table.add_column("Category")
        table.add_column("File")
        table.add_column("Line")
        table.add_column("Message")

        for finding in results:
            table.add_row(
                finding.severity.value,
                finding.category,
                finding.file_path,
                str(finding.line_number),
                finding.message,
            )

        console = Console()
        console.print(table)

    except RuntimeError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

def main():
    app()

if __name__ == "__main__":
    main()

