import typer
from gitsentinel.git import git_app

app = typer.Typer()

app.add_typer(git_app, name="diff")

@app.callback(invoke_without_command=True)
def default_command(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        typer.echo("GitSentinel")
        typer.echo("Local Codebase Auditing Tool")
        typer.echo("Version: 0.1.0")

def main():
    app()

if __name__ == "__main__":
    main()

