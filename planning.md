# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->

Domain: Off Campus Housing experiences at University of Houston
The value is that on official channels of UofHouston they do not provide any advice for off-campus housing experiences beyond links to a few recommendations to stay at. There is no official guide to important factoring questions like what is a safe area to stay at off-campus, public transit-friendly areas, grocery stores to prefer staying close to as a student on budget, navigating safe and walkable neighborhoods, understanding the true cost of off-campus living vs. grad stipends, and avoiding predatory leasing.
UofH is in a heavily car-dependent city, and the area immediately surrounding campus (like parts of the Third Ward) can be difficult to navigate safely for newcomers. International and out-of-state grad students constantly struggle to figure out if areas like Eastwood, Montrose, or the Medical Center are viable on a stipend, especially if they don't have a car.


This project will answer practical questions about neighborhood safety, commute options, rent affordability, transit access, and common lease or management issues around UH. That knowledge is hard to find in one place because it is spread across student anecdotes, local reviews, transit maps, and sparse official guidance rather than a single campus resource.

---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->


| # | Source | Description | URL or Location |
|---|-------------|---------------------|-----------------|
| 1 | Reddit | Graduate Housing Options and Local Commuter Reality | https://www.reddit.com/r/UniversityOfHouston/comments/1fc3wam/graduate_housing_options_look_bleak/ |
| 2 | Reddit | Incoming Grad Student Roommate and Budget Search | https://www.reddit.com/r/UniversityOfHouston/comments/1c00kux/how_do_grad_students_find_housing_and_roommates/ |
| 3 | Reddit | Safe Off-Campus Recommendations for International Students | https://www.reddit.com/r/UniversityOfHouston/comments/1tfko9d/safe_offcampus_housing_recommendations_for/ |
| 4 | Reddit | Graduate Student & Off-Campus Family Housing Realities | https://www.reddit.com/r/UniversityOfHouston/comments/18d0fq0/graduate_student_family_housing/ |
| 5 | Reddit | Inner-Loop Spatial Border & Neighborhood Safety Matrix | https://www.reddit.com/r/UniversityOfHouston/comments/1bbuu7m/safe_neighborhood_near_uh/ |
| 6 | Reddit | The Lofts vs. Off-Campus Complex Cost-Benefit Breakdown | https://www.reddit.com/r/UniversityOfHouston/comments/1bu5rzc/graduate_housing_recommendations_lofts/ |
| 7 | Official UH | Official UH Off-Campus Housing Search Engine Portal | https://offcampushousing.uh.edu/ |
| 8 | Official UH | UH Division of Student Affairs Commuter Resources Guide | https://www.uh.edu/dsa/commuter/ |
| 9 | ApartmentRatings (sub for Yelp) | Cullen Oaks resident reviews — management, fees, maintenance, security | https://www.apartmentratings.com/tx/houston/cullen-oaks_713748370777004/ |
| 10 | Transit/Map | METRO Red/Purple Line Rail Route, Stops, and Core Corridors | https://www.ridemetro.org/riding-metro/transit-services/metrorail |
---

**Ingestion note (Milestone 3):** Reddit, Yelp, and ridemetro.org all hard-block automated requests — not just by User-Agent but by TLS fingerprint, so *any* `requests`/`curl` call gets a 403 anti-bot wall regardless of headers. Rather than hand-saving pages, I capture them with a real headless browser engine (Playwright/Chromium, `src/scrape_browser.py`), which renders like an actual browser and writes the rendered HTML to `documents/raw/` for the pipeline to clean. Reddit threads are fetched via `old.reddit.com` (comments are server-rendered there; new Reddit loads them via JS). Specifics:

