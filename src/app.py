"""Stage 5 (interface): Gradio app for The Unofficial Guide.

A question goes in; a grounded answer comes out with a programmatically-built
Sources list and an expandable view of the exact retrieved chunks (so a grader
can see what the answer was grounded in). All generation goes through
src/generate.answer, which enforces the grounding rules.

Run:
    python -m src.app          # then open the printed local URL
"""

from __future__ import annotations

import gradio as gr

from .generate import answer
from .retrieve import DEFAULT_K

EXAMPLES = [
    "I'm an international grad student with no car. Is it safe to live in Eastwood or the Med Center and commute to UH?",
    "What hidden fees or management issues should I look out for at Cullen Oaks?",
    "Can I afford a 1-bed in Midtown or Montrose on a UH grad stipend?",
    "I have late-night labs and no car. How do I get home safely after dark?",
    "Is it cheaper to live at the University Lofts or split an off-campus apartment?",
]


def respond(query: str, k: int):
    query = (query or "").strip()
    if not query:
        return "Ask a question about UH off-campus housing, safety, transit, or cost.", ""
    out = answer(query, int(k))

    md = out["answer"]
    if out["sources"]:
        md += "\n\n---\n" + out["sources"].replace("\n", "  \n")

    # Transparency panel: the raw retrieved chunks + distances.
    retrieved = []
    for i, h in enumerate(out["hits"], 1):
        retrieved.append(
            f"**[{i}]** `distance={h['distance']:.3f}` · #{h['num']} {h['source']} "
            f"({h['doc_id']} seg {h['segment_index']})\n\n> {h['text']}"
        )
    return md, "\n\n---\n\n".join(retrieved)


def build_app() -> gr.Blocks:
    with gr.Blocks(title="The Unofficial Guide — UH Off-Campus Housing") as demo:
        gr.Markdown(
            "# The Unofficial Guide\n"
            "Ask about **off-campus housing, safety, transit, and cost** at the "
            "University of Houston, built from student threads, resident reviews, and official "
            "UH/METRO pages. Answers come **only** from retrieved sources; if the corpus doesn't "
            "cover it, the guide will say so."
        )
        with gr.Row():
            query = gr.Textbox(
                label="Your question", scale=4,
                placeholder="e.g. Is the Medical Center safe to commute from without a car?",
            )
            k = gr.Slider(1, 10, value=DEFAULT_K, step=1, label="Chunks retrieved (top-k)", scale=1)
        ask = gr.Button("Ask", variant="primary")
        answer_box = gr.Markdown(label="Answer")
        with gr.Accordion("Retrieved context (what the answer is grounded in)", open=False):
            chunks_box = gr.Markdown()

        gr.Examples(examples=EXAMPLES, inputs=query)

        ask.click(respond, inputs=[query, k], outputs=[answer_box, chunks_box])
        query.submit(respond, inputs=[query, k], outputs=[answer_box, chunks_box])
    return demo


if __name__ == "__main__":
    build_app().launch()
