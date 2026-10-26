"""Render a Document as Markdown with frontmatter."""

from __future__ import annotations

import html
import json
import posixpath
import re
from dataclasses import dataclass, replace
from pathlib import PurePosixPath

from cst_help_mcp.layout import MATERIAL_KIND, ApiLine, DocumentLine, LibraryLine

# The start of a line that Markdown reads as a block: a bullet, a heading or a quote, or the number
# of an ordered list item, whose "." or ")" is what gets escaped.
_BLOCK_MARKER = re.compile(r"(?:[-+*>]|#{1,6})(?=\s|$)")
_LIST_NUMBER = re.compile(r"\d{1,9}(?=[.)](?:\s|$))")
from cst_help_mcp.model import (
    Block,
    Document,
    ImageRef,
    Link,
    NavNode,
    image_spans,
    link_spans,
    replace_images,
    replace_links,
    replace_math,
    tex_delimited,
)

# What a block's text holds besides source text, and is not escaped again: a formula, an image or a
# link span, a code span, and the escapes the readers write, ``\$`` and ``\<``.
_MARKUP = re.compile(
    "([\ue000\ue002][^\ue000-\ue003]*[\ue001\ue003]"
    r"|!?\[(?:\\.|[^\\\]])*\]\([@^]\d+\)"
    r"|(?<!`)(`+)(?!`).+?(?<!`)\2(?!`)"
    r"|\\[$<])"
)
_READER_ESCAPE = re.compile(r"\\([$<])")
# Source text that Markdown reads as markup: a backslash before punctuation, emphasis, code and
# strikethrough marks, a tag, an entity, and the bracket that would close a link.
_SPECIAL = re.compile(r"\\(?=[!-/:-@\[-`{-~])|[*`~]|<(?=[A-Za-z/!?])|&(?=#?\w+;)|\](?=[(\[])")
# Underscores mark emphasis only in pairs that open before a word and close after one, as in
# ``__init__``; an underscore between letters or digits never does. Others stay as they are, so
# that names such as ``_cst_eda_interface`` grep as written.
_UNDERSCORE_PAIR = re.compile(r"(?<![^\W_])_+(?=\S).*?(?<=\S)_+(?![^\W_])", re.DOTALL)
_EDGE_UNDERSCORE = re.compile(r"(?<![^\W_])_|_(?![^\W_])")
# Dollars outside formulas are text, but viewers that read math pair any two of them, as in
# ``[Left$](...) and [Mid$](...)``; a lone one, as in ``Dir$``, stays as it is.
_DOLLAR = re.compile(r"\$")
_BRACKET = re.compile(r"[\[\]]")


@dataclass(frozen=True)
class Part:
    """A piece of a Document's Markdown: the frontmatter, a Section's anchors, a line of a block, or
    the blank line after a block. Joined in order, the parts are the Markdown.

    ``section`` indexes the Document's Sections, and is None for the frontmatter. ``links`` are the
    label and the index into the Document's links of each link the piece shows, and ``images`` the
    index into its images of each image it shows.
    """

    text: str
    section: int | None
    links: tuple[tuple[str, int], ...] = ()
    images: tuple[int, ...] = ()


def render_markdown(doc: Document, at: str = "") -> str:
    """A Document's Markdown, written at its Locator or, for a copy, at the path ``at`` in the tree.

    Links and images are relative to the file they are written in. A copy's frontmatter names the
    Locator to cite, the Document's own.
    """
    return "".join(part.text for part in render_parts(doc, at))


def render_parts(doc: Document, at: str = "") -> list[Part]:
    at = at or doc.locator
    base = posixpath.dirname(at)
    # A release-independent Document has no Release; it states the CST version it was written for.
    front: dict[str, object] = {"release": doc.release} if doc.release else {}
    if doc.cst_version:
        front["cst_version"] = doc.cst_version
    front |= {"area": doc.area, "title": doc.title, "source": doc.source_path}
    if doc.pages:
        front["pages"] = doc.pages
    for key, values in (
        ("toc_paths", doc.toc_paths),
        ("keywords", doc.keywords),
        ("context_ids", doc.context_ids),
    ):
        if values:
            front[key] = values
    if doc.aliases:
        front["aliases"] = doc.aliases
    if doc.alias_areas:
        front["alias_areas"] = doc.alias_areas
    if at != doc.locator:
        front["copy_of"] = doc.locator
    parts = [Part(_joined(_frontmatter(front)), None)]
    for i, section in enumerate(doc.sections):
        if section.anchors:
            parts.append(Part(_joined([f'<a id="{anchor}"></a>' for anchor in section.anchors]), i))
        for block in section.blocks:
            for line, sources in _block(block, doc.links, doc.images, base):
                spans = tuple(span for source in sources for span in link_spans(source))
                images = tuple(index for source in sources for _, index in image_spans(source))
                parts.append(Part(f"{line}\n", i, spans, images))
            parts.append(Part("\n", i))
    return _trimmed(parts)


