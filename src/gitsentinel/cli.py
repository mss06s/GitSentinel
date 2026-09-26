import time

import pyfiglet
import questionary
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from gitsentinel.git import run_git_diff, get_repo_root
from gitsentinel.diff import parse_diff, diff_to_json
from gitsentinel.context import diff_context_to_json
from gitsentinel.llm import summarize_diff, find_issues
from gitsentinel.rag import build_index
from gitsentinel.verify import verify_fix

app = typer.Typer()
console = Console()

MENU_STYLE = questionary.Style([
    ("qmark", "fg:#00d7ff bold"),
    ("question", "bold"),
    ("answer", "fg:#00d7ff bold"),
    ("pointer", "fg:#00d7ff bold"),
    ("highlighted", "fg:#00d7ff bold"),
    ("selected", "fg:#00d7ff"),
])

STATUS_COLORS = {"added": "green", "deleted": "red", "renamed": "yellow", "modified": "cyan"}
SEVERITY_COLORS = {"high": "red", "medium": "yellow", "low": "green"}


def print_banner():
    banner = pyfiglet.figlet_format("GitSentinel", font="standard")
    console.print(f"[bold cyan]{banner}[/bold cyan]", end="")

    subtitle = "Local Codebase Auditing Tool"
    for char in subtitle:
        console.print(char, end="", style="dim")
        time.sleep(0.02)
    console.print()
    console.print("[dim]Version: 0.1.0[/dim]\n")


@app.callback(invoke_without_command=True)
def default_command(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        print_banner()

        choice = questionary.select(
            "What do you want to do?",
            choices=[
                "Review changes (plain-English summary)",
                "Find issues (structured findings table)",
                "Show diff stats",
                "Show diff as JSON",
                "Exit",
            ],
            style=MENU_STYLE,
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
            table = Table(title="GitSentinel Diff")
            table.add_column("Status")
            table.add_column("File")
            table.add_column("+", justify="right")
            table.add_column("-", justify="right")

            for file in parsed_diff:
                color = STATUS_COLORS.get(file.status, "white")
                table.add_row(
                    f"[{color}]{file.status}[/{color}]",
                    file.path,
                    f"[green]+{file.additions}[/green]",
                    f"[red]-{file.deletions}[/red]",
                )

            console.print(table)

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

        with console.status("[bold cyan]Reviewing diff with Claude...", spinner="dots"):
            summary = summarize_diff(diff_json)

        console.print(Panel(summary, title="Diff Summary", border_style="cyan"))

    except RuntimeError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)


@app.command()
def findings(verify: bool = typer.Option(False, "--verify", help="Verify suggested fixes against the test suite")):
    try:
        raw_diff = run_git_diff()
        repo_root = get_repo_root()

        parsed_diff = parse_diff(raw_diff, repo=repo_root)

        with console.status("[bold cyan]Gathering structural and semantic context...", spinner="dots"):
            diff_json = diff_context_to_json(parsed_diff, repo_root)

        with console.status("[bold cyan]Analyzing diff with Claude...", spinner="dots"):
            results = find_issues(diff_json)

        table = Table(title="GitSentinel Findings")
        table.add_column("Severity")
        table.add_column("Category")
        table.add_column("File")
        table.add_column("Line")
        table.add_column("Message")
        if verify:
            table.add_column("Verified")

        for finding in results:
            color = SEVERITY_COLORS.get(finding.severity.value, "white")
            row = [
                f"[{color}]{finding.severity.value}[/{color}]",
                finding.category,
                finding.file_path,
                str(finding.line_number),
                finding.message,
            ]
            if verify:
                with console.status(f"[bold cyan]Verifying fix for line {finding.line_number}...", spinner="dots"):
                    result = verify_fix(repo_root, finding)
                if result.verified:
                    row.append("[green]Yes[/green]")
                else:
                    row.append(f"[red]No[/red] - {result.message}")
            table.add_row(*row)

        console.print(table)

    except RuntimeError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

@app.command()
def index():
    try:
        repo_root = get_repo_root()

        with console.status("[bold cyan]Indexing repository...", spinner="dots"):
            count = build_index(repo_root)

        console.print(f"[bold green]✓[/bold green] Indexed {count} code chunks.")

    except RuntimeError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

def main():
    app()

if __name__ == "__main__":
    main()
