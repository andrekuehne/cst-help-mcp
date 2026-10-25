"""Reading a Section or a Document: its Markdown exactly as the file holds it (ADR 0003), in pages.

The Markdown is cut where the parts it was rendered from meet, so each page ends at a line and
lists the links and images it shows.
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass

from cst_help_mcp.errors import KnowledgeBaseError
from cst_help_mcp.model import AssetKind, Document, Link, LinkStatus, kind_label
from cst_help_mcp.render import Part, render_parts

# Budgets are counted in characters at a pessimistic three characters per token.
CHARS_PER_TOKEN = 3
PAGE_CHARS = 8_000 * CHARS_PER_TOKEN  # a page's text and its lists of links and images
# The shortest piece a line is cut into, even when its links leave less room on a page.
_MIN_PIECE = 1_000


@dataclass(frozen=True)
class PageLink:
    label: str
    status: LinkStatus
    # The Locator of a resolved link, the URL of an external one, or else the path in the release
    # folder that the link names.
    target: str

    def __str__(self) -> str:
        return f"{self.label} -> {self.target} ({self.status})"


@dataclass(frozen=True)
class PageImage:
    """An image a page shows, by the id of its Asset, which cst_help_images returns."""

    asset: str
    kind: AssetKind
    caption: str

    def __str__(self) -> str:
        return f"{self.caption or 'no caption'} -> {self.asset} ({kind_label(self.kind)})"


@dataclass(frozen=True)
class Page:
    locator: str  # the Document's Locator, with the Section's anchor when one was read
    release: str
    area: str
    title: str
    source_path: str
    text: str
    links: list[PageLink]  # the outgoing links the page's text shows, in order
    images: list[PageImage]  # the images it shows, once each, in order; missing images are left out
    page: int  # counted from 1
    pages: int

    @property
    def next_cursor(self) -> str | None:
        """The cursor that reads the next page, or None on the last page."""
        return str(self.page + 1) if self.page < self.pages else None


# A link or an image a page lists, keyed so that the page lists it once.
_Entry = tuple[tuple[str, int | str], PageLink | PageImage]


@dataclass(frozen=True)
class _Piece:
    """A run of the Markdown that is never split across pages, and the links and images it shows."""

    start: int
    end: int
    entries: tuple[_Entry, ...]


def read_page(doc: Document, markdown: str, anchor: str | None, cursor: str | None) -> Page:
    """One page of a Section of a Document, or of the whole Document when no anchor is given.

    ``markdown`` is the Document's file, which must be what its model renders.
    """
    parts = render_parts(doc)
    if "".join(part.text for part in parts) != markdown:
        raise KnowledgeBaseError(f"The Markdown of {doc.locator} doesn't match its model; rebuild it")
    section = section_of(doc, anchor) if anchor else None
    locator = doc.locator if section is None else f"{doc.locator}#{doc.sections[section].anchor}"
    pieces = _pieces(parts, section, doc)
    pages = _paginate(pieces)
    number = _page_number(cursor, locator, len(pages))
    first, last = pages[number - 1]
    shown = pieces[first : last + 1]
    listed: dict[tuple[str, int | str], PageLink | PageImage] = {}
    for piece in shown:
        for key, entry in piece.entries:
            listed.setdefault(key, entry)
    return Page(
        locator,
        doc.release,
        doc.area,
        doc.title,
        doc.source_path,
        markdown[shown[0].start : shown[-1].end],
        [entry for entry in listed.values() if isinstance(entry, PageLink)],
        [entry for entry in listed.values() if isinstance(entry, PageImage)],
        number,
        len(pages),
    )


def section_of(doc: Document, anchor: str) -> int:
    """The index of the Section an anchor names: exactly, or else without regard to case."""
    anchors = {a: i for i, section in enumerate(doc.sections) for a in section.anchors}
    if anchor in anchors:
        return anchors[anchor]
    folded = {a.casefold(): i for a, i in anchors.items()}
    if anchor.casefold() in folded:
        return folded[anchor.casefold()]
    message = f"{doc.locator} has no Section '{anchor}'"
    nearest = difflib.get_close_matches(anchor, list(anchors), n=3)
    if nearest:
        message += f"; nearest: {', '.join(f'{doc.locator}#{a}' for a in nearest)}"
    raise KnowledgeBaseError(message + f"; read {doc.locator} for the whole Document")


def _pieces(parts: list[Part], section: int | None, doc: Document) -> list[_Piece]:
    """The Section's parts, or all of them, as pieces at their offsets in the Markdown.

    A part that doesn't fit on a page with its entries is split at its lines, and a line that
    doesn't fit at the length that does; every piece of a part shows all of the part's entries.
    """
    pieces: list[_Piece] = []
    offset = 0
    for part in parts:
        start, offset = offset, offset + len(part.text)
        if section is not None and part.section != section:
            continue
        entries = _entries(part, doc)
        room = max(_MIN_PIECE, PAGE_CHARS - _entries_cost(entries, set()))
        if len(part.text) <= room:
            pieces.append(_Piece(start, offset, entries))
            continue
        for line in part.text.splitlines(keepends=True):
            for cut in range(0, len(line), room):
                end = start + min(room, len(line) - cut)
                pieces.append(_Piece(start, end, entries))
                start = end
    return pieces


def _entries(part: Part, doc: Document) -> tuple[_Entry, ...]:
    links: list[_Entry] = [
        (("link", index), _page_link(label, doc.links[index])) for label, index in part.links
    ]
    images: list[_Entry] = [
        (("image", image.asset), PageImage(image.asset, image.kind, image.alt or image.caption))
        for image in (doc.images[index] for index in part.images)
        if image.asset
    ]
    return (*links, *images)


def _paginate(pieces: list[_Piece]) -> list[tuple[int, int]]:
    """The first and last piece of each page. A page takes pieces while its text and its lists of
    links and images stay within PAGE_CHARS, and always at least one."""
    pages: list[tuple[int, int]] = []
    first = 0
    size = 0
    listed: set[tuple[str, int | str]] = set()
    for i, piece in enumerate(pieces):
        if i > first and size + _cost(piece, listed) > PAGE_CHARS:
            pages.append((first, i - 1))
            first, size, listed = i, 0, set()
        size += _cost(piece, listed)
        listed.update(key for key, _ in piece.entries)
    pages.append((first, len(pieces) - 1))
    return pages


def _cost(piece: _Piece, listed: set[tuple[str, int | str]]) -> int:
    """The characters a piece adds to a page that already lists the entries ``listed``."""
    return piece.end - piece.start + _entries_cost(piece.entries, listed)


def _entries_cost(entries: tuple[_Entry, ...], listed: set[tuple[str, int | str]]) -> int:
    """The characters that listing the entries adds to a page that already lists ``listed``."""
    new = {key: entry for key, entry in entries if key not in listed}
    return sum(len(str(entry)) + 1 for entry in new.values())


def _page_number(cursor: str | None, locator: str, pages: int) -> int:
    if cursor is None:
        return 1
    if not cursor.isdecimal() or not 1 <= int(cursor) <= pages:
        plural = "s" if pages != 1 else ""
        raise KnowledgeBaseError(
            f"Cursor '{cursor}' is no page of {locator}, which has {pages} page{plural}: "
            "pass the cursor a page gave, or none for the first page"
        )
    return int(cursor)


def _page_link(label: str, link: Link) -> PageLink:
    target = link.target if link.status == "resolved" else link.href
    return PageLink(label, link.status, target)
