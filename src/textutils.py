"""Shared text utilities: token counting and the sentence-aware chunker.

Token counts use the *actual* all-MiniLM-L6-v2 tokenizer (the model named in
planning.md). That matters: the model has a 256-token ceiling, so counting with
its own tokenizer is the only way to know a chunk will be embedded in full
rather than silently truncated. If the tokenizer can't be loaded offline we
fall back to a ~4-chars-per-token heuristic and warn.
"""

from __future__ import annotations

import re
import sys
from functools import lru_cache

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _tokenizer():
    try:
        from transformers import AutoTokenizer

        tok = AutoTokenizer.from_pretrained(MODEL_NAME)
        return tok
    except Exception as exc:  # offline / not downloaded yet
        print(
            f"[textutils] WARNING: could not load {MODEL_NAME} tokenizer "
            f"({exc}); falling back to ~4-chars/token estimate.",
            file=sys.stderr,
        )
        return None


def count_tokens(text: str) -> int:
    """Number of tokens the embedding model would see (excludes [CLS]/[SEP])."""
    tok = _tokenizer()
    if tok is None:
        return max(1, len(text) // 4)
    return len(tok.encode(text, add_special_tokens=False))


# ---------------------------------------------------------------------------
# Sentence splitting
# ---------------------------------------------------------------------------

# Split on sentence-ending punctuation followed by whitespace, while trying not
# to break on common abbreviations / decimals. Good enough for informal forum
# prose; we are not parsing legal text.
_SENT_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])")
_ABBREV = re.compile(r"\b(?:Mr|Mrs|Ms|Dr|Prof|St|Ave|Apt|vs|etc|Inc|Co|No)\.$")


def split_sentences(text: str) -> list[str]:
    """Split a paragraph of text into sentence-ish units."""
    text = text.strip()
    if not text:
        return []
    # First split on hard line breaks, then on sentence punctuation.
    units: list[str] = []
    for line in re.split(r"\n+", text):
        line = line.strip()
        if not line:
            continue
        parts = _SENT_END.split(line)
        # Re-merge fragments that ended on an abbreviation.
        merged: list[str] = []
        for p in parts:
            if merged and _ABBREV.search(merged[-1]):
                merged[-1] = merged[-1] + " " + p
            else:
                merged.append(p)
        units.extend(s.strip() for s in merged if s.strip())
    return units


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------


def _split_long_sentence(sentence: str, max_tokens: int) -> list[str]:
    """Hard-split a single sentence that exceeds max_tokens, on word boundaries."""
    words = sentence.split()
    pieces: list[str] = []
    cur: list[str] = []
    for w in words:
        cur.append(w)
        if count_tokens(" ".join(cur)) >= max_tokens:
            pieces.append(" ".join(cur))
            cur = []
    if cur:
        pieces.append(" ".join(cur))
    return pieces


def chunk_segment(
    text: str,
    max_tokens: int = 250,
    overlap_tokens: int = 60,
) -> list[str]:
    """Pack the sentences of one logical segment into chunks.

    A "segment" is one self-contained unit of meaning (a single Reddit comment,
    one Yelp review, or one section of an official page). We never merge across
    segments — that is what keeps two different people's opinions out of the
    same chunk. Within a segment we greedily pack whole sentences up to
    ``max_tokens`` and carry the trailing ~``overlap_tokens`` of sentences into
    the next chunk so a setup->punchline thought is not severed at a boundary.
    """
    sentences = split_sentences(text)
    if not sentences:
        return []

    # Expand any single sentence longer than the window into sub-pieces.
    expanded: list[str] = []
    for s in sentences:
        if count_tokens(s) > max_tokens:
            expanded.extend(_split_long_sentence(s, max_tokens))
        else:
            expanded.append(s)
    sentences = expanded

    chunks: list[str] = []
    cur: list[str] = []
    cur_tokens = 0

    def flush():
        nonlocal cur, cur_tokens
        if cur:
            chunks.append(" ".join(cur).strip())

    for sent in sentences:
        st = count_tokens(sent)
        if cur and cur_tokens + st > max_tokens:
            flush()
            # Build overlap: take trailing sentences up to overlap_tokens.
            keep: list[str] = []
            keep_tokens = 0
            for prev in reversed(cur):
                pt = count_tokens(prev)
                if keep_tokens + pt > overlap_tokens and keep:
                    break
                keep.insert(0, prev)
                keep_tokens += pt
            cur = keep
            cur_tokens = keep_tokens
        cur.append(sent)
        cur_tokens += st

    flush()
    return chunks
