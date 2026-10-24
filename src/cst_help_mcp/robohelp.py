"""Reader for classic RoboHelp WebHelp topics.

Topic content runs between the logo header table and ``div#footer``. CST's markup
says little through its tags (VBA headings exist only as CSS classes, ``<h3>`` holds
prose), so each project has a Profile: a map from class name (matched without regard
to case), and from tag name, to block role.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field

from bs4 import BeautifulSoup, Tag
from bs4.element import CData, NavigableString, PageElement

from cst_help_mcp.links import normalise_href
from cst_help_mcp.locator import anchor_for
from cst_help_mcp.model import ApiEntry, Block, Document, Link, Section, link_span, plain


@dataclass(frozen=True)
class Profile:
    """A help project's map from CSS class (lowercase) and from tag name to block role.

    Roles: ``object``, ``category`` and ``member`` (VBA reference headings), ``first-object``
    (an object heading only while the topic has none), ``heading-<level>``, ``term`` (a
    field name, described by the ``text`` paragraph that follows it), ``text``,
    ``paragraph``, ``code`` and ``skip``. Elements without a role are paragraphs.
    """

    classes: Mapping[str, str]
    tags: Mapping[str, str] = field(default_factory=dict)


VBA = Profile(
    classes={
        "vba-heading-object": "object",
        "vba-heading-category": "category",
        "vba-heading-method": "member",
        "vba-text-example": "code",
        "vba-index-category": "skip",
        "p-vba-index-category": "skip",
    },
    tags={"h1": "first-object", "h2": "category"},
)

# The 3D Simulation project and the root project's own subtrees share one style sheet.
# A dialog field list alternates a "term" paragraph (the field name) with a "text" one.
PROSE = Profile(
    classes={
        "tip-note-heading": "term",
        "topic-text-indent": "text",
        "tip-note-text": "text",
        "vba-text-example": "code",
    },
    tags={
        "h1": "heading-1",
        "h2": "heading-2",
        # CST writes introductory prose as <h3>; its real subheadings are <h4> to <h6>.
        "h3": "paragraph",
        "h4": "heading-3",
        "h5": "heading-4",
        "h6": "heading-5",
    },
)

_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_OBJECT_SUFFIX = re.compile(r"\s+objects?$", re.IGNORECASE)
_PARENTHETICAL = re.compile(r"\s*\(.*\)\s*$")
_BLOCK_TAGS = frozenset(
    [
        "p",
        "div",
        "br",
        "li",
        "ul",
        "ol",
        "table",
        "tr",
        "td",
        "th",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "dl",
        "dt",
        "dd",
        "blockquote",
        "pre",
    ]
)
_NOTE = re.compile(r"(?:please\s+)?note\s*:\s*", re.IGNORECASE)
# Source ids are kept as anchors only when they are usable as link fragments.
_SOURCE_ID = re.compile(r"[A-Za-z][A-Za-z0-9_.:-]*")


def is_topic(html: str) -> bool:
    """WebHelp topics load ``whtopic.js``; skin, frame and list pages don't."""
    return "whtopic.js" in html


def read_topic(
    html: str, *, profile: Profile, source_path: str, locator: str, area: str, release: str
) -> Document:
    soup = BeautifulSoup(html, "html.parser")
    title = _text(soup.title) if soup.title else source_path.rsplit("/", 1)[-1]
    builder = _DocumentBuilder(title, profile, source_path)
    body = soup.body or soup
    for element in _content_elements(body):
        builder.add(element)
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
    )


def _content_elements(body: Tag) -> list[Tag]:
    """The run of elements between the logo header table and the footer."""
    children = [c for c in body.children if isinstance(c, Tag)]
    start = 0
    for i, child in enumerate(children):
        if child.name == "table" and child.find("img", src=re.compile(r"ds_simulia\.png$", re.IGNORECASE)):
            start = i + 1
            break
    content: list[Tag] = []
    for child in children[start:]:
        if child.name == "div" and child.get("id") == "footer":
            break
        if child.name in ("script", "style"):
            continue
        content.append(child)
    return content


