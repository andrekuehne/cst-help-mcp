"""Reader for the WinWrap Basic language reference, the RoboHelp import in ``sax_basic/ww_*.htm``.

Its topics have almost no block markup: the content is loose text and links separated by
``<br />``, and bold labels ("Syntax:", "Group:", "Parameter Description") open its parts. A
``<br />`` often sits inside the link that starts the next line (``<a href="..."><br />End</a>``),
so lines are split at every ``<br />`` in document order, wherever it is.

Its lists are import residue too: Word's autoformat took a line's leading ``v``, ``q`` or ``*``
for a bullet and its leading number for a numbered list's start, so ``vbOK 1 OK button`` reads
``bOK 1 OK button``. List items are read back as the lines they were, with what they lost.

A page with a syntax or a group documents one keyword or built-in, which becomes an API Entry
under its name as the title writes it, without its kind: ``Dir$ Function`` gives ``Dir$``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

from bs4 import BeautifulSoup, Tag
from bs4.element import CData, NavigableString, PageElement

from cst_help_mcp.links import normalise_href
from cst_help_mcp.locator import anchor_for
from cst_help_mcp.model import ApiEntry, Block, Document, Link, Section, link_span, plain
from cst_help_mcp.robohelp import breadcrumbs, content_nodes, source_anchors

_KIND = (
    r"(?:Function|Instruction|Definition|Statement|Data Type|Keyword|Object|Module|Sub|Prototype"
    r"|Operator|Comment|Assignment)"
)
# "Dir$ Function", "Clipboard Instruction/Function", "CheckBox Dialog Item Definition".
_TITLE = re.compile(rf"(.+?)\s+(?:Dialog Item\s+)?{_KIND}(?:/{_KIND})*")
_HEADINGS = frozenset(("h1", "h2", "h3", "h4", "h5", "h6"))
# What a bulleted line lost, by how the rest of it starts: the "v" of the vb constants and of the
# var and variantvar parameters, the "q" interval code, and the Like operator's "*".
_LOST_BULLETS = (
    (re.compile(r"b[A-Z]|ar\b|ariantvar\b"), "v"),
    (re.compile(r"quarter\b|insert quarter", re.IGNORECASE), "q "),
    (re.compile(r"Match zero or more characters"), "* "),
)


@dataclass
class _Ref:
    """Text inside a link."""

    text: str
    href: str


@dataclass
class _Line:
    """One line of a topic: text and links, perhaps opened by a bold label, or the title."""

    pieces: list[str | _Ref] = field(default_factory=list)
    label: str = ""  # the bold label that opens the line, without its colon
    title: bool = False
    listed: Literal["", "ul", "ol"] = ""  # the list the import turned the line into, if any

    def text(self) -> str:
        return "".join(p if isinstance(p, str) else p.text for p in self.pieces)

    @property
    def blank(self) -> bool:
        return not (self.label or self.title or self.text().replace("\xa0", " ").strip())


def entry_name(title: str) -> str | None:
    """The keyword or built-in a page's title names: ``Dir$ Function`` → ``Dir$``."""
    match = _TITLE.fullmatch(" ".join(title.split()))
    return match[1] if match else None


def read_winwrap_topic(html: str, *, source_path: str, locator: str, area: str, release: str) -> Document:
    soup = BeautifulSoup(html, "html.parser")
    title = " ".join(soup.title.get_text().split()) if soup.title else source_path.rsplit("/", 1)[-1]
    content = content_nodes(soup.body or soup)
    lines = _lines(content)
    documents_entry = any(line.label in ("Syntax", "Group") for line in lines)
    # The heading, not the <title>, names the entry: one <title> misspells its kind.
    heading = next((line.text() for line in lines if line.title), title)
    builder = _DocumentBuilder(title, source_path, entry_name(heading) if documents_entry else None)
    for line in lines:
        builder.add(line)
    builder.finish()
    return Document(
        kind="topic",
        release=release,
        area=area,
        locator=locator,
        source_path=source_path,
        title=title,
        sections=[s for s in builder.sections if s.blocks],
        api_entries=builder.entries,
        links=builder.links,
        source_anchors=source_anchors([node for node in content if isinstance(node, Tag)]),
        breadcrumbs=breadcrumbs(html),
    )


