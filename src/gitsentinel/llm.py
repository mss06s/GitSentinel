import anthropic
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-haiku-4-5-20251001"


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