def _text(element: PageElement | None, link: Callable[[Tag], int | None] | None = None) -> str:
    """An element's text with whitespace collapsed; block-level children are kept apart.

    With ``link``, each ``<a>`` that it registers (returning the link's index) becomes a link span.
    """
    if element is None:
        return ""
    parts: list[str] = []
    _collect_text(element, parts, link)
    return _collapse("".join(parts))


def _collapse(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def _collect_text(element: PageElement, parts: list[str], link: Callable[[Tag], int | None] | None) -> None:
    # Comments (commented-out content) and processing instructions are other string types.
    if isinstance(element, NavigableString):
        if type(element) in (NavigableString, CData):
            parts.append(str(element))
        return
    if not isinstance(element, Tag) or element.name in ("script", "style"):
        return
    if link is not None and element.name == "a":
        label = _text(element)
        index = link(element) if label else None
        if index is not None:
            raw = element.get_text().replace("\xa0", " ")
            lead = " " if raw[:1].isspace() else ""
            trail = " " if raw[-1:].isspace() else ""
            parts.append(f"{lead}{link_span(label, index)}{trail}")
            return
    spaced = element.name in _BLOCK_TAGS
    if spaced:
        parts.append(" ")
    for child in element.children:
        _collect_text(child, parts, link)
    if spaced:
        parts.append(" ")


def _code_line(element: Tag) -> str:
    raw = element.get_text().replace("\xa0", " ")
    return re.sub(r"[\r\n]+", " ", raw).rstrip()


def _span(cell: Tag, attribute: str) -> int:
    try:
        return max(1, int(str(cell.get(attribute, "1"))))
    except ValueError:
        return 1


def _role(element: Tag, profile: Profile) -> str | None:
    for cls in element.get_attribute_list("class"):
        role = profile.classes.get(str(cls).lower())
        if role:
            return role
    return profile.tags.get(element.name)


def object_name_from_heading(heading: str) -> str | None:
    """``Solver Object (HF)`` → ``Solver``; ``Coil Group Object`` → ``CoilGroup``.

    Headings without the "Object" suffix are joined the same way
    (``Doping Density Field Import`` → ``DopingDensityFieldImport``).
    """
    text = _OBJECT_SUFFIX.sub("", _PARENTHETICAL.sub("", heading).strip())
    name = re.sub(r"[\s-]+", "", text)
    return name if _IDENTIFIER.fullmatch(name) else None


def split_member_heading(heading: str) -> list[tuple[str, str]]:
    """Split a member heading into (name, signature) pairs.

    ``SetXRange / SetYRange ( double min, double max )`` gives one pair per name,
    each with the shared parameter list; ``GetFmin double`` keeps its return type.
    Prose styled as a heading ("Specifies the duration ...") gives no pairs.
    """
    head, paren, tail = heading.partition("(")
    parts = [p.strip() for p in head.split("/")]
    names: list[str] = []
    rest = ""
    for i, part in enumerate(parts):
        match = _IDENTIFIER.match(part)
        if not match:
            return []
        names.append(match.group())
        if i == len(parts) - 1:
            rest = part[match.end() :].strip()
        elif part[match.end() :].strip():
            return []
    if len(rest.split()) > 1:
        return []
    suffix = " ".join(s for s in (rest, f"{paren}{tail}".strip()) if s)
    return [(name, f"{name} {suffix}".strip()) for name in names]


@dataclass
class _DocumentBuilder:
    title: str
    profile: Profile
    source_path: str
    sections: list[Section] = field(default_factory=list)
    entries: list[ApiEntry] = field(default_factory=list)
    links: list[Link] = field(default_factory=list)
    object_name: str | None = None
    category: str | None = None
    _object_entries: list[ApiEntry] = field(default_factory=list)
    _pending_member: str | None = None
    _pending_term: str | None = None
    _code: list[str] = field(default_factory=list)
    _used_anchors: set[str] = field(default_factory=set)
    _section_entries: list[ApiEntry] = field(default_factory=list)
    _headings: list[tuple[int, str]] = field(default_factory=list)  # the open headings, by level

    def __post_init__(self) -> None:
        self.sections.append(Section(anchors=[], heading_path=[self.title]))

    @property
    def current(self) -> Section:
        return self.sections[-1]

    def add(self, element: Tag) -> None:
        if self._is_back_to_top(element):
            return
        role = _role(element, self.profile)
        if role == "first-object":
            role = "object" if self.object_name is None else None
        if self._pending_term is not None:
            term, self._pending_term = self._pending_term, None
            if role == "text":
                self._field(term, self._inline(element))
                return
            self._field(term, "")
        if role == "member":
            # A signature can wrap onto a second heading paragraph; join until the parenthesis closes.
            text = _text(element)
            pending = self._pending_member
            if pending is not None and pending.count("(") > pending.count(")"):
                self._pending_member = f"{pending} {text}"
            else:
                self._flush_member()
                self._pending_member = text
            return
        self._flush_member()
        if role == "code":
            self._code.append(_code_line(element))
            return
        self._flush_code()
        if role == "skip":
            return
        if role == "term":
            self._pending_term = _text(element) or None
        elif role == "object":
            self._object_heading(_text(element))
        elif role == "category":
            self._category_heading(element)
        elif role and role.startswith("heading-"):
            self._heading(element, int(role.removeprefix("heading-")))
        elif element.name in ("ul", "ol"):
            self._list(element)
        elif element.name == "table":
            self._table(element)
        elif element.name == "div":
            for child in element.children:
                if isinstance(child, Tag):
                    self.add(child)
        else:
            self._paragraph(self._inline(element))

    def _is_back_to_top(self, element: Tag) -> bool:
        """An "up" link back to the topic's own mini table of contents, which is navigation."""
        link = element.find("a", href=True)
        if not isinstance(link, Tag) or not _text(element).lower() == "up" == _text(link).lower():
            return False
        target = normalise_href(str(link["href"]), self.source_path) or ""
        return target.partition("#")[0].lower() == self.source_path.lower()

    def _inline(self, element: Tag) -> str:
        """An element's text, with link spans for its links."""
        return _text(element, self._link)

    def _link(self, element: Tag) -> int | None:
        href = str(element.get("href", ""))
        if href.lower().startswith("javascript:"):
            # A BSSCPopup link names its target only in the script that shows the popup.
            popup = re.search(r"BSSCPopup\('([^']+)'\)", str(element.get("onclick", "")))
            href = popup[1] if popup else ""
        normalised = normalise_href(href, self.source_path)
        if normalised is None:
            return None
        self.links.append(Link(normalised))
        return len(self.links) - 1

    def finish(self) -> None:
        if self._pending_term is not None:
            self._field(self._pending_term, "")
        self._flush_member()
        self._flush_code()
        self._close_section()
        if len(self._object_entries) == len(self.entries):
            # A page that documents no members (a ribbon or overview page) is not an API object.
            self.entries = []

    def _flush_member(self) -> None:
        if self._pending_member is not None:
            text, self._pending_member = self._pending_member, None
            self._member_heading(text)

    def _unique_anchor(self, name: str) -> str:
        base = anchor_for(name) or "section"
        anchor, n = base, 1
        while anchor in self._used_anchors:
            n += 1
            anchor = f"{base}-{n}"
        self._used_anchors.add(anchor)
        return anchor

    def _start_section(self, anchors: list[str], heading_path: list[str]) -> None:
        self._close_section()
        self.sections.append(Section(anchors=anchors, heading_path=heading_path))

    def _close_section(self) -> None:
        description = "\n\n".join(
            plain(b.text) if b.kind == "paragraph" else f"Note: {plain(b.text)}"
            for b in self.current.blocks
            if b.kind in ("paragraph", "note")
        )
        for entry in self._section_entries:
            entry.description = description
        self._section_entries = []

    def _object_heading(self, text: str) -> None:
        if not text:
            return
        name = object_name_from_heading(text)
        if self.object_name is None:
            self.object_name = name
        anchors = [self._unique_anchor(name)] if name else []
        self._start_section(anchors, [self.title])
        self.current.blocks.append(Block("heading", text=text, level=1))
        if name and anchors:
            entry = ApiEntry(name, name, None, text, "", anchors[0])
            self.entries.append(entry)
            self._object_entries.append(entry)
            self._section_entries.append(entry)

    def _category_heading(self, element: Tag) -> None:
        text = _text(element)
        if text:
            self.category = text
            self._heading(element, 2)

    def _heading(self, element: Tag, level: int) -> None:
        text = _text(element)
        if not text:
            return
        while self._headings and self._headings[-1][0] >= level:
            self._headings.pop()
        self._headings.append((level, text))
        # A heading keeps its links, such as the popup link to the ribbon in a dialog's ribbon path.
        heading = Block("heading", text=self._inline(element), level=level)
        if level == 1:
            # The topic title opens the Document's first Section rather than a Section of its own.
            if self.current.blocks:
                self._start_section([], [self.title])
            self.current.blocks.append(heading)
            return
        # A link's name only serves its popup; the heading's own anchor is a bare <a name>.
        own = element.find("a", attrs={"name": True, "href": False})
        source_id = str(own["name"]) if isinstance(own, Tag) else ""
        if _SOURCE_ID.fullmatch(source_id) and source_id not in self._used_anchors:
            self._used_anchors.add(source_id)
            anchor = source_id
        else:
            anchor = self._unique_anchor(source_id or text)
        self._start_section([anchor], [self.title, *(t for lvl, t in self._headings if lvl > 1)])
        self.current.blocks.append(heading)

    def _member_heading(self, text: str) -> None:
        pairs = split_member_heading(text)
        if not pairs:
            if text:
                self._paragraph(text)
            return
        anchors = [self._unique_anchor(name) for name, _ in pairs]
        names = " / ".join(name for name, _ in pairs)
        path = [self.title, *([self.category] if self.category else []), names]
        self._start_section(anchors, path)
        self.current.blocks.append(Block("heading", text=names, level=3))
        self.current.blocks.append(
            Block("api_signature", text="\n".join(sig for _, sig in pairs), language="vba")
        )
        for (name, signature), anchor in zip(pairs, anchors):
            qualified = f"{self.object_name}.{name}" if self.object_name else name
            entry = ApiEntry(qualified, self.object_name, name, signature, "", anchor)
            self.entries.append(entry)
            self._section_entries.append(entry)

    def _paragraph(self, text: str) -> None:
        # CST has no note markup: a note is any paragraph that starts with "Note:".
        note = _NOTE.match(text)
        if note:
            self._note(text[note.end() :])
        elif text:
            self.current.blocks.append(Block("paragraph", text=text))

    def _note(self, text: str) -> None:
        if text:
            self.current.blocks.append(Block("note", text=text))

    def _field(self, term: str, description: str) -> None:
        if _NOTE.fullmatch(term):
            self._note(description)
        else:
            self.current.blocks.append(Block("field", term=term, text=description))

    def _list(self, element: Tag) -> None:
        items = element.find_all("li", recursive=False)
        if items and all(_role(li, self.profile) == "skip" for li in items):
            return
        texts = [t for t in (self._inline(li) for li in items) if t]
        if texts:
            self.current.blocks.append(Block("list", items=texts))

    def _table(self, element: Tag) -> None:
        trs = [
            tr
            for part in (element, *element.find_all(["thead", "tbody", "tfoot"], recursive=False))
            for tr in part.find_all("tr", recursive=False)
        ]
        grid = [tr.find_all(["td", "th"], recursive=False) for tr in trs]
        spans = [[[_span(td, "rowspan"), _span(td, "colspan")] for td in tds] for tds in grid]
        merged = any(span != [1, 1] for row in spans for span in row)
        rows = [[self._inline(td) for td in tds] for tds in grid]
        if merged:
            # Rows of a table with merged cells must stay, even empty ones, or the spans shift.
            self.current.blocks.append(Block("table", rows=rows, spans=spans))
            return
        rows = [cells for cells in rows if any(cells)]
        if rows:
            self.current.blocks.append(Block("table", rows=rows))

    def _flush_code(self) -> None:
        if not self._code:
            return
        lines = self._code
        self._code = []
        while lines and not lines[0].strip():
            lines = lines[1:]
        while lines and not lines[-1].strip():
            lines = lines[:-1]
        if not lines:
            return
        indent = min(len(line) - len(line.lstrip(" ")) for line in lines if line.strip())
        text = "\n".join(line[indent:] if line.strip() else "" for line in lines)
        self.current.blocks.append(Block("code", text=text, language="vba"))
