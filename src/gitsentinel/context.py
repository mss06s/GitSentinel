import dataclasses
import json
import os

from gitsentinel.models import GitDiffInfo, Hunk


def get_context_window(repo_root: str, file_path: str, hunk: Hunk, window: int = 10) -> str:
    """
    Reads the current version of the file from disk and returns a window of
    lines surrounding the hunk (window lines before and after).

    Returns an empty string if the file can't be read (e.g. deleted files,
    binary files).
    """
    full_path = os.path.join(repo_root, file_path)

    try:
        with open(full_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except (FileNotFoundError, UnicodeDecodeError):
        return ""

    start = max(0, hunk.new_start - 1 - window)
    end = min(len(lines), hunk.new_start - 1 + hunk.new_count + window)

    return "".join(lines[start:end])


def diff_context_to_json(parsed_diff: list[GitDiffInfo], repo_root: str, window: int = 10) -> str:
    """
    Serializes the parsed diff to JSON, same as diff_to_json, but adds a
    "context" field to each hunk containing the surrounding code read from
    the current file on disk.
    """
    enriched_files = []

    for file_info in parsed_diff:
        file_dict = dataclasses.asdict(file_info)

        for hunk_dict, hunk in zip(file_dict["hunks"], file_info.hunks):
            hunk_dict["context"] = get_context_window(repo_root, file_info.path, hunk, window=window)

        enriched_files.append(file_dict)

    return json.dumps(enriched_files)
