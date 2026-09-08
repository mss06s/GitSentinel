from typer.testing import CliRunner

from gitsentinel.cli import app


runner = CliRunner()


def test_default_command_shows_banner():
    result = runner.invoke(app, [])

    assert result.exit_code == 0
    assert "GitSentinel" in result.stdout
    assert "Local Codebase Auditing Tool" in result.stdout


def test_review_command_prints_summary(monkeypatch):
    monkeypatch.setattr("gitsentinel.cli.run_git_diff", lambda: "fake diff")
    monkeypatch.setattr("gitsentinel.cli.get_repo_root", lambda: "fake/repo")
    monkeypatch.setattr("gitsentinel.cli.summarize_diff", lambda diff_json: "Mocked summary of changes")

    result = runner.invoke(app, ["review"])

    assert result.exit_code == 0
    assert "Mocked summary of changes" in result.stdout


def test_review_command_handles_llm_error(monkeypatch):
    monkeypatch.setattr("gitsentinel.cli.run_git_diff", lambda: "fake diff")
    monkeypatch.setattr("gitsentinel.cli.get_repo_root", lambda: "fake/repo")

    def raise_error(diff_json):
        raise RuntimeError("Claude API error: boom")

    monkeypatch.setattr("gitsentinel.cli.summarize_diff", raise_error)

    result = runner.invoke(app, ["review"])

    assert result.exit_code == 1
    assert "Claude API error" in result.stderr
