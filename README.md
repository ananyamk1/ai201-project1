# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

<!-- What topic or category of knowledge does your system cover?
     Why is this knowledge valuable, and why is it hard to find through official channels?
     Example: "Student reviews of CS professors at [university] — useful because official
     course descriptions don't reflect teaching style, exam difficulty, or workload." -->

Off-campus housing experiences for University of Houston students — neighborhood
safety, commute/transit options, rent affordability vs. grad stipends, and common
lease/management issues. UH's official channels list a few recommended complexes but
offer no practical guidance on which areas are safe and walkable, what's realistic on
a stipend without a car, or which complexes have predatory management. That knowledge
is scattered across student anecdotes (Reddit), resident reviews, transit maps, and
sparse official pages rather than collected in one place — which is exactly what a RAG
system over these sources can provide.

---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

All 10 sources are registered in `sources.json`. Reddit, Yelp, and ridemetro.org
hard-block scripted requests (TLS-fingerprint 403 walls), so those were captured with
a real headless browser (`src/scrape_browser.py`, Playwright/Chromium) and saved to
`documents/raw/`; the uh.edu pages are not bot-walled and are fetched live by
`src/ingest.py`. Two substitutions/fixes are noted in the table.

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | r/UniversityOfHouston — "Graduate housing options look bleak" | Reddit thread (saved HTML) | https://www.reddit.com/r/UniversityOfHouston/comments/1fc3wam/ |
| 2 | r/UniversityOfHouston — "How do grad students find housing and roommates?" | Reddit thread (saved HTML) | https://www.reddit.com/r/UniversityOfHouston/comments/1c00kux/ |
| 3 | r/UniversityOfHouston — "Safe off-campus housing recommendations for international students" | Reddit thread (saved HTML) | https://www.reddit.com/r/UniversityOfHouston/comments/1tfko9d/ |
| 4 | r/UniversityOfHouston — "Graduate student / family housing" | Reddit thread (saved HTML) | https://www.reddit.com/r/UniversityOfHouston/comments/18d0fq0/ |
| 5 | r/UniversityOfHouston — "Safe neighborhood near UH?" | Reddit thread (saved HTML) | https://www.reddit.com/r/UniversityOfHouston/comments/1bbuu7m/ |
| 6 | r/UniversityOfHouston — "Graduate housing recommendations: Lofts" | Reddit thread (saved HTML) | https://www.reddit.com/r/UniversityOfHouston/comments/1bu5rzc/ |
| 7 | UH Commuter Student Services — getting to campus, Cougar Ride, UHPD security escort | Official UH (live fetch, 5 pages) | https://www.uh.edu/dos/commuter/ (corrected from the dead /dsa/commuter/) |
| 8 | UH Parking & Transportation — METRO transit, student Q-Card, COAST | Official UH (live fetch) | https://www.uh.edu/parking/transportation-options/public-transit/ |
| 9 | Cullen Oaks resident reviews (76 reviews) | ApartmentRatings (saved HTML) | https://www.apartmentratings.com/tx/houston/cullen-oaks_713748370777004/ — **substituted for Yelp**, which is behind a DataDome CAPTCHA wall |
| 10 | METRORail — Red/Purple Line routes, stops, fares | Transit (saved HTML) | https://www.ridemetro.org/riding-metro/transit-services/metrorail (corrected from the dead `metro-rail`) |

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:** 250 tokens maximum per chunk, counted with all-MiniLM-L6-v2's own
tokenizer (not a word estimate).

**Overlap:** 60 tokens (~24%) carried between consecutive chunks of the same segment.

**Why these choices fit your documents:** The corpus is short, opinion-dense units —
Reddit comments and apartment reviews typically run 100–300 words, i.e. one person's
complete thought. Preprocessing first cleans each page into **segments** (one Reddit
comment, one resident review, or one section of an official page) with BeautifulSoup,
stripping scripts/nav/cookie banners/footers/vote+share widgets and decoding HTML
entities. The chunker then packs whole sentences within a segment up to 250 tokens and
**never merges across segments**, so a chunk is always one person's opinion, never two
blended together. The 250 cap sits just under the embedder's 256-token ceiling, so every
chunk embeds in full with nothing silently truncated; the 60-token overlap keeps a
setup→punchline thought intact when a long comment spans a boundary. Chunks under 15
tokens and exact-duplicate chunks are dropped.

**Final chunk count:** **239 chunks** across the 10 documents (avg 61 tokens, max 249) —
comfortably inside the healthy 50–2,000 range. Roughly: Reddit threads ~75, official UH
pages ~63, apartment reviews ~36, METRORail ~65.

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:**

**Production tradeoff reflection:**

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:**

**How source attribution is surfaced in the response:**

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:**

**What the system returned:**

**Root cause (tied to a specific pipeline stage):**

**What you would change to fix it:**

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**

**One way your implementation diverged from the spec, and why:**

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- *What I gave the AI:*
- *What it produced:*
- *What I changed or overrode:*

**Instance 2**

- *What I gave the AI:*
- *What it produced:*
- *What I changed or overrode:*
