import os
import sqlite3

import numpy as np
import voyageai
from dotenv import load_dotenv

from gitsentinel.treesitter import extract_symbols

load_dotenv()

MODEL = "voyage-code-4"

IGNORED_DIRS = {".git", ".venv", "__pycache__", ".gitsentinel", ".pytest_cache"}


def embed_texts(texts: list[str], input_type: str) -> list[list[float]]:
    """
    Embeds a list of texts using Voyage AI's code embedding model.
    input_type is "document" for code being indexed, "query" for search text.
    """
    client = voyageai.Client()
    result = client.embed(texts=texts, model=MODEL, input_type=input_type)
    return result.embeddings


def get_db_path(repo_root: str) -> str:
    return os.path.join(repo_root, ".gitsentinel", "index.db")


def build_index(repo_root: str) -> int:
    """
    Walks every .py file in the repo, extracts function/class chunks via
    Tree-sitter, embeds them with Voyage, and stores them in a local SQLite
    database. Rebuilds the index from scratch each time.

    Returns the number of chunks indexed.
    """
    chunks = []
    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        for filename in files:
            if filename.endswith(".py"):
                full_path = os.path.join(root, filename)
                rel_path = os.path.relpath(full_path, repo_root)
                chunks.extend(extract_symbols(repo_root, rel_path))

    db_path = get_db_path(repo_root)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.execute("DROP TABLE IF EXISTS chunks")
    conn.execute("""
        CREATE TABLE chunks (
            id INTEGER PRIMARY KEY,
            file_path TEXT,
            name TEXT,
            kind TEXT,
            start_line INTEGER,
            end_line INTEGER,
            code TEXT,
            embedding BLOB
        )
    """)

    if chunks:
        embeddings = embed_texts([c["code"] for c in chunks], input_type="document")

        for chunk, embedding in zip(chunks, embeddings):
            vector = np.array(embedding, dtype=np.float32)
            conn.execute(
                "INSERT INTO chunks (file_path, name, kind, start_line, end_line, code, embedding) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    chunk["file_path"], chunk["name"], chunk["kind"],
                    chunk["start_line"], chunk["end_line"], chunk["code"],
                    vector.tobytes(),
                ),
            )

    conn.commit()
    conn.close()

    return len(chunks)


def search_index(repo_root: str, query_text: str, top_k: int = 3) -> list[dict]:
    """
    Embeds the query text and returns the top_k most similar code chunks
    from the index, ranked by cosine similarity.

    Returns an empty list if no index has been built yet.
    """
    db_path = get_db_path(repo_root)
    if not os.path.exists(db_path):
        return []

    query_vector = np.array(embed_texts([query_text], input_type="query")[0], dtype=np.float32)

    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT file_path, name, kind, start_line, end_line, code, embedding FROM chunks"
    ).fetchall()
    conn.close()

    scored = []
    for file_path, name, kind, start_line, end_line, code, embedding_blob in rows:
        vector = np.frombuffer(embedding_blob, dtype=np.float32)
        similarity = np.dot(query_vector, vector) / (np.linalg.norm(query_vector) * np.linalg.norm(vector))
        scored.append((similarity, {
            "file_path": file_path,
            "name": name,
            "kind": kind,
            "start_line": start_line,
            "end_line": end_line,
            "code": code,
        }))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [chunk for _, chunk in scored[:top_k]]
