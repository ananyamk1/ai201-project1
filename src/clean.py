"""HTML cleaning: turn a raw page into a list of clean text *segments*.

A segment is one self-contained unit of meaning: a single Reddit comment, one
Yelp review, or one paragraph/section of an official page. Returning segments
(rather than one big blob) lets the chunker respect human boundaries and never
merge two different people's opinions into a single chunk.

Cleaning removes everything that is not substantive content: scripts, styles,
nav menus, cookie banners, footers, share/vote widgets, "load more" links, and
boilerplate. HTML entities are decoded by BeautifulSoup automatically.
"""

from __future__ import annotations

import re
from bs4 import BeautifulSoup, Comment

# Tags that never contain substantive content.
# NB: <form> is intentionally NOT here — old.reddit wraps every comment/post
# body in <form class="usertext">, so dropping forms would delete the content.
# We strip the actual form *controls* (input/select/textarea/button) instead.
_DROP_TAGS = [
    "script", "style", "noscript", "svg", "button", "iframe",
    "nav", "header", "footer", "aside", "input", "select", "textarea",
]

# Chrome/boilerplate markers, matched against *individual* class/id tokens and
# anchored at the start of the token (optionally followed by - or _). Anchoring
# matters: a bare substring like "vote" would otherwise match old.reddit's
# "unvoted"/"voted" comment classes and delete every comment.
_DROP_TOKEN = re.compile(
    r"^(nav|navbar|menu|sidebar|breadcrumb|cookie|consent|banner|footer|header|"
    r"masthead|share|sharebar|social|advert|ad|ads|promo|newsletter|subscribe|"
    r"signup|login|modal|popup|toolbar|skip|pagination|related|recommend|"
    r"comment-count|midcol|votelinks|votelink|arrow|score|award|awards)"
    r"([-_].*)?$",
    re.I,
)


def _has_drop_token(value) -> bool:
    """True if any class token (or the id) is a chrome/boilerplate marker."""
    if value is None:
        return False
    tokens = value if isinstance(value, list) else str(value).split()
    return any(_DROP_TOKEN.match(tok) for tok in tokens)

# Lines that are pure UI noise even after structural cleaning.
_NOISE_LINE = re.compile(
    r"^(reply|share|report|save|hide|give award|edit|delete|permalink|"
    r"continue this thread|load more comments?|view all \d+ comments?|"
    r"\d+ more repl(y|ies)|read more|see more|show more|upvote|downvote|"
    r"sort by|best|top|new|controversial|q&a|level \d+|·|•)$",
    re.I,
)

# Widget / UI text that leaks out of JS single-page apps (notably the METRO
# rail SPA). Matched at the *start* of a line, so a line that begins with one
# of these is dropped as non-substantive chrome.
_NOISE_PHRASE = re.compile(
    r"^(click or tap on any station|additional services near the station|"
    r"estimated wait times are also posted|scroll down for schedules|"
    r"see where all .{0,20} lines intersect|view (the )?(traditional )?metrorail map|"
    r"\*?\s*for most operating hours|(mon-?fri|sat-?sun):?\s*runs every \d+\s*min)",
    re.I,
)

_WS = re.compile(r"[ \t ]+")


