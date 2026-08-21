from typer.testing import CliRunner

from gitsentinel.cli import app


runner = CliRunner()


def test_default_command_shows_banner():
    result = runner.invoke(app, [])

    assert result.exit_code == 0
    assert "GitSentinel" in result.stdout
    assert "Local Codebase Auditing Tool" in result.stdout
