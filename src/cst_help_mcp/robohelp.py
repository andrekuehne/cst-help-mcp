"""Reader for classic RoboHelp WebHelp topics (VBA projects only, for now).

Topic content runs between the logo header table and ``div#footer``. VBA headings
exist only as CSS classes, so a map from class name (matched without regard to
case) to block role says what each paragraph is.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from bs4 import BeautifulSoup, Tag
from bs4.element import PageElement

from cst_help_mcp.locator import anchor_for
from cst_help_mcp.model import ApiEntry, Block, Document, Section

VBA_CLASS_ROLES = {
    "vba-heading-object": "object",
    "vba-heading-category": "category",
    "vba-heading-method": "member",
    "vba-text-example": "code",
    "vba-index-category": "skip",
    "p-vba-index-category": "skip",
}

_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_OBJECT_SUFFIX = re.compile(r"\s+objects?$", re.IGNORECASE)
_PARENTHETICAL = re.compile(r"\s*\(.*\)\s*$")
# Source ids are kept as anchors only when they are usable as link fragments.
_SOURCE_ID = re.compile(r"[A-Za-z][A-Za-z0-9_.:-]*")


def is_topic(html: str) -> bool:
    """WebHelp topics load ``whtopic.js``; skin, frame and list pages don't."""
    return "whtopic.js" in html


def read_vba_topic(html: str, *, source_path: str, locator: str, area: str, release: str) -> Document:
    soup = BeautifulSoup(html, "html.parser")
    title = _text(soup.title) if soup.title else source_path.rsplit("/", 1)[-1]
    builder = _VbaDocumentBuilder(title)
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


def _text(element: PageElement | None) -> str:
    if element is None:
        return ""
    raw = element.get_text() if isinstance(element, Tag) else str(element)
    return re.sub(r"\s+", " ", raw.replace("\xa0", " ")).strip()


def _code_line(element: Tag) -> str:
    raw = element.get_text().replace("\xa0", " ")
    return re.sub(r"[\r\n]+", " ", raw).rstrip()


def _role(element: Tag) -> str | None:
    for cls in element.get_attribute_list("class"):
        role = VBA_CLASS_ROLES.get(str(cls).lower())
        if role:
            return role
    return None


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
class _VbaDocumentBuilder:
    title: str
    sections: list[Section] = field(default_factory=list)
    entries: list[ApiEntry] = field(default_factory=list)
    object_name: str | None = None
    category: str | None = None
    _object_entries: list[ApiEntry] = field(default_factory=list)
    _pending_member: str | None = None
    _code: list[str] = field(default_factory=list)
    _used_anchors: set[str] = field(default_factory=set)
    _section_entries: list[ApiEntry] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.sections.append(Section(anchors=[], heading_path=[self.title]))

    @property
    def current(self) -> Section:
        return self.sections[-1]

    def add(self, element: Tag) -> None:
        role = _role(element)
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
        if role == "object" or (element.name == "h1" and self.object_name is None):
            self._object_heading(_text(element))
        elif role == "category" or element.name == "h2":
            self._category_heading(element)
        elif element.name in ("ul", "ol"):
            self._list(element)
        elif element.name == "table":
            self._table(element)
        elif element.name == "div":
            for child in element.children:
                if isinstance(child, Tag):
                    self.add(child)
        else:
            self._paragraph(_text(element))

    def finish(self) -> None:
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
        description = "\n\n".join(b.text for b in self.current.blocks if b.kind == "paragraph")
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
        if not text:
            return
        self.category = text
        own = element.find("a", attrs={"name": True})
        source_id = str(own["name"]) if isinstance(own, Tag) else ""
        if _SOURCE_ID.fullmatch(source_id) and source_id not in self._used_anchors:
            self._used_anchors.add(source_id)
            anchor = source_id
        else:
            anchor = self._unique_anchor(source_id or text)
        self._start_section([anchor], [self.title, text])
        self.current.blocks.append(Block("heading", text=text, level=2))

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
        if text:
            self.current.blocks.append(Block("paragraph", text=text))

    def _list(self, element: Tag) -> None:
        items = element.find_all("li", recursive=False)
        if items and all(_role(li) == "skip" for li in items):
            return
        texts = [t for t in (_text(li) for li in items) if t]
        if texts:
            self.current.blocks.append(Block("list", items=texts))

    def _table(self, element: Tag) -> None:
        rows = []
        for tr in element.find_all("tr"):
            cells = [_text(td) for td in tr.find_all(["td", "th"], recursive=False)]
            if any(cells):
                rows.append(cells)
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
