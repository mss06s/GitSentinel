
from gitsentinel.models import GitDiffInfo


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

    for line in raw_diff.splitlines():
        if line.startswith('diff --git'):
            if current_file is not None:
                diff_info_list.append(GitDiffInfo(path=current_file, additions=additions, deletions=deletions, repo=repo))
            parts = line.split(' ')
            current_file = parts[-1].replace('b/', '')
            additions = 0
            deletions = 0
        elif line.startswith('+') and not line.startswith('+++'):
            additions += 1
        elif line.startswith('-') and not line.startswith('---'):
            deletions += 1

    if current_file is not None:
        diff_info_list.append(GitDiffInfo(path=current_file, additions=additions, deletions=deletions, repo=repo))

    return diff_info_list