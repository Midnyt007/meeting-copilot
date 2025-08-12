from __future__ import annotations
from pathlib import Path
from typing import List, Tuple
import numpy as np
import faiss
from .store import engine

INDEX_DIR = Path(".faiss")
INDEX_DIR.mkdir(exist_ok=True)
INDEX_FILE = INDEX_DIR / "meetings.index"


def _embed(text: str) -> np.ndarray:
    # Simple deterministic bag-of-words hashing for demo (no external calls).
    # Replace with real embeddings in production.
    vec = np.zeros(512, dtype="float32")
    for tok in text.lower().split():
        vec[hash(tok) % 512] += 1.0
    norm = np.linalg.norm(vec) or 1.0
    return vec / norm


def rebuild_index():
    import sqlite3
    con = sqlite3.connect(str(engine.url.database))
    cur = con.cursor()
    rows = cur.execute("SELECT id, notes FROM meetings").fetchall()
    con.close()
    ids = np.array([r[0] for r in rows], dtype="int64")
    vecs = np.vstack([_embed(r[1]) for r in rows]) if rows else np.zeros((0, 512), dtype="float32")
    index = faiss.IndexFlatIP(512)
    if len(vecs):
        index.add(vecs)
    faiss.write_index(index, str(INDEX_FILE))
    (INDEX_DIR / "ids.npy").write_bytes(ids.tobytes())


def search_similar(query: str, k: int = 5) -> List[Tuple[int, float]]:
    if not INDEX_FILE.exists():
        rebuild_index()
    index = faiss.read_index(str(INDEX_FILE))
    ids = np.frombuffer((INDEX_DIR / "ids.npy").read_bytes(), dtype="int64")
    q = _embed(query).reshape(1, -1)
    D, I = index.search(q, k)
    res: List[Tuple[int, float]] = []
    for rank in range(I.shape[1]):
        idx = I[0, rank]
        if idx < 0 or idx >= len(ids):
            continue
        res.append((int(ids[idx]), float(D[0, rank])))
    return res
