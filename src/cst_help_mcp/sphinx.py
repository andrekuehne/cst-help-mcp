"""Reader for the Sphinx Python reference, ``Python/`` in the help (Sphinx 4.4, theme sphinxdoc).

The inventory, ``objects.inv``, lists the reference's pages and every Python object it documents,
each with the page and the anchor of its entry. A page's content is its main region,
``div.body``, without the navigation bars, the sidebar and the footer around it. Its markup is
semantic: ``<section>`` and ``<h1>`` to ``<h3>`` for headings, ``dl.py`` for an object's entry with
its signature in the ``<dt>``, ``div.highlight-*`` for code, ``div.admonition`` for notes and
``span.math`` for TeX, which Sphinx writes between ``\\(`` and ``\\)``.

Each inventory object becomes an API Entry under its dotted name, anchored to its entry, whose
id is the name as written: ``cst.results.ResultModule.get_run_ids``. Some entries carry two
names, such as ``cst.results.ProjectFile`` and its hidden alias ``_cst_results.ProjectFile``.
"""

from __future__ import annotations

import re
import zlib
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from bs4 import BeautifulSoup, Tag
from bs4.element import CData, NavigableString, PageElement

from cst_help_mcp.errors import BuildError
from cst_help_mcp.links import is_url, normalise_href
from cst_help_mcp.locator import anchor_for, is_usable_source_id
from cst_help_mcp.model import (
    ApiEntry,
    Block,
    Document,
    ImageRef,
    Link,
    Section,
    image_span,
    link_span,
    math_span,
    plain,
    replace_images,
    split_math,
)
from cst_help_mcp.robohelp import source_anchors

INVENTORY = "objects.inv"
# An inventory line: name, domain:role, priority, URI ("$" stands for the name), display name.
_INVENTORY_LINE = re.compile(r"(.+?)\s+(\S+)\s+(-?\d+)\s+(\S*)\s+(.*)")
# The roles of the objects that become API Entries; modules are the pages' sections instead.
_ENTRY_ROLES = frozenset(("py:class", "py:method", "py:property", "py:function"))
_HEADINGS = frozenset(("h1", "h2", "h3", "h4", "h5", "h6"))
_BLOCK_TAGS = frozenset(("p", "div", "li", "ul", "ol", "dl", "dt", "dd", "table", "tr", "td", "th", "pre"))
# The Pygments lexer a code block names, as the language of its fence.
_LANGUAGES = {"default": "python", "python": "python", "pycon": "python", "winbatch": "bat"}
# Alt text that only names the image's file, such as "../_images/FMCWRadarModel.svg", says nothing.
_FILE_NAME = re.compile(r"[\\/]|\.(png|gif|jpe?g|bmp|svg)$", re.IGNORECASE)


@dataclass(frozen=True)
class InventoryObject:
    """A Python object the inventory lists, with the source path of its page and its entry's anchor."""

    name: str
    role: str
    priority: int  # -1 hides it from Sphinx's search, as for an alias of another name
    page: str
    anchor: str


@dataclass(frozen=True)
class SphinxInventory:
    pages: list[str]  # the source paths of the reference's pages, in the inventory's order
    objects: list[InventoryObject]

    def on_page(self, source_path: str) -> dict[str, list[InventoryObject]]:
        """The objects documented on a page, by the anchor of their entry."""
        found: dict[str, list[InventoryObject]] = defaultdict(list)
        for obj in self.objects:
            if obj.page.lower() == source_path.lower():
                found[obj.anchor].append(obj)
        return found


