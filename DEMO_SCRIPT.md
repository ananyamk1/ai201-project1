# Demo Video Script — The Unofficial Guide (≈4 min)

> Before recording: in the terminal run `python app.py`, open http://localhost:7860,
> and have your README open in another tab for the last part. Leave the top-k slider at 5.

---

## 0:00 — Intro (~25 sec)

**[DO: Have the app open on screen, nothing typed yet.]**

> "Hey, so this is The Unofficial Guide — it's a little RAG system I built that answers
> questions about off-campus housing at the University of Houston. The whole point is the
> stuff UH won't tell you officially: is a neighborhood actually safe, can you afford rent
> on a grad stipend, which apartments have shady management. It's built from real Reddit
> threads, resident reviews, and official UH and METRO pages. And the key thing — it only
> answers from those sources, and it shows you exactly where every answer came from. Let me
> just show you."

---

## 0:25 — Query 1: works really well (~50 sec)

**[DO: Type this into the question box and hit Ask:]**
`What hidden fees or management issues should I look out for at Cullen Oaks?`

**[DO: Wait for the answer, then point at the answer text as you talk.]**

> "Okay so this one it nails. It's telling me about surprise room checks, getting charged
> fees out of nowhere, utilities not being included, pests, paper-thin walls, management
> that turns over constantly. And see these little numbers in brackets? Those are inline
> citations."

**[DO: Scroll down to the "Sources:" list and point at it.]**

> "And down here is the Sources list — this isn't the AI making it up, my code builds this
> from the actual chunks it pulled, so it's the real ApartmentRatings reviews with the link.
> This is the kind of answer where retrieval and generation both just work — specific, on
> topic, and I can trace every claim back to a real review."

---

## 1:15 — Query 2: another good one, show the receipts (~45 sec)

**[DO: Clear the box, type this, hit Ask:]**
`I'm an international grad student with no car. Is Eastwood or the Med Center safe to commute from?`

**[DO: Let it answer, point at the answer.]**

> "So here it's pulling from actual students — Eastwood's apparently safe, someone lived
> there four years, and it's like a three-minute metro ride to campus. Med Center's super
> safe, especially the gated spots. Notice it's careful too — it says these are individual
> opinions, not gospel."

**[DO: Open the "Retrieved context" drop-down at the bottom.]**

> "And if you want to see under the hood — this drop-down shows the exact chunks it
> retrieved and their distance scores. So you can literally see what the answer was grounded
> in. That's the transparency I wanted."

---

## 2:00 — Query 3: where it struggles (~60 sec)

**[DO: Clear the box, type this, hit Ask:]**
`I have late-night labs and no car. How do I get back to my apartment safely after dark?`

**[DO: Let it answer. Read it, then give an honest "eh" face.]**

> "Okay so this one is interesting because it's a partial fail, and I want to be honest
> about it. It tells me to use the Cougar Ride shuttle, carry pepper spray, contact police,
> stick together — which, fine, that's helpful. But the actual official answer is UH's UHPD
> security escort service, where you literally call them and an officer walks you, and that's
> in my data. It just didn't show up here."

**[DO: Open the "Retrieved context" drop-down and point at the chunks — mostly Reddit.]**

> "And here's why — look at what got retrieved, it's mostly Reddit chatter. The reason is a
> vocabulary mismatch in the embedding stage. I asked it 'get home safely after dark,' but
> the official page calls it a 'security escort' and an 'after-hours shuttle.' The embedding
> model doesn't know those mean the same thing, so the official chunk doesn't make the top
> five. I actually tested this — if I search using the words 'security escort,' that exact
> chunk jumps to number one. So the data's there, the model just can't connect casual
> wording to official wording. That's my main failure case, and it's all written up in the
> README."

---

## 3:00 — Bonus: it knows when to shut up (~25 sec)

**[DO: Clear the box, type something off-topic, hit Ask:]**
`Which grocery stores near UH deliver and do they offer student discounts?`

**[DO: Point at the "I don't have enough information" response.]**

> "And real quick — this is the part I'm proud of. My documents don't cover grocery
> delivery, so instead of making up something that sounds right, it just says 'I don't have
> enough information on that.' No fake answer, no fake sources. That's the grounding doing
> its job."

---

## 3:25 — Evaluation report walkthrough (~50 sec)

**[DO: Switch to the README tab, scroll to the Evaluation Report table.]**

> "Last thing — my evaluation. I ran all five of my test questions through the system and
> graded them honestly. The Cullen Oaks one was fully accurate. A few are partially
> accurate — like the affordability one, it knew rent was high but didn't quite land the
> 'you need a roommate' conclusion, and the late-night safety one we just saw. Each row has
> the question, what I expected, what it actually said, and my judgment."

**[DO: Scroll down to the Failure Case Analysis section.]**

> "And right below that is the full failure case writeup — the late-night safety question,
> why it broke at the embedding stage, and how I'd fix it: query expansion, or a hybrid
> keyword-plus-vector search, or a model that actually knows the domain vocabulary."

---

## 4:15 — Wrap (~15 sec)

> "So yeah — that's The Unofficial Guide. Grounded answers, real citations, and it's honest
> about what it doesn't know. Thanks for watching!"

**[DO: Stop recording.]**
