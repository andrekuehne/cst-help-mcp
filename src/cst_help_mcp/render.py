"""Render a Document as Markdown with frontmatter."""

from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass, replace

from cst_help_mcp.layout import ApiLine

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
    escape_label,
    image_spans,
    link_spans,
    replace_images,
    replace_links,
    replace_math,
    tex_delimited,
)


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


def render_markdown(doc: Document) -> str:
    return "".join(part.text for part in render_parts(doc))


def render_parts(doc: Document) -> list[Part]:
    front: dict[str, object] = {
        "release": doc.release,
        "area": doc.area,
        "title": doc.title,
        "source": doc.source_path,
    }
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
    parts = [Part(_joined(_frontmatter(front)), None)]
    for i, section in enumerate(doc.sections):
        if section.anchors:
            parts.append(Part(_joined([f'<a id="{anchor}"></a>' for anchor in section.anchors]), i))
        for block in section.blocks:
            for line, sources in _block(block, doc.links, doc.images):
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
            label = _link(node.name, node.locator) if node.locator else node.name
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
        cells = [entry.qualified_name, entry.area, _code(signature), _code(locator)]
        lines.append("| " + " | ".join(c.replace("|", "\\|") for c in cells) + " |")
    return "\n".join(lines) + "\n"


def _code(text: str) -> str:
    """Inline code that may itself hold backticks."""
    fence = "`" * (max((len(run) for run in re.findall(r"`+", text)), default=0) + 1)
    padding = " " if text.startswith("`") or text.endswith("`") else ""
    return f"{fence}{padding}{text}{padding}{fence}"


def _frontmatter(front: dict[str, object]) -> list[str]:
    return ["---", *(f"{k}: {json.dumps(v, ensure_ascii=False)}" for k, v in front.items()), "---", ""]


def _link(label: str, href: str) -> str:
    if re.search(r"[\s()<>]", href):
        href = f"<{href}>"
    return f"[{escape_label(label)}]({href})"


def _block(block: Block, links: list[Link], images: list[ImageRef]) -> list[tuple[str, list[str]]]:
    """The block's lines, each with the model texts whose links and images it shows."""

    def inline(text: str) -> str:
        return _inline(text, links, images)

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
                for line, sources in _block(child, links, images):
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
                cells = [[_inline_html(c, links, images) for c in r] for r in block.rows]
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


def _href(link: Link) -> str | None:
    """Where a rendered link leads: its Locator, or its URL. Other links render as their label."""
    if link.status == "resolved":
        return link.target
    if link.status == "external":
        return link.href
    return None


def _inline(text: str, links: list[Link], images: list[ImageRef]) -> str:
    def markdown(label: str, index: int) -> str:
        href = _href(links[index])
        return label if href is None else _link(label, href)

    def image(_: str, index: int) -> str:
        ref = images[index]
        return f"!{_link(ref.label, ref.file)}" if ref.file else _missing(ref)

    # A rendered image is no link span, so the link spans are replaced after the image spans; the
    # formulas come last, so their TeX is never read as a span.
    return replace_math(replace_links(replace_images(text, image), markdown), tex_delimited)


def _inline_html(text: str, links: list[Link], images: list[ImageRef]) -> str:
    anchors: list[str] = []

    def placeholder(label: str, index: int) -> str:
        href = _href(links[index])
        label = html.escape(label, quote=False)
        anchors.append(label if href is None else f'<a href="{html.escape(href)}">{label}</a>')
        return f"\x00{len(anchors) - 1}\x00"

    def image(_: str, index: int) -> str:
        ref = images[index]
        if ref.file:
            anchors.append(f'<img src="{html.escape(ref.file)}" alt="{html.escape(ref.label)}">')
        else:
            anchors.append(html.escape(_missing(ref), quote=False))
        return f"\x00{len(anchors) - 1}\x00"

    escaped = html.escape(replace_links(replace_images(text, image), placeholder), quote=False)
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
