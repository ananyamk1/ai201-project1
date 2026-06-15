# Demo Video Script — The Unofficial Guide (≈4–5 min)

> Before recording: in the terminal run `python app.py`, open http://localhost:7860,
> and have your README open in another tab for the last part. The app has two tabs:
> **Ask** and **Chat**. Leave top-k at 5 to start.

---

## 0:00 — Intro (~25 sec)

**[DO: App open on the "Ask" tab, nothing typed yet.]**

> "Hey, so this is The Unofficial Guide — a little RAG system I built that answers questions
> about off-campus housing at the University of Houston. Basically the stuff UH won't tell
> you officially: is a neighborhood safe, can you afford rent on a grad stipend, which
> apartments have shady management. It's built from real Reddit threads, resident reviews,
> and official UH and METRO pages, and the key thing — it only answers from those sources
> and shows you exactly where every answer came from. Let me show you."

---

## 0:25 — Query 1: works really well (~45 sec)

**[DO: Type into the question box and hit Ask:]**
`What hidden fees or management issues should I look out for at Cullen Oaks?`

**[DO: Point at the answer.]**

> "Okay this one it nails — surprise room checks, random fees, utilities not included,
> pests, paper-thin walls. And see these little numbers in brackets? Those are citations."

**[DO: Scroll to the "Sources" list and point at it.]**

> "And down here are the sources — this isn't the AI making it up, my code builds this list
> from the actual chunks it pulled, so it's the real ApartmentRatings reviews with the link.
> Retrieval and generation both just work here."

---

## 1:10 — Query 2: show the receipts (~45 sec)

**[DO: Clear the box, type, hit Ask:]**
`I'm an international grad student with no car. Is Eastwood or the Med Center safe to commute from?`

**[DO: Let it answer, point at it.]**

> "Here it's pulling straight from students — Eastwood's safe, someone lived there four years,
> three-minute metro ride. Med Center's super safe, especially gated spots."

**[DO: Open the "Retrieved context" drop-down.]**

> "And if you want to see under the hood, this drop-down shows the exact chunks it retrieved
> with their distance scores. So you can literally see what the answer was grounded in."

---

## 1:55 — Query 3: where it struggles (~55 sec)

**[DO: Clear the box, type, hit Ask:]**
`I have late-night labs and no car. How do I get back to my apartment safely after dark?`

**[DO: Read it, give an honest "eh" face.]**

> "So this one's a partial fail and I want to be honest about it. It tells me Cougar Ride,
> pepper spray, contact police — helpful, sure. But the actual official answer is UH's UHPD
> security escort, where an officer walks you, and that's in my data — it just didn't show up."

**[DO: Open the "Retrieved context" drop-down, point at the mostly-Reddit chunks.]**

> "And here's why — it's a vocabulary mismatch in the embedding stage. I said 'get home after
> dark,' but the official page calls it a 'security escort,' and the model doesn't know those
> are the same thing, so that chunk misses the top five. I'll come back to this in a sec."

---

## 2:50 — Bonus features (~55 sec)

> "Real quick, I also added a few extra things."

**[DO: Still on Ask tab. Type a keyword query, flip "Retrieval mode" to `hybrid`, hit Ask:]**
`student Q-Card METRO discount`

> "First, hybrid search — this mixes old-school keyword matching with the vector search, so
> exact terms like 'Q-Card' get caught even when the meaning's fuzzy. It also fixes that
> escort problem from before if you actually use the word 'escort.'"

**[DO: Change "Filter by source" to `ApartmentRatings`, re-ask the Cullen Oaks question.]**

> "I can also filter by source — like, only show me apartment reviews, nothing else. Watch
> the retrieved chunks change."

**[DO: Click the "Chat" tab. Type and send:]**
`Can I afford a 1-bed in Midtown on a grad stipend?`
**[DO: After it answers, send a follow-up that does NOT repeat the topic:]**
`what about with a roommate?`

> "And there's a chat mode that remembers context. See — I ask about Midtown, then just say
> 'what about with a roommate,' and it knows I'm still talking about affording rent. That's
> real memory, not a coincidence."

---

## 3:45 — Evaluation report walkthrough (~50 sec)

**[DO: Switch to the README tab, scroll to the "Evaluation Report" table.]**

> "Last thing — my evaluation. I ran all five test questions and graded them honestly. The
> Cullen Oaks one was fully accurate. A few are partially accurate — like affordability, it
> knew rent was high but didn't quite say 'get a roommate,' and the late-night safety one we
> just saw. Each row has the question, what I expected, what it said, and my judgment."

**[DO: Scroll to the "Failure Case Analysis" section.]**

> "And right here's the full failure writeup — that late-night question, why it broke at the
> embedding stage, and how I'd fix it: query expansion or the hybrid search I just showed."

---

## 4:35 — Wrap (~10 sec)

> "So yeah — that's The Unofficial Guide. Grounded answers, real citations, and honest about
> what it doesn't know. Thanks for watching!"

**[DO: Stop recording.]**