def _joined(lines: list[str]) -> str:
    return "".join(f"{line}\n" for line in lines)


def _trimmed(parts: list[Part]) -> list[Part]:
    """The parts without the newlines that end the last ones, but one."""
    text = "".join(part.text for part in parts)
    excess = len(text) - len(text.rstrip("\n")) - 1
    while excess > 0:
        last = parts.pop()
        kept = last.text[: max(0, len(last.text) - excess)]
        excess -= len(last.text) - len(kept)
        if kept:
            parts.append(replace(last, text=kept))
    return parts


def render_navigation(release: str, title: str, nodes: list[NavNode]) -> str:
    """An entry file, such as toc.md, listing a navigation tree as nested links to Locators.

    It sits at the root of the Collection's tree, so the Locators resolve as relative links.
    """
    lines = [*_frontmatter({"release": release, "title": title}), f"# {title}", ""]

    def add(nodes: list[NavNode], depth: int) -> None:
        for node in nodes:
            label = _link(node.name, node.locator) if node.locator else _text(node.name)
            lines.append(f"{'  ' * depth}- {label}")
            add(node.children, depth + 1)

    add(nodes, 0)
    return "\n".join(lines) + "\n"


def render_api(release: str, entries: list[ApiLine]) -> str:
    """The entry file api.md: one API Entry per line, with its Area, signature and Locator, for grep."""
    lines = [
        *_frontmatter({"release": release, "title": "API Entries"}),
        "# API Entries",
        "",
        "| Qualified name | Area | Signature | Locator |",
        "|---|---|---|---|",
    ]
    for entry in sorted(entries, key=lambda e: (e.qualified_name.lower(), e.area, e.locator)):
        signature = " ".join(entry.signature.split())
        # The Locator is code, not a link, so that a grep line stays short.
        locator = f"{entry.locator}#{entry.anchor}"
        cells = [_text(entry.qualified_name), _text(entry.area), _code(signature), _code(locator)]
        lines.append(_row(cells))
    return "\n".join(lines) + "\n"


def render_library(release: str, lines: list[LibraryLine]) -> str:
    """The entry file library.md: one Library file per line, under a heading per Library folder.

    An Include's line names its Helpers, where a Macro's or Result Template's names its Application
    Filter and Variants.
    """
    out = [*_frontmatter({"release": release, "title": "Library"}), "# Library", ""]
    by_folder: dict[str, list[LibraryLine]] = {}
    code = [line for line in lines if line.kind != MATERIAL_KIND]  # materials.md lists the rest
    for line in sorted(code, key=lambda line: line.locator.lower()):
        # The Library folder below library/, such as Macros.
        by_folder.setdefault(line.locator.split("/")[1], []).append(line)
    for folder, folder_lines in by_folder.items():
        includes = all(line.kind == "Include" for line in folder_lines)
        python = all(line.kind.startswith("Python") for line in folder_lines)
        if python:
            header = ["Path", "Kind", "Menu path or module", "Restricted to", "Modules (below lib/)"]
        else:
            header = ["Path", "Kind", "Name" if includes else "Menu path and Display Name"]
            header += ["Helpers"] if includes else ["Application Filter", "Variants"]
        out += [f"## {folder}", "", _row([*header, "First comment"])]
        out.append("|" + "---|" * (len(header) + 1))
        for line in folder_lines:
            cells = [_code(line.locator), line.kind, _text(line.display_name)]
            if python:
                cells += [_text(line.restricted_to), ", ".join(_code(m) for m in line.modules)]
            elif includes:
                cells.append(", ".join(_text(helper) for helper in line.helpers))
            else:
                cells += [_text(line.application_filter), ", ".join(_code(v) for v in line.variants)]
            cells.append(_text(line.description))
            out.append(_row(cells))
        out.append("")
    return "\n".join(out)


def render_materials(release: str, lines: list[LibraryLine]) -> str:
    """The entry file materials.md: one Material Definition per line, with its exact name, its base
    name without vendor prefix or loss qualifier, its Variants, the files with the same definition
    as links, and its description."""
    out = [
        *_frontmatter({"release": release, "title": "Materials"}),
        "# Materials",
        "",
        _row(["Path", "Name", "Base name", "Variants", "Same definition as", "Description"]),
        "|---|---|---|---|---|---|",
    ]
    materials = [line for line in lines if line.kind == MATERIAL_KIND]
    for line in sorted(materials, key=lambda line: line.locator.lower()):
        folder = line.locator.rpartition("/")[0]
        cells = [
            _code(line.locator),
            _text(line.display_name),
            _text(line.base_name),
            ", ".join(_code(v) for v in line.variants),
            ", ".join(_link(PurePosixPath(s).stem, f"{folder}/{s}") for s in line.same_definition),
            _text(line.description),
        ]
        out.append(_row(cells))
    return "\n".join(out) + "\n"