- **Sources 1–6, 10** captured via the browser scraper.
- **Sources 7, 8 (official UH)** are not bot-walled and are fetched live by `src/ingest.py`. Their original `/dsa/commuter/` URL had moved to `/dos/commuter/` and the METRO URL `metro-rail` → `metrorail`, so `sources.json` uses the corrected URLs. The UH off-campus *search portal* (originally #7) is a dynamic JS app with no static text, so it was replaced by the content-rich UH Commuter Student Services, Cougar Ride, UHPD security-escort, and Parking & Transportation pages (5 pages total), which cover the same official-guidance ground and directly support eval Q1/Q4.
- **Source 9** was **Yelp**, but Yelp sits behind a DataDome CAPTCHA wall that headless capture can't clear, so I substituted **ApartmentRatings** (76 resident reviews of the same property, Cullen Oaks), which fills the identical "property-management reviews" role for eval Q2.

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:**
250 tokens max per chunk (finalized within my 200–400 range)

**Overlap:**
60 token overlap (~24%, finalized within my 50–75 range)

**Reasoning:**
Reddit comments and Yelp reviews typically run 100–300 words. I chose 200-400 chunk size roughly to mirror one complete thought from one person. I'm not  splitting ideas mid-sentence or merging two people's opinions into one blob.
As for overlap, I chose like ~20–25% overlap. I think that's enough to preserve boundary context without making chunks nearly identical to each other, which would bloat index and confuse retrieval. Everything is experimental right now, can come back to tune these 2 as required.

**Implementation notes (Milestone 3):**
- Locked the chunk window at **250 tokens / 60-token overlap**. The 250 cap sits just under all-MiniLM-L6-v2's 256-token ceiling, so every chunk embeds in full with nothing silently truncated. Token counts are measured with the model's *own* tokenizer (`src/textutils.py`), not a word estimate.
- Chunking is **segment-aware**: documents are first cleaned into segments (one Reddit comment / one Yelp review / one section of an official page), and the chunker never merges across segments. This is what enforces "never merge two people's opinions." A long comment that exceeds 250 tokens is split into multiple overlapping chunks; the 60-token overlap carries the setup→punchline thread across the boundary (directly addressing Anticipated Challenge #1). Chunks under 15 tokens are dropped as fragments.

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**
all-MiniLM-L6-v2

**Top-k:**
5

**Production tradeoff reflection:**
The two tradeoffs I'd weigh are context length and domain specificity. On context length, all-MiniLM's 256-token ceiling forced me to cap chunks lower, Reddit comments often bury the most useful detail toward the end: someone spends two sentences on setup and then says "the commute destroyed me after month 3," and if that lands past token 256 it never gets embedded at all, meaning retrieval silently misses the most informative part of the source. On domain specificity, similarity space is calibrated to clean prose, and my corpus is informal, hedged, and contextual; a comment like "it's fine I guess if you don't mind the vibe" carries real signal that a general model may flatten into noise because it doesn't resemble typical training text. Production deployment would mean either fine-tuning on student housing or local community forums, or explicitly documenting these as known retrieval gaps when evaluating system quality.

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
| --- | --- | --- |
| 1 | I'm an international grad student with no car. Is it realistic/safe to live in Eastwood or the Med Center and commute to UH? | Yes, but pick your trade-off: The Med Center is safer and full of medical professionals, but you’ll have to ride the METRO rail/bus, which gets sketchy at night and takes long. Eastwood is closer and cheaper but still requires you to keep your guard up. |
| 2 | What hidden fees or management issues should I look out for at places right off campus like Cullen Oaks? | Expect tough management and security issues. There's complain about delayed maintenance like AC breaking down in the summer, surprise admin fees, and unmonitored parking garages where bike thefts are common. |
| 3 | Can I realistically afford a 1-bed apartment in Midtown or Montrose on a standard UH grad stipend? | No way, not unless you get a roommate. A standard stipend is around $1,800/month before fees. Average 1-bedrooms in Midtown or Montrose cost $1,300 to $2,000+. Rent would completely wipe out your paycheck. You’ll need to split a 2-bedroom. |
| 4 | I have late-night labs and no car. How do I get back to my off-campus apartment safely after dark? | Do not walk alone, and use UH safety resources. Official policy says to call Cougar Ride or request a UHPD police escort to walk you to the transit stops. Absolutely do not walk past the campus borders alone after 10 PM. |
| 5 | Is it financially smarter to live at the University Lofts on campus or split an off-campus apartment? | Off-campus with a roommate is cheaper, but the Lofts are easier. Off-campus splits save you cash, but you have to worry about separate electricity bills which skyrocket in Houston summers. The Lofts are pricey upfront but cover all utilities and require no meal plan. |
---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1.The big risk with Reddit comments is that people write in a setup-then-punchline way, they spend a few sentences explaining who they are and where they live, and then drop the actual useful take at the end. If my chunker cuts in the middle of that, the useful part gets retrieved without the setup and the LLM has no idea what it's talking about. My overlap should catch some of this but if someone writes a long intro, 50-75 tokens of overlap probably isn't enough to save it.

2.Some of my evaluation questions like the Cougar Ride safety policy or the Lofts utility costs, might only show up in one or two chunks across my entire corpus. The problem is the system doesn't know that. It'll still retrieve something, the LLM will still generate a confident-sounding answer, and the user has no way to tell that the answer is basically built on one person's comment from 2023. It won't look wrong, it'll just be weakly supported — and that's harder to catch than an obvious hallucination.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->



Document Ingestion      Chunking               Embedding + Vector Store
──────────────────      ────────────────       ────────────────────────
requests +         -->  RecursiveText      -->  all-MiniLM-L6-v2
BeautifulSoup           Splitter                ChromaDB (local)
                        250 tokens
Reddit, Yelp,           60 tok overlap
UH, METRO
                                                        │
                                                        ▼
                        ┌─────────────────────────────────────────┐
     User query  ──►    │   Retrieval  │  semantic search, top-k=5 │
                        └─────────────────────────────────────────┘
                                                        │
                                                        ▼
                        ┌─────────────────────────────────────────┐
                        │           Generation                     │
                        │   top-5 chunks + query → LLM → answer   │
                        └─────────────────────────────────────────┘
                                                        │
                                                        ▼
                                                 Answer to user

---




## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**

**Milestone 4 — Embedding and retrieval:**
Gave the Copilot AI this Retrieval Approach section + the architecture diagram and asked it to implement an embedding step that loads chunks.json, embeds with
all-MiniLM-L6-v2, and stores vectors + source metadata in ChromaDB, and aslo a retrievequery, k=5 function. Produced vectorstore.py, /embed.py, and retrieve.py. Key choices I verified:
- Cosine space, normalized embeddings (hnsw:space="cosine", normalize_embeddings=True)
  so scores are comparable across queries; report similarity = 1 − cosine distance.
- Same model on both sides** routed through vectorstore.py, if the build and query
  used different models the vectors would be incompatible.
- Verified retrieval on all 5 eval questions: Q1/Q2/Q3/Q5 retrieve strongly; Q4 (late-night
  safety) is weak** — the official Cougar Ride / UHPD escort chunks are indexed and rank #1–2 when queried with their own vocabulary (0.68/0.61), but the natural-language query "get home after dark" surfaces Reddit chatter instead. This is the domain-specificity gap predicted in the Production Reflection above; candidate fix for Milestone 5 is query expansion or a hybrid keyword+vector retrieval.

**Milestone 5 — Generation and interface:**
