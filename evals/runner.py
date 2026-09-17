"""
GitSentinel eval harness. Not part of the pytest suite - run it directly:

    python evals/runner.py            # uses cached model responses if available
    python evals/runner.py --refresh  # forces fresh API calls, overwrites cache

Scoring approach (see README's Evals section for the full rationale): a
planted issue is "caught" if any actual finding lands within LINE_TOLERANCE
lines of the expected line. Model wording varies run to run, so this scores
on the right line being flagged, not exact message text.
"""
import argparse
import hashlib
import json
from pathlib import Path

from rich.console import Console
from rich.table import Table

from gitsentinel.diff import parse_diff, diff_to_json
from gitsentinel.llm import find_issues

FIXTURES_DIR = Path(__file__).parent / "fixtures"
CACHE_DIR = Path(__file__).parent / "cache"
RESULTS_PATH = Path(__file__).parent / "results.json"

LINE_TOLERANCE = 2


def load_fixtures() -> list[dict]:
    fixtures = []
    for diff_path in sorted(FIXTURES_DIR.glob("*.diff")):
        expected_path = diff_path.with_name(diff_path.stem + ".expected.json")
        raw_diff = diff_path.read_text(encoding="utf-8")
        expected = json.loads(expected_path.read_text(encoding="utf-8"))
        fixtures.append({"name": diff_path.stem, "raw_diff": raw_diff, "expected": expected})
    return fixtures


def get_findings(name: str, raw_diff: str, refresh: bool) -> list[dict]:
    """
    Runs find_issues() on the fixture's diff, or returns a cached result if
    one exists for this exact diff content. Cache key is a hash of the diff
    text, so editing a fixture automatically invalidates its cache entry.
    """
    cache_key = hashlib.sha256(raw_diff.encode("utf-8")).hexdigest()[:16]
    cache_path = CACHE_DIR / f"{name}_{cache_key}.json"

    if cache_path.exists() and not refresh:
        return json.loads(cache_path.read_text(encoding="utf-8"))

    parsed = parse_diff(raw_diff)
    diff_json = diff_to_json(parsed)
    findings = find_issues(diff_json)

    findings_as_dicts = [
        {
            "severity": f.severity.value,
            "category": f.category,
            "file_path": f.file_path,
            "line_number": f.line_number,
            "message": f.message,
        }
        for f in findings
    ]

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(findings_as_dicts, indent=2), encoding="utf-8")

    return findings_as_dicts


def score_fixture(fixture: dict, actual_findings: list[dict]) -> dict:
    expected_items = fixture["expected"]
    matched_actual_indices = set()

    caught = 0
    category_correct = 0
    severity_correct = 0

    for expected_item in expected_items:
        match_index = None
        for i, actual in enumerate(actual_findings):
            if i in matched_actual_indices:
                continue
            if abs(actual["line_number"] - expected_item["line_number"]) <= LINE_TOLERANCE:
                match_index = i
                break

        if match_index is None:
            continue

        caught += 1
        matched_actual_indices.add(match_index)
        actual = actual_findings[match_index]

        expected_category = expected_item.get("category", "").lower()
        actual_category = actual["category"].lower()
        if expected_category in actual_category or actual_category in expected_category:
            category_correct += 1

        if actual["severity"] == expected_item.get("expected_severity"):
            severity_correct += 1

    # A fixture with zero expected findings is a "clean diff" - every
    # actual finding on it is a false positive, since nothing should have
    # been flagged at all.
    false_positives = len(actual_findings) if not expected_items else 0

    return {
        "name": fixture["name"],
        "expected_count": len(expected_items),
        "caught": caught,
        "category_correct": category_correct,
        "severity_correct": severity_correct,
        "false_positives": false_positives,
        "actual_findings": actual_findings,
    }


def run_evals(refresh: bool = False) -> dict:
    fixtures = load_fixtures()
    results = [score_fixture(fx, get_findings(fx["name"], fx["raw_diff"], refresh)) for fx in fixtures]

    total_expected = sum(r["expected_count"] for r in results)
    total_caught = sum(r["caught"] for r in results)
    total_category_correct = sum(r["category_correct"] for r in results)
    total_severity_correct = sum(r["severity_correct"] for r in results)
    total_false_positives = sum(r["false_positives"] for r in results)
    clean_fixture_count = sum(1 for r in results if r["expected_count"] == 0)

    summary = {
        "catch_rate": total_caught / total_expected if total_expected else None,
        "false_positive_rate": total_false_positives / clean_fixture_count if clean_fixture_count else None,
        "category_accuracy": total_category_correct / total_caught if total_caught else None,
        "severity_accuracy": total_severity_correct / total_caught if total_caught else None,
        "totals": {
            "expected": total_expected,
            "caught": total_caught,
            "false_positives": total_false_positives,
            "clean_fixtures": clean_fixture_count,
        },
        "fixtures": results,
    }

    RESULTS_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def print_summary(summary: dict) -> None:
    console = Console()
    table = Table(title="GitSentinel Eval Results")
    table.add_column("Fixture")
    table.add_column("Expected")
    table.add_column("Caught")
    table.add_column("False Positives")

    for r in summary["fixtures"]:
        table.add_row(r["name"], str(r["expected_count"]), str(r["caught"]), str(r["false_positives"]))

    console.print(table)

    def pct(value):
        return f"{value:.0%}" if value is not None else "n/a"

    console.print(f"\nCatch rate:          {pct(summary['catch_rate'])} "
                  f"({summary['totals']['caught']}/{summary['totals']['expected']})")
    console.print(f"False positive rate: {summary['totals']['false_positives']} findings across "
                  f"{summary['totals']['clean_fixtures']} clean fixtures")
    console.print(f"Category accuracy:   {pct(summary['category_accuracy'])} (of caught findings)")
    console.print(f"Severity accuracy:   {pct(summary['severity_accuracy'])} (of caught findings)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the GitSentinel eval harness")
    parser.add_argument("--refresh", action="store_true", help="Ignore cached responses, call the API fresh")
    args = parser.parse_args()

    print_summary(run_evals(refresh=args.refresh))
