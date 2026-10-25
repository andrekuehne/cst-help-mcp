"""The Document model (ADR 0007).

Readers parse each Source into Documents of typed blocks, and the Markdown is rendered
from them, never from raw source markup. The model is not persisted: a build re-parses.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal

BlockKind = Literal[
    "heading",
    "paragraph",
    "note",
    "admonition",
    "list",
    "field",
    "code",
    "table",
    "figure",
    "api_signature",
    "equation",
]
LinkStatus = Literal["unresolved", "resolved", "external", "outside"]
# A figure, a small inline icon, or an equation that exists only as an image (not transcribed, ADR 0006).
AssetKind = Literal["figure", "icon", "equation"]
NavTree = Literal["toc", "keywords"]  # the table of contents and the author keyword index
# The Document kinds that hold code rather than prose; the Library's readers add theirs.
CODE_KINDS: frozenset[str] = frozenset()
# Joins the names of a table-of-contents path ("3D Simulation > Solvers") or a sub-keyword.
SEPARATOR = " > "

# A link's span in a block's text: ``[label](@N)``, N indexing Document.links. The label is
# Markdown-escaped, so the text stays valid Markdown and the target can change without re-parsing.
_LINK_SPAN = re.compile(r"\[((?:\\.|[^\\\]])*)\]\(@(\d+)\)")
# An image's span: ``![alt](^N)``, N indexing Document.images, with the alt text as written.
_IMAGE_SPAN = re.compile(r"!\[((?:\\.|[^\\\]])*)\]\(\^(\d+)\)")
# A formula's span: its TeX as written, between private-use characters that no source text holds,
# U+E000 and U+E001 for inline math, U+E002 and U+E003 for display math. Nothing escapes inside it.
_MATH_SPAN = re.compile("([\ue000\ue002])([^\ue000-\ue003]*)[\ue001\ue003]")
_WHOLE_MATH_SPAN = re.compile("([\ue000\ue002][^\ue000-\ue003]*[\ue001\ue003])")
_DISPLAY_SPAN = re.compile("\ue002([^\ue000-\ue003]*)\ue003")
_ESCAPED = re.compile(r"\\(.)")
_LABEL_SPECIALS = re.compile(r"([\\\[\]])")


@dataclass
class Link:
    """A link as written in the source, and where it leads once the build has resolved it.

    ``href`` is a URL, or a path relative to the release folder with an optional ``#fragment``.
    ``target`` is the Locator it resolved to, with an anchor where the fragment matched one.
    """

    href: str
    status: LinkStatus = "unresolved"
    target: str = ""


@dataclass
class ImageRef:
    """An image as the source shows it, and the Asset it became once the build has read it.

    ``src`` is a path relative to the release folder. ``alt`` is the source's alt text, unless it
    only names a file. ``asset`` is the Asset's id, empty while the image is missing; ``file`` is
    the Asset's path in the Collection's tree, and ``caption`` the Asset's caption.
    """

    src: str
    alt: str = ""
    asset: str = ""
    kind: AssetKind = "figure"
    file: str = ""
    caption: str = ""

    @property
    def label(self) -> str:
        """The text an image is shown with: its alt text or its Asset's caption, and whether it is an
        equation that was not transcribed."""
        label = self.alt or self.caption
        if self.kind == "equation":
            return f"{label}; {kind_label(self.kind)}" if label else kind_label(self.kind)
        return label


def kind_label(kind: AssetKind) -> str:
    """How an Asset's kind is shown; an equation image says that it was not transcribed (ADR 0006)."""
    return "equation image, not transcribed" if kind == "equation" else kind


@dataclass(frozen=True)
class UnpairedMath:
    """A math delimiter without a partner in its run of text, in a topic that loads MathJax, so it
    stays text; with the text around it."""

    delimiter: str
    context: str


@dataclass
class Asset:
    """An image, deduplicated by content, as a Build's tree holds it (see assets.py)."""

    id: str
    kind: AssetKind
    caption: str  # the first alt text a Document gives it; for an icon, else its file's name
    width: int
    height: int
    file: str  # the path in the Collection's tree
    served: str  # the file itself, or its copy scaled for clients that limit an image's size
    served_width: int
    served_height: int
    sources: list[str] = field(default_factory=list)  # paths relative to the release folder
    documents: list[str] = field(default_factory=list)  # Locators of the Documents that show it


def escape_label(label: str) -> str:
    """A link label escaped for Markdown."""
    return _LABEL_SPECIALS.sub(r"\\\1", label)


def link_span(label: str, index: int) -> str:
    return f"[{escape_label(label)}](@{index})"


def image_span(alt: str, index: int) -> str:
    return f"![{escape_label(alt)}](^{index})"


def replace_images(text: str, replace: Callable[[str, int], str]) -> str:
    """Replace each image span by ``replace(alt, index)``; the alt text is unescaped."""
    return _IMAGE_SPAN.sub(lambda m: replace(_ESCAPED.sub(r"\1", m[1]), int(m[2])), text)


def image_spans(text: str) -> list[tuple[str, int]]:
    """The alt text, unescaped, and the index of each image span in the text."""
    return [(_ESCAPED.sub(r"\1", m[1]), int(m[2])) for m in _IMAGE_SPAN.finditer(text)]


def replace_links(text: str, replace: Callable[[str, int], str]) -> str:
    """Replace each link span by ``replace(label, index)``; the label is unescaped."""
    return _LINK_SPAN.sub(lambda m: replace(_ESCAPED.sub(r"\1", m[1]), int(m[2])), text)


