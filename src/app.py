"""Stage 5 (interface): Gradio app for The Unofficial Guide.

A question goes in; a grounded answer comes out with a programmatically-built
Sources list and an expandable view of the exact retrieved chunks (so a grader
can see what the answer was grounded in). All generation goes through
src/generate, which enforces the grounding rules.

Two tabs:
  - "Ask"  — single-question mode, with a retrieval-mode toggle (vector vs
             hybrid BM25+vector) and a source filter (metadata filtering).
  - "Chat" — conversational mode that remembers the previous turns.

Run:
    python -m src.app          # then open the printed local URL
"""

from __future__ import annotations

import gradio as gr

from .generate import answer, answer_chat
from .retrieve import DEFAULT_K

EXAMPLES = [
    "I'm an international grad student with no car. Is it safe to live in Eastwood or the Med Center and commute to UH?",
    "What hidden fees or management issues should I look out for at Cullen Oaks?",
    "Can I afford a 1-bed in Midtown or Montrose on a UH grad stipend?",
    "I have late-night labs and no car. How do I get home safely after dark?",
    "Is it cheaper to live at the University Lofts or split an off-campus apartment?",
]

# Values match the "source" metadata stored on each chunk (see sources.json).
SOURCES = ["All sources", "Reddit", "Official UH", "ApartmentRatings", "Transit/Map"]


def _src(choice: str) -> str | None:
    return None if choice == "All sources" else choice


def _format_answer(out: dict) -> str:
    md = out["answer"]
    if out["sources"]:
        md += "\n\n---\n" + out["sources"].replace("\n", "  \n")
    return md


def _format_chunks(out: dict) -> str:
    rows = []
    for i, h in enumerate(out["hits"], 1):
        # vector hits have a cosine distance; hybrid hits report an RRF score.
        score = (f"distance={h['distance']:.3f}" if h.get("distance") is not None
                 else f"rrf={h.get('score')}  found_by={h.get('found_by', '?')}")
        rows.append(
            f"**[{i}]** `{score}` · #{h['num']} {h['source']} "
            f"({h['doc_id']} seg {h['segment_index']})\n\n> {h['text']}"
        )
    return "\n\n---\n\n".join(rows)


def respond(query: str, k: int, source: str, mode: str):
    query = (query or "").strip()
    if not query:
        return "Ask a question about UH off-campus housing, safety, transit, or cost.", ""
    out = answer(query, int(k), mode=mode, source=_src(source))
    return _format_answer(out), _format_chunks(out)


def chat_fn(message, history, k, source, mode):
    message = (message or "").strip()
    if not message:
        return history or [], ""
    history = history or []
    out = answer_chat(history, message, int(k), mode=mode, source=_src(source))
    reply = _format_answer(out)
    history = history + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": reply},
    ]
    return history, ""


def build_app() -> gr.Blocks:
    with gr.Blocks(title="The Unofficial Guide — UH Off-Campus Housing") as demo:
        gr.Markdown(
            "# The Unofficial Guide\n"
            "Ask about **off-campus housing, safety, transit, and cost** at the "
            "University of Houston, built from student threads, resident reviews, and official "
            "UH/METRO pages. Answers come **only** from retrieved sources; if the corpus doesn't "
            "cover it, the guide will say so."
        )

        with gr.Tab("Ask"):
            with gr.Row():
                query = gr.Textbox(
                    label="Your question", scale=4,
                    placeholder="e.g. Is the Medical Center safe to commute from without a car?",
                )
                k = gr.Slider(1, 10, value=DEFAULT_K, step=1, label="Chunks retrieved (top-k)", scale=1)
            with gr.Row():
                source = gr.Dropdown(SOURCES, value="All sources", label="Filter by source", scale=1)
                mode = gr.Radio(["vector", "hybrid"], value="vector",
                                label="Retrieval mode (hybrid = BM25 + vector)", scale=2)
            ask = gr.Button("Ask", variant="primary")
            answer_box = gr.Markdown(label="Answer")
            with gr.Accordion("Retrieved context (what the answer is grounded in)", open=False):
                chunks_box = gr.Markdown()
            gr.Examples(examples=EXAMPLES, inputs=query)

            ask.click(respond, [query, k, source, mode], [answer_box, chunks_box])
            query.submit(respond, [query, k, source, mode], [answer_box, chunks_box])

        with gr.Tab("Chat (remembers context)"):
            gr.Markdown(
                "Conversational mode — follow-ups like *\"what about Montrose?\"* or "
                "*\"is that one safe?\"* use the earlier turns for context."
            )
            chatbot = gr.Chatbot(type="messages", height=380)
            with gr.Row():
                chat_msg = gr.Textbox(label="Message", scale=4, placeholder="Ask a follow-up...")
                chat_send = gr.Button("Send", variant="primary", scale=1)
            with gr.Row():
                chat_k = gr.Slider(1, 10, value=DEFAULT_K, step=1, label="top-k")
                chat_source = gr.Dropdown(SOURCES, value="All sources", label="Filter by source")
                chat_mode = gr.Radio(["vector", "hybrid"], value="vector", label="Retrieval mode")
            chat_clear = gr.Button("Clear conversation")

            chat_inputs = [chat_msg, chatbot, chat_k, chat_source, chat_mode]
            chat_send.click(chat_fn, chat_inputs, [chatbot, chat_msg])
            chat_msg.submit(chat_fn, chat_inputs, [chatbot, chat_msg])
            chat_clear.click(lambda: ([], ""), None, [chatbot, chat_msg])

    return demo


if __name__ == "__main__":
    build_app().launch()
