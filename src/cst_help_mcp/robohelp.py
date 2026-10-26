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

from cst_help_mcp.links import is_url, normalise_href
from cst_help_mcp.locator import anchor_for, is_usable_source_id
from cst_help_mcp.model import (
    SEPARATOR,
    ApiEntry,
    Block,
    Document,
    ImageRef,
    Link,
    Section,
    UnpairedMath,
    image_span,
    link_span,
    math_span,
    plain,
    replace_images,
    split_display,
    split_math,
)
from cst_help_mcp.navigation import decode_js_string
from cst_help_mcp.tex import MathConfig, find_math, math_config


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

# Class roles that a heading tag overrides.
_TEXT_ROLES = frozenset(("text", "term"))
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
_TOC_INFO = re.compile(r'addTocInfo\s*\(\s*"((?:\\.|[^"\\])*)"\s*\)', re.DOTALL)
# Images that are page chrome, not content: the per-page logos and WebHelp's skin images.
_CHROME = re.compile(
    r"(ds_simulia\.png|3dexp\.png|3ds\.png|wh[a-z0-9_]*\.gif|purple_book_\w+\.gif)", re.IGNORECASE
)
# Alt text that only names the image's file, such as "image\brick.gif", says nothing.
_FILE_NAME = re.compile(r"[\\/]|\.(png|gif|jpe?g|bmp|svg)$", re.IGNORECASE)


def is_topic(html: str) -> bool:
    """WebHelp topics load ``whtopic.js``; skin, frame and list pages don't."""
    return "whtopic.js" in html


def read_topic(
    html: str, *, profile: Profile, source_path: str, locator: str, area: str, release: str
) -> Document:
    soup = BeautifulSoup(html, "html.parser")
    title = _text(soup.title) if soup.title else source_path.rsplit("/", 1)[-1]
    builder = _DocumentBuilder(title, profile, source_path, math_config(html))
    body = soup.body or soup
    content = _content_elements(body)
    for element in content:
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
        images=builder.images,
        source_anchors=source_anchors(content),
        breadcrumbs=breadcrumbs(html),
        unpaired_math=builder.unpaired_math,
    )


def breadcrumbs(html: str) -> list[str]:
    """The table-of-contents paths a topic's script passes to ``addTocInfo``, one per place it is listed."""
    paths = []
    for body in _TOC_INFO.findall(html):
        names = [" ".join(name.split()) for name in decode_js_string(body).split("\n")]
        path = SEPARATOR.join(name for name in names if name)
        if path and path not in paths:
            paths.append(path)
    return paths


def _content_elements(body: Tag) -> list[Tag]:
    """The run of elements between the logo header table and the footer."""
    return [node for node in content_nodes(body) if isinstance(node, Tag)]


def content_nodes(body: Tag) -> list[PageElement]:
    """The run of elements and loose text between the logo header table and the footer."""
    children = list(body.children)
    start = 0
    for i, child in enumerate(children):
        if (
            isinstance(child, Tag)
            and child.name == "table"
            and child.find("img", src=re.compile(r"ds_simulia\.png$", re.IGNORECASE))
        ):
            start = i + 1
            break
    content: list[PageElement] = []
    for child in children[start:]:
        if isinstance(child, Tag) and child.name == "div" and child.get("id") == "footer":
            break
        if isinstance(child, Tag) and child.name in ("script", "style"):
            continue
        content.append(child)
    return content


def source_anchors(content: list[Tag]) -> list[str]:
    """Every id and name attribute in the content, which a link fragment may target."""
    tags = [tag for element in content for tag in (element, *element.find_all(True))]
    return sorted({str(tag[a]) for tag in tags for a in ("id", "name") if tag.get(a)})


_Register = Callable[[Tag], int | None]
_Math = Callable[[NavigableString], str]


def _text(
    element: PageElement | None,
    link: _Register | None = None,
    image: _Register | None = None,
    math: _Math | None = None,
) -> str:
    """An element's text with whitespace collapsed; block-level children are kept apart.

    With ``link``, each ``<a>`` that it registers (returning the link's index) becomes a link span;
    with ``image``, each ``<img>`` that it registers becomes an image span; with ``math``, each run
    of text becomes what it gives, the run with its formulas as math spans.
    """
    if element is None:
        return ""
    parts: list[str] = []
    _collect_text(element, parts, link, image, math)
    return _collapse("".join(parts))


def _collapse(text: str) -> str:
    """Text with its whitespace collapsed, except inside math spans: TeX stays as written."""
    pieces = split_math(text)
    pieces[::2] = [re.sub(r"\s+", " ", piece.replace("\xa0", " ")) for piece in pieces[::2]]
    return "".join(pieces).strip()


