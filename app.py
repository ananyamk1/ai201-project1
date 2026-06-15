"""Entry point for the Gradio UI.

Run from the project root with either:
    python app.py
    python -m src.app

This thin launcher exists so `python app.py` works: it imports the app from the
`src` package (which keeps the relative imports between src modules valid) and
launches it. Running `python src/app.py` directly fails, because executing a file
inside a package as a script breaks `from .generate import ...`.
"""

from src.app import build_app

if __name__ == "__main__":
    build_app().launch()
