"""Stage 5: Grounded generation.

Ties retrieval to an LLM (Groq llama-3.3-70b-versatile) with two hard grounding
guarantees, not soft suggestions:

1. The model is given ONLY the retrieved chunks as context and is instructed to
   answer solely from them, returning a fixed refusal string when the context is
   insufficient. Temperature is low to minimize improvisation.
2. Source attribution is appended **programmatically** from the retrieved chunks'
   metadata after generation — it does not depend on the model choosing to cite.
   (We also ask the model to cite inline [n], but the authoritative Sources block
   is built in code, so attribution is guaranteed even if the model omits it.)

Usage:
    python -m src.generate "is the Med Center safe without a car?"
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from .retrieve import retrieve, DEFAULT_K
from .hybrid import hybrid_retrieve

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

MODEL = "llama-3.3-70b-versatile"
REFUSAL = "I don't have enough information on that."

SYSTEM_PROMPT = (
    "You are The Unofficial Guide, a factual assistant answering questions about "
    "off-campus housing, safety, transit, and cost for University of Houston students.\n"
    "Follow these rules strictly:\n"
    "1. Answer ONLY using the information in the numbered context documents provided "
    "in the user message. Do not use any outside knowledge or assumptions.\n"
    f"2. If the context does not contain enough information to answer, reply with "
    f"exactly: \"{REFUSAL}\" and nothing else.\n"
    "3. Cite the documents you used inline with their bracket numbers, e.g. [1], [3].\n"
    "4. These are individual student opinions and reviews, not official fact — when "
    "sources disagree, say so rather than inventing a consensus.\n"
    "5. Be concise and practical."
)


def _label(h: dict) -> str:
    """Concise source label for display: drop the long planning-doc parentheticals."""
    desc = h["description"].split(" (")[0].strip()
    return f"{h['source']} — {desc}"


def build_context(hits: list[dict]) -> str:
    """Render retrieved chunks as a numbered, labeled context block."""
    blocks = []
    for i, h in enumerate(hits, 1):
        blocks.append(f"[{i}] (source: {_label(h)})\n{h['text']}")
    return "\n\n".join(blocks)


def build_user_prompt(query: str, context: str) -> str:
    return (
        f"Context documents:\n\n{context}\n\n"
        f"---\nQuestion: {query}\n\n"
        "Answer using only the context above, citing sources inline as [n]."
    )


def format_sources(hits: list[dict]) -> str:
    """Build the authoritative Sources block from metadata (code, not the LLM).

    Groups by source document so each underlying source appears once, tagged with
    the context numbers [n] that came from it."""
    by_doc: dict[str, dict] = {}
    for i, h in enumerate(hits, 1):
        d = by_doc.setdefault(h["doc_id"], {"nums": [], "label": _label(h), "url": h["url"]})
        d["nums"].append(i)
    lines = []
    for d in by_doc.values():
        tags = ",".join(f"[{n}]" for n in d["nums"])
        lines.append(f"{tags} {d['label']}\n     {d['url']}")
    return "Sources:\n" + "\n".join(lines)


def _client():
    from groq import Groq

    key = os.environ.get("GROQ_API_KEY", "")
    if not key or key == "your_key_here":
        raise SystemExit("GROQ_API_KEY missing — copy .env.example to .env and add your key.")
    return Groq(api_key=key)


def _retriever(mode: str):
    """Pick the retrieval function. 'hybrid' = BM25 + vector (RRF); else vector."""
    return hybrid_retrieve if mode == "hybrid" else retrieve


def _generate(messages: list[dict]) -> str:
    client = _client()
    resp = client.chat.completions.create(
        model=MODEL, messages=messages, temperature=0.2, max_tokens=600,
    )
    return resp.choices[0].message.content.strip()


def answer(query: str, k: int = DEFAULT_K, mode: str = "vector",
           source: str | None = None) -> dict:
    """Retrieve, generate a grounded answer, and attach guaranteed attribution.

    mode: "vector" (default) or "hybrid" (BM25 + vector). source: optional
    metadata filter, e.g. "Reddit" / "Official UH" / "ApartmentRatings".
    """
    hits = _retriever(mode)(query, k, source=source)
    if not hits:
        return {"answer": REFUSAL, "sources": "", "hits": []}

    context = build_context(hits)
    text = _generate([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_prompt(query, context)},
    ])
    # Programmatic attribution: only append sources when the model actually
    # answered (not on the refusal), so a refusal isn't given false citations.
    sources = "" if text.strip() == REFUSAL else format_sources(hits)
    return {"answer": text, "sources": sources, "hits": hits}


def answer_chat(history: list[dict], query: str, k: int = DEFAULT_K,
                mode: str = "vector", source: str | None = None) -> dict:
    """Conversational version: uses prior turns so a follow-up like "what about
    Montrose?" is understood in the context of the earlier question.

    `history` is a list of {"role": "user"|"assistant", "content": str} from
    earlier turns. We do two things with it: (1) build the retrieval query from
    the previous user turn + the current one, so retrieval pulls context for the
    thing the follow-up is actually about; (2) pass the recent turns to the model
    so its wording resolves references like "there" or "that one".
    """
    prev_user = next((m["content"] for m in reversed(history) if m["role"] == "user"), "")
    search_query = f"{prev_user} {query}".strip() if prev_user else query
    hits = _retriever(mode)(search_query, k, source=source)
    if not hits:
        return {"answer": REFUSAL, "sources": "", "hits": []}

    context = build_context(hits)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += history[-4:]  # keep the last couple of turns for context
    messages.append({"role": "user", "content": build_user_prompt(query, context)})
    text = _generate(messages)

    sources = "" if text.strip() == REFUSAL else format_sources(hits)
    return {"answer": text, "sources": sources, "hits": hits}


def main(argv: list[str]) -> None:
    if not argv:
        print('Usage: python -m src.generate "your question" [k]')
        return
    k = DEFAULT_K
    if len(argv) > 1 and argv[-1].isdigit():
        k = int(argv[-1])
        argv = argv[:-1]
    query = " ".join(argv)
    out = answer(query, k)
    print(f"\nQ: {query}\n")
    print(out["answer"])
    if out["sources"]:
        print("\n" + out["sources"])


if __name__ == "__main__":
    main(sys.argv[1:])
