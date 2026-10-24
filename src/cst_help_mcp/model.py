"""The Document model (ADR 0007).

Readers parse each Source into Documents of typed blocks. The model is persisted
next to each rendered Markdown file, and both the Markdown and the search records
are rendered from it, never from raw source markup.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

BlockKind = Literal["heading", "paragraph", "note", "list", "field", "code", "table", "api_signature"]
LinkStatus = Literal["unresolved", "resolved", "external", "outside"]
NavTree = Literal["toc", "keywords"]  # the table of contents and the author keyword index
# The Document kinds that hold code rather than prose; the Library's readers add theirs.
CODE_KINDS: frozenset[str] = frozenset()
# Joins the names of a table-of-contents path ("3D Simulation > Solvers") or a sub-keyword.
SEPARATOR = " > "

# A link's span in a block's text: ``[label](@N)``, N indexing Document.links. The label is
# Markdown-escaped, so the text stays valid Markdown and the target can change without re-parsing.
_LINK_SPAN = re.compile(r"\[((?:\\.|[^\\\]])*)\]\(@(\d+)\)")
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


def escape_label(label: str) -> str:
    """A link label escaped for Markdown."""
    return _LABEL_SPECIALS.sub(r"\\\1", label)


def link_span(label: str, index: int) -> str:
    return f"[{escape_label(label)}](@{index})"


def replace_links(text: str, replace: Callable[[str, int], str]) -> str:
    """Replace each link span by ``replace(label, index)``; the label is unescaped."""
    return _LINK_SPAN.sub(lambda m: replace(_ESCAPED.sub(r"\1", m[1]), int(m[2])), text)


def link_spans(text: str) -> list[tuple[str, int]]:
    """The label, unescaped, and the index of each link span in the text."""
    return [(_ESCAPED.sub(r"\1", m[1]), int(m[2])) for m in _LINK_SPAN.finditer(text)]


def plain(text: str) -> str:
    """Text with its link spans reduced to their labels."""
    return replace_links(text, lambda label, _: label)


@dataclass
class Block:
    kind: BlockKind
    text: str = ""
    level: int = 0
    items: list[str] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)
    # Each table cell's [rowspan, colspan], only for a table with merged cells.
    spans: list[list[list[int]]] = field(default_factory=list)
    language: str = ""
    term: str = ""  # a field definition's field name; its description is the text

    def plain_text(self) -> str:
        """The block's text without markup, for indexing."""
        if self.kind == "list":
            return "\n".join(plain(item) for item in self.items)
        if self.kind == "table":
            return "\n".join(" ".join(plain(cell) for cell in row) for row in self.rows)
        if self.kind == "field":
            return f"{self.term}\n{plain(self.text)}".strip()
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
    aliases: list[str] = field(default_factory=list)  # other source paths of the same Document
    # The Areas of Aliases published in other projects; searches narrowed to them find the Document.
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
    generated: bool = False  # written in an agent session, such as a Guide (ADR 0010)
    heuristic: bool = False  # found by the build's heuristics, such as Usages (ADR 0012)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Document:
        sections = [
            Section(
                anchors=s["anchors"],
                heading_path=s["heading_path"],
                blocks=[Block(**b) for b in s["blocks"]],
            )
            for s in data["sections"]
        ]
        entries = [ApiEntry(**e) for e in data["api_entries"]]
        links = [Link(**link) for link in data["links"]]
        fields = {k: v for k, v in data.items() if k not in ("sections", "api_entries", "links")}
        return cls(**fields, sections=sections, api_entries=entries, links=links)


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
