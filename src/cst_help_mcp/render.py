"""Render a Document as Markdown with frontmatter."""

from __future__ import annotations

import html
import json
import re

from cst_help_mcp.model import Block, Document, Link, NavNode, escape_label, replace_links


def render_markdown(doc: Document) -> str:
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
    lines = _frontmatter(front)
    for section in doc.sections:
        lines.extend(f'<a id="{anchor}"></a>' for anchor in section.anchors)
        for block in section.blocks:
            lines.extend(_block(block, doc.links))
            lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


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


def _frontmatter(front: dict[str, object]) -> list[str]:
    return ["---", *(f"{k}: {json.dumps(v, ensure_ascii=False)}" for k, v in front.items()), "---", ""]


def _link(label: str, href: str) -> str:
    if re.search(r"[\s()<>]", href):
        href = f"<{href}>"
    return f"[{escape_label(label)}]({href})"


def _block(block: Block, links: list[Link]) -> list[str]:
    def inline(text: str) -> str:
        return _inline(text, links)

    match block.kind:
        case "heading":
            return [f"{'#' * block.level} {inline(block.text)}"]
        case "paragraph":
            return [inline(block.text)]
        case "list":
            return [f"- {inline(item)}" for item in block.items]
        case "note":
            return [f"> **Note:** {inline(block.text)}"]
        case "field":
            return [f"**{block.term}**", *([f": {inline(block.text)}"] if block.text else [])]
        case "code" | "api_signature":
            return [_fence(block.text) + block.language, block.text, _fence(block.text)]
        case "table":
            # Markdown cannot merge cells, so a table with merged cells stays HTML (ADR 0007).
            if block.spans:
                return _html_table([[_inline_html(c, links) for c in r] for r in block.rows], block.spans)
            return _table([[inline(c) for c in r] for r in block.rows])


def _href(link: Link) -> str | None:
    """Where a rendered link leads: its Locator, or its URL. Other links render as their label."""
    if link.status == "resolved":
        return link.target
    if link.status == "external":
        return link.href
    return None


def _inline(text: str, links: list[Link]) -> str:
    def markdown(label: str, index: int) -> str:
        href = _href(links[index])
        return label if href is None else _link(label, href)

    return replace_links(text, markdown)


def _inline_html(text: str, links: list[Link]) -> str:
    anchors: list[str] = []

    def placeholder(label: str, index: int) -> str:
        href = _href(links[index])
        label = html.escape(label, quote=False)
        anchors.append(label if href is None else f'<a href="{html.escape(href)}">{label}</a>')
        return f"\x00{len(anchors) - 1}\x00"

    escaped = html.escape(replace_links(text, placeholder), quote=False)
    return re.sub(r"\x00(\d+)\x00", lambda m: anchors[int(m[1])], escaped)


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
