"""Reader for the PDF manuals: the text of every page, extracted with pypdf (ADR 0014).

The PDF itself is copied into the tree as it is, and its text companion beside it holds one Section
per physical page, anchored ``page-<n>``. Agents grep the text to find the page, then open the PDF
at that page when its layout or a figure matters. No OCR (ADR 0006): a PDF without a text layer
fails.
"""

from __future__ import annotations

import re
from pathlib import Path

from pypdf import PdfReader

from cst_help_mcp.locator import page_anchor
from cst_help_mcp.model import Block, Document, Section

# Word writes its symbol-font characters to the Unicode private-use area, where pypdf leaves them.
# The Ribbon Paths' arrow becomes ">", as the help writes it, and the bullets become "•"; other
# symbols, mostly Greek letters in equations, stay as they are.
_SYMBOL_FONT = str.maketrans({0xF0F0: ">", 0xF06F: "•", 0xF0A7: "•", 0xF0B7: "•"})


def read_manual(pdf: Path, *, source_path: str, locator: str, area: str, release: str) -> Document:
    """A manual as a Document of its pages, each page's text lines a paragraph."""
    reader = PdfReader(pdf)
    sections = []
    for n, page in enumerate(reader.pages, start=1):
        text = page.extract_text().translate(_SYMBOL_FONT)
        lines = (_escaped(" ".join(line.split())) for line in text.splitlines())
        blocks = [Block("paragraph", line) for line in lines if line]
        anchor = page_anchor(n)
        sections.append(Section([anchor], [anchor], [Block("heading", anchor, level=2), *blocks]))
    if not any(len(section.blocks) > 1 for section in sections):
        raise ValueError("the PDF has no text layer, and it is not read by OCR")
    title = (reader.metadata.title if reader.metadata else None) or pdf.stem
    return Document(
        kind="manual",
        release=release,
        area=area,
        locator=locator,
        source_path=source_path,
        title=title,
        sections=sections,
        pages=len(reader.pages),
        original=locator.removesuffix(".md"),
    )


def _escaped(text: str) -> str:
    """Text with each dollar escaped, so that a Markdown renderer doesn't take it for math; and each
    ``<`` that could open a tag."""
    return re.sub(r"(\$|<(?=[A-Za-z/!?]))", r"\\\1", text)