def _lines(content: list[PageElement]) -> list[_Line]:
    lines = [_Line()]

    def end() -> None:
        lines.append(_Line())

    def walk(node: PageElement, href: str | None, top: bool) -> None:
        # Comments and processing instructions are other string types.
        if isinstance(node, NavigableString):
            if type(node) in (NavigableString, CData):
                _append(lines[-1].pieces, str(node), href)
            return
        if not isinstance(node, Tag) or node.name in ("script", "style", "img"):
            return
        if node.name in ("br", "hr"):
            end()
        elif node.name == "b" and top and lines[-1].blank:
            lines[-1].label = " ".join(node.get_text().split()).rstrip(":")
        elif node.name == "h1":
            end()
            lines[-1].title = True
            lines[-1].pieces = [node.get_text()]
            end()
        elif node.name in ("ul", "ol"):
            end()
            for i, li in enumerate(node.find_all("li", recursive=False)):
                lines[-1].pieces = [_lost(node, i, li.get_text()), *_item(li)]
                lines[-1].listed = "ol" if node.name == "ol" else "ul"
                end()
        elif node.name in ("p", "div", *_HEADINGS):
            end()
            for child in node.children:
                walk(child, href, False)
            end()
        else:
            if node.name == "a" and node.get("href"):
                href = str(node["href"])
            for child in node.children:
                walk(child, href, False)

    for node in content:
        walk(node, None, True)
    return _rejoined(lines)


def _item(li: Tag) -> list[str | _Ref]:
    """A list item's text and links; a line break inside it is a space."""
    pieces: list[str | _Ref] = []
    for line in _lines(list(li.children)):
        pieces.extend([" ", *line.pieces] if pieces else line.pieces)
    return pieces


def _lost(listing: Tag, index: int, text: str) -> str:
    """What the import took from the start of a list item's line."""
    if listing.name == "ol":
        try:
            start = int(str(listing.get("start", "1")))
        except ValueError:
            start = 1
        return f"{start + index} "
    text = " ".join(text.split())
    return next((lost for pattern, lost in _LOST_BULLETS if pattern.match(text)), "")


def _rejoined(lines: list[_Line]) -> list[_Line]:
    """Rejoin a bulleted constant with the numbered value that the import split from it, such as
    ``vbAbortRetryIgnore`` and ``2 Abort, Retry, Ignore buttons``."""
    joined: list[_Line] = []
    for line in lines:
        previous = next((other for other in reversed(joined) if not other.blank), None)
        if (
            line.listed == "ol"
            and previous is not None
            and previous.listed == "ul"
            and len(previous.text().split()) == 1
        ):
            while joined[-1] is not previous:
                joined.pop()
            previous.pieces.extend([" ", *line.pieces])
            previous.listed = "ol"
        else:
            joined.append(line)
    return joined


def _append(pieces: list[str | _Ref], text: str, href: str | None) -> None:
    last = pieces[-1] if pieces else None
    if href is None:
        pieces.append(text)
    elif isinstance(last, _Ref) and last.href == href:
        last.text += text
    else:
        pieces.append(_Ref(text, href))