def read_inventory(release: Path, folder: str) -> SphinxInventory:
    """The inventory of the Sphinx project in ``folder``, a path relative to the release folder."""
    file = release / folder / INVENTORY
    try:
        header, _, compressed = _split_header(file.read_bytes())
        lines = zlib.decompress(compressed).decode("utf-8").splitlines()
    except (OSError, zlib.error, UnicodeDecodeError, ValueError) as e:
        raise BuildError(f"{file} is not a Sphinx inventory of version 2: {e}") from e
    if header != b"# Sphinx inventory version 2":
        raise BuildError(f"{file} is not a Sphinx inventory of version 2")
    pages: list[str] = []
    objects: list[InventoryObject] = []
    for line in lines:
        match = _INVENTORY_LINE.fullmatch(line.strip())
        if not match:
            continue
        name, role, priority, uri = match[1], match[2], int(match[3]), match[4]
        uri = uri[:-1] + name if uri.endswith("$") else uri
        page, _, anchor = uri.partition("#")
        if role == "std:doc":
            pages.append(f"{folder}/{page}")
        elif role in _ENTRY_ROLES:
            objects.append(InventoryObject(name, role, priority, f"{folder}/{page}", anchor))
    return SphinxInventory(pages, objects)


def _split_header(data: bytes) -> tuple[bytes, bytes, bytes]:
    """The first header line, the other three, and the compressed rest."""
    lines = data.split(b"\n", 4)
    if len(lines) < 5:
        raise ValueError("the four header lines are missing")
    return lines[0].strip(), b"\n".join(lines[1:4]), lines[4]


def read_sphinx_page(
    html: str, *, inventory: SphinxInventory, source_path: str, locator: str, area: str, release: str
) -> Document:
    soup = BeautifulSoup(html, "html.parser")
    title = " ".join(soup.title.get_text().split()) if soup.title else source_path.rsplit("/", 1)[-1]
    # "cst.results module — CST Python Libraries documentation"
    title = title.split(" — ")[0]
    main = soup.find("div", class_="body")
    if not isinstance(main, Tag):
        raise ValueError("the page has no main region, div.body")  # noqa: TRY004 (a Document failure)
    builder = _DocumentBuilder(title, source_path, inventory.on_page(source_path))
    for child in main.children:
        builder.add(child)
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
        source_anchors=source_anchors([main]),
    )


def _collapse(text: str) -> str:
    """Text with its whitespace collapsed, except inside math spans: TeX stays as written."""
    pieces = split_math(text)
    pieces[::2] = [re.sub(r"\s+", " ", piece.replace("\xa0", " ")) for piece in pieces[::2]]
    return "".join(pieces).strip()


def _escaped(text: str) -> str:
    """Text with each dollar escaped, so that a Markdown renderer doesn't take it for math, as Sphinx
    marks every formula; and each ``<`` that could open a tag, so that ``<CST_STUDIO_SUITE_FOLDER>``
    isn't read as HTML."""
    return re.sub(r"(\$|<(?=[A-Za-z/!?]))", r"\\\1", text)


def _classes(element: Tag) -> list[str]:
    return [str(c) for c in element.get_attribute_list("class") if c]


def _code_span(text: str) -> str:
    """Inline code that may itself hold backticks."""
    text = " ".join(text.split())
    fence = "`" * (max((len(run) for run in re.findall(r"`+", text)), default=0) + 1)
    padding = " " if text.startswith("`") or text.endswith("`") else ""
    return f"{fence}{padding}{text}{padding}{fence}"


def _signature(dt: Tag) -> str:
    """An entry's signature as the page shows it, without its permalink."""
    parts: list[str] = []
    for node in dt.descendants:
        if (
            isinstance(node, NavigableString)
            and type(node) in (NavigableString, CData)
            and not any(isinstance(p, Tag) and "headerlink" in _classes(p) for p in node.parents)
        ):
            parts.append(str(node))
    return " ".join("".join(parts).split())


