"""
Stage 2 of the pipeline: splitting documents into chunks.

⚠️ THIS IS THE FILE YOU CHANGE IN MILESTONE 3.

`split_documents` below is deliberately plain. It cuts every document into
fixed-size pieces with a fixed overlap and pays no attention to where sentences
or paragraphs end. It works, and it is not good.

On a corpus of short posts it may not cut anything at all: `campus_life` comes
out as 88 documents and 88 chunks, because almost nothing in it reaches 800
characters. That is the baseline, not a bug — Milestone 3 is where you decide
whether one post should stay one chunk.

Your job in Milestone 3 is to replace the *body* of `split_documents` with a
strategy that fits the documents you actually read in Milestone 1. Keep the
name and the shape of what it returns — the rest of the pipeline calls it, and
your README has to name the function that produced your chunks.

If you get stuck for 30 minutes, `fallback_split` is the original. Switch back
to it, write down what you saw, and move on. That's a real observation about
your pipeline, not giving up.
"""

import re
from dataclasses import dataclass

import config
from ingest import Document


@dataclass
class Chunk:
    """One piece of one document."""

    text: str
    source: str        # which file it came from
    index: int         # which chunk within that file, starting at 0
    produced_by: str   # the function that made it — cite this in your README

    @property
    def label(self) -> str:
        return f"{self.source}#{self.index}"


def fallback_split(
    documents: list[Document],
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[Chunk]:
    """
    The starter's original chunker. Fixed-size character windows with overlap.

    Keep this function. Milestone 3's stop rule points back at it, and having
    something to compare your own strategy against is useful in unit 2.
    """
    chunk_size = chunk_size or config.CHUNK_SIZE
    overlap = overlap or config.CHUNK_OVERLAP

    if overlap >= chunk_size:
        raise ValueError("overlap has to be smaller than chunk_size")

    chunks: list[Chunk] = []
    for doc in documents:
        start = 0
        index = 0
        while start < len(doc.text):
            piece = doc.text[start : start + chunk_size].strip()
            if piece:
                chunks.append(
                    Chunk(
                        text=piece,
                        source=doc.source,
                        index=index,
                        produced_by="chunker.py::fallback_split",
                    )
                )
                index += 1
            start += chunk_size - overlap

    return chunks


def _split_sentences(paragraph: str, limit: int) -> list[str]:
    """Break one over-long paragraph into pieces at sentence ends."""
    sentences = re.split(r"(?<=[.!?])\s+", paragraph)
    pieces: list[str] = []
    current = ""
    for sentence in sentences:
        if current and len(current) + 1 + len(sentence) > limit:
            pieces.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        pieces.append(current)
    return pieces


def _is_heading(paragraph: str) -> bool:
    """A markdown heading, or a short plain-text line like "Making the game shorter"."""
    if paragraph.startswith("#"):
        return True
    return (
        "\n" not in paragraph
        and len(paragraph) < 80
        and not paragraph.startswith("-")
        and not paragraph.endswith((".", "!", "?", ":", ")"))
    )


def split_documents(documents: list[Document]) -> list[Chunk]:
    """
    Split documents on paragraph breaks instead of character counts.

    A document that fits in CHUNK_SIZE stays whole — every campus_life post
    does, so that corpus still comes out as one chunk per document. Longer
    documents are packed paragraph by paragraph, a heading (`## ...`, or a
    short plain-text line with no full stop) always starts a new chunk, and only a single paragraph longer than CHUNK_SIZE is
    cut, at sentence ends. No sentence is ever split in half.

    Every chunk after a document's first starts with the document's title line
    (and its section heading, if any), so it still says what it's about when
    it's retrieved on its own. That replaces the fallback's character overlap.
    """
    limit = config.CHUNK_SIZE
    chunks: list[Chunk] = []

    for doc in documents:
        text = doc.text.strip()
        if not text:
            continue

        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        title = paragraphs[0] if len(paragraphs[0]) < 120 else ""

        pieces: list[str] = []
        heading = ""
        current: list[str] = []
        has_body = False   # a chunk made of only title/heading lines isn't worth keeping

        def flush() -> None:
            nonlocal has_body
            if has_body:
                pieces.append("\n\n".join(current))
                current.clear()
                has_body = False

        if len(text) <= limit:
            pieces = [text]
        else:
            for paragraph in paragraphs[1 if title else 0 :]:
                if _is_heading(paragraph):
                    flush()
                    heading = paragraph
                    current[:] = [p for p in (title, heading) if p]
                    continue

                for part in _split_sentences(paragraph, limit):
                    size = sum(len(p) + 2 for p in current) + len(part)
                    if has_body and size > limit:
                        flush()
                    if not current:
                        current.extend(p for p in (title, heading) if p)
                    current.append(part)
                    has_body = True
            flush()

        for index, piece in enumerate(pieces):
            chunks.append(
                Chunk(
                    text=piece,
                    source=doc.source,
                    index=index,
                    produced_by="chunker.py::split_documents",
                )
            )

    return chunks


def describe(chunks: list[Chunk]) -> str:
    """A one-line summary, printed after indexing."""
    if not chunks:
        return "0 chunks"
    lengths = [len(c.text) for c in chunks]
    return (
        f"{len(chunks)} chunks, "
        f"{sum(lengths) // len(lengths)} characters on average "
        f"(shortest {min(lengths)}, longest {max(lengths)}), "
        f"produced by {chunks[0].produced_by}"
    )


if __name__ == "__main__":
    from ingest import load_documents

    chunks = split_documents(load_documents())
    print(describe(chunks))
