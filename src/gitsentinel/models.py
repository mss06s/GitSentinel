from dataclasses import dataclass

@dataclass
class GitDiffInfo:
    """Stores targeted git diff metrics for a specific file."""
    path: str
    additions: int
    deletions: int