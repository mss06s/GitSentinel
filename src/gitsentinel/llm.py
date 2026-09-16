import anthropic
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError

from gitsentinel.models import Finding, Severity

load_dotenv()

MODEL = "claude-haiku-4-5-20251001"

FINDINGS_TOOL = {
    "name": "report_findings",
    "description": "Report code review findings identified in the diff.",
    "input_schema": {
        "type": "object",
        "properties": {
            "findings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "severity": {"type": "string", "enum": ["low", "medium", "high"]},
                        "category": {"type": "string"},
                        "file_path": {"type": "string"},
                        "line_number": {"type": "integer"},
                        "message": {"type": "string"},
                        "suggestion": {"type": "string"},
                        "old_code": {
                            "type": "string",
                            "description": "The exact literal code snippet to replace, copied verbatim from the file's context field.",
                        },
                        "new_code": {
                            "type": "string",
                            "description": "The corrected code that should replace old_code.",
                        },
                    },
                    "required": [
                        "severity", "category", "file_path",
                        "line_number", "message", "suggestion",
                        "old_code", "new_code",
                    ],
                },
            },
        },
        "required": ["findings"],
    },
}


class FindingSchema(BaseModel):
    severity: Severity
    category: str
    file_path: str
    line_number: int
    message: str
    suggestion: str
    old_code: str
    new_code: str


def summarize_diff(diff_json: str) -> str:
    """
    Sends a JSON-serialized diff to Claude and returns a plain-English summary.
    Raises RuntimeError if the API call fails.
    """
    client = anthropic.Anthropic()
    prompt = (
        "Summarize the following git diff in plain English. "
        "Focus on what changed and why it might matter:\n\n"
        f"{diff_json}"
    )

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.APIError as e:
        raise RuntimeError(f"Claude API error: {e}") from e

    return response.content[0].text


def find_issues(diff_json: str) -> list[Finding]:
    """
    Sends a JSON-serialized diff to Claude and returns structured findings.

    Forces Claude to respond via the report_findings tool (not free text),
    then validates each item with Pydantic before trusting it.
    Raises RuntimeError if the API call fails or the response is malformed.
    """
    client = anthropic.Anthropic()
    prompt = (
        "Review the following git diff for bugs, security issues, and code "
        "quality problems. Each hunk includes a \"context\" field with the "
        "surrounding code from the current file, and a \"related_code\" field "
        "with semantically similar code found elsewhere in the repo (e.g. other "
        "call sites or similar functions) - use both to judge whether the change "
        "is consistent with the rest of the codebase. Report every issue you "
        "find, including ones you're only somewhat confident about. For each "
        "finding, also provide old_code (the exact literal snippet to replace, "
        "copied verbatim from the context field so it can be matched exactly) "
        "and new_code (the fix):\n\n"
        f"{diff_json}"
    )

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            tools=[FINDINGS_TOOL],
            tool_choice={"type": "tool", "name": "report_findings"},
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.APIError as e:
        raise RuntimeError(f"Claude API error: {e}") from e

    tool_use_block = next(b for b in response.content if b.type == "tool_use")
    raw_findings = tool_use_block.input["findings"]

    try:
        validated = [FindingSchema(**item) for item in raw_findings]
    except ValidationError as e:
        raise RuntimeError(f"Claude returned malformed findings: {e}") from e

    return [Finding(**f.model_dump()) for f in validated]