def _collapse(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def _code(line: _Line) -> str:
    """A line of code as written, its keywords' links reduced to the keywords."""
    return re.sub(r"[\r\n]+", " ", line.text().replace("\xa0", " ")).strip()


@dataclass
class _DocumentBuilder:
    title: str
    source_path: str
    name: str | None  # the API Entry's name, for a page that documents one
    sections: list[Section] = field(default_factory=list)
    entries: list[ApiEntry] = field(default_factory=list)
    links: list[Link] = field(default_factory=list)
    # How unlabelled lines read: as paragraphs, the description's paragraphs, the syntax, or code.
    _mode: Literal["prose", "description", "syntax", "code"] = "prose"
    _syntax: list[str] = field(default_factory=list)
    _code: list[str] = field(default_factory=list)
    _signature: str = ""
    _description: list[str] = field(default_factory=list)
    _used_anchors: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        anchors = [self._unique_anchor(self.name)] if self.name else []
        self.sections.append(Section(anchors=anchors, heading_path=[self.title]))

    @property
    def current(self) -> Section:
        return self.sections[-1]

    def add(self, line: _Line) -> None:
        if line.title:
            self.current.blocks.append(Block("heading", text=_collapse(line.text()), level=1))
        elif line.label:
            self._label(line)
        elif self._mode == "syntax":
            self._syntax.append(_code(line))
        elif self._mode == "code":
            self._code.append(_code(line))
        else:
            self._paragraph(self._inline(line.pieces))

    def _label(self, line: _Line) -> None:
        self._flush()
        rest = _Line(line.pieces)
        if line.label == "Syntax":
            self._mode = "syntax"
        elif line.label == "Group":
            self.current.blocks.append(Block("field", term="Group", text=self._inline(line.pieces)))
            self._mode = "prose"
            return
        elif line.label == "Description":
            self._mode = "description"
        else:
            anchor = self._unique_anchor(line.label)
            self.sections.append(Section(anchors=[anchor], heading_path=[self.title, line.label]))
            self.current.blocks.append(Block("heading", text=line.label, level=2))
            self._mode = "code" if line.label == "Example" else "prose"
        if not rest.blank:
            self.add(rest)

    def _paragraph(self, text: str) -> None:
        if not text:
            return
        self.current.blocks.append(Block("paragraph", text=text))
        if self._mode == "description":
            self._description.append(plain(text))

    def _inline(self, pieces: list[str | _Ref]) -> str:
        parts: list[str] = []
        for piece in pieces:
            if isinstance(piece, str):
                parts.append(piece)
                continue
            label = _collapse(piece.text)
            index = self._link(piece.href) if label else None
            if index is None:
                parts.append(piece.text)
                continue
            lead = " " if piece.text[:1].isspace() else ""
            trail = " " if piece.text[-1:].isspace() else ""
            parts.append(f"{lead}{link_span(label, index)}{trail}")
        return _collapse("".join(parts))

    def _link(self, href: str) -> int | None:
        normalised = normalise_href(href, self.source_path)
        if normalised is None:
            return None
        self.links.append(Link(normalised))
        return len(self.links) - 1

    def _unique_anchor(self, name: str) -> str:
        base = anchor_for(name) or "section"
        anchor, n = base, 1
        while anchor in self._used_anchors:
            n += 1
            anchor = f"{base}-{n}"
        self._used_anchors.add(anchor)
        return anchor

    def _flush(self) -> None:
        syntax, code = _trimmed(self._syntax), _trimmed(self._code)
        self._syntax, self._code = [], []
        if syntax:
            self._signature = self._signature or "\n".join(syntax)
            self.current.blocks.append(Block("api_signature", text="\n".join(syntax), language="vba"))
        if code:
            self.current.blocks.append(Block("code", text="\n".join(code), language="vba"))

    def finish(self) -> None:
        self._flush()
        if self.name:
            signature = self._signature or self.title
            description = "\n\n".join(self._description)
            anchor = self.sections[0].anchors[0]
            self.entries.append(ApiEntry(self.name, None, self.name, signature, description, anchor))


def _trimmed(lines: list[str]) -> list[str]:
    """Lines without the blank ones at either end."""
    start = next((i for i, line in enumerate(lines) if line), len(lines))
    end = next((i for i in range(len(lines), 0, -1) if lines[i - 1]), 0)
    return lines[start:end]
