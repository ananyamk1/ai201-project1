"""Browser-based fetcher for the bot-blocked sources (Reddit, Yelp, METRO).

These sites fingerprint the TLS handshake, so plain requests/curl get a 403
anti-bot wall no matter the headers. A real Chromium engine (Playwright)
renders like an actual browser and gets the real page — this is the automated
equivalent of "open it in your browser and Save Page As".

For each local_html source it loads the page, lets it render, and writes the
fully-rendered HTML to documents/raw/<local_file> so src/ingest.py can clean it.

Reddit: we rewrite the URL to old.reddit.com, whose comments are server-rendered
into the HTML (new Reddit loads them via JS and also expands lazily).

Usage:
    python -m src.scrape_browser            # all local_html sources
    python -m src.scrape_browser reddit_01_grad_housing_bleak metro_rail
"""

from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

from .ingest import load_sources, RAW_DIR

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def fetch_url(src: dict) -> str:
    """The URL to load in the browser for this source."""
    url = src["url"]
    if src.get("cleaner") == "reddit":
        # old.reddit renders the post + comments into static HTML
        url = url.replace("://www.reddit.com", "://old.reddit.com")
        url = url.replace("://reddit.com", "://old.reddit.com")
    return url


def scrape(src: dict, page) -> bool:
    url = fetch_url(src)
    print(f"  -> {url}")
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
    except Exception as exc:
        print(f"     navigation error: {exc}")
        return False

    # Give JS-heavy pages (Yelp, METRO) a moment to render content.
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(2500)

    html = page.content()
    out = RAW_DIR / src["local_file"]
    out.write_text(html, encoding="utf-8")
    print(f"     saved {len(html):,} bytes -> documents/raw/{src['local_file']}")
    # quick wall/captcha heuristic
    low = html.lower()
    if len(html) < 5000 or "are you a robot" in low or "verify you are human" in low:
        print("     !! page looks like a block/captcha wall — inspect it")
        return False
    return True


def main(argv: list[str]) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    sources = [s for s in load_sources() if s["mode"] == "local_html"]
    if argv:
        wanted = set(argv)
        sources = [s for s in sources if s["id"] in wanted or str(s["num"]) in wanted]

    ok, failed = [], []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent=UA,
            viewport={"width": 1366, "height": 900},
            locale="en-US",
        )
        page = ctx.new_page()
        for src in sources:
            print(f"#{src['num']} {src['id']}")
            (ok if scrape(src, page) else failed).append(src["id"])
        browser.close()

    print(f"\n=== Scrape summary: {len(ok)} ok, {len(failed)} failed ===")
    if failed:
        print("failed/suspect:", ", ".join(failed))


if __name__ == "__main__":
    main(sys.argv[1:])
