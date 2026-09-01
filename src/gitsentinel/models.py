from dataclasses import dataclass, field


@dataclass
class Hunk:
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: list[str]


@dataclass
class GitDiffInfo:
    """Stores targeted git diff metrics for a specific file."""
    path: str
    additions: int
    deletions: int
    repo: str
    status: str = "modified"
    hunks: list[Hunk] = field(default_factory=list)