def _normalize(text: str) -> str:
    text = text.replace(" ", " ")
    text = _WS.sub(" ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def _is_noise(line: str) -> bool:
    line = line.strip()
    if not line:
        return True
    if _NOISE_LINE.match(line) or _NOISE_PHRASE.match(line):
        return True
    # Bare vote counts / timestamps like "12 points" or "3 yr. ago".
    if re.fullmatch(r"[\d.,kKmM]+\s*(points?|comments?|upvotes?)", line, re.I):
        return True
    if re.fullmatch(r"\d+\s*(yr|mo|wk|day|hr|min|sec)s?\.?\s*ago", line, re.I):
        return True
    return False


def _soup(html: str) -> BeautifulSoup:
    soup = BeautifulSoup(html, "lxml")
    for c in soup.find_all(string=lambda s: isinstance(s, Comment)):
        c.extract()
    for tag in soup.find_all(_DROP_TAGS):
        tag.decompose()
    for tag in soup.find_all(True):
        if tag.decomposed:  # parent already removed this node
            continue
        if _has_drop_token(tag.get("class")) or _has_drop_token(tag.get("id")):
            tag.decompose()
    return soup


def _clean_segment_text(raw: str) -> str:
    """Drop noise lines inside one block and normalize whitespace."""
    kept = [ln.strip() for ln in raw.splitlines() if not _is_noise(ln)]
    return _normalize("\n".join(kept))


# ---------------------------------------------------------------------------
# Generic pages (UH official, METRO)
# ---------------------------------------------------------------------------

def clean_generic(html: str) -> list[str]:
    soup = _soup(html)
    root = soup.find("main") or soup.find("article") or soup.body or soup

    segments: list[str] = []
    # Group consecutive content blocks under their nearest heading as segments.
    blocks = root.find_all(["h1", "h2", "h3", "p", "li", "td", "blockquote", "dd"])
    for b in blocks:
        txt = _clean_segment_text(b.get_text("\n", strip=True))
        if len(txt.split()) >= 4:  # skip stub fragments / lone labels
            segments.append(txt)
    return _merge_short(segments)


# ---------------------------------------------------------------------------
# Reddit (handles both old.reddit.com and new shreddit markup)
# ---------------------------------------------------------------------------

_DELETED = {"[deleted]", "[removed]", "[deleted by user]", "[removed by reddit]"}


def clean_reddit(html: str) -> list[str]:
    soup = _soup(html)
    segments: list[str] = []

    # --- Post title + selftext (lives in #siteTable, separate from comments) ---
    # Query in priority order: a bare combined select_one would return the first
    # match in *document order*, which is the subreddit banner <h1>, not the post.
    title = ""
    for sel in ("#siteTable a.title", "a.title", "p.title a", "h1[slot='title']"):
        el = soup.select_one(sel)
        if el and el.get_text(strip=True):
            title = el.get_text(" ", strip=True)
            break

    selftext_el = soup.select_one(
        "#siteTable .usertext-body .md, .link .usertext-body .md, div[slot='text-body']"
    )
    selftext = _clean_segment_text(selftext_el.get_text("\n", strip=True)) if selftext_el else ""

    # Prefix the thread title so the opening post (and any short body) carries
    # the topic as standalone context.
    post = " ".join(p for p in [f"[Thread] {title}" if title else "", selftext] if p).strip()
    if post and len(post.split()) >= 3:
        segments.append(post)

    # --- Comments: each .md is one comment's own body (replies are separate) ---
    comment_nodes = soup.select(".commentarea .usertext-body .md")
    if not comment_nodes:  # new-reddit fallback
        comment_nodes = soup.select(
            "shreddit-comment div[slot='comment'], div[id$='-comment-rtjson-content']"
        )

    seen = set()
    for node in comment_nodes:
        txt = _clean_segment_text(node.get_text("\n", strip=True))
        if not txt or txt.lower() in _DELETED:
            continue
        key = txt[:80]
        if len(txt.split()) >= 4 and key not in seen:
            seen.add(key)
            segments.append(txt)

    if not segments:  # markup we didn't recognize — fall back to generic
        return clean_generic(html)
    return segments


# ---------------------------------------------------------------------------
# Yelp reviews
# ---------------------------------------------------------------------------

def clean_yelp(html: str) -> list[str]:
    soup = _soup(html)
    segments: list[str] = []

    review_nodes = soup.select(
        "p[class*='comment'], span[class*='raw__'], "
        "div[class*='review'] p, li[class*='review'] p"
    )
    seen = set()
    for node in review_nodes:
        txt = _clean_segment_text(node.get_text(" ", strip=True))
        key = txt[:80]
        if txt and len(txt.split()) >= 8 and key not in seen:  # reviews are sentences, not labels
            seen.add(key)
            segments.append(txt)

    if not segments:
        return clean_generic(html)
    return segments


# ---------------------------------------------------------------------------

def clean_apartmentratings(html: str) -> list[str]:
    """ApartmentRatings.com — each resident review is one styled-component block
    (class prefix 'Styles__StyledReview'). We keep the leading rating/tenure
    context and the review body, and strip the trailing 'Helpful / Report' UI."""
    soup = _soup(html)
    segments: list[str] = []
    seen = set()
    for node in soup.select("[class*=StyledReview]"):
        txt = node.get_text(" ", strip=True)
        txt = re.sub(r"\s*(Helpful\s*)?Report\s*$", "", txt, flags=re.I)
        # strip the trailing "…See More >" JS-expansion link artifact
        txt = re.sub(r"\s*(\.{2,}|…)?\s*See More\s*>?\s*$", "", txt, flags=re.I)
        txt = _clean_segment_text(txt)
        key = txt[:80]
        if len(txt.split()) >= 8 and key not in seen:
            seen.add(key)
            segments.append(txt)
    if not segments:
        return clean_generic(html)
    return segments


def _merge_short(segments: list[str], min_words: int = 12) -> list[str]:
    """Fold tiny consecutive blocks (e.g. a heading + its first sentence)
    together so generic pages don't explode into one-line fragments."""
    out: list[str] = []
    for seg in segments:
        if out and len(out[-1].split()) < min_words:
            out[-1] = (out[-1] + " " + seg).strip()
        else:
            out.append(seg)
    return out


CLEANERS = {
    "generic": clean_generic,
    "reddit": clean_reddit,
    "yelp": clean_yelp,
    "apartmentratings": clean_apartmentratings,
}


def clean_html(html: str, cleaner: str = "generic") -> list[str]:
    return CLEANERS.get(cleaner, clean_generic)(html)
