"""Stretch feature: chunking-strategy comparison.

Re-chunks the same cleaned documents three different ways, embeds each set, and
runs the same query set against all three to see which chunking helps retrieval
most. Similarity is computed in-memory with numpy (no Chroma needed) so this is
a self-contained experiment that doesn't touch the live index.

Strategies:
  A: segment-aware 250 / 60  (my current strategy)
  B: segment-aware 120 / 30  (smaller chunks)
  C: naive fixed 500-word windows that IGNORE segment boundaries (merges
     different people's comments together — the thing my planning warned against)

Usage:
    python -m src.compare_chunking
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .textutils import chunk_segment, count_tokens
from .vectorstore import get_model

ROOT = Path(__file__).resolve().parent.parent
CLEAN_DIR = ROOT / "documents" / "clean"

QUERIES = [
    "Is the Medical Center safe to commute from without a car?",
    "What hidden fees should I expect at Cullen Oaks?",
    "Can I afford a 1-bed in Midtown or Montrose on a grad stipend?",
    "How do I get home safely after dark with no car?",
    "University Lofts vs splitting an off-campus apartment",
]


def _docs() -> list[dict]:
    return [json.loads(p.read_text()) for p in sorted(CLEAN_DIR.glob("*.json"))]


def build_segment_aware(max_tok: int, overlap: int) -> list[dict]:
    chunks = []
    for d in _docs():
        for seg in d["segments"]:
            for piece in chunk_segment(seg, max_tok, overlap):
                if count_tokens(piece) >= 15:
                    chunks.append({"text": piece, "doc_id": d["id"], "source": d["source"]})
    return chunks


def build_naive_fixed(window_words: int) -> list[dict]:
    """Ignore segment boundaries: glue a doc's segments together and cut fixed
    word windows. This merges different people's comments into one chunk."""
    chunks = []
    for d in _docs():
        words = " ".join(d["segments"]).split()
        for i in range(0, len(words), window_words):
            piece = " ".join(words[i:i + window_words])
            if len(piece.split()) >= 10:
                chunks.append({"text": piece, "doc_id": d["id"], "source": d["source"]})
    return chunks


def embed_matrix(texts: list[str]) -> np.ndarray:
    model = get_model()
    return np.asarray(model.encode(texts, normalize_embeddings=True))


def evaluate(name: str, chunks: list[dict], qmat: np.ndarray) -> None:
    mat = embed_matrix([c["text"] for c in chunks])
    print(f"\n### {name}  —  {len(chunks)} chunks")
    for qi, q in enumerate(QUERIES):
        sims = mat @ qmat[qi]               # cosine sim (vectors are normalized)
        top = np.argsort(-sims)[:3]
        best_dist = 1.0 - sims[top[0]]
        srcs = ", ".join(chunks[t]["doc_id"] for t in top)
        print(f"  Q: {q[:48]:48}  top1_dist={best_dist:.3f}  top3=[{srcs}]")


def main() -> None:
    model = get_model()
    qmat = np.asarray(model.encode(QUERIES, normalize_embeddings=True))
    strategies = {
        "A: segment-aware 250/60 (current)": build_segment_aware(250, 60),
        "B: segment-aware 120/30 (smaller)": build_segment_aware(120, 30),
        "C: naive fixed 500-word, merges segments": build_naive_fixed(500),
    }
    for name, chunks in strategies.items():
        evaluate(name, chunks, qmat)


if __name__ == "__main__":
    main()
