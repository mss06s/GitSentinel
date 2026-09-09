from enum import Enum
from dataclasses import dataclass, field


class Severity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


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

@dataclass
class Finding:
    """Represents an issue found by the LLM in a diff."""
    severity: Severity
    category: str
    file_path: str
    line_number: int
    message: str
    suggestion: str