def _collect_text(
    element: PageElement,
    parts: list[str],
    link: _Register | None,
    image: _Register | None,
    math: _Math | None,
) -> None:
    # Comments (commented-out content) and processing instructions are other string types.
    if isinstance(element, NavigableString):
        if type(element) in (NavigableString, CData):
            parts.append(str(element) if math is None else math(element))
        return
    if not isinstance(element, Tag) or element.name in ("script", "style"):
        return
    if image is not None and element.name == "img":
        index = image(element)
        if index is not None:
            parts.append(image_span(_alt(element), index))
        return
    if link is not None and element.name == "a":
        label = _text(element)
        index = link(element) if label else None
        if index is not None:
            raw = element.get_text().replace("\xa0", " ")
            lead = " " if raw[:1].isspace() else ""
            trail = " " if raw[-1:].isspace() else ""
            parts.append(f"{lead}{link_span(label, index)}{trail}")
            # The label is text only, so the link's images follow it.
            if image is not None:
                for img in element.find_all("img"):
                    _collect_text(img, parts, None, image, math)
            return
    spaced = element.name in _BLOCK_TAGS
    if spaced:
        parts.append(" ")
    for child in element.children:
        _collect_text(child, parts, link, image, math)
    if spaced:
        parts.append(" ")


def _escape_dollars(text: str) -> str:
    """Text with each dollar escaped for Markdown; one that the source already escapes stays as it is."""
    return re.sub(r"\\?\$", r"\\$", text)


def _alt(element: Tag) -> str:
    """An image's alt text, unless it only names a file."""
    alt = _collapse(str(element.get("alt", "")))
    return "" if _FILE_NAME.search(alt) else alt


def _code_line(element: Tag) -> str:
    raw = element.get_text().replace("\xa0", " ")
    return re.sub(r"[\r\n]+", " ", raw).rstrip()


def _span(cell: Tag, attribute: str) -> int:
    try:
        return max(1, int(str(cell.get(attribute, "1"))))
    except ValueError:
        return 1


def _role(element: Tag, profile: Profile) -> str | None:
    tag_role = profile.tags.get(element.name)
    for cls in element.get_attribute_list("class"):
        role = profile.classes.get(str(cls).lower())
        if role in _TEXT_ROLES and tag_role and tag_role.startswith("heading-"):
            # CST styles some headings as body text or a field name (<h4 class="Tip-Note-Text">,
            # a Ribbon Path as <h2 class="Tip-Note-Heading">); the heading tag says more.
            return tag_role
        if role:
            return role
    return tag_role


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
    math: MathConfig | None = None  # the topic's MathJax configuration; None for a topic without MathJax
    sections: list[Section] = field(default_factory=list)
    entries: list[ApiEntry] = field(default_factory=list)
    links: list[Link] = field(default_factory=list)
    images: list[ImageRef] = field(default_factory=list)
    unpaired_math: list[UnpairedMath] = field(default_factory=list)
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
            # A field name keeps its icon, such as the solver's icon beside "Time Domain Solver".
            self._pending_term = _text(element, image=self._image, math=self._math) or None
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
        """An element's text, with link spans for its links, image spans for its images and math spans
        for its formulas."""
        return _text(element, self._link, self._image, self._math)

    def _math(self, run: NavigableString) -> str:
        """A run of text with its formulas as math spans, on a page that loads MathJax.

        A dollar that is text there is escaped, so that a Markdown renderer doesn't take it for math.
        """
        if self.math is None:
            return str(run)
        elements = [
            (tag.name, " ".join(tag.get_attribute_list("class")))
            for tag in reversed(list(run.parents))
            if tag.name not in ("[document]", "html", "body")
        ]
        if not self.math.processes(elements):
            return _escape_dollars(str(run))
        pieces, unpaired = find_math(str(run), self.math)
        self.unpaired_math.extend(u for u in unpaired if u not in self.unpaired_math)
        return "".join(
            _escape_dollars(p) if isinstance(p, str) else math_span(p.tex, p.display) for p in pieces
        )

    def _image(self, element: Tag) -> int | None:
        """Register an image; page chrome and images that name no file are left out."""
        src = normalise_href(str(element.get("src", "")), self.source_path)
        if src is None or is_url(src) or _CHROME.fullmatch(src.rsplit("/", 1)[-1]):
            return None
        self.images.append(ImageRef(src.partition("#")[0], _alt(element)))
        return len(self.images) - 1

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
        if is_usable_source_id(source_id) and source_id not in self._used_anchors:
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
            return
        text, *displayed = split_display(text)
        text = text.strip()
        if text and not plain(replace_images(text, lambda *_: "")).strip():
            self.current.blocks.append(Block("figure", text=text))
        elif text:
            self.current.blocks.append(Block("paragraph", text=text))
        self._equations(displayed)

    def _note(self, text: str) -> None:
        text, *displayed = split_display(text)
        if text.strip():
            self.current.blocks.append(Block("note", text=text.strip()))
        self._equations(displayed)

    def _field(self, term: str, description: str) -> None:
        if _NOTE.fullmatch(term):
            self._note(description)
            return
        description, *displayed = split_display(description)
        self.current.blocks.append(Block("field", term=term, text=description.strip()))
        self._equations(displayed)

    def _equations(self, displayed: list[str]) -> None:
        """Displayed formulas as equations, each followed by the text after it as a paragraph.

        ``displayed`` alternates a formula's TeX and the text after it, as split_display gives them.
        """
        for tex, text in zip(displayed[::2], displayed[1::2], strict=True):
            self.current.blocks.append(Block("equation", text=tex))
            self._paragraph(text.strip())

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
