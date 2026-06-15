"""Stretch feature: hybrid retrieval (BM25 keyword + vector) via RRF.

The plain vector search misses things when the query wording doesn't match the
source wording (my documented Q4 failure: "get home after dark" vs the official
"security escort"). BM25 is a classic keyword/lexical ranker that nails exact
terms like "escort" but is blind to paraphrase. Hybrid runs both and fuses them
with Reciprocal Rank Fusion (RRF), so we get the best of both.

RRF is rank-based, not score-based: each result gets sum over methods of
1/(C + rank_in_that_method), with C=60 (the standard constant). Using ranks
sidesteps the problem that cosine distance and BM25 scores are on totally
different scales and can't be added directly.

Usage:
    python -m src.hybrid "how do I get home safely after dark?"
    python -m src.hybrid "Cullen Oaks fees" 5
"""

from __future__ import annotations

import json
import re
import sys
import textwrap
from functools import lru_cache

from .vectorstore import CHUNKS_FILE, embed, get_collection

DEFAULT_K = 5
RRF_C = 60          # standard RRF dampening constant
CANDIDATES = 25     # how many to pull from each method before fusing

_TOKEN = re.compile(r"[a-z0-9]+")


def _tok(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


@lru_cache(maxsize=1)
def _chunks() -> list[dict]:
    return [json.loads(line) for line in CHUNKS_FILE.open(encoding="utf-8")]


@lru_cache(maxsize=1)
def _by_id() -> dict:
    return {c["chunk_id"]: c for c in _chunks()}


@lru_cache(maxsize=1)
def _bm25():
    from rank_bm25 import BM25Okapi

    chunks = _chunks()
    corpus = [_tok(c["text"]) for c in chunks]
    ids = [c["chunk_id"] for c in chunks]
    return BM25Okapi(corpus), ids


def vector_rank(query: str, n: int, source: str | None) -> list[str]:
    """Chunk ids from the vector store, best first."""
    where = {"source": source} if source else None
    res = get_collection().query(
        query_embeddings=embed([query]),
        n_results=n,
        where=where,
        include=["distances"],  # ids come back by default
    )
    return res["ids"][0]


def bm25_rank(query: str, n: int, source: str | None) -> list[str]:
    """Chunk ids from BM25 keyword scoring, best first."""
    bm25, ids = _bm25()
    scores = bm25.get_scores(_tok(query))
    order = sorted(range(len(ids)), key=lambda i: scores[i], reverse=True)
    by_id = _by_id()
    out = []
    for i in order:
        if scores[i] <= 0:
            break
        cid = ids[i]
        if source and by_id[cid]["source"] != source:
            continue
        out.append(cid)
        if len(out) >= n:
            break
    return out


def _rrf(*ranked_lists: list[str]) -> dict:
    fused: dict[str, float] = {}
    for ranked in ranked_lists:
        for rank, cid in enumerate(ranked, 1):
            fused[cid] = fused.get(cid, 0.0) + 1.0 / (RRF_C + rank)
    return fused


def hybrid_retrieve(query: str, k: int = DEFAULT_K, source: str | None = None) -> list[dict]:
    """Fuse BM25 + vector rankings and return the top-k chunks, best first."""
    vec = vector_rank(query, CANDIDATES, source)
    bm = bm25_rank(query, CANDIDATES, source)
    fused = _rrf(vec, bm)

    vec_set, bm_set = set(vec), set(bm)
    by_id = _by_id()
    ranked = sorted(fused.items(), key=lambda kv: kv[1], reverse=True)[:k]

    hits = []
    for cid, score in ranked:
        c = by_id[cid]
        found = ("vector+bm25" if cid in vec_set and cid in bm_set
                 else "vector" if cid in vec_set else "bm25")
        hits.append({
            "text": c["text"], "doc_id": c["doc_id"], "source": c["source"],
            "description": c["description"], "num": c["num"],
            "segment_index": c["segment_index"], "url": c["url"],
            "rrf_score": round(score, 5), "found_by": found,
            # generate.py expects these keys; hybrid has no single distance.
            "distance": None, "score": round(score, 5),
        })
    return hits


def main(argv: list[str]) -> None:
    if not argv:
        print('Usage: python -m src.hybrid "your question" [k]')
        return
    k = DEFAULT_K
    if len(argv) > 1 and argv[-1].isdigit():
        k = int(argv[-1]); argv = argv[:-1]
    query = " ".join(argv)
    print(f"\nHybrid query: {query!r}")
    for rank, h in enumerate(hybrid_retrieve(query, k), 1):
        print(f"\n#{rank} rrf={h['rrf_score']} found_by={h['found_by']} "
              f"| {h['doc_id']} (#{h['num']} {h['source']})")
        print(textwrap.fill(h["text"], 92, initial_indent="   ", subsequent_indent="   ")[:400])


if __name__ == "__main__":
    main(sys.argv[1:])