def render_documents(title: str, lines: list[DocumentLine]) -> str:
    """The entry file documents.md of a release-independent Collection: one PDF per line, linking
    its Text Companion and the PDF, with its pages and the CST version it was written for."""
    out = [*_frontmatter({"title": title}), f"# {title}", ""]
    for line in sorted(lines, key=lambda line: line.locator.lower()):
        version = f"written for CST {line.cst_version}" if line.cst_version else "CST version unknown"
        pages = f"{line.pages} page{'s' if line.pages != 1 else ''}"
        out.append(f"- {_link(line.title, line.locator)} ({_link('PDF', line.original)}), {pages}, {version}")
    return "\n".join(out) + "\n"


def _row(cells: list[str]) -> str:
    """A Markdown table row, with each cell's ``|`` escaped."""
    return "| " + " | ".join(c.replace("|", "\\|") for c in cells) + " |"


def _code(text: str) -> str:
    """Inline code that may itself hold backticks."""
    fence = "`" * (max((len(run) for run in re.findall(r"`+", text)), default=0) + 1)
    padding = " " if text.startswith("`") or text.endswith("`") else ""
    return f"{fence}{padding}{text}{padding}{fence}"


def _frontmatter(front: dict[str, object]) -> list[str]:
    return ["---", *(f"{k}: {json.dumps(v, ensure_ascii=False)}" for k, v in front.items()), "---", ""]


def _text(text: str) -> str:
    """Plain text, such as a name or an alt text, escaped for Markdown."""
    return _escape_source(text, brackets=True)


def _escape_source(text: str, brackets: bool = False, block: str = "") -> str:
    """Model text with its source text escaped where Markdown would read it as markup, outside its
    spans and the readers' own escapes; with ``brackets``, every bracket too, as a link label needs.

    Underscores and dollars are escaped only where ``block``, the whole text of the line they end up
    in (``text`` itself by default), holds a pair of them that a viewer would read as markup.
    """
    block = replace_math(_READER_ESCAPE.sub("", block or text), lambda *_: "")
    underscores = _UNDERSCORE_PAIR.search(block) is not None
    dollars = len(_DOLLAR.findall(block)) > 1

    def escape(plain: str) -> str:
        plain = _SPECIAL.sub(lambda m: f"\\{m[0]}", plain)
        if underscores:
            plain = _EDGE_UNDERSCORE.sub(r"\\_", plain)
        if dollars:
            plain = _DOLLAR.sub(r"\\$", plain)
        return _BRACKET.sub(lambda m: f"\\{m[0]}", plain) if brackets else plain

    # Split by the markup, the pieces are source text, the markup and its backtick group, in turn.
    pieces = _MARKUP.split(text)
    return "".join(escape(piece) if i % 3 == 0 else piece for i, piece in enumerate(pieces) if i % 3 != 2)


def _link(label: str, href: str) -> str:
    """A link labelled with plain text."""
    return _markdown_link(_text(label), href)


def _markdown_link(label: str, href: str) -> str:
    """A link whose label is already Markdown."""
    if re.search(r"[\s()<>]", href):
        href = f"<{href}>"
    return f"[{label}]({href})"


def _block(block: Block, links: list[Link], images: list[ImageRef], base: str) -> list[tuple[str, list[str]]]:
    """The block's lines, each with the model texts whose links and images it shows; ``base`` is the
    folder of the file they are written in."""

    def inline(text: str) -> str:
        return _inline(text, links, images, base)

    match block.kind:
        case "heading":
            return [(f"{'#' * block.level} {inline(block.text)}", [block.text])]
        case "paragraph" | "figure":
            return [(_unmarked(inline(block.text)), [block.text])]
        case "list":
            # A list inside another's item is indented under it.
            return [(f"{'  ' * block.level}- {inline(item)}", [item]) for item in block.items]
        case "note":
            return [(f"> **Note:** {inline(block.text)}", [block.text])]
        case "admonition":
            # A quote: its title in bold, then its blocks, every line of them quoted.
            quoted: list[tuple[str, list[str]]] = [(f"> **{inline(block.term)}**", [block.term])]
            for child in block.blocks:
                quoted.append((">", []))
                for line, sources in _block(child, links, images, base):
                    quoted.extend(
                        (f"> {piece}" if piece else ">", sources if i == 0 else [])
                        for i, piece in enumerate(line.split("\n"))
                    )
            return quoted
        case "field":
            term: tuple[str, list[str]] = (f"**{inline(block.term)}**", [block.term])
            return [term, *([(f": {inline(block.text)}", [block.text])] if block.text else [])]
        case "code" | "api_signature":
            fence = _fence(block.text)
            return [(fence + block.language, []), (block.text, []), (fence, [])]
        case "equation":
            return [("$$", []), (block.text, []), ("$$", [])]
        case "table":
            # Markdown cannot merge cells, so a table with merged cells stays HTML (ADR 0007).
            if block.spans:
                cells = [[_inline_html(c, links, images, base) for c in r] for r in block.rows]
                rows = _html_table(cells, block.spans)
                return list(zip(rows, [[], *block.rows, []], strict=True))
            rows = _table([[inline(c) for c in r] for r in block.rows])
            return list(zip(rows, [block.rows[0], [], *block.rows[1:]], strict=True))


