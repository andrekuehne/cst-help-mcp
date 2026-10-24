"""Render a Document as Markdown with frontmatter."""

from __future__ import annotations

import json
import re

from cst_help_mcp.model import Block, Document


def render_markdown(doc: Document) -> str:
    front = {
        "release": doc.release,
        "area": doc.area,
        "title": doc.title,
        "source": doc.source_path,
    }
    lines = ["---", *(f"{k}: {json.dumps(v, ensure_ascii=False)}" for k, v in front.items()), "---", ""]
    for section in doc.sections:
        lines.extend(f'<a id="{anchor}"></a>' for anchor in section.anchors)
        for block in section.blocks:
            lines.extend(_block(block))
            lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def _block(block: Block) -> list[str]:
    match block.kind:
        case "heading":
            return [f"{'#' * block.level} {block.text}"]
        case "paragraph":
            return [block.text]
        case "list":
            return [f"- {item}" for item in block.items]
        case "code" | "api_signature":
            return [_fence(block.text) + block.language, block.text, _fence(block.text)]
        case "table":
            return _table(block.rows)


def _fence(text: str) -> str:
    longest = max((len(run) for run in re.findall(r"`+", text)), default=0)
    return "`" * max(3, longest + 1)


def _table(rows: list[list[str]]) -> list[str]:
    width = max(len(r) for r in rows)
    padded = [[c.replace("|", "\\|") for c in r] + [""] * (width - len(r)) for r in rows]
    out = ["| " + " | ".join(padded[0]) + " |", "|" + "---|" * width]
    out.extend("| " + " | ".join(r) + " |" for r in padded[1:])
    return out
