# Milestone 3 — Ingestion & Chunking Pipeline

Three stages, driven by `sources.json`:

```
                 src/scrape_browser.py            src/ingest.py              src/chunk.py
bot-walled sites ────────────────────► documents/raw/*.html ──► documents/clean/*.json ──► documents/chunks.jsonl
uh.edu pages ──────(live fetch in ingest)────────────────────►        (segments)            (250 tok / 60 overlap)
```

1. **Scrape** — `src/scrape_browser.py`: the bot-walled sources (Reddit, METRO, ApartmentRatings)
   fingerprint the TLS handshake, so `requests`/`curl` get a 403 wall no matter the headers.
   A real headless Chromium (Playwright) renders like a browser and gets the real page, saved to
   `documents/raw/`. Reddit is fetched via `old.reddit.com` (its comments are server-rendered).
2. **Ingest** — `src/ingest.py`: live-fetches the uh.edu pages (`mode: url`) and reads the
   browser-saved HTML (`mode: local_html`). Cleans each page into **segments** (one Reddit
   comment / review / page section) with BeautifulSoup, stripping scripts, nav, cookie banners,
   footers, vote/share widgets; decodes HTML entities. → `documents/clean/<id>.json`
3. **Chunk** — `src/chunk.py`: packs sentences into ≤250-token chunks with 60-token overlap
   (measured with all-MiniLM-L6-v2's own tokenizer), never crossing a segment boundary. Drops
   <15-token fragments and exact duplicates. → `documents/chunks.jsonl`

## Milestone 4 — Embedding + retrieval

```
documents/chunks.jsonl --(src/embed.py)--> ChromaDB ./chroma_db --(src/retrieve.py)--> top-k chunks
                          all-MiniLM-L6-v2     (cosine, 384-dim)        query -> nearest neighbors
```

- **Embed** — `src/embed.py`: embeds every chunk with all-MiniLM-L6-v2 (local, no API key)
  and stores the 384-dim vectors in a local ChromaDB collection with source metadata
  (`doc_id`, `source`, `segment_index`, `url`, ...) for attribution. Rebuilds from scratch each run.
- **Retrieve** — `src/retrieve.py`: `retrieve(query, k=5)` embeds the query with the same
  model and returns the k nearest chunks by cosine distance, each with its source info and a
  similarity score in [0, 1]. Shared config (model + collection) lives in `src/vectorstore.py`.

## Milestone 5 — Grounded generation + interface

```
query --> src/retrieve.py --> top-k chunks --> src/generate.py --> grounded answer + Sources
                                                (Groq llama-3.3-70b)   ^ attribution built in code
                                              src/app.py = Gradio UI over generate.answer()
```

- **Generate** — `src/generate.py`: `answer(query, k=5)` retrieves, builds a numbered context
  block, and calls Groq `llama-3.3-70b-versatile` with a strict system prompt (answer ONLY from
  context; exact refusal string otherwise; temperature 0.2). Source attribution is appended
  **programmatically** from chunk metadata — it does not depend on the model citing. Needs
  `GROQ_API_KEY` in `.env`.
- **Interface** — `src/app.py`: Gradio app over `generate.answer`, with a top-k slider and an
  expandable panel showing the exact retrieved chunks + distances.

## Run it

```bash
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium          # one-time, downloads the browser engine

python -m src.scrape_browser         # bot-walled sites -> documents/raw/*.html
python -m src.ingest                 # raw -> documents/clean/*.json
python -m src.chunk --inspect        # clean -> chunks.jsonl + 5 sample chunks + stats
python -m src.embed                  # chunks.jsonl -> ChromaDB (./chroma_db)
python -m src.retrieve "is the Med Center safe without a car?"   # query the index
python -m src.generate "what fees should I expect at Cullen Oaks?"  # grounded answer in terminal
python -m src.app                    # launch the Gradio web UI (http://127.0.0.1:7860)
```

Re-running is idempotent: the scraper overwrites the saved HTML, ingest re-fetches the uh.edu
pages (cached by index name), and chunk rebuilds `chunks.jsonl`.

## Notes on sources

- **Yelp (original #9)** sits behind a DataDome CAPTCHA wall that headless capture can't clear.
  Substituted with **ApartmentRatings** (76 resident reviews of the same property, Cullen Oaks).
- The two **uh.edu** URLs in the original plan had moved (`/dsa/commuter/` → `/dos/commuter/`,
  `metro-rail` → `metrorail`); `sources.json` uses the corrected URLs.
- Current corpus: **239 chunks** across 10 documents.
