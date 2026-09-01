from gitsentinel.diff import parse_diff
from gitsentinel.models import GitDiffInfo


def test_parse_diff_single_file():
    raw_diff = """diff --git a/foo.py b/foo.py
index abc123..def456 100644
--- a/foo.py
+++ b/foo.py
@@ -1,2 +1,2 @@
-old line
+new line
+another new line
"""

    result = parse_diff(raw_diff, repo="myrepo")

    assert result == [
        GitDiffInfo(path="foo.py", additions=2, deletions=1, repo="myrepo")
    ]


def test_parse_diff_multiple_files():
    raw_diff = """diff --git a/foo.py b/foo.py
index abc123..def456 100644
--- a/foo.py
+++ b/foo.py
@@ -1,1 +1,1 @@
-old foo
+new foo
diff --git a/bar.py b/bar.py
index 111111..222222 100644
--- a/bar.py
+++ b/bar.py
@@ -1,1 +1,2 @@
+new bar line
+another bar line
"""

    result = parse_diff(raw_diff, repo="myrepo")

    assert result == [
        GitDiffInfo(path="foo.py", additions=1, deletions=1, repo="myrepo"),
        GitDiffInfo(path="bar.py", additions=2, deletions=0, repo="myrepo"),
    ]


def test_parse_diff_empty_string():
    result = parse_diff("", repo="myrepo")

    assert result == []


def test_parse_diff_excludes_file_header_lines():
    raw_diff = """diff --git a/foo.py b/foo.py
index abc123..def456 100644
--- a/foo.py
+++ b/foo.py
@@ -1,1 +1,1 @@
-old line
+new line
"""

    result = parse_diff(raw_diff, repo="myrepo")

    assert result == [
        GitDiffInfo(path="foo.py", additions=1, deletions=1, repo="myrepo")
    ]
