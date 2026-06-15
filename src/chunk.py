"""Stage 2: Chunking.

Reads the cleaned docs in documents/clean/*.json and splits each into chunks
using the sentence-aware packer in textutils. Per planning.md:

    chunk size  = 250 tokens   (kept under all-MiniLM-L6-v2's 256-token ceiling)
    overlap     = 60 tokens    (~24%, enough to carry setup->punchline context)

Chunks never cross segment boundaries, so one chunk is always one person's
comment / one review / one section -- never two people's opinions merged.

Output: documents/chunks.jsonl  (one JSON object per line, with metadata)

Usage:
    python -m src.chunk                 # build chunks.jsonl + print stats
    python -m src.chunk --inspect       # also print 5 representative chunks
    python -m src.chunk --inspect 8     # print 8 chunks
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .textutils import chunk_segment, count_tokens

ROOT = Path(__file__).resolve().parent.parent
CLEAN_DIR = ROOT / "documents" / "clean"
CHUNKS_FILE = ROOT / "documents" / "chunks.jsonl"

MAX_TOKENS = 250
OVERLAP_TOKENS = 60
MIN_CHUNK_TOKENS = 15  # drop standalone fragments with no retrievable meaning


def build_chunks() -> list[dict]:
    chunks: list[dict] = []
    docs = sorted(CLEAN_DIR.glob("*.json"), key=lambda p: p.name)
    if not docs:
        print("No cleaned docs found. Run `python -m src.ingest` first.")
        return chunks

    seen_text: set[str] = set()  # drop exact-duplicate chunks (e.g. repeated UI widgets)
    for doc_path in docs:
        doc = json.loads(doc_path.read_text())
        local_idx = 0
        for seg_i, segment in enumerate(doc["segments"]):
            for piece in chunk_segment(segment, MAX_TOKENS, OVERLAP_TOKENS):
                n = count_tokens(piece)
                if n < MIN_CHUNK_TOKENS:
                    continue
                norm = " ".join(piece.split()).lower()
                if norm in seen_text:
                    continue
                seen_text.add(norm)
                chunks.append({
                    "chunk_id": f"{doc['id']}::{local_idx}",
                    "doc_id": doc["id"],
                    "num": doc["num"],
                    "source": doc["source"],
                    "description": doc["description"],
                    "url": doc["url"],
                    "segment_index": seg_i,
                    "n_tokens": n,
                    "text": piece,
                })
                local_idx += 1
    return chunks


def write_chunks(chunks: list[dict]) -> None:
    with CHUNKS_FILE.open("w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")


def print_stats(chunks: list[dict]) -> None:
    print("\n=== Chunk statistics ===")
    total = len(chunks)
    print(f"TOTAL CHUNKS: {total}")
    if not total:
        return
    toks = [c["n_tokens"] for c in chunks]
    print(f"tokens/chunk: min={min(toks)}  max={max(toks)}  avg={sum(toks)/total:.0f}")

    by_source: dict[str, int] = {}
    for c in chunks:
        key = f"#{c['num']:>2} {c['doc_id']}"
        by_source[key] = by_source.get(key, 0) + 1
    print("\nchunks per document:")
    for key in sorted(by_source):
        print(f"  {by_source[key]:>4}  {key}")

    # Sanity check against the assignment's 50–2000 guideline.
    if total < 50:
        print("\n!! Fewer than 50 chunks — chunks may be too large, or sources are missing.")
    elif total > 2000:
        print("\n!! More than 2000 chunks — chunks may be too small.")
    else:
        print("\nChunk count is within the 50–2000 healthy range.")


def inspect(chunks: list[dict], k: int = 5) -> None:
    """Print k representative chunks spread across the corpus for manual review."""
    if not chunks:
        return
    step = max(1, len(chunks) // k)
    picks = chunks[::step][:k]
    print(f"\n=== {len(picks)} representative chunks ===")
    for c in picks:
        print("\n" + "-" * 70)
        print(f"chunk_id : {c['chunk_id']}")
        print(f"source   : #{c['num']} {c['source']} — {c['description']}")
        print(f"tokens   : {c['n_tokens']}")
        print("text     :")
        print(c["text"])


def main(argv: list[str]) -> None:
    chunks = build_chunks()
    if not chunks:
        return
    write_chunks(chunks)
    print(f"Wrote {len(chunks)} chunks -> documents/chunks.jsonl")
    print_stats(chunks)
    if "--inspect" in argv:
        i = argv.index("--inspect")
        k = int(argv[i + 1]) if i + 1 < len(argv) and argv[i + 1].isdigit() else 5
        inspect(chunks, k)


if __name__ == "__main__":
    main(sys.argv[1:])
