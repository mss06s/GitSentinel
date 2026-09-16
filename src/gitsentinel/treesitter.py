import os

import tree_sitter_python as tspython
from tree_sitter import Language, Parser, Query, QueryCursor

from gitsentinel.models import Hunk

PY_LANGUAGE = Language(tspython.language())

ENCLOSING_QUERY = Query(PY_LANGUAGE, """
(function_definition) @function
(class_definition) @class
""")


def get_enclosing_function(repo_root: str, file_path: str, hunk: Hunk) -> str | None:
    """
    Uses Tree-sitter to find the smallest function or class definition that
    contains the hunk's first changed line, and returns its source text.

    Returns None if the file isn't Python, can't be read, or the hunk isn't
    inside any function/class (e.g. a change at the top level of the module).
    """
    if not file_path.endswith(".py"):
        return None

    full_path = os.path.join(repo_root, file_path)

    try:
        with open(full_path, "rb") as f:
            source = f.read()
    except FileNotFoundError:
        return None

    parser = Parser(PY_LANGUAGE)
    tree = parser.parse(source)

    cursor = QueryCursor(ENCLOSING_QUERY)
    captures = cursor.captures(tree.root_node)

    target_line = hunk.new_start - 1  # tree-sitter rows are 0-indexed

    candidates = []
    for nodes in captures.values():
        for node in nodes:
            if node.start_point[0] <= target_line <= node.end_point[0]:
                candidates.append(node)

    if not candidates:
        return None

    smallest = min(candidates, key=lambda n: n.end_point[0] - n.start_point[0])

    try:
        return source[smallest.start_byte:smallest.end_byte].decode("utf-8")
    except UnicodeDecodeError:
        return None


def extract_symbols(repo_root: str, file_path: str) -> list[dict]:
    """
    Uses Tree-sitter to find every function and class definition in a Python
    file, for indexing. Returns a list of dicts with name, kind, code, and
    line range for each one.

    Returns an empty list if the file isn't Python or can't be read.
    """
    if not file_path.endswith(".py"):
        return []

    full_path = os.path.join(repo_root, file_path)

    try:
        with open(full_path, "rb") as f:
            source = f.read()
    except FileNotFoundError:
        return []

    parser = Parser(PY_LANGUAGE)
    tree = parser.parse(source)

    cursor = QueryCursor(ENCLOSING_QUERY)
    captures = cursor.captures(tree.root_node)

    symbols = []
    for kind, nodes in captures.items():
        for node in nodes:
            name_node = node.child_by_field_name("name")
            name = name_node.text.decode("utf-8") if name_node else "<anonymous>"

            try:
                code = source[node.start_byte:node.end_byte].decode("utf-8")
            except UnicodeDecodeError:
                continue

            symbols.append({
                "name": name,
                "kind": kind,
                "code": code,
                "file_path": file_path,
                "start_line": node.start_point[0] + 1,
                "end_line": node.end_point[0] + 1,
            })

    return symbols
