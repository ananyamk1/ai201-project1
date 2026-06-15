"""Stage 3: Embedding + vector store.

Loads the chunks produced by the Milestone-3 pipeline (documents/chunks.jsonl),
embeds each chunk's text with all-MiniLM-L6-v2, and stores the vectors in a
local ChromaDB collection together with source metadata (document name, chunk
position, source type, url) needed for attribution at generation time.

Usage:
    python -m src.embed            # build / refresh the index
"""

from __future__ import annotations

import json

from .vectorstore import CHUNKS_FILE, COLLECTION_NAME, MODEL_NAME, embed, get_client, get_collection


def load_chunks() -> list[dict]:
    if not CHUNKS_FILE.exists():
        raise SystemExit("documents/chunks.jsonl not found — run the Milestone-3 pipeline first.")
    return [json.loads(line) for line in CHUNKS_FILE.open(encoding="utf-8")]


def build_index() -> None:
    chunks = load_chunks()
    print(f"Loaded {len(chunks)} chunks from {CHUNKS_FILE.name}")

    # Rebuild from scratch so re-running never leaves stale vectors behind.
    client = get_client()
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = get_collection(create=True)

    ids = [c["chunk_id"] for c in chunks]
    documents = [c["text"] for c in chunks]
    # Chroma metadata values must be str/int/float/bool — no None, no lists.
    metadatas = [
        {
            "doc_id": c["doc_id"],            # source document name (for attribution)
            "source": c["source"],            # source type (Reddit / Official UH / ...)
            "description": c["description"],  # human-readable source label
            "num": c["num"],                  # source number 1..10
            "segment_index": c["segment_index"],  # chunk's position within the document
            "url": c["url"],                  # link back to the original
            "n_tokens": c["n_tokens"],
        }
        for c in chunks
    ]

    print(f"Embedding with {MODEL_NAME} ...")
    embeddings = embed(documents)

    # Add in batches (Chroma is happy with a few thousand at once, but batching
    # keeps memory flat and is the standard pattern for larger corpora).
    BATCH = 256
    for i in range(0, len(ids), BATCH):
        sl = slice(i, i + BATCH)
        collection.add(
            ids=ids[sl],
            embeddings=embeddings[sl],
            documents=documents[sl],
            metadatas=metadatas[sl],
        )

    count = collection.count()
    dim = len(embeddings[0]) if embeddings else 0
    print(f"\nIndex built: {count} vectors ({dim}-dim) in collection '{COLLECTION_NAME}'")
    by_source: dict[str, int] = {}
    for m in metadatas:
        by_source[m["source"]] = by_source.get(m["source"], 0) + 1
    for s in sorted(by_source):
        print(f"  {by_source[s]:>4}  {s}")


if __name__ == "__main__":
    build_index()