@dataclass
class _DocumentBuilder:
    title: str
    source_path: str
    objects: dict[str, list[InventoryObject]]  # the page's inventory objects, by their entry's anchor
    sections: list[Section] = field(default_factory=list)
    entries: list[ApiEntry] = field(default_factory=list)
    links: list[Link] = field(default_factory=list)
    images: list[ImageRef] = field(default_factory=list)
    _level: int = 1  # the level of the heading or entry the content belongs to
    _headings: list[tuple[int, str]] = field(default_factory=list)  # the open headings, by level
    _pending_anchors: list[str] = field(default_factory=list)  # a <section>'s ids, for its heading
    _admonitions: list[Block] = field(default_factory=list)  # the admonitions being read, innermost last
    _section_entries: list[ApiEntry] = field(default_factory=list)
    _used_anchors: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        self.sections.append(Section(anchors=[], heading_path=[self.title]))

    @property
    def current(self) -> Section:
        return self.sections[-1]

    def _append(self, block: Block) -> None:
        (self._admonitions[-1].blocks if self._admonitions else self.current.blocks).append(block)

    def add(self, node: PageElement) -> None:
        if isinstance(node, NavigableString):
            if type(node) in (NavigableString, CData) and node.strip():
                self._paragraph(self._inline(node))
            return
        if not isinstance(node, Tag) or node.name in ("script", "style"):
            return
        classes = _classes(node)
        if node.name == "section":
            self._section(node)
        elif node.name in _HEADINGS:
            self._heading(node, int(node.name[1]))
        elif node.name == "dl" and "py" in classes:
            self._entry(node)
        elif node.name == "dl":
            self._definitions(node)
        elif node.name == "div" and "admonition" in classes:
            self._admonition(node)
        elif node.name == "div" and "math" in classes:
            self._equation(node.get_text())
        elif node.name == "div" and any(c.startswith("highlight-") for c in classes):
            lexer = next(c for c in classes if c.startswith("highlight-")).removeprefix("highlight-")
            pre = node.find("pre")
            if isinstance(pre, Tag):
                self._code(pre, _LANGUAGES.get(lexer, lexer))
        elif node.name == "pre":
            self._code(node, "python")
        elif node.name in ("ul", "ol"):
            self._list(node, 0)
        elif node.name == "table":
            self._table(node)
        elif node.name == "figure":
            self._figure(node)
        elif node.name == "span" and not node.get_text().strip():
            return  # a link target, such as a module's
        elif node.name in ("div", "blockquote", "figcaption"):
            for child in node.children:
                self.add(child)
        else:
            self._paragraph(self._inline(node))

    def _section(self, element: Tag) -> None:
        """A <section>: its id, and those of the empty targets before its heading, anchor the heading."""
        ids = [str(element["id"])] if element.get("id") else []
        for child in element.children:
            if isinstance(child, Tag) and child.name == "span" and child.get("id"):
                ids.append(str(child["id"]))
            elif isinstance(child, Tag):
                break
        self._pending_anchors = ids
        for child in element.children:
            self.add(child)

    def _anchors(self, ids: list[str], fallback: str) -> list[str]:
        anchors = [i for i in ids if is_usable_source_id(i) and i not in self._used_anchors]
        if not anchors:
            base = anchor_for(fallback) or "section"
            anchor, n = base, 1
            while anchor in self._used_anchors:
                n += 1
                anchor = f"{base}-{n}"
            anchors = [anchor]
        self._used_anchors.update(anchors)
        return anchors

    def _open(self, level: int, text: str, ids: list[str]) -> None:
        """Start the Section of a heading or an entry."""
        while self._headings and self._headings[-1][0] >= level:
            self._headings.pop()
        self._headings.append((level, text))
        anchors = self._anchors(ids, text)
        self._close_section()
        if level == 1 and not self.current.blocks and not self.current.anchors:
            # The page title opens the Document's first Section rather than a Section of its own.
            self.current.anchors = anchors
            return
        path = [self.title, *(t for lvl, t in self._headings if lvl > 1)]
        self.sections.append(Section(anchors=anchors, heading_path=path))

    def _heading(self, element: Tag, level: int) -> None:
        text = self._inline(element)
        if not text:
            return
        ids, self._pending_anchors = self._pending_anchors, []
        self._open(level, plain(text), ids)
        self._level = level
        self.current.blocks.append(Block("heading", text=text, level=level))

    def _entry(self, element: Tag) -> None:
        """An object's entry: a heading with its name, its signature, then its description and members."""
        dt = element.find("dt", recursive=False)
        dd = element.find("dd", recursive=False)
        if not isinstance(dt, Tag):
            return
        anchor = str(dt.get("id", ""))
        objects = self.objects.pop(anchor, [])
        # The heading shows the name that Sphinx's search shows, not a hidden alias.
        name = next((o.name for o in objects if o.priority >= 0), objects[0].name if objects else anchor)
        signature = _signature(dt)
        outer = self._level
        level = min(outer + 1, 6)
        self._open(level, name, [anchor] if anchor else [])
        self._level = level
        # Code, so that a name such as __init__ isn't read as emphasis.
        self.current.blocks.append(Block("heading", text=_code_span(name), level=level))
        self.current.blocks.append(Block("api_signature", text=signature, language="python"))
        for obj in objects:
            parent, _, member = obj.name.rpartition(".")
            is_class = obj.role == "py:class"
            entry = ApiEntry(
                obj.name,
                obj.name if is_class else (parent or None),
                None if is_class else member,
                signature,
                "",
                self.current.anchors[0],
            )
            self.entries.append(entry)
            self._section_entries.append(entry)
        if isinstance(dd, Tag):
            for child in dd.children:
                self.add(child)
        self._level = outer

    def _definitions(self, element: Tag) -> None:
        """A definition list, such as a field list ("Parameters", "Returns"): each term is a field,
        described by its definition's first paragraph; the rest of the definition follows it."""
        term: str | None = None
        for child in element.children:
            if not isinstance(child, Tag):
                continue
            if child.name == "dt":
                if term is not None:
                    self._append(Block("field", term=term))
                term = self._inline(child)
            elif child.name == "dd":
                rest = [c for c in child.children if not (isinstance(c, NavigableString) and not c.strip())]
                first = rest[0] if rest else None
                text = ""
                if isinstance(first, Tag) and first.name == "p":
                    text, rest = self._inline(first), rest[1:]
                self._append(Block("field", term=term or "", text=text))
                term = None
                for node in rest:
                    self.add(node)
        if term is not None:
            self._append(Block("field", term=term))

    def _list(self, element: Tag, level: int) -> None:
        """A list, each list inside an item as a list of the next level after that item."""
        items: list[str] = []
        for li in element.find_all("li", recursive=False):
            if text := self._inline(li, skip=frozenset(("ul", "ol"))):
                items.append(text)
            inner = li.find_all(["ul", "ol"])
            nested = [n for n in inner if not any(p in inner for p in n.find_parents(["ul", "ol"]))]
            if nested and items:
                self._append(Block("list", items=items, level=level))
                items = []
            for listing in nested:
                self._list(listing, level + 1)
        if items:
            self._append(Block("list", items=items, level=level))

    def _admonition(self, element: Tag) -> None:
        title = element.find("p", class_="admonition-title")
        block = Block("admonition", term=self._inline(title) if isinstance(title, Tag) else "Note")
        self._append(block)
        self._admonitions.append(block)
        for child in element.children:
            if child is not title:
                self.add(child)
        self._admonitions.pop()

    def _code(self, pre: Tag, language: str) -> None:
        text = pre.get_text().replace("\xa0", " ").rstrip()
        text = "\n".join(line.rstrip() for line in text.split("\n")).strip("\n")
        if text:
            self._append(Block("code", text=text, language=language))

    def _equation(self, tex: str) -> None:
        tex = tex.strip()
        if tex.startswith("\\[") and tex.endswith("\\]"):
            tex = tex[2:-2].strip()
        if tex:
            self._append(Block("equation", text=tex))

    def _figure(self, element: Tag) -> None:
        caption = element.find("figcaption")
        alt = _collapse(caption.get_text()).rstrip("¶").strip() if isinstance(caption, Tag) else ""
        spans = []
        for img in element.find_all("img"):
            index = self._image(img, alt)
            if index is not None:
                spans.append(image_span(self.images[index].alt, index))
        if spans:
            self._append(Block("figure", text=" ".join(spans)))
        elif alt:
            self._paragraph(alt)

    def _table(self, element: Tag) -> None:
        trs = [
            tr
            for part in (element, *element.find_all(["thead", "tbody", "tfoot"], recursive=False))
            for tr in part.find_all("tr", recursive=False)
        ]
        grid = [tr.find_all(["td", "th"], recursive=False) for tr in trs]
        spans = [[[_span(td, "rowspan"), _span(td, "colspan")] for td in tds] for tds in grid]
        rows = [[self._inline(td) for td in tds] for tds in grid]
        # Rows of a table with merged cells must stay, even empty ones, or the spans shift.
        if any(span != [1, 1] for row in spans for span in row):
            self._append(Block("table", rows=rows, spans=spans))
        elif rows := [cells for cells in rows if any(cells)]:
            self._append(Block("table", rows=rows))

    def _paragraph(self, text: str) -> None:
        if not text:
            return
        if not plain(replace_images(text, lambda *_: "")).strip():
            self._append(Block("figure", text=text))
        else:
            self._append(Block("paragraph", text=text))

    def _inline(self, node: PageElement, skip: frozenset[str] = frozenset()) -> str:
        """A node's text, with link spans for its links, image spans for its images, math spans for its
        formulas and code spans for its inline code; without the elements named in ``skip``."""
        parts: list[str] = []
        self._collect(node, parts, links=True, skip=skip)
        return _collapse("".join(parts))

    def _collect(
        self, node: PageElement, parts: list[str], links: bool, skip: frozenset[str] = frozenset()
    ) -> None:
        if isinstance(node, NavigableString):
            if type(node) in (NavigableString, CData):
                parts.append(_escaped(str(node)))
            return
        if not isinstance(node, Tag) or node.name in ("script", "style", *skip):
            return
        classes = _classes(node)
        if "headerlink" in classes:
            return
        if node.name == "span" and "math" in classes:
            tex = node.get_text()
            display = tex.startswith("\\[")
            if tex[:2] in ("\\(", "\\[") and tex[-2:] in ("\\)", "\\]"):
                tex = tex[2:-2]
            parts.append(math_span(tex, display))
            return
        # These pages write code in the default role, which Sphinx shows as <cite>: `h5py`.
        if node.name in ("code", "cite"):
            parts.append(_code_span(node.get_text()))
            return
        if node.name == "img":
            index = self._image(node, "")
            if index is not None:
                parts.append(image_span(self.images[index].alt, index))
            return
        # A link around an image, such as a figure's to its full size, is only the image.
        if links and node.name == "a" and node.get("href") is not None and not node.find("img"):
            label: list[str] = []
            for child in node.children:
                self._collect(child, label, links=False)
            text = _collapse("".join(label))
            index = self._link(str(node["href"])) if text else None
            if index is not None:
                raw = node.get_text()
                lead = " " if raw[:1].isspace() else ""
                trail = " " if raw[-1:].isspace() else ""
                parts.append(f"{lead}{link_span(text, index)}{trail}")
                return
        spaced = node.name in _BLOCK_TAGS
        if spaced:
            parts.append(" ")
        for child in node.children:
            self._collect(child, parts, links, skip)
        if spaced:
            parts.append(" ")

    def _link(self, href: str) -> int | None:
        normalised = normalise_href(href, self.source_path)
        if normalised is None:
            return None
        self.links.append(Link(normalised))
        return len(self.links) - 1

    def _image(self, element: Tag, caption: str) -> int | None:
        src = normalise_href(str(element.get("src", "")), self.source_path)
        if src is None or is_url(src):
            return None
        alt = _collapse(str(element.get("alt", "")))
        self.images.append(ImageRef(src.partition("#")[0], caption if _FILE_NAME.search(alt) else alt))
        return len(self.images) - 1

    def _close_section(self) -> None:
        """Give the entries of the Section that ends its paragraphs and fields as their description."""
        texts = []
        for block in self.current.blocks:
            if block.kind == "paragraph":
                texts.append(plain(block.text))
            elif block.kind == "field":
                texts.append(f"{plain(block.term)}: {plain(block.text)}".rstrip(": "))
            elif block.kind == "list":
                texts.extend(f"- {plain(item)}" for item in block.items)
        for entry in self._section_entries:
            entry.description = "\n\n".join(texts)
        self._section_entries = []

    def finish(self) -> None:
        self._close_section()
        if self.objects:
            missing = ", ".join(o.name for objects in self.objects.values() for o in objects)
            raise ValueError(f"the inventory lists objects that have no entry on the page: {missing}")


def _span(cell: Tag, attribute: str) -> int:
    try:
        return max(1, int(str(cell.get(attribute, "1"))))
    except ValueError:
        return 1
