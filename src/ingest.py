"""Stage 1: Document ingestion.

For each source in sources.json:
  * mode == "url"        -> live-fetch the page(s) with requests (uh.edu pages)
  * mode == "local_html" -> read a page saved from the browser into documents/raw/
                            (Reddit, Yelp, METRO — these hard-block scripts)

Each raw page is cleaned into a list of segments and written to
documents/clean/<id>.json. Live-fetched HTML is also cached under documents/raw/
so the run is repeatable without re-hitting the network.

Usage:
    python -m src.ingest            # ingest every source
    python -m src.ingest reddit_01_grad_housing_bleak   # one source by id
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import requests

from .clean import clean_html

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "documents" / "raw"
CLEAN_DIR = ROOT / "documents" / "clean"
SOURCES_FILE = ROOT / "sources.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def load_sources() -> list[dict]:
    data = json.loads(SOURCES_FILE.read_text())
    return data["sources"]


def fetch_url(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.text


def raw_pages_for(src: dict) -> tuple[list[str], list[str]]:
    """Return (list_of_raw_html_pages, notes).

    Each page is cleaned *separately* and the segments concatenated. A url-mode
    source may list several pages that together form one logical document; they
    must NOT be merged into one HTML blob, because BeautifulSoup's find("main")
    would then only see the first page's content.
    """
    notes: list[str] = []
    if src["mode"] == "url":
        pages: list[str] = []
        for i, url in enumerate(src["urls"]):
            try:
                html = fetch_url(url)
                # cache for repeatability — stable name (index), so re-runs
                # overwrite rather than accumulate duplicate copies
                fn = RAW_DIR / f"{src['id']}__{i}.html"
                fn.write_text(html, encoding="utf-8")
                pages.append(html)
                notes.append(f"fetched {url} ({len(html)} bytes)")
                time.sleep(1)  # be polite to uh.edu
            except Exception as exc:
                notes.append(f"FAILED {url}: {exc}")
        return pages, notes

    # local_html
    path = RAW_DIR / src["local_file"]
    if not path.exists():
        notes.append(f"MISSING local file: documents/raw/{src['local_file']}")
        return [], notes
    notes.append(f"loaded documents/raw/{src['local_file']} ({path.stat().st_size} bytes)")
    return [path.read_text(encoding="utf-8", errors="ignore")], notes


def ingest_source(src: dict) -> dict:
    pages, notes = raw_pages_for(src)
    cleaner = src.get("cleaner", "generic")
    segments: list[str] = []
    for html in pages:
        segments.extend(clean_html(html, cleaner))

    doc = {
        "id": src["id"],
        "num": src["num"],
        "source": src["source"],
        "description": src["description"],
        "url": src.get("url", (src.get("urls") or [""])[0]),
        "segments": segments,
    }
    out = CLEAN_DIR / f"{src['id']}.json"
    out.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")

    n_words = sum(len(s.split()) for s in segments)
    status = "OK " if segments else "EMPTY"
    print(f"[{status}] #{src['num']:>2} {src['id']}: "
          f"{len(segments)} segments, {n_words} words")
    for note in notes:
        print(f"        - {note}")
    return doc


def main(argv: list[str]) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    sources = load_sources()
    if argv:
        wanted = set(argv)
        sources = [s for s in sources if s["id"] in wanted or str(s["num"]) in wanted]

    empty = []
    for src in sources:
        doc = ingest_source(src)
        if not doc["segments"]:
            empty.append(src["id"])

    print("\n=== Ingestion summary ===")
    print("Cleaned docs written to documents/clean/")
    if empty:
        print(f"!! {len(empty)} source(s) produced NO content: {', '.join(empty)}")
        print("   For local_html sources, save the page from your browser into documents/raw/.")


if __name__ == "__main__":
    main(sys.argv[1:])
