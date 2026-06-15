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
| 9 | Yelp Business | Cullen Oaks Property Management Review Index & Warnings | https://www.yelp.com/biz/cullen-oaks-houston |
| 10 | Transit/Map | METRO Purple Line Rail Route, Stops, and Core Corridors | https://www.ridemetro.org/riding-metro/transit-services/metro-rail |
---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:**
200-400 tokens per chunk

**Overlap:**
50-75 token overlap

**Reasoning:**
Reddit comments and Yelp reviews typically run 100–300 words. I chose 200-400 chunk size roughly to mirror one complete thought from one person. I'm not  splitting ideas mid-sentence or merging two people's opinions into one blob.
As for overlap, I chose like ~20–25% overlap. I think that's enough to preserve boundary context without making chunks nearly identical to each other, which would bloat index and confuse retrieval. Everything is experimental right now, can come back to tune these 2 as required.

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
| 1 | In the source set, which location is described as safer for no-car grad students: Eastwood or the Med Center? | Med Center. A complete answer must also mention that this option depends on METRO rail/bus commuting, especially for late-night travel. |
| 2 | Name two concrete Cullen Oaks problems that are explicitly reported in the corpus. | Any two of the following are required for full credit: delayed maintenance response (including AC), surprise/extra administrative fees, and parking-garage/security concerns such as bike theft. |
| 3 | Given corpus figures (about $1,800 monthly stipend and roughly $1,300-$2,000+ for Midtown/Montrose 1-bedroom rent), is living alone there supported? | No. A correct answer must conclude that solo living is generally not affordable and suggest roommate/shared housing as the practical option. |
| 4 | Which two UH safety resources are explicitly named for returning home after dark? | Cougar Ride and UHPD escort/walking escort service. |
| 5 | In the Lofts vs shared off-campus comparison, which option is usually lower monthly cost and what caveat must be included for each? | Shared off-campus is usually lower monthly cost. Required caveats: off-campus has variable utilities (notably high summer electricity), while Lofts has higher rent but bundled utilities and no required meal plan. |
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
- AI tool: Copilot Chat (GPT-5.3-Codex).
- Input to AI: Domain + Documents + Chunking Strategy sections from this file.
- Pipeline components to implement: source ingest scripts using `requests` + `BeautifulSoup`; document cleaning; `chunk_text()` with `RecursiveCharacterTextSplitter`; metadata schema with `source`, `url`, `doc_id`, `chunk_id`.
- Expected output: `ingest.py` and chunked JSONL in `documents/`.
- Verification: Run on at least 3 sources, then confirm chunk size/overlap and that each chunk has URL-linked metadata.

**Milestone 4 — Embedding and retrieval:**
- AI tool: Copilot Chat (GPT-5.3-Codex).
- Input to AI: Retrieval Approach + Evaluation Plan sections.
- Pipeline components to implement: embedding with `sentence-transformers` (`all-MiniLM-L6-v2`), local ChromaDB index creation, `retrieve(query, k=5)` with scores + citations.
- Expected output: `index.py` and `retriever.py` that return top-k chunks with source metadata.
- Verification: For each of the 5 evaluation questions, top-5 results should include at least one chunk containing key answer evidence.

**Milestone 5 — Generation and interface:**
- AI tool: Copilot Chat (GPT-5.3-Codex).
- Input to AI: Architecture stage definitions + citation rules + Evaluation Plan.
- Pipeline components to implement: answer generation module that uses retrieved chunks only, includes citations in output, and falls back with uncertainty language when evidence is weak.
- Expected output: `app.py` CLI loop (`ask question -> retrieve -> generate -> cite sources`).
- Verification: Run all 5 test questions and mark pass/fail by checking factual match to expected answers plus citation presence.
