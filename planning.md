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

**Overlap:**

**Reasoning:**

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**

**Top-k:**

**Production tradeoff reflection:**

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

1.

2.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

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

**Milestone 5 — Generation and interface:**