def _unmarked(line: str) -> str:
    """A paragraph line whose start Markdown would read as a list, heading or quote marker, escaped,
    such as WinWrap's unary minus ``- n1 Negate n1``."""
    if _BLOCK_MARKER.match(line):
        return f"\\{line}"
    number = _LIST_NUMBER.match(line)
    return f"{line[: number.end()]}\\{line[number.end() :]}" if number else line


def _relative(target: str, base: str) -> str:
    """A path in the tree, with its anchor, as a link from a file in the folder ``base``."""
    path, sep, anchor = target.partition("#")
    return posixpath.relpath(path, base or ".") + sep + anchor


def _href(link: Link, base: str) -> str | None:
    """Where a rendered link leads: its Locator, relative to the folder ``base``, or its URL. Other
    links render as their label."""
    if link.status == "resolved":
        return _relative(link.target, base)
    if link.status == "external":
        return link.href
    return None


def _inline(text: str, links: list[Link], images: list[ImageRef], base: str) -> str:
    def markdown(label: str, index: int) -> str:
        href = _href(links[index], base)
        escaped = _escape_source(label, brackets=True, block=text)
        return escaped if href is None else _markdown_link(escaped, href)

    def image(_: str, index: int) -> str:
        ref = images[index]
        return f"!{_link(ref.label, _relative(ref.file, base))}" if ref.file else _missing(ref)

    # A rendered image is no link span, so the link spans are replaced after the image spans; the
    # formulas come last, so their TeX is never read as a span.
    escaped = _escape_source(text)
    return replace_math(replace_links(replace_images(escaped, image), markdown), tex_delimited)


def _inline_html(text: str, links: list[Link], images: list[ImageRef], base: str) -> str:
    anchors: list[str] = []

    def placeholder(label: str, index: int) -> str:
        href = _href(links[index], base)
        label = html.escape(_READER_ESCAPE.sub(r"\1", label), quote=False)
        anchors.append(label if href is None else f'<a href="{html.escape(href)}">{label}</a>')
        return f"\x00{len(anchors) - 1}\x00"

    def image(_: str, index: int) -> str:
        ref = images[index]
        if ref.file:
            anchors.append(
                f'<img src="{html.escape(_relative(ref.file, base))}" alt="{html.escape(ref.label)}">'
            )
        else:
            anchors.append(html.escape(_missing(ref), quote=False))
        return f"\x00{len(anchors) - 1}\x00"

    # HTML takes no Markdown escapes, so the readers' are undone.
    text = _READER_ESCAPE.sub(r"\1", replace_links(replace_images(text, image), placeholder))
    escaped = html.escape(text, quote=False)
    return re.sub(r"\x00(\d+)\x00", lambda m: anchors[int(m[1])], escaped)


def _missing(image: ImageRef) -> str:
    """How an image without an Asset is shown: by its alt text, or else by the file it names."""
    return image.alt or f"(missing image {image.src.rsplit('/', 1)[-1]})"


def _fence(text: str) -> str:
    longest = max((len(run) for run in re.findall(r"`+", text)), default=0)
    return "`" * max(3, longest + 1)


def _table(rows: list[list[str]]) -> list[str]:
    width = max(len(r) for r in rows)
    padded = [[c.replace("|", "\\|") for c in r] + [""] * (width - len(r)) for r in rows]
    out = ["| " + " | ".join(padded[0]) + " |", "|" + "---|" * width]
    out.extend("| " + " | ".join(r) + " |" for r in padded[1:])
    return out


def _html_table(rows: list[list[str]], spans: list[list[list[int]]]) -> list[str]:
    """An HTML table of cells that are already HTML."""
    out = ["<table>"]
    for cells, row_spans in zip(rows, spans):
        tds = []
        for cell, (rowspan, colspan) in zip(cells, row_spans):
            attributes = "".join(
                f' {name}="{n}"' for name, n in (("rowspan", rowspan), ("colspan", colspan)) if n > 1
            )
            tds.append(f"<td{attributes}>{cell}</td>")
        out.append(f"<tr>{''.join(tds)}</tr>")
    out.append("</table>")
    return out
