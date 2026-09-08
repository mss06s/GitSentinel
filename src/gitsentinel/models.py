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
    """Represents a finding in the codebase."""
    file_path: str
    line_number: int
    message: str
    severity: Severity
    rule_id: str
    commit_hash: str
    repo: str