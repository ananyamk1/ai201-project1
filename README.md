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

**Final chunk count:** **230 chunks** across the 10 documents (avg 63 tokens, max 249) —
comfortably inside the healthy 50–2,000 range. Breakdown: Reddit threads 75, official UH
pages 63, METRORail 58, apartment reviews 34. (A random-sample inspection
[`python -m src.chunk --random 5`] surfaced UI/widget fragments leaking from the METRO
single-page app and a "See More" truncation artifact in reviews; both were filtered out
before this final count.)

---

## Sample Chunks

<!-- At least 5 labeled sample chunks, each with its source document name. -->

Here are 5 real chunks straight out of `documents/chunks.jsonl`, each labeled with the source document it came from:

**1. Source document: `reddit_05_safe_neighborhood` (#5 Reddit) — 38 tokens**
> [Thread] Safe neighborhood near uh? Me and my friends are planing to rent an apartment senior year. What's the closest neighborhood to uh that would be considered a safe neighborhood?

**2. Source document: `reviews_cullen_oaks` (#9 ApartmentRatings) — 63 tokens**
> Current Resident 716765 Resident • 2023 1.7 7/25/2023 The place is disaster, terribly infected by cockroaches. The roaches are every where. They are even in the microwave and fridge. Building has always a terrible smell and the rooms are very small and dingy

**3. Source document: `uh_parking_transit` (#8 Official UH) — 37 tokens**
> Parking and Transportation Services offers eligible faculty, staff and students the opportunity to join COAST (Coogs on Alternative and Sustainable Transportation), and sign up for the METRO fare card incentive.

**4. Source document: `reddit_01_grad_housing_bleak` (#1 Reddit) — 60 tokens**
> Most people at UH live off campus both grad and undergrad we're an 85% commuter school I suggest looking into midtown lots of young adults and young families. Restraints and bars in walking distance one of the safer areas near campus it's about a ten minute drive to campus which is nice

**5. Source document: `metro_rail` (#10 Transit/Map) — 70 tokens**
> METRORail is Houston's light rail network, offering convenient access to many popular destinations in and around downtown Houston. These include the Texas Medical Center, Museum District, Houston Zoo, Theater District, NRG Stadium, University of Houston and Texas Southern University. With trains running frequently, you'll be on board and on track to your destination quickly.

Each chunk keeps its source attached as metadata (`doc_id`, source type, URL, position), so anything retrieved can be traced straight back to where it came from.

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:**
I used all-MiniLM-L6-v2 from sentence-transformers, the recommended default. I picked it because it runs locally with no API key and no rate limits, the vectors are small (384 dimensions) so search is quick, and it let me keep the exact same model on both the indexing side and the query side. It also lined up with my chunking plan: its input ceiling is 256 tokens, which is the whole reason I capped my chunks at 250 so nothing gets cut off before it's embedded.

**Production tradeoff reflection:**
If I were shipping this for real and money wasn't a concern, the two things I'd weigh most are context length and how well the model handles my kind of text. The 256-token limit means a long Reddit comment can get clipped, and the most useful line is often near the end ("the commute destroyed me after month 3"), so a longer-context model would stop me from losing that. The bigger one is domain fit: my data is informal, hedged, slangy student talk, and a general model can flatten that into noise, which is exactly what hurt my late-night safety question. So I'd look at a larger or domain-tuned embedding model (or an API one like OpenAI's text-embedding-3-large), and since a lot of my users are international students, better multilingual handling would matter too. The trade-off is cost and latency, since those usually mean API calls and rate limits instead of a free local model.

---

## Retrieval Test Results

<!-- At least 3 queries, each with the top returned chunks; for at least 2, why they're relevant. -->

I tested retrieval by querying the vector store directly with `python -m src.retrieve "..."`. The scores are cosine **distance**, so lower = closer match.

**Query 1: "What hidden fees should I expect at Cullen Oaks?"**
- `distance=0.477` — `reviews_cullen_oaks` (#9 ApartmentRatings): *"...Cullen Oaks is a magical type of place where you can read all the brochures... and still be shocked. SURPRISE, monthly room checks!..."*
- `distance=0.527` — `reviews_cullen_oaks` (#9 ApartmentRatings): *"...a million reasons why I would not recommend this so called 'apartment' complex... charged $200 for a tear in the carpet that was there when I moved in..."*
- `distance=0.548` — `uh_parking_transit` (#8 Official UH): *"...You will be prompted to pay the $10 application fee..."*

*Why these are relevant:* the top two are actual Cullen Oaks resident reviews that literally describe the surprise fees and charges the question is asking about — exactly the right source and the right topic. The third is weaker and a bit off (it's a UH Q-Card application fee, not a Cullen Oaks fee) — it got pulled in just because it shares the word "fee," which is the kind of tail noise that shows up at rank 3.

**Query 2: "Is the Medical Center safe to commute from without a car?"**
- `distance=0.378` — `reddit_05_safe_neighborhood` (#5 Reddit): *"As a resident, med center is super safe in a practical sense, especially if you live in a gated community. The traffic is more likely to be a bigger pain..."*
- `distance=0.510` — `reddit_05_safe_neighborhood` (#5 Reddit): *"I know hella people who live near the med center. It's like a 10-15 min drive."*
- `distance=0.569` — `reddit_05_safe_neighborhood` (#5 Reddit): *"My son commutes from Spring and the drive isn't bad."*

*Why these are relevant:* all three come from the "safe neighborhood near UH" thread and speak directly to the Med Center being safe and how the commute feels — the #1 hit (distance 0.378, very close) answers both halves of the question, safety and commute, in one chunk.

**Query 3: "Is it cheaper to live at the University Lofts or split an off-campus apartment?"**
- `distance=0.361` — `reddit_01_grad_housing_bleak` (#1 Reddit): *"Story about the Lofts... most graduate students live off campus in districts like Montrose, Heights, EaDo, TMC, Midtown..."*
- `distance=0.377` — `reddit_01_grad_housing_bleak` (#1 Reddit): *"Campus housing can be pretty expensive. I have a... house 3 blocks south of U of H with one large bedroom... Rent is $500/mn + one share of house bills."*
- `distance=0.397` — `reddit_06_lofts_vs_offcampus` (#6 Reddit): *"I live in the lofts right now 1b1b furnished... I highly suggest it..."*

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:**
My system prompt doesn't just suggest using the documents, it forces it. I tell the model it can answer ONLY from the numbered context chunks I pass in, to use no outside knowledge, and that if the context doesn't have the answer it must reply with the exact line "I don't have enough information on that." and nothing else. I also tell it these are individual student opinions and reviews, not official fact, so it should point out when sources disagree instead of inventing a consensus, and I run it at a low temperature (0.2) so it doesn't get creative. I checked this by asking something totally off-topic (a taco truck in Austin) and it refused word-for-word like it was told to.

**How source attribution is surfaced in the response:**
Attribution is built in code, not left up to the model. After the answer comes back, my code takes the chunks that were actually retrieved, groups them by their source document, and builds a "Sources:" list from the metadata, where each source shows the [n] numbers it covered plus the real URL. So even if the model forgot to cite anything, the sources are still there and correct. On top of that I ask the model to cite [n] inline in its sentences, and the Gradio app has a drop-down that shows the exact chunks (with their distance scores) the answer was grounded in. One small thing I added: I don't attach sources to a refusal, so a "no info" answer never gets fake citations stapled to it.

---

## Example Responses

<!-- At least 2 responses with source attribution visible, plus one out-of-scope refusal. -->

These are real outputs from the system (the Sources block is built in code, so it always shows up). Wording shifts a little between runs since the model runs at a low temperature, but the grounding and sources stay the same.

Example 1 — "What hidden fees or management issues should I look out for at Cullen Oaks?"
> At Cullen Oaks, you should look out for surprise monthly room checks, unauthorized gathering policies that can lead to eviction, and surprise fees [1]. The management has been described as naggy and negligent, with a tendency to threaten residents with eviction for small offenses [1]. Additionally, utilities are not included in the rent, and you may be charged for electricity bills over $20 [2]. The complex also has issues with paper-thin walls, pests like roaches and gnats, and nonexistent wifi [4].
>
> Sources:
> [1],[2],[4] ApartmentRatings — Cullen Oaks resident reviews
>      https://www.apartmentratings.com/tx/houston/cullen-oaks_713748370777004/
> [3] Reddit — Graduate Housing Options and Local Commuter Reality
>      https://www.reddit.com/r/UniversityOfHouston/comments/1fc3wam/
> [5] Reddit — Graduate Student & Off-Campus Family Housing Realities
>      https://www.reddit.com/r/UniversityOfHouston/comments/18d0fq0/

Example 2 — "Is Eastwood or the Med Center safe to commute from without a car?"
> According to [1], Eastwood is considered safe by one resident who has lived there for 4 years without incident, and it's about a 3-minute metro ride to campus. As for the Med Center, [2] says it's "super safe" in a practical sense, especially in gated communities, though traffic can be a pain.
>
> Sources:
> [1],[2] Reddit — Inner-Loop Spatial Border & Neighborhood Safety Matrix
>      https://www.reddit.com/r/UniversityOfHouston/comments/1bbuu7m/
> [3],[5] Reddit — Safe Off-Campus Recommendations for International Students
>      https://www.reddit.com/r/UniversityOfHouston/comments/1tfko9d/

Out-of-scope query: "Which grocery stores near UH deliver, and do they offer student discounts?"**
> I don't have enough information on that.

My corpus has nothing about grocery delivery, so instead of making up a plausible answer the system returns the exact refusal line and attaches **no sources** (I suppress the Sources block on a refusal so a "no info" answer never gets fake citations).

---

## Query Interface

<!-- Describe the input and output fields, plus a sample interaction transcript. -->

The interface is a Gradio web app (`python app.py`, opens at http://localhost:7860).

**Input fields:**
- **Your question** — a text box where you type the question (pressing Enter also submits).
- **Chunks retrieved (top-k)** — a slider from 1 to 10, default 5, to control how many chunks get pulled into the context.
- **Ask** — the button that runs it. There are also clickable example questions underneath.

**Output fields:**
- **Answer** — the grounded answer, with inline `[n]` citations and the code-built **Sources** list (source name + URL) appended at the bottom.
- **Retrieved context (what the answer is grounded in)** — an expandable drop-down that shows the exact chunks that were retrieved, each with its distance score and source document, so you can see what the answer was built from.

Extra:
> Your question: What hidden fees or management issues should I look out for at Cullen Oaks?
> top-k: 5
> (click Ask)
>
> Answer: At Cullen Oaks, you should look out for surprise monthly room checks, unauthorized gathering policies that can lead to eviction, and surprise fees [1]. Utilities are not included, and you may be charged for electricity over $20 [2]. The complex also has paper-thin walls, pests, and nonexistent wifi [4].
>
> Sources:
> [1],[2],[4] ApartmentRatings — Cullen Oaks resident reviews — https://www.apartmentratings.com/tx/houston/cullen-oaks_713748370777004/
> [3] Reddit — Graduate Housing Options and Local Commuter Reality — https://www.reddit.com/r/UniversityOfHouston/comments/1fc3wam/
> [5] Reddit — Graduate Student & Off-Campus Family Housing Realities — https://www.reddit.com/r/UniversityOfHouston/comments/18d0fq0/
>
> (expand "Retrieved context") → shows chunk [1] `distance=0.443` from `reviews_cullen_oaks`, chunk [2] `distance=0.452` from `reviews_cullen_oaks`, and so on.

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | International grad student, no car — is Eastwood or the Med Center safe and realistic to commute from? | Yes, with trade-offs: the Med Center is safer but the METRO ride at night can feel sketchy and slow; Eastwood is closer and cheaper but still stay alert. | Said both are viable — Eastwood is safe and ~3 min to campus by metro, and the Med Center is "super safe" in gated communities with traffic the main downside. | Relevant | Partially accurate (got both-viable + Eastwood-by-metro, but missed the night-time METRO caveat) |
| 2 | What hidden fees or management problems should I expect at a place like Cullen Oaks? | Tough management and security issues: slow maintenance (e.g. AC in summer), surprise admin fees, and unmonitored garages where bikes get stolen. | Listed surprise room checks, eviction over small things, surprise fees, utilities not included / ~$20 electricity, pests, thin walls, and constant management turnover. | Relevant | Accurate (nailed the fees + bad management + maintenance theme, just with different specifics than I expected) |
| 3 | Can I afford a 1-bed in Midtown or Montrose on a standard grad stipend? | No — not without a roommate. A stipend is ~$1,800/mo and 1-beds run $1,300–$2,000+, so you'd need to split a 2-bed. | Said grad students pay around $1,400 and it's hard to find under $1k, gave no Midtown/Montrose 1-bed price, and partly fell back to "I don't have enough information." | Partially relevant | Partially accurate (showed rent is high but never reached the clear "no, get a roommate" conclusion) |
| 4 | Late-night labs, no car — how do I get home safely after dark? | Don't walk alone; call Cougar Ride or request a UHPD police escort, and don't walk past campus borders alone after 10pm. | Recommended the Cougar Ride shuttle plus pepper spray, contacting police, and sticking together after 6pm. | Partially relevant | Partially accurate (got Cougar Ride + general safety, but missed the official UHPD security escort) |
| 5 | Is it cheaper to live at the University Lofts or split an off-campus apartment? | Off-campus with a roommate is cheaper but the Lofts are easier; splits save cash but you pay separate electricity (brutal in Houston summers), while the Lofts cost more but include utilities and no meal plan. | Said an off-campus shared room (~$500/mo) looks cheaper and the Lofts are "expensive" with no exact price, concluding splitting is probably smarter but Lofts pricing is missing. | Relevant | Partially accurate (right that splitting is cheaper, but missed the utilities-included vs separate-electricity point) |

Retrieval quality: Relevant / Partially relevant / Off-target  
Response accuracy: Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

Question that failed:
"I have late-night labs and no car. How do I get back to my off-campus apartment safely after dark?" (test question 4)

What the system returned:
It suggested the Cougar Ride shuttle plus Reddit advice — carry pepper spray, know how to contact the police, and stick together after 6pm. It never mentioned the official UHPD security escort service, even though that's basically the official answer to this question and that exact content is sitting in my corpus.

Root cause:
This is a retrieval/embedding-stage problem, a vocab mismatch. My question is phrased like a student ("get home safely after dark"), but the official UH page describes the service as a "security escort" and an "after-hours shuttle." all-MiniLM is a general model and doesn't really know those are the same idea, so when I embed the query and search, the UHPD escort chunk doesn't make the top 5 — casual Reddit comments that literally share words like "safe" and "night" score closer. I confirmed it's a wording gap and not missing data: if I search using the page's own language ("Cougar Ride security escort"), that exact chunk jumps to the #1 spot with a much lower distance (~0.32). So the chunk is indexed perfectly fine; the embedding model just can't bridge casual wording to official wording. (Cougar Ride only slipped in this time because it happened to land in the top 5 for this phrasing.)

What I'd change to fix it:
A few options. The cheapest is query expansion, have a small model rewrite the question into official terms "escort, shuttle, night safety" before searching. Another is hybrid retrieval, mixing keyword matching with the vector search so an exact term like escort gets weight even when the vectors don't agree. The heavier fix is swapping in or fine-tuning an embedding model that actually understands this housing/safety vocabulary. Bumping top-k up a little also helps pull the official chunk into the context window.

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

One way the spec helped during implementation:
Writing the Chunking Strategy and Retrieval Approach down first really paid off. Because I'd already noted that all-MiniLM has a 256-token ceiling, I knew to cap chunks at 250 and to count tokens with the model's own tokenizer, so nothing gets quietly cut off before it's embedded. And because my planning said "one chunk = one person's complete thought, never blend two people," I built the chunker to be segment-aware from the start instead of just splitting on character count. Having those decisions written down meant I could hand the spec straight to the AI and get back code that already matched what I wanted, instead of going back and forth.

One way my implementation diverged from the spec, & why:
My plan said I'd scrape everything live with requests + BeautifulSoup, but that fell apart right away. Reddit, Yelp, and the METRO site block scripts at the TLS level, so every request came back as a 403 wall no matter what headers I used. So I switched to driving a real headless browser (Playwright/Chromium) to capture those pages, and read Reddit through old.reddit.com so the comments actually load. I also had to swap Yelp out for ApartmentRatings because Yelp sits behind a DataDome CAPTCHA I couldn't get past, and fix two official UH/METRO URLs that had moved. The end goal — clean text from those 10 sources — stayed exactly the same; only the "how" changed, and I wrote all of that down in the ingestion notes in planning.md.

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

- *What I gave the AI:* My Documents and Chunking Strategy sections plus the pipeline diagram, and I asked it to write the load → clean → chunk pipeline at my 250-token / 60-overlap setting.
- *What it produced:* The ingest, clean, and chunk scripts that output a chunks file with source metadata attached to each chunk.
- *What I changed or overrode:* The first cleaner quietly deleted every single Reddit comment. It was throwing away all <form> tags (old.reddit wraps each comment in a form), and its junk filter matched the word "vote" inside "unvoted," which is on every comment. I caught it because all my Reddit sources came out empty, and I directed the fix. I also had it add a random-chunk inspector, and that's what exposed METRO menu/widget text leaking into chunks, which I then had it filter out.

**Instance 2**

- What I gave the AI: My Retrieval Approach section, my grounding requirement (answer only from retrieved chunks, refuse otherwise, always cite sources), the output format I wanted, and a basic Gradio skeleton, and asked it to wire up generation on Groq's llama-3.3-70b plus the web UI.
- What it produced: generate.py (the prompt building + Groq call) and app.py (the Gradio interface).
- What I changed or overrode: I made source attribution programmatic instead of trusting the model to cite, the Sources list is built in code from the retrieved chunks' metadata, so it can't be skipped or made up. I also tightened the system prompt to force the exact refusal line, and fixed a dependency clash where installing gradio 6 broke my embedding model (it forced a huggingface-hub version that transformers couldn't use) by pinning gradio 5 instead.

---

## Stretch Features

I added four stretch features on top of the base system. All four are toggleable in the Gradio app (the **Ask** tab has a retrieval-mode radio and a source filter; the **Chat** tab has memory) and runnable from the command line.

### 1. Hybrid search (BM25 + vector)

The plain vector search misses things when the query wording doesn't match the source wording. So I added a keyword ranker (BM25, via `rank-bm25`) alongside the vector search and fused the two rankings with **Reciprocal Rank Fusion (RRF)**: each chunk gets a score of `sum over methods of 1 / (60 + its_rank_in_that_method)`, and I sort by that. RRF is rank-based, which sidesteps the fact that cosine distance and BM25 scores are on totally different scales and can't just be added. Code is in `src/hybrid.py` (`python -m src.hybrid "..."`), and the app has a vector/hybrid toggle.

**Comparison on 3 queries (vector-only vs BM25-only vs hybrid):**

| Query | Vector top result | BM25 top result | Hybrid top-3 | Winner |
|---|---|---|---|---|
| "student Q-Card 50% METRO discount" | Q-Card 50%-off chunk | same Q-Card chunk | both Q-Card chunks up top | **Tie** — both nail it (keyword + meaning match) |
| "What hidden fees should I expect at Cullen Oaks?" | 2 Cullen Oaks reviews, but #3 is an off-target UH **$10 application fee** | 2 Cullen Oaks reviews + a slightly off Reddit "open spot" | the two real Cullen Oaks reviews, drops the $10-app-fee noise | **Hybrid** — cleaner top-3, no false positive |
| "is it safe to live near campus without a car" (vague) | coherent safety chunks | adds keyword noise ("hand over money without a struggle") | a mix | **Vector** — pure semantic wins on a vague query |

I also checked "Cougar Ride security escort": BM25 surfaces the official UHPD escort chunk that pure vector ranks lower. Takeaway: hybrid clearly helps on keyword / proper-noun queries and trims some false positives, while pure vector is better on vague paraphrased queries. I kept vector as the default with hybrid as a toggle.

### 2. Chunking strategy comparison

I re-chunked the same cleaned documents three ways, embedded each set, and ran the same 5 queries against all three, measuring the top-1 cosine distance (lower = closer). Code: `src/compare_chunking.py`.

| Query (top-1 distance) | A: 250/60 segment-aware (current) | B: 120/30 segment-aware (smaller) | C: 500-word, merges segments |
|---|---|---|---|
| Med Center safe to commute? | 0.378 | 0.378 | 0.619 |
| Cullen Oaks hidden fees | 0.477 | **0.435** | 0.616 |
| Afford Midtown/Montrose | 0.369 | 0.369 | 0.509 |
| Get home after dark | 0.665 | 0.629 | 0.686 |
| Lofts vs off-campus | 0.351 | 0.360 | 0.388 |
| **# chunks** | 231 | 271 | 27 |

**Analysis:** strategy **C (big 500-word chunks that merge different people's comments) is clearly the worst** — its distances jump to ~0.6+ because each chunk blends multiple people and topics, so the embedding is diluted and matches any specific query less precisely. That's direct evidence for the segment-aware decision in my planning ("never merge two people's opinions"). Strategy **B (smaller 120/30) is marginally tighter** on review-heavy queries like Cullen Oaks (0.435 vs 0.477) because shorter chunks are more focused, but it makes more chunks and gives the LLM less context per chunk. My current **A (250/60)** is the best balance of retrieval precision and enough context to generate from. Also note the "get home after dark" query stays high-distance across *all three* strategies — confirming that failure is an embedding/vocabulary issue, not a chunking one.

### 3. Metadata filtering

Every chunk is stored with its `source` type in metadata, so I can filter retrieval to one source. In code it's ChromaDB's `where={"source": ...}` filter on the vector path plus an equivalent filter on the BM25 candidates (`retrieve(query, k, source=...)` and `hybrid_retrieve(...)`); in the app it's the "Filter by source" dropdown. Visible effect: filtering "How do I get home safely after dark?" to **Official UH** surfaces the UHPD security-escort and Cougar Ride chunks at the top (which the unfiltered search buries under Reddit chatter), and filtering the Cullen Oaks question to **ApartmentRatings** returns only resident reviews — no Reddit or transit chunks.

### 4. Conversational memory

The **Chat** tab keeps the conversation so a follow-up can lean on earlier turns (`answer_chat()` in `src/generate.py`). It does two things with the history: it builds the retrieval query from the previous user turn plus the new message (so the follow-up retrieves the right context), and it passes the recent turns to the model so references resolve. Sample exchange:

> **User:** Can I afford a 1-bed apartment in Midtown on a UH grad stipend?
> **Bot:** ...most grad students spend around $1,400 on rent... [1]
> **User:** what about with a roommate?  *(never repeats "Midtown" or "rent")*
> **Bot:** Splitting a place could help — a 2-bed at Cullen Oaks runs $1,914, about $807 per person [4]...

The second answer correctly stays on affordability/splitting rent, which only makes sense if it remembered the first turn — not just topic overlap.
