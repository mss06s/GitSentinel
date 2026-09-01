
import re

from gitsentinel.models import GitDiffInfo


HUNK_HEADER_RE = re.compile(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@')


def parse_hunk_header(line: str):
    """
    Parses a hunk header line like '@@ -1,2 +1,3 @@' and returns
    (old_start, old_count, new_start, new_count) as ints.

    If the count is omitted (e.g. '@@ -1 +1 @@'), it defaults to 1,
    per unified diff format rules.

    Returns None if the line doesn't match a hunk header at all.
    """
    match = HUNK_HEADER_RE.match(line)
    if match is None:
        return None

    old_start_str, old_count_str, new_start_str, new_count_str = match.groups()

    old_start = int(old_start_str)
    old_count = int(old_count_str) if old_count_str is not None else 1
    new_start = int(new_start_str)
    new_count = int(new_count_str) if new_count_str is not None else 1

    return old_start, old_count, new_start, new_count


def parse_diff(raw_diff: str, repo: str = ""):
    
    """
    Parses the raw git diff output and returns a list of GitDiffInfo objects.

    Args:
        raw_diff (str): The raw output from the 'git diff' command.
        repo (str): The repository root path to attach to each entry.

    Returns:
        list[GitDiffInfo]: A list of GitDiffInfo objects representing the diff information for each file.
    """
    diff_info_list = []
    current_file = None
    additions = 0
    deletions = 0
    status = "modified"

    for line in raw_diff.splitlines():
        if line.startswith('diff --git'): 
            if current_file is not None:
                diff_info_list.append(GitDiffInfo(path=current_file, additions=additions, deletions=deletions, repo=repo, status=status))

            parts = line.split(' ')
            current_file = parts[-1].replace('b/', '')
            additions = 0
            deletions = 0
            status = "modified"

        elif line.startswith('new file mode'):
            status = "added"
        elif line.startswith('deleted file mode'):
            status = "deleted"
        elif line.startswith('rename to'):
            status = "renamed"
        
        elif line.startswith('+') and not line.startswith('+++'):
            additions += 1
        elif line.startswith('-') and not line.startswith('---'):
            deletions += 1

    if current_file is not None:
        diff_info_list.append(GitDiffInfo(path=current_file, additions=additions, deletions=deletions, repo=repo, status=status))

    return diff_info_list