"""Shared embedding + vector-store config for Milestone 4.

Both the index builder (src/embed.py) and the retriever (src/retrieve.py) go
through here so they always use the *same* embedding model and the *same*
ChromaDB collection. If the build and query sides used different models the
vectors would live in incompatible spaces and retrieval would be garbage.

Embedding model : all-MiniLM-L6-v2 (sentence-transformers) — local, no API key,
                  384-dim vectors, 256-token input ceiling (we capped chunks at
                  250 tokens in Milestone 3 precisely so nothing is truncated).
Vector store    : ChromaDB PersistentClient on disk at ./chroma_db (gitignored).
Distance        : cosine. We store L2-normalized embeddings and tell Chroma to
                  use the cosine space, so query distance is 1 - cosine_similarity.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHROMA_DIR = ROOT / "chroma_db"
CHUNKS_FILE = ROOT / "documents" / "chunks.jsonl"

MODEL_NAME = "all-MiniLM-L6-v2"
COLLECTION_NAME = "uh_housing"


@lru_cache(maxsize=1)
def get_model():
    """Load the SentenceTransformer once and reuse it (it is ~90MB on disk and
    a few hundred ms to load, so we never want to load it twice in a process)."""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(MODEL_NAME)


def embed(texts: list[str]):
    """Embed a list of texts into L2-normalized 384-dim vectors.

    normalize_embeddings=True makes every vector unit length, which is what lets
    cosine similarity behave well and keeps scores comparable across queries.
    Returns a plain list of lists (Chroma wants JSON-serializable embeddings).
    """
    model = get_model()
    vecs = model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=len(texts) > 64,
    )
    return vecs.tolist()


@lru_cache(maxsize=1)
def get_client():
    import chromadb

    # PersistentClient writes the collection to disk so we embed once and can
    # query across many runs without re-embedding.
    return chromadb.PersistentClient(path=str(CHROMA_DIR))


def get_collection(create: bool = False):
    """Return the Chroma collection.

    get_or_create_collection is idempotent: it creates the collection on first
    use and returns the existing one afterwards. The metadata dict configures
    the index — "hnsw:space": "cosine" tells Chroma's HNSW nearest-neighbor
    index to rank by cosine distance instead of the default squared-L2.
    """
    client = get_client()
    if create:
        return client.get_or_create_collection(
            name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
        )
    return client.get_collection(name=COLLECTION_NAME)
