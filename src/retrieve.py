"""Stage 4: Retrieval.

retrieve(query, k) embeds the query with the same model used at index time and
asks ChromaDB for the k nearest chunks by cosine distance, returning each
chunk's text plus its source metadata (for attribution in Milestone 5).

Default k=5 per planning.md. Too few and the relevant chunk may not be in the
set at all; too many and loosely-related chunks dilute the context.

Usage:
    python -m src.retrieve "is the Medical Center safe without a car?"
    python -m src.retrieve "Cullen Oaks hidden fees" 3
"""

from __future__ import annotations

import sys
import textwrap

from .vectorstore import embed, get_collection

DEFAULT_K = 5


def retrieve(query: str, k: int = DEFAULT_K) -> list[dict]:
    """Return the top-k chunks most relevant to `query`, best first."""
    collection = get_collection()
    query_vec = embed([query])  # same model + normalization as the index

    res = collection.query(
        query_embeddings=query_vec,
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    # Chroma returns parallel lists nested one level per query; we sent one query.
    docs = res["documents"][0]
    metas = res["metadatas"][0]
    dists = res["distances"][0]

    hits = []
    for doc, meta, dist in zip(docs, metas, dists):
        hits.append({
            "text": doc,
            "doc_id": meta["doc_id"],
            "source": meta["source"],
            "description": meta["description"],
            "num": meta["num"],
            "segment_index": meta["segment_index"],
            "url": meta["url"],
            "distance": dist,
            # cosine distance -> similarity in [0, 1]; higher is more relevant.
            "score": round(1.0 - dist, 3),
        })
    return hits


def _print(query: str, hits: list[dict]) -> None:
    print(f"\nQuery: {query!r}  (top {len(hits)})")
    for rank, h in enumerate(hits, 1):
        print("\n" + "-" * 70)
        print(f"#{rank}  distance={h['distance']:.3f}  (cosine sim={h['score']})  "
              f"source: #{h['num']} {h['source']} ({h['doc_id']} seg {h['segment_index']})")
        print(textwrap.fill(h["text"], width=88))


def main(argv: list[str]) -> None:
    if not argv:
        print('Usage: python -m src.retrieve "your question" [k]')
        return
    k = DEFAULT_K
    if len(argv) > 1 and argv[-1].isdigit():
        k = int(argv[-1])
        argv = argv[:-1]
    query = " ".join(argv)
    _print(query, retrieve(query, k))


if __name__ == "__main__":
    main(sys.argv[1:])