def link_spans(text: str) -> list[tuple[str, int]]:
    """The label, unescaped, and the index of each link span in the text."""
    return [(_ESCAPED.sub(r"\1", m[1]), int(m[2])) for m in _LINK_SPAN.finditer(text)]


def math_span(tex: str, display: bool) -> str:
    return f"\ue002{tex}\ue003" if display else f"\ue000{tex}\ue001"


def replace_math(text: str, replace: Callable[[str, bool], str]) -> str:
    """Replace each math span by ``replace(tex, display)``."""
    return _MATH_SPAN.sub(lambda m: replace(m[2], m[1] == "\ue002"), text)


def split_math(text: str) -> list[str]:
    """The text split at its math spans: text and spans alternate, starting with text."""
    return _WHOLE_MATH_SPAN.split(text)


def split_display(text: str) -> list[str]:
    """The text split at its display math: text and the TeX of each displayed formula alternate,
    starting and ending with text."""
    return _DISPLAY_SPAN.split(text)


def tex_delimited(tex: str, display: bool) -> str:
    """A formula as Markdown math: ``$...$`` inline, ``$$...$$`` displayed.

    Markdown takes ``$`` for inline math only when no space follows the opening one or precedes the
    closing one, so inline TeX loses the spaces at its ends, which TeX ignores anyway.
    """
    return f"$${tex}$$" if display else f"${tex.strip()}$"


def plain(text: str) -> str:
    """Text with its link spans reduced to their labels, its image spans to their alt text, and its
    math spans to their TeX between Markdown math delimiters."""
    text = replace_math(text, tex_delimited)
    return replace_links(replace_images(text, lambda alt, _: alt), lambda label, _: label)


@dataclass
class Block:
    kind: BlockKind
    text: str = ""
    level: int = 0  # a heading's level; a list's nesting, 0 for a list inside no other
    items: list[str] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)
    # Each table cell's [rowspan, colspan], only for a table with merged cells.
    spans: list[list[list[int]]] = field(default_factory=list)
    language: str = ""
    # A field definition's field name, its description being the text; or an admonition's title.
    term: str = ""
    blocks: list[Block] = field(default_factory=list)  # an admonition's content

    def images(self) -> list[int]:
        """The index into its Document's images of each image the block shows, in order."""
        if self.kind in ("code", "api_signature", "equation"):
            return []  # code and an equation's TeX are verbatim, never spans
        texts = [self.term, self.text, *self.items, *(cell for row in self.rows for cell in row)]
        own = [index for text in texts for _, index in image_spans(text)]
        return own + [index for block in self.blocks for index in block.images()]

    def plain_text(self) -> str:
        """The block's text without markup, for indexing."""
        if self.kind == "admonition":
            return "\n".join([plain(self.term), *(block.plain_text() for block in self.blocks)])
        if self.kind == "list":
            return "\n".join(plain(item) for item in self.items)
        if self.kind == "table":
            return "\n".join(" ".join(plain(cell) for cell in row) for row in self.rows)
        if self.kind == "field":
            return f"{plain(self.term)}\n{plain(self.text)}".strip()
        if self.kind == "equation":
            return tex_delimited(self.text, True)
        return plain(self.text)


@dataclass
class Section:
    anchors: list[str]
    heading_path: list[str]
    blocks: list[Block] = field(default_factory=list)

    @property
    def anchor(self) -> str | None:
        return self.anchors[0] if self.anchors else None


@dataclass
class ApiEntry:
    """A documented object or member, identified by its Area plus qualified name."""

    qualified_name: str
    object_name: str | None
    member_name: str | None
    signature: str
    description: str
    anchor: str


@dataclass
class Document:
    kind: str
    release: str
    area: str
    locator: str
    source_path: str
    title: str
    sections: list[Section] = field(default_factory=list)
    api_entries: list[ApiEntry] = field(default_factory=list)
    links: list[Link] = field(default_factory=list)
    images: list[ImageRef] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)  # other source paths of the same Document
    # The Areas of Aliases published in other projects.
    alias_areas: list[str] = field(default_factory=list)
    # Every id and name the source declares, so link fragments are checked beyond Section anchors.
    source_anchors: list[str] = field(default_factory=list)
    # Table-of-contents paths ("3D Simulation > Solvers > ..."), from the table of contents or,
    # for a Document in none, from its breadcrumbs.
    toc_paths: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)  # author keywords, a sub-keyword as "Key > Sub"
    context_ids: list[str] = field(default_factory=list)  # context-help map ids
    # The breadcrumb paths embedded in the source, relative to its own project's table of contents.
    breadcrumbs: list[str] = field(default_factory=list)
    unpaired_math: list[UnpairedMath] = field(default_factory=list)
    # Folders of the tree where its Markdown is also written, so that a grep confined to its Area's
    # folder finds a Document whose Locator lies outside it.
    copied_to: list[str] = field(default_factory=list)
    generated: bool = False  # written in an agent session, such as a Guide (ADR 0010)
    heuristic: bool = False  # found by the build's heuristics, such as Usages (ADR 0012)


@dataclass
class NavNode:
    """A table-of-contents entry or a keyword index entry.

    A book or a keyword holds children; an entry that leads to a topic has an ``href`` (relative
    to the release folder) until the build resolves it to a Document's ``locator``. A keyword's
    children are its topics, then its sub-keywords.
    """

    name: str
    href: str | None = None
    locator: str | None = None
    children: list[NavNode] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "locator": self.locator,
            "children": [child.to_dict() for child in self.children],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NavNode:
        return cls(
            data["name"], locator=data["locator"], children=[cls.from_dict(c) for c in data["children"]]
        )
